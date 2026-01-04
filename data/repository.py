"""
데이터베이스 Repository
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import pandas as pd
import asyncio
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session

from data.models import Base, BacktestResultModel, TradeModel, StrategyConfigModel
from data.storage import FileStorage
from utils.types import BacktestResult, Trade, OHLC
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


def get_db_session() -> Session:
    """
    데이터베이스 세션 생성 (헬퍼 함수)
    
    Returns:
        SQLAlchemy Session
    """
    db_type = config.get("database.type", "sqlite")
    if db_type == "sqlite":
        db_path = config.get("database.path", "data/hts.db")
        db_url = f"sqlite:///{db_path}"
    else:
        # PostgreSQL
        host = config.get("database.host", "localhost")
        port = config.get("database.port", 5432)
        database = config.get("database.database", "hts")
        username = config.get("database.user", "hts_user")
        password = config.get("database.password", "")
        db_url = f"postgresql+pg8000://{username}:{password}@{host}:{port}/{database}"
    
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class DataRepository:
    """
    데이터 조회 Repository (통합)
    
    PostgreSQL 우선, 없으면 Parquet 파일 폴백
    """
    
    def __init__(self, use_db: bool = True):
        """
        Args:
            use_db: DB 사용 여부 (False면 파일만 사용)
        """
        self.use_db = use_db
        self.storage = FileStorage()
        
        if use_db:
            self.ohlc_repo = OHLCRepository()
        else:
            self.ohlc_repo = None
    
    def get_ohlc(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        OHLC 데이터 조회 (로컬 캐시 우선, 부족하면 브로커 API 호출)
        
        로직:
        1. 로컬 캐시(Parquet/DB)에 데이터가 있는지 확인
        2. 데이터가 없거나 부족할 경우, broker/ls/client.py를 사용하여 API 호출
           - 일봉: TR 't8413'
           - 60분봉: TR 't8410'
        3. API로부터 받은 JSON 응답을 시스템 표준 스키마로 변환
        4. 변환된 데이터를 Parquet 파일로 즉시 저장(Caching)한 뒤 DataFrame 반환
        5. LS증권 API의 초당 호출 제한을 고려한 지연 로직 포함
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격 ("1d": 일봉, "60m": 60분봉)
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            OHLC DataFrame (columns: open, high, low, close, volume, index: timestamp)
        """
        try:
            # 기본 날짜 설정 (없으면 최근 1년)
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=365)
            
            # 1. 로컬 캐시 확인: DB에서 조회 시도
            cached_data = None
            if self.use_db and self.ohlc_repo:
                cached_data = self.ohlc_repo.get_ohlc(symbol, interval, start_date, end_date)
                if not cached_data.empty:
                    # 요청한 날짜 범위의 데이터가 충분한지 확인
                    if cached_data.index.min() <= start_date and cached_data.index.max() >= end_date:
                        logger.debug(f"Loaded {len(cached_data)} records from DB: {symbol}")
                        return cached_data
            
            # 2. 로컬 캐시 확인: Parquet 파일에서 조회 시도
            if cached_data is None or cached_data.empty:
                cached_data = self.storage.load(symbol, interval)
                
                # 날짜 필터링
                if not cached_data.empty:
                    if start_date:
                        cached_data = cached_data[cached_data.index >= start_date]
                    if end_date:
                        cached_data = cached_data[cached_data.index <= end_date]
                    
                    # 요청한 날짜 범위의 데이터가 충분한지 확인
                    if not cached_data.empty:
                        if cached_data.index.min() <= start_date and cached_data.index.max() >= end_date:
                            logger.debug(f"Loaded {len(cached_data)} records from file: {symbol}")
                            return cached_data
            
            # 3. 데이터가 없거나 부족하면 브로커 API 호출
            logger.info(f"Cache miss or insufficient data for {symbol} ({interval}), fetching from broker API...")
            
            # 비동기 브로커 API 호출
            ohlc_list = self._fetch_from_ls_api(symbol, interval, start_date, end_date)
            
            if not ohlc_list:
                logger.warning(f"No data fetched from broker API for {symbol}")
                # 캐시된 데이터가 있으면 반환
                if cached_data is not None and not cached_data.empty:
                    return cached_data
                return pd.DataFrame()
            
            # 4. OHLC 리스트를 DataFrame으로 변환 (표준 스키마)
            data = pd.DataFrame([
                {
                    'timestamp': ohlc.timestamp,
                    'open': ohlc.open,
                    'high': ohlc.high,
                    'low': ohlc.low,
                    'close': ohlc.close,
                    'volume': ohlc.volume
                }
                for ohlc in ohlc_list
            ])
            
            if data.empty:
                # 캐시된 데이터가 있으면 반환
                if cached_data is not None and not cached_data.empty:
                    return cached_data
                return pd.DataFrame()
            
            # timestamp를 인덱스로 설정
            data.set_index('timestamp', inplace=True)
            
            # 날짜 필터링
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]
            
            # 5. Parquet 파일에 즉시 저장 (Caching)
            try:
                # 비동기 저장을 동기로 래핑
                self._save_to_parquet(symbol, interval, ohlc_list)
                logger.info(f"Saved {len(ohlc_list)} OHLC records to Parquet: {symbol}")
            except Exception as e:
                logger.warning(f"Failed to save to Parquet: {e}")
            
            # DB에 저장 시도 (선택적)
            if self.use_db and self.ohlc_repo and not data.empty:
                try:
                    self._save_to_db(symbol, interval, ohlc_list)
                except Exception as e:
                    logger.warning(f"Failed to save to DB: {e}")
            
            logger.info(f"Loaded {len(data)} records from broker API: {symbol}")
            return data
        
        except Exception as e:
            logger.error(f"Failed to get OHLC data: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _fetch_from_ls_api(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[OHLC]:
        """
        LS증권 API에서 OHLC 데이터 가져오기 (동기 래퍼)
        
        - 일봉: TR 't8413' 사용
        - 60분봉: TR 't8410' 사용
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격 ("1d": 일봉, "60m": 60분봉)
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            OHLC 데이터 리스트
        """
        async def _async_fetch():
            try:
                from broker.ls.client import LSClient
                import asyncio
                
                # LSClient 초기화 및 연결
                async with LSClient() as client:
                    # interval에 따라 TR 코드 결정
                    if interval == "1d":
                        # 일봉: TR 't8413'
                        tr_id = "t8413"
                        tr_in_block = "t8413InBlock"
                        tr_out_block = "t8413OutBlock1"
                        
                        # 일봉 요청 파라미터
                        request_data = {
                            tr_in_block: {
                                "shcode": symbol,
                                "gubun": "2",  # 2:일봉
                                "qrycnt": 500,  # 최대 조회 개수
                                "sdate": start_date.strftime("%Y%m%d"),
                                "edate": end_date.strftime("%Y%m%d"),
                                "cts_date": "",
                                "comp_yn": "N",  # 압축 여부
                                "sujung": "Y",  # 수정주가 여부
                                "exchgubun": "U"  # U:통합
                            }
                        }
                    elif interval == "60m":
                        # 60분봉: TR 't8410'
                        tr_id = "t8410"
                        tr_in_block = "t8410InBlock"
                        tr_out_block = "t8410OutBlock1"
                        
                        # 60분봉 요청 파라미터
                        # 분봉은 날짜 범위 대신 개수 기반 조회
                        days_diff = (end_date - start_date).days
                        qrycnt = min(days_diff * 6, 500)  # 하루 최대 6개 (9:00-15:30, 60분 간격)
                        
                        request_data = {
                            tr_in_block: {
                                "shcode": symbol,
                                "ncnt": 60,  # 60분봉
                                "qrycnt": qrycnt,
                                "nday": "1",  # 조회영업일수
                                "sdate": start_date.strftime("%Y%m%d"),
                                "stime": "0900",  # 시작시간
                                "edate": end_date.strftime("%Y%m%d"),
                                "etime": "1530",  # 종료시간
                                "cts_date": "",
                                "cts_time": "",
                                "comp_yn": "N",
                                "exchgubun": "U"
                            }
                        }
                    else:
                        logger.error(f"Unsupported interval: {interval}. Only '1d' and '60m' are supported.")
                        return []
                    
                    # API 호출
                    response = await client.request(
                        method="POST",
                        endpoint="/stock/chart",
                        data=request_data,
                        headers={
                            "tr_id": tr_id,
                            "tr_cont": "N",
                            "custtype": "P"
                        }
                    )
                    
                    # 5. LS증권 API 호출 제한 고려 (초당 1건)
                    await asyncio.sleep(1.1)
                    
                    # JSON 응답을 표준 스키마로 변환
                    ohlc_list = []
                    items = response.get(tr_out_block, [])
                    
                    logger.info(f"Fetched {len(items)} records from LS API (TR: {tr_id})")
                    
                    for item in items:
                        try:
                            # 일봉과 60분봉의 필드명이 다를 수 있으므로 처리
                            if interval == "1d":
                                # 일봉 필드명 (예상)
                                date_str = item.get("date", "")
                                timestamp = datetime.strptime(date_str, "%Y%m%d")
                                open_price = float(item.get("open", 0))
                                high_price = float(item.get("high", 0))
                                low_price = float(item.get("low", 0))
                                close_price = float(item.get("close", 0))
                                volume = int(item.get("jdiff_vol", item.get("volume", 0)))
                            else:  # 60분봉
                                # 60분봉 필드명 (예상)
                                date_str = item.get("date", "")
                                time_str = item.get("time", "0000")
                                timestamp = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M")
                                open_price = float(item.get("open", 0))
                                high_price = float(item.get("high", 0))
                                low_price = float(item.get("low", 0))
                                close_price = float(item.get("close", 0))
                                volume = int(item.get("jdiff_vol", item.get("volume", 0)))
                            
                            # 표준 OHLC 객체 생성
                            ohlc = OHLC(
                                symbol=symbol,
                                timestamp=timestamp,
                                open=open_price,
                                high=high_price,
                                low=low_price,
                                close=close_price,
                                volume=volume
                            )
                            ohlc_list.append(ohlc)
                        except Exception as e:
                            logger.warning(f"Failed to parse OHLC item: {e}, item: {item}")
                            continue
                    
                    return ohlc_list
                    
            except Exception as e:
                logger.error(f"Failed to fetch from LS API: {e}", exc_info=True)
                return []
        
        try:
            # 기존 이벤트 루프가 있으면 사용, 없으면 새로 생성
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _async_fetch())
                        return future.result()
                else:
                    return loop.run_until_complete(_async_fetch())
            except RuntimeError:
                # 이벤트 루프가 없으면 새로 생성
                return asyncio.run(_async_fetch())
        except Exception as e:
            logger.error(f"Error in _fetch_from_ls_api: {e}", exc_info=True)
            return []
    
    def _save_to_db(
        self,
        symbol: str,
        interval: str,
        ohlc_list: List[OHLC]
    ):
        """
        DB에 OHLC 데이터 저장 (동기 래퍼)
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격
            ohlc_list: OHLC 데이터 리스트
        """
        if not self.use_db or not self.ohlc_repo:
            return
        
        async def _async_save():
            try:
                saved_count = await self.ohlc_repo.save_ohlc_batch(ohlc_list, interval)
                logger.info(f"Saved {saved_count} OHLC records to DB: {symbol}")
            except Exception as e:
                logger.error(f"Failed to save to DB: {e}", exc_info=True)
        
        try:
            # 기존 이벤트 루프가 있으면 사용, 없으면 새로 생성
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _async_save())
                        future.result()
                else:
                    loop.run_until_complete(_async_save())
            except RuntimeError:
                # 이벤트 루프가 없으면 새로 생성
                asyncio.run(_async_save())
        except Exception as e:
            logger.error(f"Error in _save_to_db: {e}", exc_info=True)
    
    def _save_to_parquet(
        self,
        symbol: str,
        interval: str,
        ohlc_list: List[OHLC]
    ):
        """
        Parquet 파일에 OHLC 데이터 저장 (동기 래퍼)
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격
            ohlc_list: OHLC 데이터 리스트
        """
        async def _async_save():
            try:
                await self.storage.save_ohlc(symbol, interval, ohlc_list)
            except Exception as e:
                logger.error(f"Failed to save to Parquet: {e}", exc_info=True)
                raise
        
        try:
            # 기존 이벤트 루프가 있으면 사용, 없으면 새로 생성
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _async_save())
                        future.result()
                else:
                    loop.run_until_complete(_async_save())
            except RuntimeError:
                # 이벤트 루프가 없으면 새로 생성
                asyncio.run(_async_save())
        except Exception as e:
            logger.error(f"Error in _save_to_parquet: {e}", exc_info=True)
    
    def get_ohlc_as_list(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List:
        """
        OHLC 데이터를 List[OHLC] 형태로 조회 (백테스트 엔진용)
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            OHLC 객체 리스트
        """
        from utils.types import OHLC
        
        df = self.get_ohlc(symbol, interval, start_date, end_date)
        
        if df.empty:
            return []
        
        # DataFrame → List[OHLC] 변환
        ohlc_list = []
        for timestamp, row in df.iterrows():
            ohlc = OHLC(
                symbol=symbol,
                timestamp=timestamp,
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                value=float(row.get('value', row['volume'] * row['close']))
            )
            ohlc_list.append(ohlc)
        
        return ohlc_list
    
    def get_available_symbols(self) -> List[str]:
        """
        사용 가능한 종목 목록
        
        Returns:
            종목 코드 리스트
        """
        try:
            # DB에서 조회
            if self.use_db and self.ohlc_repo:
                from data.stock_filter import StockFilter
                stock_filter = StockFilter()
                return stock_filter.get_all_symbols()
            
            # 파일에서 조회
            return self.storage.list_symbols()
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            return []
    
    def get_market_snapshot(
        self,
        date: datetime,
        symbols: List[str] = None
    ) -> pd.DataFrame:
        """
        특정 날짜의 시장 스냅샷 조회 (포트폴리오 백테스트용)
        
        Args:
            date: 날짜
            symbols: 종목 리스트 (None이면 전체)
        
        Returns:
            시장 데이터 DataFrame
            - Index: symbol
            - Columns: close, volume, volume_amount, per, pbr, roe, market_cap, ...
        """
        try:
            from data.models import StockMasterModel, OHLCModel
            
            session = get_db_session()
            try:
                # 1. 활성 종목 목록 조회
                query = session.query(StockMasterModel).filter_by(is_active=True)
                
                if symbols:
                    query = query.filter(StockMasterModel.symbol.in_(symbols))
                
                stocks = query.all()
                
                if not stocks:
                    return pd.DataFrame()
                
                # 2. 해당 날짜의 OHLC 데이터 조회
                symbol_list = [s.symbol for s in stocks]
                
                # 날짜 범위: date 당일 또는 이전 최근 데이터
                ohlc_query = session.query(OHLCModel).filter(
                    OHLCModel.symbol.in_(symbol_list),
                    OHLCModel.interval == '1d',
                    OHLCModel.timestamp <= date
                )
                
                # 각 종목별 최신 데이터만 (서브쿼리)
                from sqlalchemy import func
                subquery = session.query(
                    OHLCModel.symbol,
                    func.max(OHLCModel.timestamp).label('max_timestamp')
                ).filter(
                    OHLCModel.symbol.in_(symbol_list),
                    OHLCModel.interval == '1d',
                    OHLCModel.timestamp <= date
                ).group_by(OHLCModel.symbol).subquery()
                
                ohlc_data = session.query(OHLCModel).join(
                    subquery,
                    (OHLCModel.symbol == subquery.c.symbol) &
                    (OHLCModel.timestamp == subquery.c.max_timestamp)
                ).all()
                
                # OHLC 데이터를 딕셔너리로 변환
                ohlc_dict = {
                    ohlc.symbol: {
                        'close': ohlc.close,
                        'volume': ohlc.volume,
                        'volume_amount': ohlc.close * ohlc.volume
                    }
                    for ohlc in ohlc_data
                }
                
                # 3. 종목 정보 + OHLC 데이터 결합
                data = []
                for stock in stocks:
                    ohlc_info = ohlc_dict.get(stock.symbol)
                    
                    # OHLC 데이터가 없는 종목은 제외
                    if not ohlc_info:
                        continue
                    
                    data.append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'close': ohlc_info['close'],
                        'volume': ohlc_info['volume'],
                        'volume_amount': ohlc_info['volume_amount'],
                        'per': stock.per or 0,
                        'pbr': stock.pbr or 0,
                        'roe': stock.roe or 0,
                        'roa': stock.roa or 0,
                        'market_cap': stock.market_cap or 0,
                        'dividend_yield': stock.dividend_yield or 0,
                        'price_position': stock.price_position or 0,
                    })
                
                if not data:
                    return pd.DataFrame()
                
                df = pd.DataFrame(data)
                df = df.set_index('symbol')
                
                logger.debug(f"Market snapshot for {date.date()}: {len(df)} stocks")
                return df
            finally:
                session.close()
        
        except Exception as e:
            logger.error(f"Failed to get market snapshot: {e}", exc_info=True)
            return pd.DataFrame()
    
    def get_multi_ohlc(
        self,
        symbols: List[str],
        interval: str = "1d",
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, pd.DataFrame]:
        """
        여러 종목의 OHLC 데이터를 한번에 조회 (배치)
        
        Args:
            symbols: 종목 코드 리스트
            interval: 시간 간격
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            {종목코드: OHLC DataFrame} 딕셔너리
        """
        result = {}
        
        for symbol in symbols:
            try:
                df = self.get_ohlc(symbol, interval, start_date, end_date)
                if not df.empty:
                    result[symbol] = df
            except Exception as e:
                logger.error(f"Failed to load {symbol}: {e}")
                continue
        
        return result


class OHLCRepository:
    """OHLC 데이터 저장소"""
    
    def __init__(self, db_url: str = None):
        """
        Args:
            db_url: 데이터베이스 URL (None이면 config에서 로드)
        """
        if db_url is None:
            db_type = config.get("database.type", "sqlite")
            if db_type == "sqlite":
                db_path = config.get("database.path", "data/hts.db")
                db_url = f"sqlite:///{db_path}"
            else:
                # PostgreSQL
                host = config.get("database.host", "localhost")
                port = config.get("database.port", 5432)
                database = config.get("database.database", "hts")
                username = config.get("database.user", "hts_user")
                password = config.get("database.password", "")
                db_url = f"postgresql+pg8000://{username}:{password}@{host}:{port}/{database}"
        
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # 테이블 생성
        from data.models import OHLCModel
        Base.metadata.create_all(self.engine)
        
        logger.info(f"OHLCRepository initialized: {db_url}")
    
    async def save_ohlc(self, ohlc, interval: str) -> bool:
        """
        OHLC 데이터 저장 (단일)
        
        Args:
            ohlc: OHLC 데이터
            interval: 시간 간격
        
        Returns:
            저장 성공 여부
        """
        from data.models import OHLCModel
        session = self.SessionLocal()
        
        try:
            model = OHLCModel(
                symbol=ohlc.symbol,
                interval=interval,
                timestamp=ohlc.timestamp,
                open=float(ohlc.open),
                high=float(ohlc.high),
                low=float(ohlc.low),
                close=float(ohlc.close),
                volume=int(ohlc.volume)
            )
            
            session.merge(model)  # INSERT or UPDATE
            session.commit()
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save OHLC: {e}")
            return False
        finally:
            session.close()
    
    async def save_ohlc_batch(self, ohlc_list: List, interval: str) -> int:
        """
        OHLC 데이터 배치 저장 (중복 무시)
        
        Args:
            ohlc_list: OHLC 데이터 리스트
            interval: 시간 간격
        
        Returns:
            저장된 레코드 수
        """
        from data.models import OHLCModel
        from sqlalchemy.exc import IntegrityError
        
        session = self.SessionLocal()
        
        try:
            saved_count = 0
            
            with session.no_autoflush:
                for ohlc in ohlc_list:
                    # 기존 데이터 확인
                    existing = session.query(OHLCModel).filter_by(
                        symbol=ohlc.symbol,
                        interval=interval,
                        timestamp=ohlc.timestamp
                    ).first()
                    
                    if existing:
                        # 기존 데이터 업데이트
                        existing.open = float(ohlc.open)
                        existing.high = float(ohlc.high)
                        existing.low = float(ohlc.low)
                        existing.close = float(ohlc.close)
                        existing.volume = int(ohlc.volume)
                    else:
                        # 새 데이터 추가
                        model = OHLCModel(
                            symbol=ohlc.symbol,
                            interval=interval,
                            timestamp=ohlc.timestamp,
                            open=float(ohlc.open),
                            high=float(ohlc.high),
                            low=float(ohlc.low),
                            close=float(ohlc.close),
                            volume=int(ohlc.volume)
                        )
                        session.add(model)
                        saved_count += 1
            
            session.commit()
            logger.info(f"Saved {saved_count} new OHLC records (total processed: {len(ohlc_list)})")
            return saved_count
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save OHLC batch: {e}")
            return 0
        finally:
            session.close()
    
    def get_ohlc(
        self,
        symbol: str,
        interval: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        OHLC 데이터 조회
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            OHLC DataFrame
        """
        from data.models import OHLCModel
        session = self.SessionLocal()
        
        try:
            query = session.query(OHLCModel).filter_by(
                symbol=symbol,
                interval=interval
            )
            
            if start_date:
                query = query.filter(OHLCModel.timestamp >= start_date)
            if end_date:
                query = query.filter(OHLCModel.timestamp <= end_date)
            
            query = query.order_by(OHLCModel.timestamp)
            
            results = query.all()
            
            if not results:
                return pd.DataFrame()
            
            # DataFrame 변환
            data = {
                'timestamp': [r.timestamp for r in results],
                'open': [r.open for r in results],
                'high': [r.high for r in results],
                'low': [r.low for r in results],
                'close': [r.close for r in results],
                'volume': [r.volume for r in results]
            }
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            return df
        
        except Exception as e:
            logger.error(f"Failed to get OHLC: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_latest_timestamp(self, symbol: str, interval: str) -> Optional[datetime]:
        """
        마지막 데이터 시점 조회 (증분 업데이트용)
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격
        
        Returns:
            마지막 timestamp (없으면 None)
        """
        from data.models import OHLCModel
        session = self.SessionLocal()
        
        try:
            result = session.query(OHLCModel).filter_by(
                symbol=symbol,
                interval=interval
            ).order_by(OHLCModel.timestamp.desc()).first()
            
            return result.timestamp if result else None
        finally:
            session.close()
    
    def delete_ohlc(self, symbol: str, interval: str) -> bool:
        """
        OHLC 데이터 삭제
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격
        
        Returns:
            삭제 성공 여부
        """
        from data.models import OHLCModel
        session = self.SessionLocal()
        
        try:
            count = session.query(OHLCModel).filter_by(
                symbol=symbol,
                interval=interval
            ).delete()
            
            session.commit()
            logger.info(f"Deleted {count} OHLC records for {symbol}")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete OHLC: {e}")
            return False
        finally:
            session.close()


class BacktestRepository:
    """백테스트 결과 저장소"""
    
    def __init__(self, db_url: str = None):
        """
        Args:
            db_url: 데이터베이스 URL (None이면 config에서 로드)
        """
        if db_url is None:
            db_type = config.get("database.type", "sqlite")
            if db_type == "sqlite":
                db_path = config.get("database.path", "data/hts.db")
                db_url = f"sqlite:///{db_path}"
            else:
                # PostgreSQL
                host = config.get("database.host", "localhost")
                port = config.get("database.port", 5432)
                database = config.get("database.database", "hts")
                username = config.get("database.user", "hts_user")
                password = config.get("database.password", "")
                db_url = f"postgresql+pg8000://{username}:{password}@{host}:{port}/{database}"
        
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # 테이블 생성
        Base.metadata.create_all(self.engine)
        
        logger.info(f"BacktestRepository initialized: {db_url}")
    
    def save_backtest_result(self, result: BacktestResult) -> int:
        """
        백테스트 결과 저장
        
        Args:
            result: 백테스트 결과
        
        Returns:
            저장된 레코드 ID
        """
        session = self.SessionLocal()
        
        try:
            # 백테스트 결과 저장
            # equity_timestamps를 ISO 문자열로 변환
            equity_timestamps_str = [ts.isoformat() for ts in result.equity_timestamps] if result.equity_timestamps else []
            
            model = BacktestResultModel(
                strategy_name=result.strategy_name,
                parameters=result.parameters,
                start_date=result.start_date,
                end_date=result.end_date,
                initial_capital=result.initial_capital,
                final_equity=result.final_equity,
                total_return=result.total_return,
                mdd=result.mdd,
                sharpe_ratio=result.sharpe_ratio,
                win_rate=result.win_rate,
                profit_factor=result.profit_factor,
                total_trades=result.total_trades,
                equity_curve=result.equity_curve,
                equity_timestamps=equity_timestamps_str
            )
            
            session.add(model)
            session.commit()
            session.refresh(model)
            
            backtest_id = model.id
            
            # 거래 내역 저장
            for trade in result.trades:
                trade_model = TradeModel(
                    backtest_id=backtest_id,
                    trade_id=trade.trade_id,
                    order_id=trade.order_id,
                    symbol=trade.symbol,
                    side=trade.side.value,
                    quantity=trade.quantity,
                    price=trade.price,
                    commission=trade.commission,
                    timestamp=trade.timestamp
                )
                session.add(trade_model)
            
            session.commit()
            
            logger.info(f"Backtest result saved: ID={backtest_id}, {result.total_trades} trades")
            return backtest_id
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save backtest result: {e}")
            raise
        finally:
            session.close()
    
    def get_backtest_result(self, backtest_id: int) -> Optional[BacktestResultModel]:
        """
        백테스트 결과 조회
        
        Args:
            backtest_id: 백테스트 ID
        
        Returns:
            백테스트 결과 (없으면 None)
        """
        session = self.SessionLocal()
        
        try:
            result = session.query(BacktestResultModel).filter_by(id=backtest_id).first()
            return result
        finally:
            session.close()
    
    def get_all_backtest_results(
        self,
        strategy_name: str = None,
        limit: int = 100
    ) -> List[BacktestResultModel]:
        """
        백테스트 결과 목록 조회
        
        Args:
            strategy_name: 전략 이름 필터 (None이면 전체)
            limit: 최대 개수
        
        Returns:
            백테스트 결과 리스트
        """
        session = self.SessionLocal()
        
        try:
            query = session.query(BacktestResultModel)
            
            if strategy_name:
                query = query.filter_by(strategy_name=strategy_name)
            
            results = query.order_by(desc(BacktestResultModel.created_at)).limit(limit).all()
            return results
        finally:
            session.close()
    
    def get_trades(self, backtest_id: int) -> List[TradeModel]:
        """
        백테스트의 거래 내역 조회
        
        Args:
            backtest_id: 백테스트 ID
        
        Returns:
            거래 내역 리스트
        """
        session = self.SessionLocal()
        
        try:
            trades = session.query(TradeModel).filter_by(backtest_id=backtest_id).all()
            return trades
        finally:
            session.close()
    
    def delete_backtest_result(self, backtest_id: int) -> bool:
        """
        백테스트 결과 삭제
        
        Args:
            backtest_id: 백테스트 ID
        
        Returns:
            삭제 성공 여부
        """
        session = self.SessionLocal()
        
        try:
            # 거래 내역 삭제
            session.query(TradeModel).filter_by(backtest_id=backtest_id).delete()
            
            # 백테스트 결과 삭제
            result = session.query(BacktestResultModel).filter_by(id=backtest_id).delete()
            
            session.commit()
            
            logger.info(f"Backtest result deleted: ID={backtest_id}")
            return result > 0
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete backtest result: {e}")
            return False
        finally:
            session.close()
    
    def get_best_results(
        self,
        strategy_name: str = None,
        metric: str = "total_return",
        limit: int = 10
    ) -> List[BacktestResultModel]:
        """
        최고 성과 백테스트 조회
        
        Args:
            strategy_name: 전략 이름 필터
            metric: 정렬 기준 메트릭
            limit: 최대 개수
        
        Returns:
            백테스트 결과 리스트
        """
        session = self.SessionLocal()
        
        try:
            query = session.query(BacktestResultModel)
            
            if strategy_name:
                query = query.filter_by(strategy_name=strategy_name)
            
            # 메트릭별 정렬
            if metric == "total_return":
                query = query.order_by(desc(BacktestResultModel.total_return))
            elif metric == "sharpe_ratio":
                query = query.order_by(desc(BacktestResultModel.sharpe_ratio))
            elif metric == "mdd":
                query = query.order_by(BacktestResultModel.mdd)  # MDD는 낮을수록 좋음
            
            results = query.limit(limit).all()
            return results
        finally:
            session.close()
