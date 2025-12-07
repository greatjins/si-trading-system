"""
시세 관련 서비스
"""
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio

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
            
            # 응답 파싱 (t1101 정확한 필드명)
            output = response.get("t1101OutBlock", {})
            
            # 매도/매수 호가 파싱 (10호가)
            ask_prices = []
            ask_volumes = []
            bid_prices = []
            bid_volumes = []
            
            for i in range(1, 11):  # 10호가
                ask_prices.append(float(output.get(f"offerho{i}", 0)))      # 매도호가
                ask_volumes.append(int(output.get(f"offerrem{i}", 0)))      # 매도호가수량
                bid_prices.append(float(output.get(f"bidho{i}", 0)))        # 매수호가
                bid_volumes.append(int(output.get(f"bidrem{i}", 0)))        # 매수호가수량
            
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
        일봉 데이터 조회 (t8451 - 통합 주식차트 API용)
        기간을 나눠서 전체 데이터 수집 (API 제한: 약 200일)
        
        Args:
            symbol: 종목코드
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            OHLC 데이터 리스트
        """
        try:
            logger.info(f"Fetching daily OHLC for {symbol} ({start_date.date()} ~ {end_date.date()})")
            
            all_ohlc = []
            current_end = end_date
            chunk_days = 200  # 한 번에 200일씩 조회 (API 최대치)
            
            # 기간을 나눠서 조회
            while current_end >= start_date:
                current_start = max(current_end - timedelta(days=chunk_days), start_date)
                
                logger.info(f"Fetching chunk: {current_start.date()} ~ {current_end.date()}")
                
                # LS증권 일봉 조회 API (t8451)
                response = await self.client.request(
                    method="POST",
                    endpoint="/stock/chart",
                    data={
                        "t8451InBlock": {
                            "shcode": symbol,
                            "gubun": "2",  # 2:일
                            "qrycnt": 500,
                            "sdate": current_start.strftime("%Y%m%d"),
                            "edate": current_end.strftime("%Y%m%d"),
                            "cts_date": "",
                            "comp_yn": "N",
                            "sujung": "Y",
                            "exchgubun": "U"
                        }
                    },
                    headers={
                        "tr_id": "t8451",
                        "tr_cont": "N",
                        "custtype": "P"
                    }
                )
                
                # OHLC 데이터 파싱
                items = response.get("t8451OutBlock1", [])
                logger.info(f"Fetched {len(items)} records for this chunk")
                
                for item in items:
                    ohlc = OHLC(
                        symbol=symbol,
                        timestamp=datetime.strptime(item.get("date", ""), "%Y%m%d"),
                        open=float(item.get("open", 0)),
                        high=float(item.get("high", 0)),
                        low=float(item.get("low", 0)),
                        close=float(item.get("close", 0)),
                        volume=int(item.get("jdiff_vol", 0))
                    )
                    all_ohlc.append(ohlc)
                
                # 다음 청크로 이동 (하루 겹치지 않도록)
                current_end = current_start - timedelta(days=1)
                
                # 시작일에 도달하면 종료
                if current_start <= start_date:
                    break
                
                # Rate Limit
                await asyncio.sleep(1.1)
            
            # 날짜 순으로 정렬 (오래된 것부터)
            all_ohlc.sort(key=lambda x: x.timestamp)
            
            logger.info(f"Fetched {len(all_ohlc)} OHLC records total")
            return all_ohlc
        
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
        분봉 데이터 조회 (t8452 - 통합 주식차트 N분 API용)
        
        Args:
            symbol: 종목코드
            interval: 분봉 간격 (1, 5, 10, 30, 60)
            count: 조회 개수
        
        Returns:
            OHLC 데이터 리스트
        """
        try:
            logger.info(f"Fetching {interval}min OHLC for {symbol}")
            
            # LS증권 분봉 조회 API (t8452 - 통합 API용)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/chart",  # 차트 전용 엔드포인트
                data={
                    "t8452InBlock": {
                        "shcode": symbol,
                        "ncnt": interval,      # 단위(n분)
                        "qrycnt": count,       # 요청건수(최대:500)
                        "nday": "1",           # 조회영업일수(0:미사용, 1>=사용)
                        "sdate": "",           # 시작일자
                        "stime": "",           # 시작시간
                        "edate": "",           # 종료일자
                        "etime": "",           # 종료시간
                        "cts_date": "",        # 연속일자
                        "cts_time": "",        # 연속시간
                        "comp_yn": "N",        # 압축여부(N:비압축)
                        "exchgubun": "U"       # U:통합 (K:KRX, N:NXT, U:통합)
                    }
                },
                headers={
                    "tr_id": "t8452",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # OHLC 데이터 파싱 (t8452 정확한 필드명)
            ohlc_list = []
            for item in response.get("t8452OutBlock1", []):
                # 날짜+시간 파싱 (time은 10자리 문자열)
                date_str = item.get("date", "")      # "20241130"
                time_str = item.get("time", "")      # "0935000000" (10자리)
                
                # 시간은 앞 4자리만 사용 (HHMM)
                time_hhmm = time_str[:4] if len(time_str) >= 4 else "0000"
                timestamp = datetime.strptime(f"{date_str}{time_hhmm}", "%Y%m%d%H%M")
                
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
    
    async def get_all_symbols(self, market: str = "0") -> List[dict]:
        """
        전체 종목 조회 (t8436 - 주식종목조회 API용)
        
        Args:
            market: 시장 구분 (0:전체, 1:코스피, 2:코스닥)
            
        Returns:
            종목 목록 [{"symbol": "005930", "name": "삼성전자", "market": "1"}]
        """
        try:
            logger.info(f"Fetching all symbols (market={market})")
            
            # LS증권 종목 조회 API (t8436)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/etc",
                data={
                    "t8436InBlock": {
                        "gubun": market  # 0:전체, 1:코스피, 2:코스닥
                    }
                },
                headers={
                    "tr_id": "t8436",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 종목 리스트 파싱
            symbols = []
            for item in response.get("t8436OutBlock", []):
                symbols.append({
                    "symbol": item.get("shcode", ""),
                    "name": item.get("hname", ""),
                    "market": item.get("gubun", ""),  # 1:코스피, 2:코스닥
                    "prev_close": float(item.get("jnilclose", 0))
                })
            
            logger.info(f"Fetched {len(symbols)} symbols")
            return symbols
        
        except Exception as e:
            logger.error(f"Failed to get all symbols: {e}")
            raise
    
    async def get_top_volume_stocks(
        self,
        market: str = "0",
        count: int = 200
    ) -> List[dict]:
        """
        거래대금 상위 종목 조회 (t1463 - 거래대금상위)
        
        Args:
            market: 시장 구분 (0:전체, 1:코스피, 2:코스닥)
            count: 조회 개수 (연속조회로 최대 500개까지 가능)
            
        Returns:
            종목 목록 [{"symbol": "005930", "name": "삼성전자", "volume_amount": 1500000000000}]
        """
        try:
            logger.info(f"Fetching top {count} volume stocks")
            
            stocks = []
            idx = 0
            
            # 연속조회로 원하는 개수만큼 가져오기 (한 번에 50개씩)
            while len(stocks) < count:
                # LS증권 거래대금상위 API (t1463)
                # jc_num: 거래정지(512) + 정리매매(16777216) + 불성실공시(2147483648) 제외
                # jc_num2: ETF(1) + 선박투자(2) + 스펙(4) + ETN(8) 제외
                response = await self.client.request(
                    method="POST",
                    endpoint="/stock/high-item",
                    data={
                        "t1463InBlock": {
                            "gubun": "0",         # 0:전체, 1:코스피, 2:코스닥
                            "jnilgubun": "0",     # 0:당일, 1:전일
                            "jc_num": 2164260928, # 512 + 16777216 + 2147483648
                            "sprice": 0,
                            "eprice": 0,
                            "volume": 0,
                            "idx": idx,           # 연속조회용 인덱스
                            "jc_num2": 15,        # 1 + 2 + 4 + 8
                            "exchgubun": "U"      # U:통합
                        }
                    },
                    headers={
                        "tr_id": "t1463",
                        "tr_cont": "Y" if idx > 0 else "N",  # 연속조회 플래그
                        "custtype": "P"
                    }
                )
                
                # 종목 리스트 파싱
                items = response.get("t1463OutBlock1", [])
                if not items:
                    logger.info(f"No more data available. Total fetched: {len(stocks)}")
                    break
                
                for item in items:
                    if len(stocks) >= count:
                        break
                    
                    # jnilvalue는 백만원 단위로 반환됨 → 원 단위로 변환
                    volume_amount_million = int(item.get("jnilvalue", 0))
                    volume_amount = volume_amount_million * 1_000_000  # 백만원 → 원
                    
                    # 시장 구분 (t1463에는 gubun 필드가 없으므로 추정)
                    # 응답에 gubun 필드가 있으면 사용, 없으면 기본값
                    market_code = item.get("gubun", "")
                    if market_code == "1":
                        market = "KOSPI"
                    elif market_code == "2":
                        market = "KOSDAQ"
                    else:
                        # gubun 필드가 없는 경우 기본값 (나중에 개별 조회로 업데이트)
                        market = "UNKNOWN"
                    
                    stocks.append({
                        "symbol": item.get("shcode", ""),
                        "name": item.get("hname", ""),
                        "price": float(item.get("price", 0)),
                        "volume_amount": volume_amount,  # 전일거래대금 (원)
                        "volume": int(item.get("jnilvolume", 0)),  # 전일거래량
                        "market": market  # 시장 구분
                    })
                
                # 다음 페이지 인덱스 (OutBlock에서 가져오기)
                out_block = response.get("t1463OutBlock", {})
                next_idx = out_block.get("idx", 0)
                
                if next_idx == idx or next_idx == 0:
                    logger.info(f"No more pages. Total fetched: {len(stocks)}")
                    break
                
                idx = next_idx
                logger.info(f"Fetched {len(stocks)} stocks so far, continuing...")
                
                # Rate Limit
                await asyncio.sleep(1.1)
            
            logger.info(f"Fetched {len(stocks)} top volume stocks")
            return stocks
        
        except Exception as e:
            logger.error(f"Failed to get top volume stocks: {e}")
            raise
