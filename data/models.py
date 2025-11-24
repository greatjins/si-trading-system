"""
데이터베이스 모델
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class BacktestResultModel(Base):
    """백테스트 결과 테이블"""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String(100), nullable=False)
    parameters = Column(JSON, nullable=False)
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
    equity_curve = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self) -> str:
        return f"<BacktestResult(id={self.id}, strategy={self.strategy_name}, return={self.total_return:.2%})>"


class TradeModel(Base):
    """거래 내역 테이블"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_id = Column(Integer, nullable=True)  # 백테스트 결과 ID (실전은 NULL)
    trade_id = Column(String(100), nullable=False)
    order_id = Column(String(100), nullable=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self) -> str:
        return f"<Trade(id={self.id}, {self.side} {self.quantity} {self.symbol} @ {self.price})>"


class StrategyConfigModel(Base):
    """전략 설정 테이블"""
    __tablename__ = "strategy_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    strategy_class = Column(String(100), nullable=False)
    parameters = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)  # PostgreSQL 호환
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self) -> str:
        return f"<StrategyConfig(id={self.id}, name={self.name}, active={bool(self.is_active)})>"


class StrategyBuilderModel(Base):
    """전략 빌더 테이블 (노코드 전략)"""
    __tablename__ = "strategy_builder"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)  # 전략 빌더 설정 (JSON)
    python_code = Column(Text, nullable=True)  # 생성된 Python 코드
    is_active = Column(Boolean, default=True)  # PostgreSQL 호환
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self) -> str:
        return f"<StrategyBuilder(id={self.id}, name={self.name}, user_id={self.user_id})>"
