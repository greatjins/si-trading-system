"""
TradeAnalyzer 테스트
"""
import pytest
from datetime import datetime, timedelta
from typing import List

from core.backtest.trade_analyzer import TradeAnalyzer
from utils.types import Trade, CompletedTrade, SymbolPerformance, OrderSide


def create_trade(
    symbol: str, 
    side: OrderSide, 
    quantity: int, 
    price: float, 
    days_offset: int = 0,
    commission: float = 1000.0,
    base_time: datetime = None
) -> Trade:
    """테스트용 거래 생성"""
    if base_time is None:
        base_time = datetime(2024, 1, 1, 9, 0, 0)
    
    return Trade(
        trade_id=f"trade_{symbol}_{days_offset}",
        order_id=f"order_{symbol}_{days_offset}",
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        commission=commission,
        timestamp=base_time + timedelta(days=days_offset)
    )


def test_group_trades_by_symbol():
    """종목별 거래 그룹화 테스트"""
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    trades = [
        create_trade("AAPL", OrderSide.BUY, 100, 150.0, 0, base_time=base_time),
        create_trade("MSFT", OrderSide.BUY, 50, 300.0, 1, base_time=base_time),
        create_trade("AAPL", OrderSide.SELL, 100, 160.0, 2, base_time=base_time),
        create_trade("MSFT", OrderSide.SELL, 50, 310.0, 3, base_time=base_time),
    ]
    
    grouped = TradeAnalyzer.group_trades_by_symbol(trades)
    
    assert len(grouped) == 2
    assert "AAPL" in grouped
    assert "MSFT" in grouped
    assert len(grouped["AAPL"]) == 2
    assert len(grouped["MSFT"]) == 2
    
    # 시간순 정렬 확인
    aapl_trades = grouped["AAPL"]
    assert aapl_trades[0].timestamp < aapl_trades[1].timestamp


def test_match_entry_exit_simple():
    """단순 매수-매도 매칭 테스트"""
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    trades = [
        create_trade("AAPL", OrderSide.BUY, 100, 150.0, 0, base_time=base_time),
        create_trade("AAPL", OrderSide.SELL, 100, 160.0, 5, base_time=base_time),
    ]
    
    completed = TradeAnalyzer.match_entry_exit(trades)
    
    assert len(completed) == 1
    trade = completed[0]
    assert trade.symbol == "AAPL"
    assert trade.entry_price == 150.0
    assert trade.exit_price == 160.0
    assert trade.entry_quantity == 100
    assert trade.exit_quantity == 100
    assert trade.holding_period == 5
    assert trade.pnl == 1000.0 - 2000.0  # (160-150)*100 - commission
    assert abs(trade.return_pct - (-6.67)) < 0.01  # -1000/15000 * 100


def test_match_entry_exit_partial():
    """부분 매도 매칭 테스트"""
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    trades = [
        create_trade("AAPL", OrderSide.BUY, 100, 150.0, 0, base_time=base_time),
        create_trade("AAPL", OrderSide.SELL, 60, 160.0, 3, base_time=base_time),
        create_trade("AAPL", OrderSide.SELL, 40, 170.0, 7, base_time=base_time),
    ]
    
    completed = TradeAnalyzer.match_entry_exit(trades)
    
    assert len(completed) == 2
    
    # 첫 번째 완결 거래 (60주)
    trade1 = completed[0]
    assert trade1.entry_quantity == 60
    assert trade1.exit_quantity == 60
    assert trade1.exit_price == 160.0
    assert trade1.holding_period == 3
    
    # 두 번째 완결 거래 (40주)
    trade2 = completed[1]
    assert trade2.entry_quantity == 40
    assert trade2.exit_quantity == 40
    assert trade2.exit_price == 170.0
    assert trade2.holding_period == 7


def test_match_entry_exit_multiple_buys():
    """여러 매수 후 매도 매칭 테스트 (FIFO)"""
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    trades = [
        create_trade("AAPL", OrderSide.BUY, 100, 150.0, 0, base_time=base_time),
        create_trade("AAPL", OrderSide.BUY, 50, 155.0, 2, base_time=base_time),
        create_trade("AAPL", OrderSide.SELL, 120, 160.0, 5, base_time=base_time),
    ]
    
    completed = TradeAnalyzer.match_entry_exit(trades)
    
    assert len(completed) == 2
    
    # 첫 번째 완결 거래 (첫 번째 매수 100주 전체)
    trade1 = completed[0]
    assert trade1.entry_price == 150.0
    assert trade1.entry_quantity == 100
    assert trade1.exit_quantity == 100
    
    # 두 번째 완결 거래 (두 번째 매수 50주 중 20주)
    trade2 = completed[1]
    assert trade2.entry_price == 155.0
    assert trade2.entry_quantity == 20
    assert trade2.exit_quantity == 20


def test_match_entry_exit_empty_trades():
    """빈 거래 리스트 테스트"""
    completed = TradeAnalyzer.match_entry_exit([])
    assert len(completed) == 0


def test_calculate_symbol_metrics_profitable():
    """수익 종목 메트릭 계산 테스트"""
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    completed_trades = [
        CompletedTrade(
            symbol="AAPL",
            entry_date=base_time,
            entry_price=100.0,
            entry_quantity=100,
            exit_date=base_time + timedelta(days=10),
            exit_price=110.0,
            exit_quantity=100,
            pnl=1000.0 - 200.0,  # 1000 profit - 200 commission
            return_pct=8.0,  # 800/10000 * 100
            holding_period=10,
            commission=200.0
        ),
        CompletedTrade(
            symbol="AAPL",
            entry_date=base_time + timedelta(days=15),
            entry_price=110.0,
            entry_quantity=50,
            exit_date=base_time + timedelta(days=20),
            exit_price=120.0,
            exit_quantity=50,
            pnl=500.0 - 100.0,  # 500 profit - 100 commission
            return_pct=7.27,  # 400/5500 * 100
            holding_period=5,
            commission=100.0
        )
    ]
    
    metrics = TradeAnalyzer.calculate_symbol_metrics(completed_trades)
    
    assert metrics.symbol == "AAPL"
    assert metrics.trade_count == 2
    assert metrics.total_pnl == 1200.0  # 800 + 400
    assert metrics.win_rate == 100.0  # 2/2 * 100
    assert metrics.profit_factor == float('inf')  # no losses
    assert metrics.avg_holding_period == 7  # (10 + 5) / 2
    
    # 누적 수익률: (1 + 0.08) * (1 + 0.0727) - 1 = 0.1585 = 15.85%
    expected_return = (1.08 * 1.0727 - 1) * 100
    assert abs(metrics.total_return - expected_return) < 0.01


def test_calculate_symbol_metrics_mixed():
    """수익/손실 혼재 종목 메트릭 계산 테스트"""
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    completed_trades = [
        CompletedTrade(
            symbol="MSFT",
            entry_date=base_time,
            entry_price=200.0,
            entry_quantity=50,
            exit_date=base_time + timedelta(days=5),
            exit_price=220.0,
            exit_quantity=50,
            pnl=1000.0 - 150.0,  # 1000 profit - 150 commission
            return_pct=8.5,
            holding_period=5,
            commission=150.0
        ),
        CompletedTrade(
            symbol="MSFT",
            entry_date=base_time + timedelta(days=10),
            entry_price=220.0,
            entry_quantity=30,
            exit_date=base_time + timedelta(days=15),
            exit_price=200.0,
            exit_quantity=30,
            pnl=-600.0 - 120.0,  # -600 loss - 120 commission
            return_pct=-10.91,
            holding_period=5,
            commission=120.0
        )
    ]
    
    metrics = TradeAnalyzer.calculate_symbol_metrics(completed_trades)
    
    assert metrics.symbol == "MSFT"
    assert metrics.trade_count == 2
    assert metrics.total_pnl == 130.0  # 850 + (-720)
    assert metrics.win_rate == 50.0  # 1/2 * 100
    assert abs(metrics.profit_factor - (850.0 / 720.0)) < 0.01
    assert metrics.avg_holding_period == 5


def test_calculate_symbol_metrics_empty():
    """빈 완결 거래 리스트 메트릭 테스트"""
    metrics = TradeAnalyzer.calculate_symbol_metrics([])
    
    assert metrics.symbol == ""
    assert metrics.name == ""
    assert metrics.total_return == 0.0
    assert metrics.trade_count == 0
    assert metrics.win_rate == 0.0
    assert metrics.profit_factor == 0.0
    assert metrics.avg_holding_period == 0
    assert metrics.total_pnl == 0.0


def test_analyze_all_symbols():
    """전체 종목 분석 테스트"""
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    trades = [
        # AAPL 거래
        create_trade("AAPL", OrderSide.BUY, 100, 150.0, 0, base_time=base_time),
        create_trade("AAPL", OrderSide.SELL, 100, 160.0, 5, base_time=base_time),
        
        # MSFT 거래
        create_trade("MSFT", OrderSide.BUY, 50, 300.0, 1, base_time=base_time),
        create_trade("MSFT", OrderSide.SELL, 50, 290.0, 6, base_time=base_time),
        
        # GOOGL 거래 (매수만)
        create_trade("GOOGL", OrderSide.BUY, 20, 2500.0, 2, base_time=base_time),
    ]
    
    results = TradeAnalyzer.analyze_all_symbols(trades)
    
    assert len(results) == 3
    assert "AAPL" in results
    assert "MSFT" in results
    assert "GOOGL" in results
    
    # AAPL 수익 확인
    aapl_metrics = results["AAPL"]
    assert aapl_metrics.trade_count == 1
    assert aapl_metrics.total_pnl == -1000.0  # (160-150)*100 - 2000 commission
    
    # MSFT 손실 확인
    msft_metrics = results["MSFT"]
    assert msft_metrics.trade_count == 1
    assert msft_metrics.total_pnl == -2500.0  # (290-300)*50 - 2000 commission
    
    # GOOGL 거래 없음 (매수만)
    googl_metrics = results["GOOGL"]
    assert googl_metrics.trade_count == 0


def test_fifo_ordering():
    """FIFO 순서 정확성 테스트"""
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    trades = [
        create_trade("TEST", OrderSide.BUY, 100, 100.0, 0, base_time=base_time),  # 첫 번째 매수
        create_trade("TEST", OrderSide.BUY, 100, 110.0, 1, base_time=base_time),  # 두 번째 매수
        create_trade("TEST", OrderSide.BUY, 100, 120.0, 2, base_time=base_time),  # 세 번째 매수
        create_trade("TEST", OrderSide.SELL, 150, 115.0, 5, base_time=base_time), # 150주 매도
    ]
    
    completed = TradeAnalyzer.match_entry_exit(trades)
    
    assert len(completed) == 2
    
    # 첫 번째 완결 거래: 첫 번째 매수 100주 전체
    trade1 = completed[0]
    assert trade1.entry_price == 100.0
    assert trade1.entry_quantity == 100
    
    # 두 번째 완결 거래: 두 번째 매수 100주 중 50주
    trade2 = completed[1]
    assert trade2.entry_price == 110.0
    assert trade2.entry_quantity == 50