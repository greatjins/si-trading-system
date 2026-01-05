"""
LS증권 WebSocket 실시간 데이터
"""
import asyncio
import json
from typing import List, Dict, Any, AsyncIterator, Optional
import websockets  # type: ignore
from datetime import datetime, time

from utils.logger import setup_logger
from utils.exceptions import ConnectionError
from broker.ls.endpoints import LSEndpoints
from broker.ls.services.market_status import MarketStatusManager

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
        
        # 장운영정보 관리자
        self.market_status_manager = MarketStatusManager()
        
        logger.info(f"LSRealtimeService initialized (URL: {self.ws_url})")
    
    async def connect(self) -> None:
        """
        WebSocket 연결
        
        'wss://openapi.ls-sec.co.kr:9443/websocket' 주소에 연결하고
        OAuth 토큰 인증 헤더를 포함합니다.
        """
        try:
            # WebSocket URL 사용 (실거래: 9443, 모의투자: 29443)
            # self.ws_url은 __init__에서 LSEndpoints.get_wss_url()로 설정됨
            logger.info(f"Connecting to WebSocket: {self.ws_url}")
            
            # websockets 라이브러리를 사용하여 WSS 연결
            # OAuth 토큰 인증 헤더 포함
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers={
                    "authorization": f"Bearer {self.access_token}",  # OAuth 토큰 인증 헤더
                    "appkey": self.api_key,
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
        
        실시간 체결가 TR인 'S3_'를 사용하여 종목 구독 메시지를 전송합니다.
        
        Args:
            symbols: 구독할 종목 코드 리스트
        """
        if not self.is_connected or not self.websocket:
            raise ConnectionError("WebSocket not connected")
        
        logger.info(f"Subscribing to symbols: {symbols} (TR: S3_)")
        
        # 장운영정보(JIF) 구독 (단축코드 없이)
        try:
            jif_subscribe_msg = {
                "header": {
                    "token": self.access_token,  # OAuth 토큰
                    "tr_type": "3"  # 3: 실시간 시세 등록
                },
                "body": {
                    "tr_cd": "JIF",  # 장운영정보 TR 코드
                    "tr_key": ""  # 단축코드 없이 (전체 장운영정보)
                }
            }
            jif_message = json.dumps(jif_subscribe_msg, ensure_ascii=False)
            await self.websocket.send(jif_message)
            logger.info("Subscribed to JIF (장운영정보)")
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to subscribe to JIF: {e}", exc_info=True)
        
        # LS증권 실시간 주식체결(S3_) 구독 메시지 전송
        for symbol in symbols:
            try:
                # LS증권 WebSocket 구독 메시지 형식
                subscribe_msg = {
                    "header": {
                        "approval_key": self.access_token,  # OAuth 토큰
                        "custtype": "P",  # 개인투자자
                        "tr_type": "1",   # 실시간 데이터
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "S3_",  # 실시간 주식체결 TR 코드
                            "tr_key": symbol  # 종목코드 (예: "005930")
                        }
                    }
                }
                
                # JSON 메시지를 문자열로 변환하여 전송
                message = json.dumps(subscribe_msg, ensure_ascii=False)
                await self.websocket.send(message)
                logger.debug(f"Subscribed to {symbol} (S3_)")
                
                # 구독 메시지 간 짧은 지연 (API 제한 고려)
                await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Failed to subscribe to {symbol}: {e}", exc_info=True)
                continue
        
        logger.info(f"Subscribed to {len(symbols)} symbols")
    
    async def stream(self, symbols: List[str]) -> AsyncIterator[Dict[str, Any]]:
        """
        실시간 데이터 스트리밍
        
        실제 수신된 바이너리/JSON 데이터를 파싱해서 
        {'symbol', 'price', 'volume', 'timestamp'} 형태의 딕셔너리를 yield 합니다.
        
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
                    # 바이너리 또는 텍스트(JSON) 데이터 모두 처리 가능
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=30.0
                    )
                    
                    # 바이너리 데이터인 경우 텍스트로 디코딩 시도
                    if isinstance(message, bytes):
                        try:
                            message = message.decode('utf-8')
                        except UnicodeDecodeError:
                            logger.warning(f"Failed to decode binary message: {message[:50]}")
                            continue
                    
                    # JSON 파싱 시도
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        # JSON이 아닌 경우, 다른 형식일 수 있으므로 로깅 후 건너뜀
                        logger.debug(f"Received non-JSON message: {message[:100]}")
                        continue
                    
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
                
                except Exception as e:
                    logger.error(f"Error receiving message: {e}", exc_info=True)
                    continue
        
        except asyncio.CancelledError:
            logger.info("Realtime stream cancelled")
        finally:
            await self.disconnect()
    
    def _parse_realtime_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        WebSocket 메시지 파싱 (S3_ 실시간 주식체결, JIF 장운영정보)
        
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
        
        JIF 메시지 형식:
        {
            "header": {
                "tr_cd": "JIF",
                ...
            },
            "body": {
                "jangubun": "1",  # 장구분 (1:코스피, 2:코스닥, 6:NXT)
                "jstatus": "21"   # 장상태
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
            
            # JIF (장운영정보) 메시지 처리
            if tr_cd == "JIF":
                body = data.get("body", {})
                jangubun = body.get("jangubun", "")
                jstatus = body.get("jstatus", "")
                
                if jangubun and jstatus:
                    self.market_status_manager.update_jif(jangubun, jstatus)
                    logger.debug(f"JIF 업데이트: jangubun={jangubun}, jstatus={jstatus}")
                
                # JIF는 가격 데이터가 아니므로 None 반환
                return None
            
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
