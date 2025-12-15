#!/usr/bin/env python3
"""
개선된 ICT 전략 테스트 (MDD 최소화)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timedelta
from data.repository import DataRepository, get_db_session
from core.backtest.engine import BacktestEngine
from core.strategy.examples.ict_strategy import ICTStrategy
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_improved_ict():
    """개선된 ICT 전략 테스트"""
    
    print("=== 개선된 ICT 전략 테스트 시작 ===")
    
    # 데이터베이스 연결
    db = get_db_session()
    repo = DataRepository(db)
    
    try:
        # 보수적인 ICT 전략 생성
        strategy = ICTStrategy(
            params={
                "symbol": "005930",
                "lookback_period": 30,  # 단축
                "fvg_threshold": 0.003,  # 증가 (더 엄격)
                "liquidity_threshold": 0.02,  # 증가 (더 엄격)
                "risk_per_trade": 0.01,  # 감소 (1%로 축소)
                "rr_ratio": 3.0  # 증가 (더 보수적)
            }
        )
        
        strategy.name = "Conservative_ICT_Strategy"
        
        # 백테스트 엔진 생성 (보수적 설정)
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=10000000,  # 1천만원 (기존 1억에서 축소)
            commission=0.0015,
            slippage=0.0005,
            rebalance_days=30
        )
        
        # 백테스트 기간 (실제 데이터 있는 기간으로 수정)
        start_date = datetime(2025, 2, 3)
        end_date = datetime(2025, 11, 30)  # 2025년 데이터
        
        print(f"백테스트 기간: {start_date.date()} ~ {end_date.date()}")
        print(f"초기 자본: {engine.initial_capital:,.0f}원")
        
        # OHLC 데이터 조회
        ohlc_data = repo.get_ohlc_as_list("005930", "1d", start_date, end_date)
        
        if not ohlc_data:
            print("❌ OHLC 데이터를 찾을 수 없습니다.")
            return None
        
        print(f"OHLC 데이터 로드 완료: {len(ohlc_data)}개 바")
        
        # 백테스트 실행
        result = await engine.run(ohlc_data=ohlc_data)
        
        # 결과 분석
        print(f"\n=== 개선된 백테스트 결과 ===")
        print(f"최종 자산: {result.final_equity:,.0f}원")
        print(f"총 수익률: {result.total_return:.2%}")
        print(f"MDD: {result.mdd:.2%}")
        print(f"샤프 비율: {result.sharpe_ratio:.2f}")
        print(f"총 거래 수: {result.total_trades}")
        
        # MDD 분석
        if result.mdd > 0.2:  # 20% 이상
            print(f"⚠️ 여전히 높은 MDD: {result.mdd:.2%}")
        elif result.mdd > 0.1:  # 10% 이상
            print(f"⚠️ 보통 수준 MDD: {result.mdd:.2%}")
        else:
            print(f"✅ 낮은 MDD: {result.mdd:.2%}")
        
        # 자산 곡선 안정성 분석
        if result.equity_curve:
            min_equity = min(result.equity_curve)
            max_equity = max(result.equity_curve)
            
            print(f"\n=== 자산 곡선 분석 ===")
            print(f"최소 자산: {min_equity:,.0f}원")
            print(f"최대 자산: {max_equity:,.0f}원")
            print(f"변동 범위: {((max_equity - min_equity) / result.initial_capital):.1%}")
            
            # 음수 자산 체크
            if min_equity <= 0:
                print(f"🚨 음수 자산 발생!")
            else:
                print(f"✅ 자산이 항상 양수 유지")
        
        return result
        
    except Exception as e:
        logger.error(f"테스트 실행 중 오류: {e}", exc_info=True)
        return None
    
    finally:
        db.close()


async def main():
    """메인 함수"""
    result = await test_improved_ict()
    
    if result:
        if result.mdd < 0.15:  # 15% 미만
            print(f"\n🎉 MDD 개선 성공: {result.mdd:.2%}")
        else:
            print(f"\n⚠️ 추가 개선 필요: MDD {result.mdd:.2%}")
    else:
        print(f"\n❌ 테스트 실행 실패")


if __name__ == "__main__":
    asyncio.run(main())