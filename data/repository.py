"""
데이터베이스 Repository
"""
from typing import List, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session

from data.models import Base, BacktestResultModel, TradeModel, StrategyConfigModel
from data.storage import FileStorage
from utils.types import BacktestResult, Trade
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
        OHLC 데이터 조회 (DB 우선, 파일 폴백)
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            OHLC DataFrame
        """
        try:
            # 1. DB에서 조회 시도
            if self.use_db and self.ohlc_repo:
                data = self.ohlc_repo.get_ohlc(symbol, interval, start_date, end_date)
                if not data.empty:
                    logger.debug(f"Loaded {len(data)} records from DB: {symbol}")
                    return data
            
            # 2. 파일에서 조회 (폴백)
            data = self.storage.load(symbol, interval)
            
            if data.empty:
                return data
            
            # 날짜 필터링
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]
            
            logger.debug(f"Loaded {len(data)} records from file: {symbol}")
            return data
        
        except Exception as e:
            logger.error(f"Failed to get OHLC data: {e}")
            return pd.DataFrame()
    
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
                equity_curve=result.equity_curve
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
