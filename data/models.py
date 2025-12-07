"""
데이터베이스 모델
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Text, JSON, Boolean
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


class StockMasterModel(Base):
    """종목 마스터 테이블"""
    __tablename__ = "stock_master"
    
    symbol = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    market = Column(String(20), nullable=True)  # KOSPI, KOSDAQ
    sector = Column(String(50), nullable=True)
    current_price = Column(Float, nullable=True)
    volume_amount = Column(BigInteger, nullable=True)  # 거래대금 (BIGINT)
    high_52w = Column(Float, nullable=True)  # 52주 최고가
    low_52w = Column(Float, nullable=True)   # 52주 최저가
    price_position = Column(Float, nullable=True)  # 현재가 / 52주 최고가
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self) -> str:
        return f"<StockMaster(symbol={self.symbol}, name={self.name}, volume={self.volume_amount})>"


class StockUniverseModel(Base):
    """전략별 종목 유니버스 테이블"""
    __tablename__ = "stock_universe"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_type = Column(String(50), nullable=False)  # mean_reversion, momentum
    symbol = Column(String(20), nullable=False)
    rank = Column(Integer, nullable=True)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self) -> str:
        return f"<StockUniverse(strategy={self.strategy_type}, symbol={self.symbol}, rank={self.rank})>"


class OHLCModel(Base):
    """OHLC 데이터 테이블"""
    __tablename__ = "ohlc_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False, index=True)  # 1d, 1m, 5m, etc
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self) -> str:
        return f"<OHLC(symbol={self.symbol}, interval={self.interval}, timestamp={self.timestamp}, close={self.close})>"
