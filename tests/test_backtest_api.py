"""
백테스트 API 엔드포인트 테스트
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from api.main import app
from utils.types import BacktestResult, Trade, OrderSide


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def sample_backtest_result():
    """샘플 백테스트 결과"""
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    
    return BacktestResult(
        strategy_name="TestStrategy",
        parameters={"param1": 10},
        start_date=base_time,
        end_date=base_time + timedelta(days=30),
        initial_capital=10_000_000,
        final_equity=11_000_000,
        total_return=0.10,
        mdd=0.05,
        sharpe_ratio=1.5,
        win_rate=0.6,
        profit_factor=2.0,
        total_trades=5,
        equity_curve=[10_000_000, 10_500_000, 11_000_000],
        equity_timestamps=[
            base_time,
            base_time + timedelta(days=15),
            base_time + timedelta(days=30)
        ],
        trades=[
            Trade(
                trade_id="T1",
                order_id="O1",
                symbol="005930",
                side=OrderSide.BUY,
                quantity=100,
                price=50000,
                commission=1000,
                timestamp=base_time + timedelta(days=1)
            ),
            Trade(
                trade_id="T2",
                order_id="O2",
                symbol="005930",
                side=OrderSide.SELL,
                quantity=100,
                price=55000,
                commission=1000,
                timestamp=base_time + timedelta(days=10)
            )
        ]
    )


def test_get_backtest_result_detail(client, sample_backtest_result):
    """백테스트 결과 상세 조회 API 테스트"""
    with patch('data.repository.BacktestRepository.get_backtest_result') as mock_get:
        mock_get.return_value = sample_backtest_result
        
        response = client.get("/api/backtest/results/1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["backtest_id"] == 1
        assert data["strategy_name"] == "TestStrategy"
        assert data["total_return"] == 0.10
        assert len(data["equity_curve"]) == 3
        assert len(data["equity_timestamps"]) == 3


def test_get_symbol_performances(client, sample_backtest_result):
    """종목별 성과 리스트 API 테스트"""
    with patch('data.repository.BacktestRepository.get_backtest_result') as mock_get:
        mock_get.return_value = sample_backtest_result
        
        response = client.get("/api/backtest/results/1/symbols")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # 샘플 데이터에는 005930 종목이 있어야 함
        symbols = [item["symbol"] for item in data]
        assert "005930" in symbols


def test_get_symbol_detail(client, sample_backtest_result):
    """종목 상세 정보 API 테스트"""
    with patch('data.repository.BacktestRepository.get_backtest_result') as mock_get:
        mock_get.return_value = sample_backtest_result
        
        response = client.get("/api/backtest/results/1/symbols/005930")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "005930"
        assert "metrics" in data
        assert "completed_trades" in data
        assert "all_trades" in data


def test_get_backtest_result_not_found(client):
    """존재하지 않는 백테스트 결과 조회 테스트"""
    with patch('data.repository.BacktestRepository.get_backtest_result') as mock_get:
        mock_get.return_value = None
        
        response = client.get("/api/backtest/results/999")
        
        assert response.status_code == 404


def test_compare_backtest_results(client, sample_backtest_result):
    """백테스트 비교 API 테스트"""
    with patch('data.repository.BacktestRepository.get_backtest_result') as mock_get:
        mock_get.return_value = sample_backtest_result
        
        request_data = {"backtest_ids": [1, 2]}
        response = client.post("/api/backtest/results/compare", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 2  # 2개 백테스트 결과