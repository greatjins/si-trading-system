"""
시세 관련 서비스
"""
from typing import List, Optional
from datetime import datetime, timedelta

from broker.ls.client import LSClient
from broker.ls.models.market import LSOHLC, LSQuote, LSOrderbook
from utils.logger import setup_logger
from utils.types import OHLC

logger = setup_logger(__name__)


class LSMarketService:
    """LS증권 시세 서비스"""
    
    def __init__(self, client: LSClient):
        """
        Args:
            client: LS API 클라이언트
        """
        self.client = client
    
    async def get_current_price(self, symbol: str) -> LSQuote:
        """
        현재가 조회 (t1102 - 주식현재가시세조회)
        
        Args:
            symbol: 종목 코드
            
        Returns:
            현재가 정보
        """
        try:
            logger.info(f"Fetching current price for {symbol}")
            
            # LS증권 현재가 조회 API (t1102)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/market-data",
                data={
                    "t1102InBlock": {
                        "shcode": symbol
                    }
                },
                headers={
                    "tr_id": "t1102",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 응답 파싱
            output = response.get("t1102OutBlock", {})
            
            quote = LSQuote(
                symbol=symbol,
                name=output.get("hname", ""),
                price=float(output.get("price", 0)),
                change=float(output.get("change", 0)),
                change_rate=float(output.get("drate", 0)),
                volume=int(output.get("volume", 0)),
                open_price=float(output.get("open", 0)),
                high_price=float(output.get("high", 0)),
                low_price=float(output.get("low", 0)),
                prev_close=float(output.get("jnilclose", 0)),
                timestamp=datetime.now()
            )
            
            logger.info(f"Current price: {quote.price:,.0f}원")
            return quote
        
        except Exception as e:
            logger.error(f"Failed to get current price: {e}")
            raise
    
    async def get_orderbook(self, symbol: str) -> LSOrderbook:
        """
        호가 조회 (t1101 - 주식호가조회)
        
        Args:
            symbol: 종목 코드
            
        Returns:
            호가 정보
        """
        try:
            logger.info(f"Fetching orderbook for {symbol}")
            
            # LS증권 호가 조회 API (t1101)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/market-data",
                data={
                    "t1101InBlock": {
                        "shcode": symbol
                    }
                },
                headers={
                    "tr_id": "t1101",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 응답 파싱
            output = response.get("t1101OutBlock", {})
            
            # 매도/매수 호가 파싱
            ask_prices = []
            ask_volumes = []
            bid_prices = []
            bid_volumes = []
            
            for i in range(1, 11):  # 10호가
                ask_prices.append(float(output.get(f"offerho{i}", 0)))
                ask_volumes.append(int(output.get(f"offerrem{i}", 0)))
                bid_prices.append(float(output.get(f"bidho{i}", 0)))
                bid_volumes.append(int(output.get(f"bidrem{i}", 0)))
            
            orderbook = LSOrderbook(
                symbol=symbol,
                ask_prices=ask_prices,
                ask_volumes=ask_volumes,
                bid_prices=bid_prices,
                bid_volumes=bid_volumes,
                timestamp=datetime.now()
            )
            
            logger.info(f"Orderbook fetched: {len(ask_prices)} levels")
            return orderbook
        
        except Exception as e:
            logger.error(f"Failed to get orderbook: {e}")
            raise
    
    async def get_daily_ohlc(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[OHLC]:
        """
        일봉 데이터 조회 (t8410 - 일별주가)
        
        Args:
            symbol: 종목코드
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            OHLC 데이터 리스트
        """
        try:
            logger.info(f"Fetching daily OHLC for {symbol}")
            
            # LS증권 일봉 조회 API (t8410)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/market-data",
                data={
                    "t8410InBlock": {
                        "shcode": symbol,
                        "gubun": "2",  # 1:기간, 2:개수
                        "qrycnt": 100,  # 조회개수
                        "sdate": start_date.strftime("%Y%m%d"),
                        "edate": end_date.strftime("%Y%m%d"),
                        "comp_yn": "N"  # 압축여부
                    }
                },
                headers={
                    "tr_id": "t8410",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # OHLC 데이터 파싱
            ohlc_list = []
            for item in response.get("t8410OutBlock1", []):
                ohlc = OHLC(
                    symbol=symbol,
                    timestamp=datetime.strptime(item.get("date", ""), "%Y%m%d"),
                    open=float(item.get("open", 0)),
                    high=float(item.get("high", 0)),
                    low=float(item.get("low", 0)),
                    close=float(item.get("close", 0)),
                    volume=int(item.get("jdiff_vol", 0))
                )
                ohlc_list.append(ohlc)
            
            logger.info(f"Fetched {len(ohlc_list)} OHLC records")
            return ohlc_list
        
        except Exception as e:
            logger.error(f"Failed to get daily OHLC: {e}")
            raise
    
    async def get_minute_ohlc(
        self,
        symbol: str,
        interval: int,  # 1, 5, 10, 30, 60
        count: int = 100
    ) -> List[OHLC]:
        """
        분봉 데이터 조회 (t8412 - 분별주가)
        
        Args:
            symbol: 종목코드
            interval: 분봉 간격 (1, 5, 10, 30, 60)
            count: 조회 개수
        
        Returns:
            OHLC 데이터 리스트
        """
        try:
            logger.info(f"Fetching {interval}min OHLC for {symbol}")
            
            # LS증권 분봉 조회 API (t8412)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/market-data",
                data={
                    "t8412InBlock": {
                        "shcode": symbol,
                        "ncnt": interval,  # 분간격
                        "qrycnt": count,  # 조회개수
                        "nday": 1,  # 조회일수
                        "comp_yn": "N"
                    }
                },
                headers={
                    "tr_id": "t8412",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # OHLC 데이터 파싱
            ohlc_list = []
            for item in response.get("t8412OutBlock1", []):
                # 날짜+시간 파싱
                date_str = item.get("date", "")
                time_str = item.get("time", "")
                timestamp = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M")
                
                ohlc = OHLC(
                    symbol=symbol,
                    timestamp=timestamp,
                    open=float(item.get("open", 0)),
                    high=float(item.get("high", 0)),
                    low=float(item.get("low", 0)),
                    close=float(item.get("close", 0)),
                    volume=int(item.get("jdiff_vol", 0))
                )
                ohlc_list.append(ohlc)
            
            logger.info(f"Fetched {len(ohlc_list)} OHLC records")
            return ohlc_list
        
        except Exception as e:
            logger.error(f"Failed to get minute OHLC: {e}")
            raise
    
    async def search_symbol(self, keyword: str) -> List[dict]:
        """
        종목 검색
        
        Args:
            keyword: 검색 키워드
            
        Returns:
            종목 목록
        """
        try:
            logger.info(f"Searching symbol: {keyword}")
            
            # TODO: LS증권 종목 검색 API 구현
            # 일반적으로 t8436 (주식종목조회) 사용
            
            logger.warning("Symbol search not implemented yet")
            return []
        
        except Exception as e:
            logger.error(f"Failed to search symbol: {e}")
            raise
