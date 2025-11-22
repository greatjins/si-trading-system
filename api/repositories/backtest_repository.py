"""
백테스트 결과 저장소
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from utils.logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()


class BacktestResultModel(Base):
    """백테스트 결과 모델"""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False)
    symbol = Column(String, nullable=False)
    interval = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_equity = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    mdd = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    win_rate = Column(Float, nullable=False)
    profit_factor = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class BacktestRepository:
    """백테스트 결과 저장소"""
    
    def __init__(self, db_path: str = "data/hts.db"):
        """
        Args:
            db_path: 데이터베이스 경로
        """
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def save_result(self, result: dict) -> int:
        """
        백테스트 결과 저장
        
        Args:
            result: 백테스트 결과
            
        Returns:
            저장된 결과 ID
        """
        session = self.Session()
        try:
            model = BacktestResultModel(**result)
            session.add(model)
            session.commit()
            
            logger.info(f"Backtest result saved: {model.id}")
            return model.id
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save backtest result: {e}")
            raise
        
        finally:
            session.close()
    
    def get_result(self, result_id: int) -> Optional[dict]:
        """
        백테스트 결과 조회
        
        Args:
            result_id: 결과 ID
            
        Returns:
            백테스트 결과
        """
        session = self.Session()
        try:
            model = session.query(BacktestResultModel).filter_by(id=result_id).first()
            
            if not model:
                return None
            
            return {
                "id": model.id,
                "strategy_name": model.strategy_name,
                "parameters": model.parameters,
                "symbol": model.symbol,
                "interval": model.interval,
                "start_date": model.start_date,
                "end_date": model.end_date,
                "initial_capital": model.initial_capital,
                "final_equity": model.final_equity,
                "total_return": model.total_return,
                "mdd": model.mdd,
                "sharpe_ratio": model.sharpe_ratio,
                "win_rate": model.win_rate,
                "profit_factor": model.profit_factor,
                "total_trades": model.total_trades,
                "created_at": model.created_at
            }
        
        finally:
            session.close()
    
    def get_all_results(self, limit: int = 100) -> List[dict]:
        """
        모든 백테스트 결과 조회
        
        Args:
            limit: 최대 개수
            
        Returns:
            백테스트 결과 리스트
        """
        session = self.Session()
        try:
            models = session.query(BacktestResultModel)\
                .order_by(BacktestResultModel.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [
                {
                    "id": model.id,
                    "strategy_name": model.strategy_name,
                    "parameters": model.parameters,
                    "symbol": model.symbol,
                    "interval": model.interval,
                    "start_date": model.start_date,
                    "end_date": model.end_date,
                    "initial_capital": model.initial_capital,
                    "final_equity": model.final_equity,
                    "total_return": model.total_return,
                    "mdd": model.mdd,
                    "sharpe_ratio": model.sharpe_ratio,
                    "win_rate": model.win_rate,
                    "profit_factor": model.profit_factor,
                    "total_trades": model.total_trades,
                    "created_at": model.created_at
                }
                for model in models
            ]
        
        finally:
            session.close()
