"""
AutoML 사용 예제
"""
import asyncio
from datetime import datetime

from broker.mock.adapter import MockBroker
from core.strategy.examples.ma_cross import MACrossStrategy
from core.automl.parameter_space import ParameterSpace
from core.automl.grid_search import GridSearch
from core.automl.random_search import RandomSearch
from core.automl.genetic import GeneticAlgorithm
from core.automl.result_manager import AutoMLResultManager


async def main():
    print("=" * 60)
    print("AutoML 파라미터 최적화 테스트")
    print("=" * 60)
    
    # Mock 데이터 준비
    print(f"\n[데이터 준비]")
    broker = MockBroker()
    
    symbol = "005930"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 6, 30)
    
    ohlc_data = await broker.get_ohlc(
        symbol=symbol,
        interval="1d",
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"  - 종목: {symbol}")
    print(f"  - 기간: {start_date.date()} ~ {end_date.date()}")
    print(f"  - 데이터 수: {len(ohlc_data)}개")
    
    # 파라미터 공간 정의
    print(f"\n[파라미터 공간 정의]")
    space = ParameterSpace()
    space.add_parameter("short_period", 3, 10, step=2)
    space.add_parameter("long_period", 15, 25, step=5)
    space.add_fixed_parameter("symbol", symbol)
    space.add_fixed_parameter("position_size", 0.1)
    
    print(f"  - 탐색 파라미터: short_period, long_period")
    print(f"  - 고정 파라미터: symbol, position_size")
    print(f"  - 총 조합 수: {space.get_total_combinations()}개")
    
    # 1. Grid Search
    print(f"\n" + "=" * 60)
    print("[1] Grid Search")
    print("=" * 60)
    
    grid_search = GridSearch(
        strategy_class=MACrossStrategy,
        parameter_space=space,
        initial_capital=10_000_000
    )
    
    grid_results = await grid_search.run(ohlc_data, start_date, end_date)
    
    print(f"\n결과: {len(grid_results)}개")
    
    best_grid = grid_search.get_best_results(metric="sharpe_ratio", top_n=3)
    print(f"\n[상위 3개 - Sharpe 기준]")
    for i, result in enumerate(best_grid, 1):
        print(f"{i}. {result.parameters}")
        print(f"   Return: {result.total_return:+.2%}, MDD: {result.mdd:.2%}, Sharpe: {result.sharpe_ratio:.2f}")
    
    stats = grid_search.get_statistics()
    print(f"\n[통계]")
    print(f"  평균 수익률: {stats['avg_return']:+.2%}")
    print(f"  최고 Sharpe: {stats['max_sharpe']:.2f}")
    
    # 2. Random Search
    print(f"\n" + "=" * 60)
    print("[2] Random Search")
    print("=" * 60)
    
    random_search = RandomSearch(
        strategy_class=MACrossStrategy,
        parameter_space=space,
        n_iterations=10,
        initial_capital=10_000_000
    )
    
    random_results = await random_search.run(ohlc_data, start_date, end_date)
    
    print(f"\n결과: {len(random_results)}개")
    
    best_random = random_search.get_best_results(metric="total_return", top_n=3)
    print(f"\n[상위 3개 - 수익률 기준]")
    for i, result in enumerate(best_random, 1):
        print(f"{i}. {result.parameters}")
        print(f"   Return: {result.total_return:+.2%}, MDD: {result.mdd:.2%}, Sharpe: {result.sharpe_ratio:.2f}")
    
    # 3. Genetic Algorithm
    print(f"\n" + "=" * 60)
    print("[3] Genetic Algorithm")
    print("=" * 60)
    
    genetic = GeneticAlgorithm(
        strategy_class=MACrossStrategy,
        parameter_space=space,
        population_size=10,
        generations=3,
        initial_capital=10_000_000
    )
    
    genetic_results = await genetic.run(
        ohlc_data,
        start_date,
        end_date,
        fitness_metric="sharpe_ratio"
    )
    
    print(f"\n최고 개체: {genetic.best_individual}")
    print(f"최고 적합도: {genetic.best_fitness:.4f}")
    
    best_genetic = genetic.get_best_results(top_n=3)
    print(f"\n[상위 3개]")
    for i, result in enumerate(best_genetic, 1):
        print(f"{i}. {result.parameters}")
        print(f"   Return: {result.total_return:+.2%}, MDD: {result.mdd:.2%}, Sharpe: {result.sharpe_ratio:.2f}")
    
    # 4. 결과 저장
    print(f"\n" + "=" * 60)
    print("[4] 결과 저장")
    print("=" * 60)
    
    result_manager = AutoMLResultManager(output_dir="automl_results")
    
    # 최고 파라미터 저장
    param_file = result_manager.save_best_parameters(
        grid_results,
        metric="sharpe_ratio",
        top_n=5
    )
    print(f"  ✓ 파라미터 저장: {param_file}")
    
    # 리포트 생성
    report_file = result_manager.generate_report(grid_results)
    print(f"  ✓ 리포트 생성: {report_file}")
    
    # 데이터베이스 저장
    saved_ids = result_manager.save_to_database(best_grid[:3])
    print(f"  ✓ DB 저장: {len(saved_ids)}개 결과")
    
    print(f"\n" + "=" * 60)
    print("AutoML 테스트 완료!")
    print("=" * 60)
    
    print(f"\n📊 총 백테스트 수: {len(grid_results) + len(random_results) + len(genetic_results)}개")
    print(f"📁 결과 저장 위치: automl_results/")


if __name__ == "__main__":
    asyncio.run(main())
