"""
LS증권 WebSocket 실시간 데이터
"""
import asyncio
import json
from typing import List, Dict, Any, AsyncIterator, Optional
import websockets
from datetime import datetime, time

from utils.logger import setup_logger
from utils.exceptions import ConnectionError
from broker.ls.endpoints import LSEndpoints

logger = setup_logger(__name__)


class LSRealtimeService:
    """LS증권 실시간 데이터 서비스"""
    
    def __init__(
        self,
        api_key: str,
        access_token: str,
        paper_trading: bool = False
    ):
        """
        Args:
            api_key: API 키 (appkey)
            access_token: 액세스 토큰
            paper_trading: 모의투자 여부
        """
        self.api_key = api_key
        self.access_token = access_token
        self.paper_trading = paper_trading
        # WebSocket URL 설정 (모의투자 여부에 따라)
        self.ws_url = LSEndpoints.get_wss_url(paper_trading=paper_trading)
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        
        logger.info(f"LSRealtimeService initialized (URL: {self.ws_url})")
    
    async def connect(self) -> None:
        """WebSocket 연결"""
        try:
            logger.info(f"Connecting to WebSocket: {self.ws_url}")
            
            # websockets 라이브러리를 사용하여 WSS 연결
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers={
                    "authorization": f"Bearer {self.access_token}",
                    "appkey": self.api_key,
                    "appsecretkey": "",  # WebSocket은 appkey만 필요
                    "tr_cd": "",  # 구독 시 설정
                    "custtype": "P"  # 개인투자자
                },
                ping_interval=20,  # 20초마다 ping 전송 (연결 유지)
                ping_timeout=10,   # ping 응답 대기 시간
                close_timeout=10   # 종료 대기 시간
            )
            
            self.is_connected = True
            logger.info("WebSocket connected successfully")
        
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}", exc_info=True)
            self.is_connected = False
            raise ConnectionError(f"WebSocket connection failed: {e}")
    
    async def disconnect(self) -> None:
        """WebSocket 연결 종료"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            finally:
                self.websocket = None
        
        self.is_connected = False
        logger.info("WebSocket disconnected")
    
    async def subscribe(self, symbols: List[str]) -> None:
        """
        실시간 주식체결(S3_) 데이터 구독
        
        Args:
            symbols: 구독할 종목 코드 리스트
        """
        if not self.is_connected or not self.websocket:
            raise ConnectionError("WebSocket not connected")
        
        logger.info(f"Subscribing to symbols: {symbols} (TR: S3_)")
        
        # LS증권 실시간 주식체결 구독 메시지 전송
        for symbol in symbols:
            try:
                subscribe_msg = {
                    "header": {
                        "approval_key": self.access_token,
                        "custtype": "P",  # 개인투자자
                        "tr_type": "1",   # 실시간 데이터
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "S3_",  # 실시간 주식체결
                            "tr_key": symbol  # 종목코드
                        }
                    }
                }
                
                message = json.dumps(subscribe_msg, ensure_ascii=False)
                await self.websocket.send(message)
                logger.debug(f"Subscribed to {symbol}")
                
                # 구독 메시지 간 짧은 지연 (API 제한 고려)
                await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Failed to subscribe to {symbol}: {e}")
                continue
        
        logger.info(f"Subscribed to {len(symbols)} symbols")
    
    async def stream(self, symbols: List[str]) -> AsyncIterator[Dict[str, Any]]:
        """
        실시간 데이터 스트리밍
        
        Args:
            symbols: 구독할 종목 코드 리스트
        
        Yields:
            실시간 가격 데이터 {'symbol', 'price', 'volume', 'timestamp'}
        """
        await self.connect()
        await self.subscribe(symbols)
        
        try:
            # WebSocket 메시지 수신 루프
            while self.is_connected and self.websocket:
                try:
                    # 메시지 수신 (타임아웃: 30초)
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=30.0
                    )
                    
                    # JSON 파싱
                    data = json.loads(message)
                    
                    # 메시지 파싱 및 변환
                    parsed_data = self._parse_realtime_data(data)
                    if parsed_data:
                        yield parsed_data
                
                except asyncio.TimeoutError:
                    # 타임아웃 시 ping 전송 (연결 유지)
                    try:
                        await self.websocket.ping()
                        logger.debug("Sent ping to keep connection alive")
                    except Exception as e:
                        logger.warning(f"Ping failed: {e}")
                        break
                
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    break
                
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON message: {e}, message: {message[:100]}")
                    continue
                
                except Exception as e:
                    logger.error(f"Error receiving message: {e}", exc_info=True)
                    continue
        
        except asyncio.CancelledError:
            logger.info("Realtime stream cancelled")
        finally:
            await self.disconnect()
    
    def _parse_realtime_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        WebSocket 메시지 파싱 (S3_ 실시간 주식체결)
        
        LS증권 S3_ 메시지 형식:
        {
            "header": {
                "tr_cd": "S3_",
                "tr_key": "005930",
                ...
            },
            "body": {
                "output": {
                    "MKSC_SHRN_ISCD": "005930",  # 종목코드
                    "STCK_PRPR": "70000",        # 현재가
                    "CNTG_VOL": "123456",        # 체결량
                    "STCK_CNTG_HOUR": "143025",  # 체결시간 (HHMMSS)
                    ...
                }
            }
        }
        
        Args:
            data: 원본 WebSocket 메시지
        
        Returns:
            파싱된 데이터 {'symbol', 'price', 'volume', 'timestamp'} 또는 None
        """
        try:
            # 헤더에서 TR 코드 확인
            header = data.get("header", {})
            tr_cd = header.get("tr_cd", "")
            
            # S3_ (실시간 주식체결) 메시지만 처리
            if tr_cd != "S3_":
                return None
            
            # body에서 output 추출
            body = data.get("body", {})
            output = body.get("output", {})
            
            if not output:
                return None
            
            # 종목코드
            symbol = output.get("MKSC_SHRN_ISCD", "").strip()
            if not symbol:
                return None
            
            # 현재가 (체결가)
            price_str = output.get("STCK_PRPR", "0").strip()
            try:
                price = float(price_str)
            except (ValueError, TypeError):
                logger.warning(f"Invalid price: {price_str}")
                return None
            
            # 체결량
            volume_str = output.get("CNTG_VOL", "0").strip()
            try:
                volume = int(volume_str)
            except (ValueError, TypeError):
                logger.warning(f"Invalid volume: {volume_str}")
                volume = 0
            
            # 체결시간 파싱 (HHMMSS 형식)
            time_str = output.get("STCK_CNTG_HOUR", "").strip()
            timestamp = datetime.now()  # 기본값: 현재 시간
            
            if time_str and len(time_str) == 6:
                try:
                    hour = int(time_str[:2])
                    minute = int(time_str[2:4])
                    second = int(time_str[4:6])
                    
                    # 오늘 날짜에 시간 적용
                    today = datetime.now().date()
                    timestamp = datetime.combine(today, time(hour, minute, second))
                except (ValueError, TypeError):
                    pass  # 파싱 실패 시 현재 시간 사용
            
            # 표준 형식으로 변환하여 반환
            return {
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "timestamp": timestamp
            }
        
        except Exception as e:
            logger.warning(f"Failed to parse realtime data: {e}, data: {data}")
            return None
