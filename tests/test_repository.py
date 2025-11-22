"""
Repository 테스트
"""
import pytest
from datetime import datetime
import tempfile
import os

from data.repository import BacktestRepository
from utils.types import BacktestResult, Trade, OrderSide


@pytest.fixture
def temp_db():
    """임시 데이터베이스 생성"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db_url = f"sqlite:///{path}"
    repo = BacktestRepository(db_url=db_url)
    
    yield repo
    
    # 정리 (엔진 종료 후 파일 삭제)
    repo.engine.dispose()
    try:
        os.unlink(path)
    except PermissionError:
        pass  # Windows에서 파일이 잠겨있을 수 있음


def test_save_and_load_backtest_result(temp_db):
    """백테스트 결과 저장 및 조회 테스트"""
    repo = temp_db
    
    # 백테스트 결과 생성
    result = BacktestResult(
        strategy_name="TestStrategy",
        parameters={"param1": 10, "param2": 20},
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        initial_capital=10_000_000,
        final_equity=11_000_000,
        total_return=0.10,
        mdd=0.05,
        sharpe_ratio=1.5,
        win_rate=0.6,
        profit_factor=2.0,
        total_trades=10,
        equity_curve=[10_000_000, 10_500_000, 11_000_000],
        trades=[
            Trade(
                trade_id="T1",
                order_id="O1",
                symbol="005930",
                side=OrderSide.BUY,
                quantity=10,
                price=50000,
                commission=750,
                timestamp=datetime(2024, 1, 15)
            )
        ]
    )
    
    # 저장
    backtest_id = repo.save_backtest_result(result)
    assert backtest_id > 0
    
    # 조회
    loaded = repo.get_backtest_result(backtest_id)
    assert loaded is not None
    assert loaded.strategy_name == "TestStrategy"
    assert loaded.total_return == 0.10
    assert loaded.total_trades == 10


def test_get_all_backtest_results(temp_db):
    """백테스트 결과 목록 조회 테스트"""
    repo = temp_db
    
    # 여러 결과 저장
    for i in range(3):
        result = BacktestResult(
            strategy_name=f"Strategy{i}",
            parameters={},
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=10_000_000,
            final_equity=10_000_000 + i * 100_000,
            total_return=i * 0.01,
            mdd=0.05,
            sharpe_ratio=1.0,
            win_rate=0.5,
            profit_factor=1.0,
            total_trades=5,
            equity_curve=[],
            trades=[]
        )
        repo.save_backtest_result(result)
    
    # 전체 조회
    results = repo.get_all_backtest_results()
    assert len(results) == 3


def test_get_best_results(temp_db):
    """최고 성과 백테스트 조회 테스트"""
    repo = temp_db
    
    # 다양한 수익률로 저장
    returns = [0.05, 0.15, 0.10, 0.20, 0.08]
    
    for ret in returns:
        result = BacktestResult(
            strategy_name="TestStrategy",
            parameters={},
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=10_000_000,
            final_equity=10_000_000 * (1 + ret),
            total_return=ret,
            mdd=0.05,
            sharpe_ratio=1.0,
            win_rate=0.5,
            profit_factor=1.0,
            total_trades=5,
            equity_curve=[],
            trades=[]
        )
        repo.save_backtest_result(result)
    
    # 최고 수익률 조회
    best = repo.get_best_results(metric="total_return", limit=3)
    assert len(best) == 3
    assert best[0].total_return == 0.20
    assert best[1].total_return == 0.15
    assert best[2].total_return == 0.10


def test_delete_backtest_result(temp_db):
    """백테스트 결과 삭제 테스트"""
    repo = temp_db
    
    # 저장
    result = BacktestResult(
        strategy_name="TestStrategy",
        parameters={},
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        initial_capital=10_000_000,
        final_equity=11_000_000,
        total_return=0.10,
        mdd=0.05,
        sharpe_ratio=1.0,
        win_rate=0.5,
        profit_factor=1.0,
        total_trades=5,
        equity_curve=[],
        trades=[]
    )
    
    backtest_id = repo.save_backtest_result(result)
    
    # 삭제
    success = repo.delete_backtest_result(backtest_id)
    assert success
    
    # 조회 시 없음
    loaded = repo.get_backtest_result(backtest_id)
    assert loaded is None
