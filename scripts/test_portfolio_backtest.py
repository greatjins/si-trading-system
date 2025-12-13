"""
포트폴리오 백테스트 테스트 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from datetime import datetime, timedelta

from core.strategy.examples.simple_portfolio import SimplePortfolioStrategy
from core.backtest.engine import BacktestEngine
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    """포트폴리오 백테스트 테스트"""
    
    # 전략 생성 (가치주 전략)
    from core.strategy.examples.value_portfolio import ValuePortfolioStrategy
    strategy = ValuePortfolioStrategy(params={
        "per_max": 10.0,
        "pbr_max": 1.0,
        "max_stocks": 20
    })
    
    # 백테스트 엔진 생성
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=10_000_000,
        commission=0.00015
    )
    
    # 백테스트 실행
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    logger.info(f"Starting portfolio backtest")
    logger.info(f"Period: {start_date.date()} ~ {end_date.date()}")
    logger.info(f"Strategy: {strategy.name}")
    logger.info(f"Parameters: {strategy.params}")
    
    try:
        result = await engine.run(
            start_date=start_date,
            end_date=end_date
        )
        
        # 결과 출력
        print("\n" + "="*60)
        print("백테스트 결과")
        print("="*60)
        print(f"전략: {result.strategy_name}")
        print(f"기간: {result.start_date.date()} ~ {result.end_date.date()}")
        print(f"초기 자본: {result.initial_capital:,.0f}원")
        print(f"최종 자산: {result.final_equity:,.0f}원")
        print(f"총 수익률: {result.total_return:.2%}")
        print(f"MDD: {result.mdd:.2%}")
        print(f"샤프 비율: {result.sharpe_ratio:.2f}")
        print(f"승률: {result.win_rate:.2%}")
        print(f"Profit Factor: {result.profit_factor:.2f}")
        print(f"총 거래 수: {result.total_trades}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        print(f"\n❌ 백테스트 실패: {e}")


if __name__ == "__main__":
    asyncio.run(main())
