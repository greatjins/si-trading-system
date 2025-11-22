"""
백테스트 엔진 사용 예제
"""
import asyncio
from datetime import datetime

from broker.mock.adapter import MockBroker
from core.strategy.examples.ma_cross import MACrossStrategy
from core.backtest.engine import BacktestEngine


async def main():
    print("=" * 60)
    print("백테스트 엔진 테스트")
    print("=" * 60)
    
    # Mock 브로커로 데이터 생성
    broker = MockBroker()
    
    # OHLC 데이터 조회
    print(f"\n[데이터 준비]")
    symbol = "005930"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
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
    print(f"  - 단기 이동평균: {strategy.short_period}일")
    print(f"  - 장기 이동평균: {strategy.long_period}일")
    print(f"  - 포지션 크기: {strategy.position_size:.1%}")
    
    # 백테스트 엔진 생성
    print(f"\n[백테스트 실행]")
    initial_capital = 10_000_000
    
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=initial_capital,
        commission=0.0015,
        slippage=0.001
    )
    
    print(f"  - 초기 자본: {initial_capital:,.0f}원")
    print(f"  - 수수료: 0.15%")
    print(f"  - 슬리피지: 0.1%")
    print(f"\n  실행 중...")
    
    # 백테스트 실행
    result = await engine.run(ohlc_data, start_date, end_date)
    
    # 결과 출력
    print(f"\n" + "=" * 60)
    print("백테스트 결과")
    print("=" * 60)
    
    print(f"\n[기본 정보]")
    print(f"  - 전략: {result.strategy_name}")
    print(f"  - 기간: {result.start_date.date()} ~ {result.end_date.date()}")
    print(f"  - 총 거래 수: {result.total_trades}회")
    
    print(f"\n[수익성]")
    print(f"  - 초기 자본: {result.initial_capital:,.0f}원")
    print(f"  - 최종 자산: {result.final_equity:,.0f}원")
    print(f"  - 총 수익률: {result.total_return:+.2%}")
    
    profit = result.final_equity - result.initial_capital
    print(f"  - 손익: {profit:+,.0f}원")
    
    print(f"\n[리스크 지표]")
    print(f"  - MDD: {result.mdd:.2%}")
    print(f"  - 샤프 비율: {result.sharpe_ratio:.2f}")
    
    print(f"\n[거래 통계]")
    print(f"  - 승률: {result.win_rate:.2%}")
    print(f"  - 손익비: {result.profit_factor:.2f}")
    
    # 자산 곡선 요약
    print(f"\n[자산 곡선]")
    print(f"  - 시작: {result.equity_curve[0]:,.0f}원")
    print(f"  - 최고: {max(result.equity_curve):,.0f}원")
    print(f"  - 최저: {min(result.equity_curve):,.0f}원")
    print(f"  - 종료: {result.equity_curve[-1]:,.0f}원")
    
    # 거래 내역 샘플
    if result.trades:
        print(f"\n[거래 내역 (최근 5개)]")
        for trade in result.trades[-5:]:
            print(f"  - {trade.timestamp.date()} | {trade.side.value.upper():4s} | "
                  f"{trade.quantity:3d}주 @ {trade.price:,.0f}원 | "
                  f"수수료: {trade.commission:,.0f}원")
    
    print(f"\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
