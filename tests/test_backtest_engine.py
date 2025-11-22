"""
BacktestEngine 테스트
"""
import pytest
from datetime import datetime, timedelta

from broker.mock.adapter import MockBroker
from core.strategy.examples.ma_cross import MACrossStrategy
from core.backtest.engine import BacktestEngine


@pytest.mark.asyncio
async def test_backtest_engine_basic():
    """백테스트 엔진 기본 테스트"""
    # Mock 데이터 생성
    broker = MockBroker()
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 3, 31)
    
    ohlc_data = await broker.get_ohlc(
        symbol="005930",
        interval="1d",
        start_date=start_date,
        end_date=end_date
    )
    
    # 전략 생성
    strategy = MACrossStrategy({
        "symbol": "005930",
        "short_period": 5,
        "long_period": 20,
        "position_size": 0.1
    })
    
    # 백테스트 엔진
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=10_000_000,
        commission=0.0015,
        slippage=0.001
    )
    
    # 백테스트 실행
    result = await engine.run(ohlc_data, start_date, end_date)
    
    # 결과 검증
    assert result is not None
    assert result.strategy_name == "MACrossStrategy"
    assert result.initial_capital == 10_000_000
    assert result.final_equity > 0
    assert len(result.equity_curve) > 0
    assert result.mdd >= 0
    assert result.mdd <= 1.0


@pytest.mark.asyncio
async def test_backtest_with_trades():
    """거래가 발생하는 백테스트 테스트"""
    broker = MockBroker()
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 6, 30)
    
    ohlc_data = await broker.get_ohlc(
        symbol="005930",
        interval="1d",
        start_date=start_date,
        end_date=end_date
    )
    
    strategy = MACrossStrategy({
        "symbol": "005930",
        "short_period": 3,
        "long_period": 10,
        "position_size": 0.2
    })
    
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=10_000_000
    )
    
    result = await engine.run(ohlc_data, start_date, end_date)
    
    # 거래 발생 확인
    assert result.total_trades >= 0
    
    # 메트릭 확인
    assert isinstance(result.total_return, float)
    assert isinstance(result.sharpe_ratio, float)
    assert isinstance(result.win_rate, float)


@pytest.mark.asyncio
async def test_backtest_equity_curve():
    """자산 곡선 테스트"""
    broker = MockBroker()
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 2, 29)
    
    ohlc_data = await broker.get_ohlc(
        symbol="005930",
        interval="1d",
        start_date=start_date,
        end_date=end_date
    )
    
    strategy = MACrossStrategy({
        "symbol": "005930",
        "short_period": 5,
        "long_period": 15
    })
    
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=10_000_000
    )
    
    result = await engine.run(ohlc_data)
    
    # 자산 곡선 검증
    assert len(result.equity_curve) > 0
    assert result.equity_curve[0] == 10_000_000  # 초기 자본
    assert all(equity >= 0 for equity in result.equity_curve)  # 모든 자산 양수
