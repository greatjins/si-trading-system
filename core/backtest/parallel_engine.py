"""
병렬 백테스트 엔진
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp
from dataclasses import asdict

from core.strategy.base import BaseStrategy
from core.backtest.engine import BacktestEngine
from utils.types import OHLC, BacktestResult
from utils.logger import setup_logger
from utils.exceptions import BacktestError

logger = setup_logger(__name__)


class ParallelBacktestEngine:
    """
    병렬 백테스트 엔진
    
    여러 전략을 동시에 실행하거나, 하나의 전략을 여러 파라미터로 병렬 실행
    """
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_processes: bool = True
    ):
        """
        Args:
            max_workers: 최대 워커 수 (None이면 CPU 코어 수)
            use_processes: True면 프로세스 풀, False면 스레드 풀
        """
        self.max_workers = max_workers or mp.cpu_count()
        self.use_processes = use_processes
        
        logger.info(f"ParallelBacktestEngine initialized: {self.max_workers} workers, processes={use_processes}")
    
    async def run_multiple_strategies(
        self,
        strategies: List[BaseStrategy],
        ohlc_data: List[OHLC],
        initial_capital: float = 10_000_000,
        commission: float = 0.0015,
        slippage: float = 0.0005
    ) -> List[BacktestResult]:
        """
        여러 전략을 병렬로 실행
        
        Args:
            strategies: 전략 리스트
            ohlc_data: OHLC 데이터
            initial_capital: 초기 자본
            commission: 수수료율
            slippage: 슬리피지
            
        Returns:
            백테스트 결과 리스트
        """
        logger.info(f"Running {len(strategies)} strategies in parallel")
        
        # 전략별 태스크 생성
        tasks = []
        for strategy in strategies:
            task = self._run_single_strategy_async(
                strategy, ohlc_data, initial_capital, commission, slippage
            )
            tasks.append(task)
        
        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Strategy {strategies[i].name} failed: {result}")
            else:
                successful_results.append(result)
        
        logger.info(f"Completed {len(successful_results)}/{len(strategies)} strategies")
        return successful_results
    
    async def run_parameter_optimization(
        self,
        strategy_class: type,
        parameter_grid: Dict[str, List[Any]],
        ohlc_data: List[OHLC],
        initial_capital: float = 10_000_000,
        commission: float = 0.0015,
        slippage: float = 0.0005
    ) -> List[BacktestResult]:
        """
        파라미터 그리드 서치를 병렬로 실행
        
        Args:
            strategy_class: 전략 클래스
            parameter_grid: 파라미터 그리드 {"param1": [val1, val2], "param2": [val3, val4]}
            ohlc_data: OHLC 데이터
            initial_capital: 초기 자본
            commission: 수수료율
            slippage: 슬리피지
            
        Returns:
            백테스트 결과 리스트
        """
        # 파라미터 조합 생성
        param_combinations = self._generate_parameter_combinations(parameter_grid)
        
        logger.info(f"Running parameter optimization: {len(param_combinations)} combinations")
        
        # 전략 인스턴스 생성
        strategies = []
        for params in param_combinations:
            strategy = strategy_class(params)
            strategies.append(strategy)
        
        # 병렬 실행
        return await self.run_multiple_strategies(
            strategies, ohlc_data, initial_capital, commission, slippage
        )
    
    async def _run_single_strategy_async(
        self,
        strategy: BaseStrategy,
        ohlc_data: List[OHLC],
        initial_capital: float,
        commission: float,
        slippage: float
    ) -> BacktestResult:
        """
        단일 전략을 비동기로 실행
        """
        loop = asyncio.get_event_loop()
        
        if self.use_processes:
            # 프로세스 풀 사용
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                result = await loop.run_in_executor(
                    executor,
                    self._run_strategy_sync,
                    strategy, ohlc_data, initial_capital, commission, slippage
                )
        else:
            # 스레드 풀 사용
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                result = await loop.run_in_executor(
                    executor,
                    self._run_strategy_sync,
                    strategy, ohlc_data, initial_capital, commission, slippage
                )
        
        return result
    
    @staticmethod
    def _run_strategy_sync(
        strategy: BaseStrategy,
        ohlc_data: List[OHLC],
        initial_capital: float,
        commission: float,
        slippage: float
    ) -> BacktestResult:
        """
        동기 방식으로 전략 실행 (워커 프로세스/스레드에서 실행)
        """
        try:
            # 새로운 백테스트 엔진 생성
            engine = BacktestEngine(
                strategy=strategy,
                initial_capital=initial_capital,
                commission=commission,
                slippage=slippage
            )
            
            # 동기 실행 (asyncio.run 사용)
            result = asyncio.run(engine.run_single(ohlc_data))
            return result
            
        except Exception as e:
            logger.error(f"Strategy {strategy.name} execution failed: {e}")
            raise BacktestError(f"Strategy execution failed: {e}")
    
    def _generate_parameter_combinations(
        self, 
        parameter_grid: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """
        파라미터 그리드에서 모든 조합 생성
        
        Args:
            parameter_grid: {"param1": [val1, val2], "param2": [val3, val4]}
            
        Returns:
            [{"param1": val1, "param2": val3}, {"param1": val1, "param2": val4}, ...]
        """
        import itertools
        
        keys = list(parameter_grid.keys())
        values = list(parameter_grid.values())
        
        combinations = []
        for combination in itertools.product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)
        
        return combinations


class BatchBacktestEngine:
    """
    배치 백테스트 엔진
    
    대용량 데이터나 많은 전략을 메모리 효율적으로 처리
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        memory_limit_mb: int = 1024
    ):
        """
        Args:
            batch_size: 배치 크기
            memory_limit_mb: 메모리 제한 (MB)
        """
        self.batch_size = batch_size
        self.memory_limit_mb = memory_limit_mb
        
        logger.info(f"BatchBacktestEngine initialized: batch_size={batch_size}, memory_limit={memory_limit_mb}MB")
    
    async def run_large_scale_backtest(
        self,
        strategies: List[BaseStrategy],
        ohlc_data: List[OHLC],
        initial_capital: float = 10_000_000,
        commission: float = 0.0015,
        slippage: float = 0.0005
    ) -> List[BacktestResult]:
        """
        대규모 백테스트를 배치로 실행
        
        Args:
            strategies: 전략 리스트
            ohlc_data: OHLC 데이터
            initial_capital: 초기 자본
            commission: 수수료율
            slippage: 슬리피지
            
        Returns:
            백테스트 결과 리스트
        """
        logger.info(f"Running large scale backtest: {len(strategies)} strategies")
        
        all_results = []
        parallel_engine = ParallelBacktestEngine()
        
        # 배치별로 실행
        for i in range(0, len(strategies), self.batch_size):
            batch = strategies[i:i + self.batch_size]
            
            logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(strategies) + self.batch_size - 1)//self.batch_size}")
            
            # 배치 실행
            batch_results = await parallel_engine.run_multiple_strategies(
                batch, ohlc_data, initial_capital, commission, slippage
            )
            
            all_results.extend(batch_results)
            
            # 메모리 정리
            import gc
            gc.collect()
        
        logger.info(f"Large scale backtest completed: {len(all_results)} results")
        return all_results


# 사용 예제
async def example_parallel_backtest():
    """병렬 백테스트 사용 예제"""
    from core.strategy.examples.ma_cross import MACrossStrategy
    
    # 여러 파라미터로 전략 생성
    strategies = [
        MACrossStrategy({"fast_period": 5, "slow_period": 20}),
        MACrossStrategy({"fast_period": 10, "slow_period": 30}),
        MACrossStrategy({"fast_period": 15, "slow_period": 50}),
    ]
    
    # 샘플 데이터 (실제로는 데이터 로더에서 가져옴)
    ohlc_data = []  # OHLC 데이터 리스트
    
    # 병렬 실행
    engine = ParallelBacktestEngine()
    results = await engine.run_multiple_strategies(strategies, ohlc_data)
    
    # 결과 분석
    for result in results:
        print(f"Strategy: {result.strategy_name}")
        print(f"Total Return: {result.total_return:.2%}")
        print(f"MDD: {result.mdd:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print("-" * 40)


if __name__ == "__main__":
    asyncio.run(example_parallel_backtest())