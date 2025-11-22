"""
백테스트 + 데이터베이스 연동 예제
"""
import asyncio
from datetime import datetime

from broker.mock.adapter import MockBroker
from core.strategy.examples.ma_cross import MACrossStrategy
from core.backtest.engine import BacktestEngine
from data.repository import BacktestRepository


async def main():
    print("=" * 60)
    print("백테스트 + 데이터베이스 연동 테스트")
    print("=" * 60)
    
    # 데이터베이스 초기화
    print(f"\n[데이터베이스 초기화]")
    repo = BacktestRepository(db_url="sqlite:///data/hts.db")
    print(f"  ✓ 데이터베이스 연결 완료")
    
    # Mock 브로커로 데이터 생성
    broker = MockBroker()
    
    symbol = "005930"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 6, 30)
    
    print(f"\n[데이터 준비]")
    print(f"  - 종목: {symbol}")
    print(f"  - 기간: {start_date.date()} ~ {end_date.date()}")
    
    ohlc_data = await broker.get_ohlc(
        symbol=symbol,
        interval="1d",
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"  - 데이터 수: {len(ohlc_data)}개")
    
    # 전략 생성
    print(f"\n[전략 설정]")
    strategy = MACrossStrategy({
        "symbol": symbol,
        "short_period": 5,
        "long_period": 20,
        "position_size": 0.1
    })
    
    print(f"  - 전략: {strategy.name}")
    
    # 백테스트 실행
    print(f"\n[백테스트 실행]")
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=10_000_000
    )
    
    result = await engine.run(ohlc_data, start_date, end_date)
    
    print(f"  ✓ 백테스트 완료")
    print(f"    - 총 거래: {result.total_trades}회")
    print(f"    - 총 수익률: {result.total_return:+.2%}")
    print(f"    - MDD: {result.mdd:.2%}")
    
    # 데이터베이스에 저장
    print(f"\n[데이터베이스 저장]")
    backtest_id = repo.save_backtest_result(result)
    print(f"  ✓ 저장 완료: ID={backtest_id}")
    
    # 저장된 결과 조회
    print(f"\n[저장된 결과 조회]")
    loaded = repo.get_backtest_result(backtest_id)
    print(f"  - 전략: {loaded.strategy_name}")
    print(f"  - 수익률: {loaded.total_return:+.2%}")
    print(f"  - 거래 수: {loaded.total_trades}회")
    print(f"  - 저장 시간: {loaded.created_at}")
    
    # 거래 내역 조회
    trades = repo.get_trades(backtest_id)
    print(f"\n[거래 내역]")
    print(f"  - 총 {len(trades)}개 거래")
    if trades:
        print(f"  - 첫 거래: {trades[0].timestamp.date()} | {trades[0].side} {trades[0].quantity}주")
        print(f"  - 마지막 거래: {trades[-1].timestamp.date()} | {trades[-1].side} {trades[-1].quantity}주")
    
    # 전체 백테스트 목록
    print(f"\n[전체 백테스트 목록]")
    all_results = repo.get_all_backtest_results(limit=5)
    print(f"  - 총 {len(all_results)}개 백테스트")
    for r in all_results:
        print(f"    ID={r.id} | {r.strategy_name} | {r.total_return:+.2%} | {r.created_at.date()}")
    
    # 최고 성과 백테스트
    print(f"\n[최고 성과 백테스트 (Top 3)]")
    best = repo.get_best_results(metric="total_return", limit=3)
    for i, r in enumerate(best, 1):
        print(f"  {i}. ID={r.id} | {r.strategy_name} | {r.total_return:+.2%}")
    
    print(f"\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print(f"\n💾 데이터베이스: data/hts.db")
    print(f"📊 백테스트 ID: {backtest_id}")


if __name__ == "__main__":
    asyncio.run(main())
