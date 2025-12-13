#!/usr/bin/env python3
"""
TradeAnalyzer 간단 테스트
"""
import sys
import os
from datetime import datetime, timedelta

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.getcwd())

from core.backtest.trade_analyzer import TradeAnalyzer
from utils.types import Trade, CompletedTrade, SymbolPerformance, OrderSide

def test_basic_functionality():
    """기본 기능 테스트"""
    print("TradeAnalyzer 기본 기능 테스트 시작...")
    
    # 테스트 데이터 생성
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    trades = [
        Trade(
            trade_id="T1",
            order_id="O1",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=100,
            price=150.0,
            commission=1000.0,
            timestamp=base_time
        ),
        Trade(
            trade_id="T2",
            order_id="O2",
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=100,
            price=160.0,
            commission=1000.0,
            timestamp=base_time + timedelta(days=5)
        ),
        Trade(
            trade_id="T3",
            order_id="O3",
            symbol="MSFT",
            side=OrderSide.BUY,
            quantity=50,
            price=300.0,
            commission=1000.0,
            timestamp=base_time + timedelta(days=1)
        ),
        Trade(
            trade_id="T4",
            order_id="O4",
            symbol="MSFT",
            side=OrderSide.SELL,
            quantity=50,
            price=290.0,
            commission=1000.0,
            timestamp=base_time + timedelta(days=6)
        ),
    ]
    
    # 1. 종목별 그룹화 테스트
    print("1. 종목별 거래 그룹화 테스트...")
    grouped = TradeAnalyzer.group_trades_by_symbol(trades)
    assert len(grouped) == 2, f"Expected 2 symbols, got {len(grouped)}"
    assert "AAPL" in grouped, "AAPL not found in grouped trades"
    assert "MSFT" in grouped, "MSFT not found in grouped trades"
    print("   ✅ 종목별 그룹화 성공")
    
    # 2. 매수-매도 매칭 테스트
    print("2. 매수-매도 매칭 테스트...")
    aapl_trades = grouped["AAPL"]
    completed_aapl = TradeAnalyzer.match_entry_exit(aapl_trades)
    assert len(completed_aapl) == 1, f"Expected 1 completed trade, got {len(completed_aapl)}"
    
    trade = completed_aapl[0]
    assert trade.symbol == "AAPL", f"Expected AAPL, got {trade.symbol}"
    assert trade.entry_price == 150.0, f"Expected entry price 150.0, got {trade.entry_price}"
    assert trade.exit_price == 160.0, f"Expected exit price 160.0, got {trade.exit_price}"
    assert trade.holding_period == 5, f"Expected holding period 5, got {trade.holding_period}"
    print("   ✅ 매수-매도 매칭 성공")
    
    # 3. 메트릭 계산 테스트
    print("3. 메트릭 계산 테스트...")
    metrics = TradeAnalyzer.calculate_symbol_metrics(completed_aapl)
    assert metrics.symbol == "AAPL", f"Expected AAPL, got {metrics.symbol}"
    assert metrics.trade_count == 1, f"Expected 1 trade, got {metrics.trade_count}"
    print(f"   총 손익: {metrics.total_pnl}")
    print(f"   승률: {metrics.win_rate}%")
    print("   ✅ 메트릭 계산 성공")
    
    # 4. 전체 분석 테스트
    print("4. 전체 종목 분석 테스트...")
    all_results = TradeAnalyzer.analyze_all_symbols(trades)
    assert len(all_results) == 2, f"Expected 2 symbols, got {len(all_results)}"
    assert "AAPL" in all_results, "AAPL not found in results"
    assert "MSFT" in all_results, "MSFT not found in results"
    
    aapl_result = all_results["AAPL"]
    msft_result = all_results["MSFT"]
    
    print(f"   AAPL - 거래수: {aapl_result.trade_count}, 손익: {aapl_result.total_pnl}")
    print(f"   MSFT - 거래수: {msft_result.trade_count}, 손익: {msft_result.total_pnl}")
    print("   ✅ 전체 분석 성공")
    
    print("\n🎉 모든 기본 테스트가 통과했습니다!")
    return True

if __name__ == "__main__":
    try:
        success = test_basic_functionality()
        print("\n✅ TradeAnalyzer 테스트 완료!")
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)