"""
시세 관련 서비스
"""
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio

from broker.ls.client import LSClient
from broker.ls.models.market import LSOHLC, LSQuote, LSOrderbook, LSFinancialInfo
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
    
    async def get_top_change_rate_stocks(
        self,
        gubun1: str = "0",      # 0:전체, 1:코스피, 2:코스닥
        gubun2: str = "0",      # 0:상승률, 1:하락률, 2:보합
        gubun3: str = "0",      # 0:당일, 1:전일
        count: int = 200
    ) -> List[dict]:
        """
        등락율 상위 종목 조회 (t1441 - 등락율상위)
        
        Args:
            gubun1: 시장 구분 (0:전체, 1:코스피, 2:코스닥)
            gubun2: 상승하락 구분 (0:상승률, 1:하락률, 2:보합)
            gubun3: 당일전일 구분 (0:당일, 1:전일)
            count: 조회 개수 (연속조회로 최대 500개까지 가능)
            
        Returns:
            종목 목록 [{"symbol": "005930", "name": "삼성전자", "change_rate": 5.5}]
        """
        try:
            logger.info(f"Fetching top {count} change rate stocks (gubun1={gubun1}, gubun2={gubun2}, gubun3={gubun3})")
            
            stocks = []
            idx = 0  # 처음 조회시는 0
            tr_cont_key = ""
            
            # 연속조회로 원하는 개수만큼 가져오기
            while len(stocks) < count:
                # LS증권 등락율상위 API (t1441)
                # jc_num: 대상제외값 (비트 OR 연산)
                # - 거래정지: 0x00000200 (512)
                # - 정리매매: 0x01000000 (16777216)
                # - 불성실공시: 0x80000000 (2147483648)
                jc_num = 512 + 16777216 + 2147483648  # = 2164260928
                
                # jc_num2: 대상제외2
                # - 상장지수펀드(ETF): 1
                # - 선박투자회사: 2
                # - 스펙: 4
                # - ETN: 8
                jc_num2 = 1 + 2 + 4 + 8  # = 15
                
                response = await self.client.request(
                    method="POST",
                    endpoint="/stock/high-item",
                    data={
                        "t1441InBlock": {
                            "gubun1": gubun1,      # 0:전체, 1:코스피, 2:코스닥
                            "gubun2": gubun2,      # 0:상승률, 1:하락률, 2:보합
                            "gubun3": gubun3,      # 0:당일, 1:전일
                            "jc_num": jc_num,      # 대상제외
                            "sprice": 0,           # 시작가격 (현재가 >= sprice)
                            "eprice": 0,           # 종료가격 (현재가 <= eprice)
                            "volume": 0,           # 거래량 (거래량 >= volume)
                            "idx": int(idx),       # 숫자 타입으로 변환
                            "jc_num2": jc_num2,    # 대상제외2
                            "exchgubun": "U"       # K:KRX, N:NXT, U:통합
                        }
                    },
                    headers={
                        "content-type": "application/json; charset=utf-8",
                        "tr_cd": "t1441",
                        "tr_cont": "Y" if idx > 0 else "N",  # 연속거래 여부
                        "tr_cont_key": tr_cont_key,          # 연속거래 Key
                        "custtype": "P"
                    }
                )
                
                # 종목 리스트 파싱
                items = response.get("t1441OutBlock1", [])
                if not items:
                    logger.info(f"No more data available. Total fetched: {len(stocks)}")
                    break
                
                for item in items:
                    if len(stocks) >= count:
                        break
                    
                    stocks.append({
                        "symbol": item.get("shcode", ""),
                        "name": item.get("hname", ""),
                        "price": float(item.get("price", 0)),
                        "sign": item.get("sign", ""),
                        "change": float(item.get("change", 0)),
                        "change_rate": float(item.get("diff", 0)),  # 등락율 (diff)
                        "volume": int(item.get("volume", 0)),
                        "volume_amount": int(item.get("value", 0)),  # 거래대금
                        "open": float(item.get("open", 0)),
                        "high": float(item.get("high", 0)),
                        "low": float(item.get("low", 0)),
                        "offer_ho1": float(item.get("offerho1", 0)),  # 매도호가
                        "bid_ho1": float(item.get("bidho1", 0)),      # 매수호가
                        "jnildiff": float(item.get("jnildiff", 0)),   # 전일등락율
                        "market_cap": int(item.get("total", 0))       # 시가총액
                    })
                
                # 다음 페이지 인덱스 (OutBlock에서 가져오기)
                out_block = response.get("t1441OutBlock", {})
                next_idx = int(out_block.get("idx", 0))
                
                # 연속키 업데이트 (응답 헤더에서 가져오기)
                # 실제 응답 구조에 따라 조정 필요
                tr_cont_key = response.get("tr_cont_key", "")
                
                if next_idx == 0 or next_idx == idx:
                    logger.info(f"No more pages. Total fetched: {len(stocks)}")
                    break
                
                idx = next_idx
                logger.info(f"Fetched {len(stocks)} stocks so far, continuing...")
                
                # Rate Limit
                await asyncio.sleep(1.1)
            
            logger.info(f"Fetched {len(stocks)} top change rate stocks")
            return stocks
        
        except Exception as e:
            logger.error(f"Failed to get top change rate stocks: {e}")
            raise
    
    async def get_financial_info(self, symbol: str) -> LSFinancialInfo:
        """
        종목 재무 정보 조회 (t3320 - FNG_요약)
        
        Args:
            symbol: 종목 코드 (6자리)
            
        Returns:
            재무 정보
        """
        try:
            logger.info(f"Fetching financial info for {symbol}")
            
            # 종목코드는 6자리 (A 접두사 없이)
            # 문서 샘플: "001200" (6자리)
            gicode = symbol if len(symbol) == 6 else symbol[1:]
            
            # LS증권 재무정보 조회 API (t3320)
            # 엔드포인트: /stock/investinfo (투자정보)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/investinfo",
                data={
                    "t3320InBlock": {
                        "gicode": gicode
                    }
                },
                headers={
                    "content-type": "application/json; charset=utf-8",
                    "tr_cd": "t3320",
                    "tr_cont": "N",
                    "tr_cont_key": "",
                    "custtype": "P",
                    "mac_address": ""
                }
            )
            
            # 기본 정보 파싱
            out_block = response.get("t3320OutBlock", {})
            
            # 재무 지표 파싱
            out_block1 = response.get("t3320OutBlock1", {})
            
            financial_info = LSFinancialInfo(
                symbol=symbol,
                company=out_block.get("company", ""),
                market=out_block.get("sijangcd", ""),
                market_name=out_block.get("marketnm", ""),
                
                # 주식 정보
                price=float(out_block.get("price", 0)),
                prev_close=float(out_block.get("jnilclose", 0)),
                market_cap=float(out_block.get("sigavalue", 0)),
                shares=float(out_block.get("gstock", 0)),
                capital=float(out_block.get("capital", 0)),
                par_value=float(out_block.get("lstprice", 0)),
                
                # 재무 지표
                per=float(out_block1.get("per", 0)) if out_block1.get("per") else None,
                eps=float(out_block1.get("eps", 0)) if out_block1.get("eps") else None,
                pbr=float(out_block1.get("pbr", 0)) if out_block1.get("pbr") else None,
                bps=float(out_block1.get("bps", 0)) if out_block1.get("bps") else None,
                roa=float(out_block1.get("roa", 0)) if out_block1.get("roa") else None,
                roe=float(out_block1.get("roe", 0)) if out_block1.get("roe") else None,
                
                # 추가 지표
                sps=float(out_block1.get("sps", 0)) if out_block1.get("sps") else None,
                cps=float(out_block1.get("cps", 0)) if out_block1.get("cps") else None,
                ebitda=float(out_block1.get("ebitda", 0)) if out_block1.get("ebitda") else None,
                ev_ebitda=float(out_block1.get("evebitda", 0)) if out_block1.get("evebitda") else None,
                peg=float(out_block1.get("peg", 0)) if out_block1.get("peg") else None,
                
                # 배당 정보
                dividend=float(out_block.get("cashsis", 0)) if out_block.get("cashsis") else None,
                dividend_yield=float(out_block.get("cashrate", 0)) if out_block.get("cashrate") else None,
                
                # 외국인 정보
                foreign_ratio=float(out_block.get("foreignratio", 0)) if out_block.get("foreignratio") else None,
                
                # 결산 정보
                fiscal_year=out_block.get("gsyyyy", ""),
                fiscal_month=out_block.get("gsmm", ""),
                fiscal_ym=out_block.get("gsym", ""),
                
                # 기타
                group_name=out_block.get("grdnm", ""),
                homepage=out_block.get("homeurl", ""),
                address=out_block.get("baddress", ""),
                tel=out_block.get("btelno", "")
            )
            
            logger.info(f"Financial info fetched: PER={financial_info.per}, PBR={financial_info.pbr}, ROE={financial_info.roe}")
            return financial_info
        
        except Exception as e:
            logger.error(f"Failed to get financial info: {e}")
            raise
    
    async def get_server_time(self) -> datetime:
        """
        서버 시간 조회 (t0167 - 서버시간조회)
        
        Returns:
            서버 시간 (datetime 객체)
        """
        try:
            logger.info("Fetching server time (t0167)")
            
            # LS증권 서버시간조회 API (t0167)
            response = await self.client.request(
                method="POST",
                endpoint="/etc/time-search",
                data={
                    "t0167InBlock": {
                        "id": ""  # id 필드 (8자리, 공백 가능)
                    }
                },
                headers={
                    "tr_cd": "t0167",
                    "tr_cont": "N",
                    "tr_cont_key": "",
                    "mac_address": "",
                    "custtype": "P"
                }
            )
            
            # 응답 파싱
            output = response.get("t0167OutBlock", {})
            date_str = output.get("dt", "")  # YYYYMMDD
            time_str = output.get("time", "")  # HHMMSSssssss (12자리)
            
            if not date_str or not time_str:
                raise ValueError("서버 시간 응답이 올바르지 않습니다")
            
            # 시간 파싱 (HHMMSSssssss -> HHMMSS만 사용)
            hour = int(time_str[:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])
            
            # 날짜 파싱 (YYYYMMDD)
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            
            # 서버 시간 생성 (KST)
            from datetime import timezone, timedelta
            kst = timezone(timedelta(hours=9))
            server_time = datetime(year, month, day, hour, minute, second, tzinfo=kst)
            
            logger.info(f"Server time: {server_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            return server_time
        
        except Exception as e:
            logger.error(f"Failed to get server time: {e}")
            raise