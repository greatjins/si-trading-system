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
    equity_timestamps = Column(JSON, nullable=True)  # 자산 곡선 타임스탬프
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
    """
    전략 빌더 테이블 (노코드 전략)
    
    config_json 필드 구조:
    {
        "indicators": [
            {
                "type": "technical" | "ict",
                "name": "rsi" | "ma" | "fvg" | "liquidity" | "order_block" | "mss" | "bos",
                "parameters": {
                    "period": 14,
                    "lookback": 20,
                    ...
                }
            }
        ],
        "conditions": {
            "buy": [
                {
                    "id": "condition_1",
                    "type": "indicator" | "price" | "volume" | "ict",
                    "indicator": "rsi" | "fvg" | "liquidity" | ...,
                    "operator": ">" | "<" | ">=" | "<=" | "==" | "in_range" | "in_gap" | "in_zone",
                    "value": 70 | "bullish" | {...},
                    "period": 14,
                    ...
                }
            ],
            "sell": [...]
        },
        "ict_config": {
            "fvg": {
                "enabled": true,
                "min_gap_size": 0.002,
                "check_filled": true
            },
            "liquidity_zones": {
                "enabled": true,
                "period": 20,
                "tolerance": 0.001
            },
            "order_block": {
                "enabled": true,
                "lookback": 20,
                "volume_multiplier": 1.5
            },
            "mss_bos": {
                "enabled": true,
                "swing_lookback": 5
            }
        },
        "parameters": {
            "timeframe": "1m" | "5m" | "1d",
            "lookback_period": 100,
            ...
        },
        "stock_selection": {...},
        "entry_strategy": {...},
        "position_management": {...},
        "risk_management": {...}
    }
    """
    __tablename__ = "strategy_builder"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)  # 전략 빌더 설정 (JSON) - 기존 호환성 유지
    config_json = Column(JSON, nullable=True)  # 구조화된 전략 설정 (지표, 조건, ICT 등)
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
    
    # 가격 정보
    current_price = Column(Float, nullable=True)
    volume_amount = Column(BigInteger, nullable=True)  # 거래대금 (BIGINT)
    high_52w = Column(Float, nullable=True)  # 52주 최고가
    low_52w = Column(Float, nullable=True)   # 52주 최저가
    price_position = Column(Float, nullable=True)  # 현재가 / 52주 최고가
    
    # 재무 지표 (t3320)
    market_cap = Column(Float, nullable=True)  # 시가총액
    shares = Column(Float, nullable=True)  # 주식수
    per = Column(Float, nullable=True)  # PER
    pbr = Column(Float, nullable=True)  # PBR
    eps = Column(Float, nullable=True)  # EPS
    bps = Column(Float, nullable=True)  # BPS
    roe = Column(Float, nullable=True)  # ROE
    roa = Column(Float, nullable=True)  # ROA
    
    # 추가 재무 지표
    dividend_yield = Column(Float, nullable=True)  # 배당수익률
    foreign_ratio = Column(Float, nullable=True)  # 외국인지분율
    
    # 메타 정보
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self) -> str:
        return f"<StockMaster(symbol={self.symbol}, name={self.name}, PER={self.per}, PBR={self.pbr})>"


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


class DataCollectionJobModel(Base):
    """데이터 수집 작업 테이블"""
    __tablename__ = "data_collection_jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(20), nullable=False, default="running")  # running, completed, stopped, error
    current_symbol = Column(String(100), nullable=True)
    progress = Column(Integer, default=0)
    total = Column(Integer, default=0)
    logs = Column(JSON, nullable=True)  # 로그 배열
    error = Column(Text, nullable=True)
    
    # 수집 설정
    count = Column(Integer, nullable=False)
    days = Column(Integer, nullable=False)
    strategy = Column(String(20), nullable=False)
    volume_ratio = Column(Float, nullable=True)
    
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<DataCollectionJob(id={self.id}, status={self.status}, progress={self.progress}/{self.total})>"


class LiveTradeModel(Base):
    """실전 거래 내역 테이블 (backtest_id는 NULL)"""
    __tablename__ = "live_trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, nullable=False, index=True)  # StrategyBuilderModel.id 또는 전략 ID
    user_id = Column(Integer, nullable=False, index=True)
    trade_id = Column(String(100), nullable=False, unique=True)
    order_id = Column(String(100), nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, nullable=False)
    slippage = Column(Float, nullable=True)  # 실제 슬리피지 (선택적)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self) -> str:
        return f"<LiveTrade(id={self.id}, {self.side} {self.quantity} {self.symbol} @ {self.price})>"


class StrategyPerformanceModel(Base):
    """전략별 실시간 성과 추적 테이블"""
    __tablename__ = "strategy_performance"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, nullable=False, index=True)  # StrategyBuilderModel.id
    user_id = Column(Integer, nullable=False, index=True)
    
    # 성과 지표
    total_return = Column(Float, nullable=False, default=0.0)  # 총 수익률
    daily_return = Column(Float, nullable=True)  # 일일 수익률
    total_trades = Column(Integer, nullable=False, default=0)  # 총 거래 횟수
    win_rate = Column(Float, nullable=True)  # 승률
    profit_factor = Column(Float, nullable=True)  # 수익 팩터
    
    # 자산 정보
    initial_capital = Column(Float, nullable=False)
    current_equity = Column(Float, nullable=False)  # 현재 자산
    realized_pnl = Column(Float, nullable=False, default=0.0)  # 실현 손익
    unrealized_pnl = Column(Float, nullable=False, default=0.0)  # 미실현 손익
    
    # 최대 낙폭
    max_drawdown = Column(Float, nullable=True)
    peak_equity = Column(Float, nullable=True)  # 최고 자산
    
    # 기간 정보
    start_date = Column(DateTime, nullable=False)
    last_update = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 상태
    is_active = Column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<StrategyPerformance(strategy_id={self.strategy_id}, return={self.total_return:.2%}, trades={self.total_trades})>"


class BacktestLiveComparisonModel(Base):
    """백테스트-실전 비교 결과 테이블"""
    __tablename__ = "backtest_live_comparisons"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_id = Column(Integer, nullable=False, index=True)  # BacktestResultModel.id
    strategy_id = Column(Integer, nullable=False, index=True)  # StrategyBuilderModel.id
    user_id = Column(Integer, nullable=False, index=True)
    
    # 비교 기간
    backtest_start = Column(DateTime, nullable=False)
    backtest_end = Column(DateTime, nullable=False)
    live_start = Column(DateTime, nullable=False)
    live_end = Column(DateTime, nullable=False)
    
    # 백테스트 결과
    backtest_return = Column(Float, nullable=False)
    backtest_trades = Column(Integer, nullable=False)
    backtest_win_rate = Column(Float, nullable=True)
    
    # 실전 결과
    live_return = Column(Float, nullable=False)
    live_trades = Column(Integer, nullable=False)
    live_win_rate = Column(Float, nullable=True)
    
    # 차이 분석
    return_difference = Column(Float, nullable=False)  # 실전 - 백테스트
    trade_difference = Column(Integer, nullable=False)  # 실전 - 백테스트
    
    # 차이 원인 기여도 (%)
    slippage_contribution = Column(Float, nullable=True)  # 슬리피지로 인한 차이 기여도
    commission_contribution = Column(Float, nullable=True)  # 수수료로 인한 차이 기여도
    delay_contribution = Column(Float, nullable=True)  # 체결 지연으로 인한 차이 기여도
    liquidity_contribution = Column(Float, nullable=True)  # 유동성 문제로 인한 차이 기여도
    market_change_contribution = Column(Float, nullable=True)  # 시장 상황 변화로 인한 차이 기여도
    
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self) -> str:
        return f"<BacktestLiveComparison(id={self.id}, return_diff={self.return_difference:.2%})>"
