#!/usr/bin/env python3
"""
MDD 일관성 문제 해결 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from data.repository import get_db_session
from data.models import BacktestResultModel
from core.backtest.metrics import calculate_mdd
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def fix_mdd_consistency():
    """
    저장된 백테스트 결과의 MDD 값을 재계산하여 일관성 확보
    """
    print("=== MDD 일관성 문제 해결 시작 ===")
    
    db = get_db_session()
    
    try:
        # 모든 백테스트 결과 조회
        backtests = db.query(BacktestResultModel).all()
        print(f"총 {len(backtests)}개의 백테스트 결과 발견")
        
        updated_count = 0
        error_count = 0
        
        for backtest in backtests:
            try:
                # 자산 곡선이 있는 경우만 처리
                if not backtest.equity_curve or len(backtest.equity_curve) < 2:
                    print(f"백테스트 {backtest.id}: 자산 곡선 데이터 부족, 건너뜀")
                    continue
                
                # 기존 MDD
                old_mdd = backtest.mdd
                
                # 새로운 MDD 계산
                new_mdd = calculate_mdd(backtest.equity_curve)
                
                # 차이가 있는 경우만 업데이트
                mdd_diff = abs(new_mdd - old_mdd)
                if mdd_diff > 0.001:  # 0.1% 이상 차이
                    print(f"백테스트 {backtest.id} ({backtest.strategy_name}):")
                    print(f"  기존 MDD: {old_mdd:.4f} ({old_mdd*100:.2f}%)")
                    print(f"  새로운 MDD: {new_mdd:.4f} ({new_mdd*100:.2f}%)")
                    print(f"  차이: {mdd_diff:.4f} ({mdd_diff*100:.2f}%)")
                    
                    # 데이터베이스 업데이트
                    backtest.mdd = new_mdd
                    updated_count += 1
                else:
                    print(f"백테스트 {backtest.id}: MDD 일치 (차이: {mdd_diff:.4f})")
            
            except Exception as e:
                print(f"백테스트 {backtest.id} 처리 중 오류: {e}")
                error_count += 1
                continue
        
        # 변경사항 저장
        if updated_count > 0:
            db.commit()
            print(f"\n✅ {updated_count}개 백테스트의 MDD 값이 업데이트되었습니다.")
        else:
            print(f"\n✅ 모든 MDD 값이 일치합니다.")
        
        if error_count > 0:
            print(f"⚠️ {error_count}개 백테스트에서 오류 발생")
        
        print("=== MDD 일관성 문제 해결 완료 ===")
        
    except Exception as e:
        logger.error(f"MDD 일관성 해결 중 오류: {e}", exc_info=True)
        db.rollback()
    
    finally:
        db.close()


async def validate_mdd_calculation():
    """
    MDD 계산 로직 검증
    """
    print("\n=== MDD 계산 로직 검증 ===")
    
    # 테스트 케이스 1: 정상적인 상승 곡선
    test_curve_1 = [100000, 105000, 110000, 115000, 120000]
    mdd_1 = calculate_mdd(test_curve_1)
    print(f"테스트 1 (상승): {test_curve_1} → MDD: {mdd_1:.4f} (예상: 0.0000)")
    
    # 테스트 케이스 2: 단순 하락 후 회복
    test_curve_2 = [100000, 90000, 95000, 105000, 110000]
    mdd_2 = calculate_mdd(test_curve_2)
    expected_2 = (100000 - 90000) / 100000  # 10%
    print(f"테스트 2 (하락-회복): {test_curve_2} → MDD: {mdd_2:.4f} (예상: {expected_2:.4f})")
    
    # 테스트 케이스 3: 복잡한 패턴
    test_curve_3 = [100000, 120000, 80000, 110000, 70000, 130000]
    mdd_3 = calculate_mdd(test_curve_3)
    expected_3 = (120000 - 70000) / 120000  # 약 41.67%
    print(f"테스트 3 (복잡): {test_curve_3} → MDD: {mdd_3:.4f} (예상: {expected_3:.4f})")
    
    # 테스트 케이스 4: 음수 값 포함 (비정상)
    test_curve_4 = [100000, 50000, -10000, 20000, 80000]
    mdd_4 = calculate_mdd(test_curve_4)
    print(f"테스트 4 (음수 포함): {test_curve_4} → MDD: {mdd_4:.4f}")
    
    print("=== MDD 계산 로직 검증 완료 ===")


async def main():
    """메인 함수"""
    await validate_mdd_calculation()
    await fix_mdd_consistency()


if __name__ == "__main__":
    asyncio.run(main())