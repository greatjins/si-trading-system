"""
Grid Search 구현
"""
import asyncio
from typing import List, Dict, Any, Type
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

from core.strategy.base import BaseStrategy
from core.backtest.engine import BacktestEngine
from core.automl.parameter_space import ParameterSpace
from utils.types import OHLC, BacktestResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GridSearch:
    """
    Grid Search 파라미터 최적화
    
    모든 파라미터 조합을 체계적으로 탐색합니다.
    """
    
    def __init__(
        self,
        strategy_class: Type[BaseStrategy],
        parameter_space: ParameterSpace,
        initial_capital: float = 10_000_000,
        commission: float = 0.0015,
        slippage: float = 0.001,
        n_jobs: int = None
    ):
        """
        Args:
            strategy_class: 전략 클래스
            parameter_space: 파라미터 공간
            initial_capital: 초기 자본
            commission: 수수료율
            slippage: 슬리피지
            n_jobs: 병렬 작업 수 (None이면 CPU 코어 수)
        """
        self.strategy_class = strategy_class
        self.parameter_space = parameter_space
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.n_jobs = n_jobs or mp.cpu_count()
        
        self.results: List[BacktestResult] = []
        
        logger.info(f"GridSearch initialized: {parameter_space}")
        logger.info(f"Parallel jobs: {self.n_jobs}")
    
    async def run(
        self,
        ohlc_data: List[OHLC],
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[BacktestResult]:
        """
        Grid Search 실행
        
        Args:
            ohlc_data: OHLC 데이터
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            백테스트 결과 리스트
        """
        # 파라미터 조합 생성
        param_combinations = self.parameter_space.get_grid()
        total_combinations = len(param_combinations)
        
        logger.info(f"Starting Grid Search: {total_combinations} combinations")
        
        # 백테스트 실행
        self.results = []
        
        for i, params in enumerate(param_combinations, 1):
            logger.info(f"[{i}/{total_combinations}] Testing: {params}")
            
            try:
                # 전략 생성
                strategy = self.strategy_class(params)
                
                # 백테스트 실행
                engine = BacktestEngine(
                    strategy=strategy,
                    initial_capital=self.initial_capital,
                    commission=self.commission,
                    slippage=self.slippage
                )
                
                result = await engine.run(ohlc_data, start_date, end_date)
                self.results.append(result)
                
                logger.info(
                    f"  Result: Return={result.total_return:+.2%}, "
                    f"MDD={result.mdd:.2%}, Sharpe={result.sharpe_ratio:.2f}"
                )
            
            except Exception as e:
                logger.error(f"  Error: {e}")
                continue
        
        logger.info(f"Grid Search completed: {len(self.results)} results")
        return self.results
    
    def get_best_results(
        self,
        metric: str = "sharpe_ratio",
        top_n: int = 10
    ) -> List[BacktestResult]:
        """
        최고 성과 결과 조회
        
        Args:
            metric: 정렬 기준 메트릭
            top_n: 상위 N개
        
        Returns:
            상위 결과 리스트
        """
        if not self.results:
            return []
        
        # 메트릭별 정렬
        if metric == "total_return":
            sorted_results = sorted(
                self.results,
                key=lambda r: r.total_return,
                reverse=True
            )
        elif metric == "sharpe_ratio":
            sorted_results = sorted(
                self.results,
                key=lambda r: r.sharpe_ratio,
                reverse=True
            )
        elif metric == "mdd":
            sorted_results = sorted(
                self.results,
                key=lambda r: r.mdd
            )  # MDD는 낮을수록 좋음
        else:
            sorted_results = self.results
        
        return sorted_results[:top_n]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        탐색 통계
        
        Returns:
            통계 딕셔너리
        """
        if not self.results:
            return {}
        
        returns = [r.total_return for r in self.results]
        mdds = [r.mdd for r in self.results]
        sharpes = [r.sharpe_ratio for r in self.results]
        
        return {
            "total_combinations": len(self.results),
            "avg_return": sum(returns) / len(returns),
            "max_return": max(returns),
            "min_return": min(returns),
            "avg_mdd": sum(mdds) / len(mdds),
            "min_mdd": min(mdds),
            "max_mdd": max(mdds),
            "avg_sharpe": sum(sharpes) / len(sharpes),
            "max_sharpe": max(sharpes),
            "min_sharpe": min(sharpes),
        }
