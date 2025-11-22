"""
Genetic Algorithm 구현
"""
import asyncio
import random
from typing import List, Dict, Any, Type, Tuple
from datetime import datetime
from copy import deepcopy

from core.strategy.base import BaseStrategy
from core.backtest.engine import BacktestEngine
from core.automl.parameter_space import ParameterSpace
from utils.types import OHLC, BacktestResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GeneticAlgorithm:
    """
    Genetic Algorithm 파라미터 최적화
    
    진화 알고리즘을 사용하여 최적 파라미터를 탐색합니다.
    - 선택 (Selection)
    - 교차 (Crossover)
    - 돌연변이 (Mutation)
    """
    
    def __init__(
        self,
        strategy_class: Type[BaseStrategy],
        parameter_space: ParameterSpace,
        population_size: int = 20,
        generations: int = 10,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        initial_capital: float = 10_000_000,
        commission: float = 0.0015,
        slippage: float = 0.001
    ):
        """
        Args:
            strategy_class: 전략 클래스
            parameter_space: 파라미터 공간
            population_size: 개체군 크기
            generations: 세대 수
            mutation_rate: 돌연변이 확률
            crossover_rate: 교차 확률
            initial_capital: 초기 자본
            commission: 수수료율
            slippage: 슬리피지
        """
        self.strategy_class = strategy_class
        self.parameter_space = parameter_space
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        self.population: List[Dict[str, Any]] = []
        self.fitness_scores: List[float] = []
        self.results: List[BacktestResult] = []
        self.best_individual: Dict[str, Any] = None
        self.best_fitness: float = float('-inf')
        
        logger.info(
            f"GeneticAlgorithm initialized: "
            f"pop={population_size}, gen={generations}, "
            f"mutation={mutation_rate}, crossover={crossover_rate}"
        )
    
    async def run(
        self,
        ohlc_data: List[OHLC],
        start_date: datetime = None,
        end_date: datetime = None,
        fitness_metric: str = "sharpe_ratio"
    ) -> List[BacktestResult]:
        """
        Genetic Algorithm 실행
        
        Args:
            ohlc_data: OHLC 데이터
            start_date: 시작일
            end_date: 종료일
            fitness_metric: 적합도 메트릭
        
        Returns:
            백테스트 결과 리스트
        """
        logger.info(f"Starting Genetic Algorithm: {self.generations} generations")
        
        # 초기 개체군 생성
        self._initialize_population()
        
        # 세대 반복
        for generation in range(self.generations):
            logger.info(f"\n=== Generation {generation + 1}/{self.generations} ===")
            
            # 적합도 평가
            await self._evaluate_fitness(ohlc_data, start_date, end_date, fitness_metric)
            
            # 최고 개체 기록
            best_idx = self.fitness_scores.index(max(self.fitness_scores))
            if self.fitness_scores[best_idx] > self.best_fitness:
                self.best_fitness = self.fitness_scores[best_idx]
                self.best_individual = self.population[best_idx].copy()
                logger.info(f"New best fitness: {self.best_fitness:.4f}")
            
            # 통계 출력
            avg_fitness = sum(self.fitness_scores) / len(self.fitness_scores)
            logger.info(
                f"Fitness - Best: {max(self.fitness_scores):.4f}, "
                f"Avg: {avg_fitness:.4f}, "
                f"Worst: {min(self.fitness_scores):.4f}"
            )
            
            # 마지막 세대가 아니면 다음 세대 생성
            if generation < self.generations - 1:
                self._evolve()
        
        logger.info(f"\nGenetic Algorithm completed")
        logger.info(f"Best individual: {self.best_individual}")
        logger.info(f"Best fitness: {self.best_fitness:.4f}")
        
        return self.results
    
    def _initialize_population(self) -> None:
        """초기 개체군 생성"""
        logger.info(f"Initializing population: {self.population_size} individuals")
        
        self.population = []
        for _ in range(self.population_size):
            individual = self.parameter_space.sample()
            self.population.append(individual)
    
    async def _evaluate_fitness(
        self,
        ohlc_data: List[OHLC],
        start_date: datetime,
        end_date: datetime,
        fitness_metric: str
    ) -> None:
        """적합도 평가"""
        self.fitness_scores = []
        
        for i, individual in enumerate(self.population):
            try:
                # 전략 생성
                strategy = self.strategy_class(individual)
                
                # 백테스트 실행
                engine = BacktestEngine(
                    strategy=strategy,
                    initial_capital=self.initial_capital,
                    commission=self.commission,
                    slippage=self.slippage
                )
                
                result = await engine.run(ohlc_data, start_date, end_date)
                self.results.append(result)
                
                # 적합도 계산
                if fitness_metric == "sharpe_ratio":
                    fitness = result.sharpe_ratio
                elif fitness_metric == "total_return":
                    fitness = result.total_return
                elif fitness_metric == "mdd":
                    fitness = -result.mdd  # MDD는 낮을수록 좋음
                else:
                    fitness = result.sharpe_ratio
                
                self.fitness_scores.append(fitness)
            
            except Exception as e:
                logger.error(f"Error evaluating individual {i}: {e}")
                self.fitness_scores.append(float('-inf'))
    
    def _evolve(self) -> None:
        """다음 세대 생성"""
        new_population = []
        
        # 엘리트 보존 (상위 10%)
        elite_count = max(1, self.population_size // 10)
        elite_indices = sorted(
            range(len(self.fitness_scores)),
            key=lambda i: self.fitness_scores[i],
            reverse=True
        )[:elite_count]
        
        for idx in elite_indices:
            new_population.append(self.population[idx].copy())
        
        # 나머지 개체 생성
        while len(new_population) < self.population_size:
            # 선택
            parent1 = self._select_parent()
            parent2 = self._select_parent()
            
            # 교차
            if random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()
            
            # 돌연변이
            child1 = self._mutate(child1)
            child2 = self._mutate(child2)
            
            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)
        
        self.population = new_population[:self.population_size]
    
    def _select_parent(self) -> Dict[str, Any]:
        """토너먼트 선택"""
        tournament_size = 3
        tournament_indices = random.sample(
            range(len(self.population)),
            min(tournament_size, len(self.population))
        )
        
        best_idx = max(
            tournament_indices,
            key=lambda i: self.fitness_scores[i]
        )
        
        return self.population[best_idx].copy()
    
    def _crossover(
        self,
        parent1: Dict[str, Any],
        parent2: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """단일점 교차"""
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        # 탐색 파라미터만 교차
        param_keys = list(self.parameter_space.parameters.keys())
        if len(param_keys) > 1:
            crossover_point = random.randint(1, len(param_keys) - 1)
            
            for i, key in enumerate(param_keys):
                if i >= crossover_point:
                    child1[key], child2[key] = child2[key], child1[key]
        
        return child1, child2
    
    def _mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """돌연변이"""
        mutated = individual.copy()
        
        for param_name, param_range in self.parameter_space.parameters.items():
            if random.random() < self.mutation_rate:
                # 새로운 값으로 변이
                mutated[param_name] = param_range.sample()
        
        return mutated
    
    def get_best_results(self, top_n: int = 10) -> List[BacktestResult]:
        """최고 성과 결과 조회"""
        if not self.results:
            return []
        
        sorted_results = sorted(
            self.results,
            key=lambda r: r.sharpe_ratio,
            reverse=True
        )
        
        return sorted_results[:top_n]
