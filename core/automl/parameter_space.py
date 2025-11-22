"""
파라미터 공간 정의
"""
from typing import Dict, Any, List, Union
from dataclasses import dataclass
import random

from utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ParameterRange:
    """파라미터 범위"""
    name: str
    min_value: Union[int, float]
    max_value: Union[int, float]
    step: Union[int, float] = None
    param_type: str = "int"  # "int", "float"
    
    def sample(self) -> Union[int, float]:
        """랜덤 샘플링"""
        if self.param_type == "int":
            return random.randint(int(self.min_value), int(self.max_value))
        else:
            return random.uniform(self.min_value, self.max_value)
    
    def get_grid_values(self) -> List[Union[int, float]]:
        """그리드 값 생성"""
        if self.step is None:
            # 기본 스텝 설정
            if self.param_type == "int":
                self.step = 1
            else:
                self.step = (self.max_value - self.min_value) / 10
        
        values = []
        current = self.min_value
        
        while current <= self.max_value:
            if self.param_type == "int":
                values.append(int(current))
            else:
                values.append(float(current))
            current += self.step
        
        return values


class ParameterSpace:
    """
    파라미터 공간
    
    전략 파라미터의 탐색 범위를 정의합니다.
    """
    
    def __init__(self):
        self.parameters: Dict[str, ParameterRange] = {}
        self.fixed_params: Dict[str, Any] = {}
    
    def add_parameter(
        self,
        name: str,
        min_value: Union[int, float],
        max_value: Union[int, float],
        step: Union[int, float] = None,
        param_type: str = "int"
    ) -> None:
        """
        파라미터 추가
        
        Args:
            name: 파라미터 이름
            min_value: 최소값
            max_value: 최대값
            step: 스텝 (그리드 탐색용)
            param_type: 타입 ("int" 또는 "float")
        """
        param_range = ParameterRange(
            name=name,
            min_value=min_value,
            max_value=max_value,
            step=step,
            param_type=param_type
        )
        self.parameters[name] = param_range
        
        logger.debug(f"Parameter added: {name} [{min_value}, {max_value}]")
    
    def add_fixed_parameter(self, name: str, value: Any) -> None:
        """
        고정 파라미터 추가 (탐색하지 않음)
        
        Args:
            name: 파라미터 이름
            value: 고정값
        """
        self.fixed_params[name] = value
        logger.debug(f"Fixed parameter added: {name} = {value}")
    
    def sample(self) -> Dict[str, Any]:
        """
        랜덤 파라미터 샘플링
        
        Returns:
            파라미터 딕셔너리
        """
        params = {}
        
        # 탐색 파라미터
        for name, param_range in self.parameters.items():
            params[name] = param_range.sample()
        
        # 고정 파라미터
        params.update(self.fixed_params)
        
        return params
    
    def get_grid(self) -> List[Dict[str, Any]]:
        """
        그리드 파라미터 조합 생성
        
        Returns:
            파라미터 조합 리스트
        """
        # 각 파라미터의 그리드 값
        param_grids = {}
        for name, param_range in self.parameters.items():
            param_grids[name] = param_range.get_grid_values()
        
        # 카르테시안 곱
        combinations = self._cartesian_product(param_grids)
        
        # 고정 파라미터 추가
        for combo in combinations:
            combo.update(self.fixed_params)
        
        logger.info(f"Generated {len(combinations)} parameter combinations")
        return combinations
    
    def _cartesian_product(self, param_grids: Dict[str, List]) -> List[Dict[str, Any]]:
        """카르테시안 곱 계산"""
        if not param_grids:
            return [{}]
        
        keys = list(param_grids.keys())
        values = list(param_grids.values())
        
        combinations = []
        self._generate_combinations(keys, values, 0, {}, combinations)
        
        return combinations
    
    def _generate_combinations(
        self,
        keys: List[str],
        values: List[List],
        index: int,
        current: Dict[str, Any],
        result: List[Dict[str, Any]]
    ) -> None:
        """재귀적으로 조합 생성"""
        if index == len(keys):
            result.append(current.copy())
            return
        
        key = keys[index]
        for value in values[index]:
            current[key] = value
            self._generate_combinations(keys, values, index + 1, current, result)
    
    def get_parameter_count(self) -> int:
        """탐색 파라미터 개수"""
        return len(self.parameters)
    
    def get_total_combinations(self) -> int:
        """총 조합 개수 (그리드 탐색)"""
        total = 1
        for param_range in self.parameters.values():
            grid_values = param_range.get_grid_values()
            total *= len(grid_values)
        return total
    
    def __repr__(self) -> str:
        return f"ParameterSpace({len(self.parameters)} params, {self.get_total_combinations()} combinations)"
