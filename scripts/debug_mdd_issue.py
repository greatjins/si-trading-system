#!/usr/bin/env python3
"""
실제 백테스트에서 MDD 문제 디버깅
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


async def debug_backtest_mdd():
    """실제 백테스트에서 MDD 문제 디버깅"""
    
    print("=== 백테스트 MDD 디버깅 시작 ===")
    
    # 데이터베이스 연결
    db = get_db_session()
    repo = DataRepository(db)
    
    try:
        # ICT 전략 생성 (올바른 파라미터)
        strategy = ICTStrategy(
            params={
                "symbol": "005930",
                "lookback_period": 50,
                "fvg_threshold": 0.002,
                "liquidity_threshold": 0.015,
                "risk_per_trade": 0.02,
                "rr_ratio": 2.0
            }
        )
        
        # 전략 이름 설정
        strategy.name = "Debug_ICT_Strategy"
        
        # 백테스트 엔진 생성
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=100000000,  # 1억원
            commission=0.0015,  # 0.15%
            slippage=0.0005,  # 0.05%
            rebalance_days=30
        )
        
        # 백테스트 기간 (짧게 설정)
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31)  # 3개월만
        
        print(f"백테스트 기간: {start_date.date()} ~ {end_date.date()}")
        print(f"초기 자본: {engine.initial_capital:,.0f}원")
        
        # 백테스트 실행
        # ICT 전략이 포트폴리오 전략인지 확인
        if hasattr(strategy, 'is_portfolio_strategy') and strategy.is_portfolio_strategy():
            result = await engine.run_portfolio(start_date, end_date, repo)
        else:
            # 단일 종목 전략인 경우 OHLC 데이터 필요
            # 삼성전자 데이터 조회 (올바른 파라미터 순서)
            ohlc_df = repo.get_ohlc("005930", "1d", start_date, end_date)
            print(f"OHLC DataFrame 크기: {len(ohlc_df)}")
            print(f"DataFrame 컬럼: {list(ohlc_df.columns) if not ohlc_df.empty else 'Empty'}")
            
            if ohlc_df.empty:
                # 날짜 범위 없이 시도
                ohlc_df = repo.get_ohlc("005930", "1d")
                print(f"전체 데이터 크기: {len(ohlc_df)}")
                
                if ohlc_df.empty:
                    print("❌ OHLC 데이터를 찾을 수 없습니다.")
                    return None
            
            # DataFrame을 OHLC 리스트로 변환
            ohlc_data = repo.get_ohlc_as_list("005930", "1d", start_date, end_date)
            if not ohlc_data:
                # 날짜 범위 없이 시도
                ohlc_data = repo.get_ohlc_as_list("005930", "1d")
                if not ohlc_data:
                    print("❌ OHLC 데이터 변환 실패")
                    return None
                
            print(f"OHLC 데이터 로드 완료: {len(ohlc_data)}개 바")
            result = await engine.run(ohlc_data=ohlc_data)
        
        # 결과 분석
        print(f"\n=== 백테스트 결과 ===")
        print(f"최종 자산: {result.final_equity:,.0f}원")
        print(f"총 수익률: {result.total_return:.2%}")
        print(f"MDD: {result.mdd:.2%}")
        print(f"샤프 비율: {result.sharpe_ratio:.2f}")
        print(f"총 거래 수: {result.total_trades}")
        
        # 자산 곡선 분석
        if result.equity_curve:
            print(f"\n=== 자산 곡선 분석 ===")
            print(f"데이터 포인트 수: {len(result.equity_curve)}")
            print(f"최소값: {min(result.equity_curve):,.0f}원")
            print(f"최대값: {max(result.equity_curve):,.0f}원")
            
            # 처음 10개와 마지막 10개 값 출력
            print(f"처음 10개 값: {[f'{v:,.0f}' for v in result.equity_curve[:10]]}")
            print(f"마지막 10개 값: {[f'{v:,.0f}' for v in result.equity_curve[-10:]]}")
            
            # 음수 값 체크
            negative_values = [v for v in result.equity_curve if v < 0]
            if negative_values:
                print(f"⚠️ 음수 값 발견: {len(negative_values)}개")
                print(f"음수 값들: {negative_values[:5]}")
            
            # 0 값 체크
            zero_values = [v for v in result.equity_curve if v == 0]
            if zero_values:
                print(f"⚠️ 0 값 발견: {len(zero_values)}개")
            
            # 급격한 변화 체크
            large_changes = []
            for i in range(1, len(result.equity_curve)):
                prev_val = result.equity_curve[i-1]
                curr_val = result.equity_curve[i]
                if prev_val > 0:
                    change_pct = abs(curr_val - prev_val) / prev_val
                    if change_pct > 0.5:  # 50% 이상 변화
                        large_changes.append((i, prev_val, curr_val, change_pct))
            
            if large_changes:
                print(f"⚠️ 급격한 변화 발견: {len(large_changes)}개")
                for idx, prev, curr, pct in large_changes[:3]:
                    print(f"  인덱스 {idx}: {prev:,.0f} → {curr:,.0f} ({pct:.1%})")
        
        # 거래 내역 분석
        if result.trades:
            print(f"\n=== 거래 내역 분석 ===")
            print(f"총 거래 수: {len(result.trades)}")
            
            # 거래 금액 분석
            trade_amounts = [t.quantity * t.price for t in result.trades]
            if trade_amounts:
                print(f"평균 거래 금액: {sum(trade_amounts) / len(trade_amounts):,.0f}원")
                print(f"최대 거래 금액: {max(trade_amounts):,.0f}원")
                print(f"최소 거래 금액: {min(trade_amounts):,.0f}원")
            
            # 처음 5개 거래 출력
            print(f"처음 5개 거래:")
            for i, trade in enumerate(result.trades[:5]):
                print(f"  {i+1}. {trade.symbol} {trade.side.value} {trade.quantity}주 @ {trade.price:,.0f}원")
        
        return result
        
    except Exception as e:
        logger.error(f"백테스트 실행 중 오류: {e}", exc_info=True)
        return None
    
    finally:
        db.close()


async def main():
    """메인 함수"""
    result = await debug_backtest_mdd()
    
    if result and result.mdd > 0.5:  # 50% 이상 MDD인 경우
        print(f"\n🚨 비정상적인 MDD 감지: {result.mdd:.2%}")
        print("추가 분석이 필요합니다.")
    else:
        print(f"\n✅ MDD가 정상 범위입니다: {result.mdd:.2%}" if result else "\n❌ 백테스트 실행 실패")


if __name__ == "__main__":
    asyncio.run(main())