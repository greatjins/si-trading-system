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
        
        'wss://openapi.ls-sec.co.kr:9443' 주소에 연결하고
        OAuth 토큰 인증 헤더를 포함합니다.
        """
        if self.is_connected and self.websocket:
            logger.warning("WebSocket already connected")
            return
        
        try:
            # websockets.connect를 사용하여 실제 LS증권 서버에 연결
            # LSEndpoints에서 URL 가져오기 (실거래: wss://openapi.ls-sec.co.kr:9443/websocket)
            ws_url = self.ws_url  # LSEndpoints.get_wss_url()로 초기화된 URL 사용
            
            logger.info(f"Connecting to LS증권 WebSocket: {ws_url}")
            
            # websockets.connect를 사용하여 LS증권 운영 서버에 연결
            # OAuth 토큰을 헤더에 포함하여 인증
            self.websocket = await websockets.connect(
                ws_url,
                extra_headers={
                    "authorization": f"Bearer {self.access_token}",  # OAuth 토큰 인증 헤더
                    "appkey": self.api_key,
                    "appsecretkey": "",  # WebSocket에서는 사용하지 않지만 일관성을 위해 포함
                    "custtype": "P"  # 개인투자자
                },
                ping_interval=20,  # 20초마다 ping 전송 (연결 유지)
                ping_timeout=10,   # ping 응답 대기 시간
                close_timeout=10   # 종료 대기 시간
            )
            
            self.is_connected = True
            logger.info(f"WebSocket connected successfully to LS증권 서버: {ws_url}")
        
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}", exc_info=True)
            self.is_connected = False
            self.websocket = None
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
        실시간 주식체결(S3_) 및 장운영정보(JIF) 구독
        
        'S3_' (주식체결) TR과 'JIF' (장운영정보) TR을 실제로 구독합니다.
        
        Args:
            symbols: 구독할 종목 코드 리스트
        """
        if not self.is_connected or not self.websocket:
            raise ConnectionError("WebSocket not connected")
        
        if not symbols:
            logger.warning("No symbols provided for subscription")
            return
        
        logger.info(f"Subscribing to symbols: {symbols} (TR: S3_, JIF)")
        
        # 1. 장운영정보(JIF) 구독 (단축코드 없이)
        try:
            jif_subscribe_msg = {
                "header": {
                    "approval_key": self.access_token,  # OAuth 토큰
                    "custtype": "P",  # 개인투자자
                    "tr_type": "3"  # 3: 실시간 시세 등록
                },
                "body": {
                    "input": {
                        "tr_id": "JIF",  # 장운영정보 TR 코드
                        "tr_key": ""  # 단축코드 없이 (전체 장운영정보)
                    }
                }
            }
            jif_message = json.dumps(jif_subscribe_msg, ensure_ascii=False)
            await self.websocket.send(jif_message)
            logger.info("Successfully subscribed to JIF (장운영정보)")
            await asyncio.sleep(0.1)  # 구독 메시지 간 지연
        except Exception as e:
            logger.error(f"Failed to subscribe to JIF: {e}", exc_info=True)
            raise
        
        # 2. 실시간 주식체결(S3_) TR을 사용하여 구독 메시지 전송
        subscribed_count = 0
        for symbol in symbols:
            try:
                # 종목코드 검증 (6자리 숫자)
                if not symbol or len(symbol) != 6 or not symbol.isdigit():
                    logger.warning(f"Invalid symbol format: {symbol}, skipping")
                    continue
                
                # LS증권 WebSocket 구독 메시지 형식 (S3_ TR 사용)
                subscribe_msg = {
                    "header": {
                        "approval_key": self.access_token,  # OAuth 토큰
                        "custtype": "P",  # 개인투자자
                        "tr_type": "1"   # 1: 실시간 데이터
                    },
                    "body": {
                        "input": {
                            "tr_id": "S3_",  # 실시간 주식체결 TR 코드
                            "tr_key": symbol  # 종목코드 (예: "005930")
                        }
                    }
                }
                
                # JSON 메시지를 문자열로 변환하여 WebSocket으로 전송
                message = json.dumps(subscribe_msg, ensure_ascii=False)
                await self.websocket.send(message)
                subscribed_count += 1
                logger.debug(f"Subscribed to {symbol} using S3_ TR")
                
                # 구독 메시지 간 짧은 지연 (API 제한 고려)
                await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Failed to subscribe to {symbol} (S3_): {e}", exc_info=True)
                continue
        
        logger.info(f"Successfully subscribed to {subscribed_count} symbols using S3_ TR and JIF")
    
    async def stream(self, symbols: List[str]) -> AsyncIterator[Dict[str, Any]]:
        """
        실시간 데이터 스트리밍
        
        실제 수신된 WebSocket 바이너리 데이터를 파싱하여 
        {'symbol', 'price', 'volume', 'status', 'timestamp'} 형태의 딕셔너리를 yield 합니다.
        
        Args:
            symbols: 구독할 종목 코드 리스트
        
        Yields:
            실시간 가격 데이터 딕셔너리:
            {
                'symbol': str,      # 종목코드 (예: "005930")
                'price': float,     # 현재가
                'volume': int,       # 체결량
                'status': str,       # 장상태 (JIF에서 받은 정보)
                'timestamp': datetime  # 체결시간
            }
        """
        await self.connect()
        await self.subscribe(symbols)
        
        try:
            # WebSocket 메시지 수신 루프 - 실제 수신된 바이너리 데이터를 파싱하여 yield
            while self.is_connected and self.websocket:
                try:
                    # 실제 WebSocket에서 바이너리 또는 텍스트 메시지 수신 (타임아웃: 30초)
                    raw_message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=30.0
                    )
                    
                    # 바이너리 데이터 처리
                    if isinstance(raw_message, bytes):
                        # 바이너리 데이터를 UTF-8로 디코딩
                        try:
                            message_text = raw_message.decode('utf-8')
                        except UnicodeDecodeError as e:
                            logger.warning(f"Failed to decode binary message: {e}, bytes: {raw_message[:50]}")
                            continue
                    else:
                        # 이미 텍스트인 경우
                        message_text = raw_message
                    
                    # JSON 파싱
                    try:
                        data = json.loads(message_text)
                    except json.JSONDecodeError as e:
                        # JSON이 아닌 경우 로깅 후 건너뜀
                        logger.debug(f"Received non-JSON message: {message_text[:100]}, error: {e}")
                        continue
                    
                    # 실제 수신된 데이터를 파싱하여 표준 형식으로 변환
                    # _parse_realtime_data가 {'symbol', 'price', 'volume', 'status', 'timestamp'} 형태로 반환
                    parsed_data = self._parse_realtime_data(data)
                    if parsed_data:
                        # 파싱된 데이터를 yield하여 스트리밍
                        yield parsed_data
                
                except asyncio.TimeoutError:
                    # 타임아웃 시 ping 전송 (연결 유지)
                    try:
                        if self.websocket:
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
        
        실제 수신된 데이터를 파싱하여 {'symbol', 'price', 'volume', 'status', 'timestamp'} 형태로 변환합니다.
        
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
                "output": {
                    "jangubun": "1",  # 장구분 (1:코스피, 2:코스닥, 6:NXT)
                    "jstatus": "21"   # 장상태
                }
            }
        }
        
        Args:
            data: 원본 WebSocket 메시지 (JSON 파싱된 딕셔너리)
        
        Returns:
            파싱된 데이터 {'symbol', 'price', 'volume', 'status', 'timestamp'} 또는 None
        """
        try:
            # 헤더에서 TR 코드 확인
            header = data.get("header", {})
            tr_cd = header.get("tr_cd", "")
            
            # JIF (장운영정보) 메시지 처리
            if tr_cd == "JIF":
                body = data.get("body", {})
                output = body.get("output", {})
                
                if not output:
                    # body에서 직접 가져오기 시도 (구버전 형식)
                    jangubun = body.get("jangubun", "")
                    jstatus = body.get("jstatus", "")
                else:
                    jangubun = output.get("jangubun", "")
                    jstatus = output.get("jstatus", "")
                
                if jangubun and jstatus:
                    self.market_status_manager.update_jif(jangubun, jstatus)
                    logger.debug(f"JIF 업데이트: jangubun={jangubun}, jstatus={jstatus}")
                    
                    # JIF 메시지도 status 정보를 포함하여 반환
                    # 표준 형식: {'symbol', 'price', 'volume', 'status', 'timestamp'}
                    return {
                        "symbol": "",  # JIF는 종목별 정보가 아님
                        "price": 0.0,
                        "volume": 0,
                        "status": jstatus,  # 장상태
                        "timestamp": datetime.now()
                    }
                
                return None
            
            # S3_ (실시간 주식체결) 메시지 처리
            if tr_cd != "S3_":
                logger.debug(f"Unknown TR code: {tr_cd}, skipping")
                return None
            
            # body에서 output 추출
            body = data.get("body", {})
            output = body.get("output", {})
            
            if not output:
                logger.warning(f"No output in S3_ message: {data}")
                return None
            
            # 종목코드 추출
            symbol = output.get("MKSC_SHRN_ISCD", "").strip()
            if not symbol:
                # tr_key에서 가져오기 시도
                symbol = header.get("tr_key", "").strip()
                if not symbol:
                    logger.warning(f"No symbol found in S3_ message: {data}")
                    return None
            
            # 현재가 (체결가) 추출 및 변환
            price_str = output.get("STCK_PRPR", "0").strip()
            try:
                price = float(price_str)
            except (ValueError, TypeError):
                logger.warning(f"Invalid price format: {price_str} for symbol {symbol}")
                return None
            
            # 체결량 추출 및 변환
            volume_str = output.get("CNTG_VOL", "0").strip()
            try:
                volume = int(volume_str) if volume_str else 0
            except (ValueError, TypeError):
                logger.debug(f"Invalid volume format: {volume_str} for symbol {symbol}, using 0")
                volume = 0
            
            # 체결시간 파싱 (HHMMSS 형식)
            time_str = output.get("STCK_CNTG_HOUR", "").strip()
            timestamp = datetime.now()  # 기본값: 현재 시간
            
            if time_str and len(time_str) >= 6:
                try:
                    hour = int(time_str[:2])
                    minute = int(time_str[2:4])
                    second = int(time_str[4:6])
                    
                    # 오늘 날짜에 시간 적용
                    today = datetime.now().date()
                    timestamp = datetime.combine(today, time(hour, minute, second))
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse time '{time_str}': {e}, using current time")
                    # 파싱 실패 시 현재 시간 사용
            
            # 장상태 정보 가져오기 (MarketStatusManager에서)
            # 현재 활성화된 시장의 status를 반환
            status_info = self.market_status_manager.get_status()
            status = status_info.get("krx_status") or status_info.get("nxt_status") or ""
            
            # 표준 형식으로 변환하여 반환 {'symbol', 'price', 'volume', 'status', 'timestamp'}
            parsed_result = {
                "symbol": symbol,
                "price": price,
                "volume": volume,  # 체결량
                "status": status,  # 장상태 정보 (jstatus)
                "timestamp": timestamp
            }
            
            logger.debug(f"Parsed realtime data: {parsed_result}")
            return parsed_result
        
        except Exception as e:
            logger.warning(f"Failed to parse realtime data: {e}, data: {data}", exc_info=True)
            return None
