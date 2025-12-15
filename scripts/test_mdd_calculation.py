#!/usr/bin/env python3
"""
MDD 계산 테스트 및 검증 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backtest.metrics import calculate_mdd, calculate_metrics
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_mdd_calculation():
    """MDD 계산 테스트"""
    
    print("=== MDD 계산 테스트 ===")
    
    # 테스트 케이스 1: 정상적인 경우
    equity_curve_1 = [1000000, 1100000, 1050000, 1200000, 900000, 950000, 1100000]
    mdd_1 = calculate_mdd(equity_curve_1)
    expected_mdd_1 = (1200000 - 900000) / 1200000  # 25%
    print(f"테스트 1 - 정상 케이스:")
    print(f"  자산 곡선: {equity_curve_1}")
    print(f"  계산된 MDD: {mdd_1:.2%}")
    print(f"  예상 MDD: {expected_mdd_1:.2%}")
    print(f"  결과: {'✅ 통과' if abs(mdd_1 - expected_mdd_1) < 0.01 else '❌ 실패'}")
    print()
    
    # 테스트 케이스 2: 극단적 손실
    equity_curve_2 = [1000000, 1100000, 500000, 100000, 50000, 60000]
    mdd_2 = calculate_mdd(equity_curve_2)
    expected_mdd_2 = (1100000 - 50000) / 1100000  # 95.45%
    print(f"테스트 2 - 극단적 손실:")
    print(f"  자산 곡선: {equity_curve_2}")
    print(f"  계산된 MDD: {mdd_2:.2%}")
    print(f"  예상 MDD: {expected_mdd_2:.2%}")
    print(f"  결과: {'✅ 통과' if abs(mdd_2 - expected_mdd_2) < 0.01 else '❌ 실패'}")
    print()
    
    # 테스트 케이스 3: 음수 값 포함 (문제 케이스)
    equity_curve_3 = [1000000, 1100000, 500000, -100000, 0, 50000]
    mdd_3 = calculate_mdd(equity_curve_3)
    print(f"테스트 3 - 음수 값 포함:")
    print(f"  자산 곡선: {equity_curve_3}")
    print(f"  계산된 MDD: {mdd_3:.2%}")
    print(f"  결과: {'✅ 통과' if mdd_3 <= 1.0 else '❌ 실패 (MDD > 100%)'}")
    print()
    
    # 테스트 케이스 4: 지속적 상승
    equity_curve_4 = [1000000, 1100000, 1200000, 1300000, 1400000]
    mdd_4 = calculate_mdd(equity_curve_4)
    print(f"테스트 4 - 지속적 상승:")
    print(f"  자산 곡선: {equity_curve_4}")
    print(f"  계산된 MDD: {mdd_4:.2%}")
    print(f"  결과: {'✅ 통과' if mdd_4 == 0.0 else '❌ 실패'}")
    print()
    
    # 테스트 케이스 5: 빈 리스트
    equity_curve_5 = []
    mdd_5 = calculate_mdd(equity_curve_5)
    print(f"테스트 5 - 빈 리스트:")
    print(f"  자산 곡선: {equity_curve_5}")
    print(f"  계산된 MDD: {mdd_5:.2%}")
    print(f"  결과: {'✅ 통과' if mdd_5 == 0.0 else '❌ 실패'}")


def test_full_metrics():
    """전체 메트릭 계산 테스트"""
    
    print("\n=== 전체 메트릭 계산 테스트 ===")
    
    # 샘플 자산 곡선 (정상적인 케이스)
    equity_curve = [
        1000000, 1050000, 1020000, 1100000, 1080000,
        1150000, 1120000, 1200000, 1050000, 1100000,
        1180000, 1160000, 1220000, 1200000, 1250000
    ]
    
    initial_capital = 1000000
    
    metrics = calculate_metrics(
        equity_curve=equity_curve,
        trades=[],  # 거래 없음
        initial_capital=initial_capital
    )
    
    print(f"자산 곡선: {len(equity_curve)}개 포인트")
    print(f"초기 자본: {initial_capital:,.0f}")
    print(f"최종 자산: {equity_curve[-1]:,.0f}")
    print(f"총 수익률: {metrics['total_return']:.2%}")
    print(f"MDD: {metrics['mdd']:.2%}")
    print(f"샤프 비율: {metrics['sharpe_ratio']:.2f}")
    
    # 검증
    expected_return = (equity_curve[-1] - initial_capital) / initial_capital
    print(f"\n검증:")
    print(f"  예상 수익률: {expected_return:.2%}")
    print(f"  계산 수익률: {metrics['total_return']:.2%}")
    print(f"  수익률 일치: {'✅' if abs(metrics['total_return'] - expected_return) < 0.001 else '❌'}")
    print(f"  MDD 범위: {'✅' if 0 <= metrics['mdd'] <= 1 else '❌'}")


if __name__ == "__main__":
    test_mdd_calculation()
    test_full_metrics()
    print("\n=== MDD 계산 테스트 완료 ===")