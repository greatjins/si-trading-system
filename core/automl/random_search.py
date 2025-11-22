"""
Random Search 구현
"""
import asyncio
from typing import List, Dict, Any, Type
from datetime import datetime

from core.strategy.base import BaseStrategy
from core.backtest.engine import BacktestEngine
from core.automl.parameter_space import ParameterSpace
from utils.types import OHLC, BacktestResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RandomSearch:
    """
    Random Search 파라미터 최적화
    
    파라미터 공간에서 랜덤하게 샘플링하여 탐색합니다.
    Grid Search보다 빠르고 효율적일 수 있습니다.
    """
    
    def __init__(
        self,
        strategy_class: Type[BaseStrategy],
        parameter_space: ParameterSpace,
        n_iterations: int = 100,
        initial_capital: float = 10_000_000,
        commission: float = 0.0015,
        slippage: float = 0.001
    ):
        """
        Args:
            strategy_class: 전략 클래스
            parameter_space: 파라미터 공간
            n_iterations: 반복 횟수
            initial_capital: 초기 자본
            commission: 수수료율
            slippage: 슬리피지
        """
        self.strategy_class = strategy_class
        self.parameter_space = parameter_space
        self.n_iterations = n_iterations
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        self.results: List[BacktestResult] = []
        
        logger.info(f"RandomSearch initialized: {n_iterations} iterations")
    
    async def run(
        self,
        ohlc_data: List[OHLC],
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[BacktestResult]:
        """
        Random Search 실행
        
        Args:
            ohlc_data: OHLC 데이터
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            백테스트 결과 리스트
        """
        logger.info(f"Starting Random Search: {self.n_iterations} iterations")
        
        self.results = []
        tested_params = set()  # 중복 방지
        
        for i in range(self.n_iterations):
            # 랜덤 파라미터 샘플링
            params = self.parameter_space.sample()
            
            # 중복 확인
            params_tuple = tuple(sorted(params.items()))
            if params_tuple in tested_params:
                logger.debug(f"[{i+1}/{self.n_iterations}] Duplicate params, skipping")
                continue
            
            tested_params.add(params_tuple)
            
            logger.info(f"[{i+1}/{self.n_iterations}] Testing: {params}")
            
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
        
        logger.info(f"Random Search completed: {len(self.results)} results")
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
            )
        else:
            sorted_results = self.results
        
        return sorted_results[:top_n]
    
    def get_statistics(self) -> Dict[str, Any]:
        """탐색 통계"""
        if not self.results:
            return {}
        
        returns = [r.total_return for r in self.results]
        mdds = [r.mdd for r in self.results]
        sharpes = [r.sharpe_ratio for r in self.results]
        
        return {
            "total_iterations": len(self.results),
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
