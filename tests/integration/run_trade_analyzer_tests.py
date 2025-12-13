#!/usr/bin/env python3
"""
TradeAnalyzer 테스트 실행 스크립트
"""
import sys
import os

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.getcwd())

# 테스트 함수들 import
from tests.test_trade_analyzer import (
    test_group_trades_by_symbol,
    test_match_entry_exit_simple,
    test_match_entry_exit_partial,
    test_match_entry_exit_multiple_buys,
    test_match_entry_exit_empty_trades,
    test_calculate_symbol_metrics_profitable,
    test_calculate_symbol_metrics_mixed,
    test_calculate_symbol_metrics_empty,
    test_analyze_all_symbols,
    test_fifo_ordering
)

def run_tests():
    """모든 테스트 실행"""
    tests = [
        ("종목별 거래 그룹화", test_group_trades_by_symbol),
        ("단순 매수-매도 매칭", test_match_entry_exit_simple),
        ("부분 매도 매칭", test_match_entry_exit_partial),
        ("여러 매수 후 매도 매칭", test_match_entry_exit_multiple_buys),
        ("빈 거래 리스트", test_match_entry_exit_empty_trades),
        ("수익 종목 메트릭 계산", test_calculate_symbol_metrics_profitable),
        ("수익/손실 혼재 메트릭", test_calculate_symbol_metrics_mixed),
        ("빈 완결 거래 메트릭", test_calculate_symbol_metrics_empty),
        ("전체 종목 분석", test_analyze_all_symbols),
        ("FIFO 순서 정확성", test_fifo_ordering),
    ]
    
    passed = 0
    failed = 0
    
    print("TradeAnalyzer 테스트 실행 중...")
    print("=" * 50)
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {str(e)}")
            failed += 1
    
    print("=" * 50)
    print(f"총 {len(tests)}개 테스트 중 {passed}개 통과, {failed}개 실패")
    
    if failed == 0:
        print("🎉 모든 테스트가 통과했습니다!")
        return True
    else:
        print(f"⚠️  {failed}개 테스트가 실패했습니다.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)