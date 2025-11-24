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
    """데이터 조회 Repository"""
    
    def __init__(self):
        self.storage = FileStorage()
    
    def get_ohlc(
        self,
        symbol: str,
        interval: str = "1d",
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
        try:
            data = self.storage.load(symbol, interval)
            
            if data.empty:
                return data
            
            # 날짜 필터링
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]
            
            return data
        
        except Exception as e:
            logger.error(f"Failed to get OHLC data: {e}")
            return pd.DataFrame()
    
    def get_available_symbols(self) -> List[str]:
        """
        사용 가능한 종목 목록
        
        Returns:
            종목 코드 리스트
        """
        try:
            return self.storage.list_symbols()
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            return []


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
