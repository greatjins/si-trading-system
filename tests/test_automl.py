"""
AutoML 테스트
"""
import pytest
from datetime import datetime

from broker.mock.adapter import MockBroker
from core.strategy.examples.ma_cross import MACrossStrategy
from core.automl.parameter_space import ParameterSpace
from core.automl.grid_search import GridSearch
from core.automl.random_search import RandomSearch


@pytest.mark.asyncio
async def test_parameter_space():
    """파라미터 공간 테스트"""
    space = ParameterSpace()
    
    # 파라미터 추가
    space.add_parameter("short_period", 3, 10, step=1)
    space.add_parameter("long_period", 15, 30, step=5)
    space.add_fixed_parameter("symbol", "005930")
    
    # 샘플링
    params = space.sample()
    assert "short_period" in params
    assert "long_period" in params
    assert "symbol" in params
    assert params["symbol"] == "005930"
    assert 3 <= params["short_period"] <= 10
    assert 15 <= params["long_period"] <= 30
    
    # 그리드 생성
    grid = space.get_grid()
    assert len(grid) > 0
    assert all("symbol" in p for p in grid)


@pytest.mark.asyncio
async def test_grid_search():
    """Grid Search 테스트"""
    # Mock 데이터
    broker = MockBroker()
    ohlc_data = await broker.get_ohlc(
        symbol="005930",
        interval="1d",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 3, 31)
    )
    
    # 파라미터 공간 (작은 범위)
    space = ParameterSpace()
    space.add_parameter("short_period", 3, 5, step=1)
    space.add_parameter("long_period", 10, 15, step=5)
    space.add_fixed_parameter("symbol", "005930")
    space.add_fixed_parameter("position_size", 0.1)
    
    # Grid Search
    search = GridSearch(
        strategy_class=MACrossStrategy,
        parameter_space=space,
        initial_capital=10_000_000
    )
    
    results = await search.run(ohlc_data)
    
    # 결과 검증
    assert len(results) > 0
    assert all(r.strategy_name == "MACrossStrategy" for r in results)
    
    # 최고 결과
    best = search.get_best_results(metric="sharpe_ratio", top_n=3)
    assert len(best) <= 3
    
    # 통계
    stats = search.get_statistics()
    assert "avg_return" in stats
    assert "max_sharpe" in stats


@pytest.mark.asyncio
async def test_random_search():
    """Random Search 테스트"""
    # Mock 데이터
    broker = MockBroker()
    ohlc_data = await broker.get_ohlc(
        symbol="005930",
        interval="1d",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 3, 31)
    )
    
    # 파라미터 공간
    space = ParameterSpace()
    space.add_parameter("short_period", 3, 10)
    space.add_parameter("long_period", 15, 30)
    space.add_fixed_parameter("symbol", "005930")
    space.add_fixed_parameter("position_size", 0.1)
    
    # Random Search (적은 반복)
    search = RandomSearch(
        strategy_class=MACrossStrategy,
        parameter_space=space,
        n_iterations=5,
        initial_capital=10_000_000
    )
    
    results = await search.run(ohlc_data)
    
    # 결과 검증
    assert len(results) > 0
    assert len(results) <= 5
    
    # 최고 결과
    best = search.get_best_results(metric="total_return", top_n=3)
    assert len(best) > 0
