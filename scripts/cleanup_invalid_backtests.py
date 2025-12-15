#!/usr/bin/env python3
"""
잘못된 백테스트 결과 정리 스크립트
- MDD > 50% 인 비정상적인 결과들 삭제
- 거래 수 = 0 인 실패한 백테스트 삭제
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.repository import get_db_session
from data.models import BacktestResultModel, TradeModel
from utils.logger import setup_logger

logger = setup_logger(__name__)


def cleanup_invalid_backtests():
    """비정상적인 백테스트 결과 정리"""
    
    db = get_db_session()
    
    try:
        print("🧹 잘못된 백테스트 결과 정리 시작...")
        
        # 1. MDD > 50% 인 비정상적인 결과들 찾기
        invalid_mdd_results = db.query(BacktestResultModel).filter(
            BacktestResultModel.mdd > 0.5  # 50% 이상 MDD
        ).all()
        
        print(f"📊 MDD > 50% 인 결과: {len(invalid_mdd_results)}개")
        
        # 2. 거래 수 = 0 인 실패한 백테스트 찾기
        zero_trade_results = db.query(BacktestResultModel).filter(
            BacktestResultModel.total_trades == 0
        ).all()
        
        print(f"📊 거래 수 = 0 인 결과: {len(zero_trade_results)}개")
        
        # 3. 사용자 확인
        total_to_delete = len(set([r.id for r in invalid_mdd_results + zero_trade_results]))
        
        if total_to_delete == 0:
            print("✅ 정리할 잘못된 결과가 없습니다.")
            return
        
        print(f"\n⚠️  총 {total_to_delete}개의 잘못된 백테스트 결과를 삭제하시겠습니까?")
        print("   (y/N): ", end="")
        
        response = input().strip().lower()
        
        if response != 'y':
            print("❌ 삭제가 취소되었습니다.")
            return
        
        # 4. 삭제 실행
        deleted_count = 0
        
        for result in invalid_mdd_results + zero_trade_results:
            try:
                # 관련 거래 내역 먼저 삭제
                db.query(TradeModel).filter(
                    TradeModel.backtest_id == result.id
                ).delete()
                
                # 백테스트 결과 삭제
                db.delete(result)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"삭제 실패 (ID: {result.id}): {e}")
                continue
        
        db.commit()
        
        print(f"✅ {deleted_count}개의 잘못된 백테스트 결과를 삭제했습니다.")
        
        # 5. 남은 결과 확인
        remaining_results = db.query(BacktestResultModel).count()
        print(f"📊 남은 백테스트 결과: {remaining_results}개")
        
    except Exception as e:
        db.rollback()
        logger.error(f"정리 중 오류 발생: {e}", exc_info=True)
        
    finally:
        db.close()


def show_backtest_stats():
    """백테스트 결과 통계 표시"""
    
    db = get_db_session()
    
    try:
        print("\n📊 현재 백테스트 결과 통계:")
        
        # 전체 결과 수
        total_count = db.query(BacktestResultModel).count()
        print(f"   전체 결과: {total_count}개")
        
        if total_count == 0:
            return
        
        # MDD 분포
        high_mdd_count = db.query(BacktestResultModel).filter(
            BacktestResultModel.mdd > 0.5
        ).count()
        
        normal_mdd_count = db.query(BacktestResultModel).filter(
            BacktestResultModel.mdd <= 0.5
        ).count()
        
        print(f"   정상 MDD (≤50%): {normal_mdd_count}개")
        print(f"   비정상 MDD (>50%): {high_mdd_count}개")
        
        # 거래 수 분포
        zero_trades = db.query(BacktestResultModel).filter(
            BacktestResultModel.total_trades == 0
        ).count()
        
        with_trades = db.query(BacktestResultModel).filter(
            BacktestResultModel.total_trades > 0
        ).count()
        
        print(f"   거래 있음: {with_trades}개")
        print(f"   거래 없음: {zero_trades}개")
        
    except Exception as e:
        logger.error(f"통계 조회 중 오류: {e}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("🔍 백테스트 결과 분석 및 정리 도구")
    print("=" * 50)
    
    # 현재 상태 확인
    show_backtest_stats()
    
    # 정리 실행
    cleanup_invalid_backtests()
    
    # 정리 후 상태 확인
    show_backtest_stats()
    
    print("\n✅ 정리 완료!")
    print("💡 앞으로의 백테스트는 수정된 엔진으로 정확한 결과가 나올 것입니다.")