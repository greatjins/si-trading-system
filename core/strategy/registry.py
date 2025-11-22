"""
전략 레지스트리 - 전략 동적 로딩 및 관리
"""
from typing import Dict, Type, List, Any
import importlib
import inspect
from pathlib import Path

from core.strategy.base import BaseStrategy
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StrategyMetadata:
    """전략 메타데이터"""
    
    def __init__(
        self,
        name: str,
        strategy_class: Type[BaseStrategy],
        description: str = "",
        author: str = "",
        version: str = "1.0.0",
        parameters: Dict[str, Any] = None
    ):
        """
        Args:
            name: 전략 이름
            strategy_class: 전략 클래스
            description: 설명
            author: 작성자
            version: 버전
            parameters: 파라미터 정의
        """
        self.name = name
        self.strategy_class = strategy_class
        self.description = description
        self.author = author
        self.version = version
        self.parameters = parameters or {}
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "parameters": self.parameters,
            "class_name": self.strategy_class.__name__,
            "module": self.strategy_class.__module__
        }


class StrategyRegistry:
    """전략 레지스트리 - 싱글톤"""
    
    _instance = None
    _strategies: Dict[str, StrategyMetadata] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(
        cls,
        name: str,
        strategy_class: Type[BaseStrategy],
        description: str = "",
        author: str = "",
        version: str = "1.0.0",
        parameters: Dict[str, Any] = None
    ):
        """
        전략 등록
        
        Args:
            name: 전략 이름
            strategy_class: 전략 클래스
            description: 설명
            author: 작성자
            version: 버전
            parameters: 파라미터 정의
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"{strategy_class} must inherit from BaseStrategy")
        
        metadata = StrategyMetadata(
            name=name,
            strategy_class=strategy_class,
            description=description,
            author=author,
            version=version,
            parameters=parameters
        )
        
        cls._strategies[name] = metadata
        logger.info(f"Strategy registered: {name} (v{version})")
    
    @classmethod
    def unregister(cls, name: str):
        """
        전략 등록 해제
        
        Args:
            name: 전략 이름
        """
        if name in cls._strategies:
            del cls._strategies[name]
            logger.info(f"Strategy unregistered: {name}")
    
    @classmethod
    def get(cls, name: str) -> Type[BaseStrategy]:
        """
        전략 클래스 조회
        
        Args:
            name: 전략 이름
            
        Returns:
            전략 클래스
        """
        if name not in cls._strategies:
            raise ValueError(f"Strategy '{name}' not found in registry")
        
        return cls._strategies[name].strategy_class
    
    @classmethod
    def get_metadata(cls, name: str) -> StrategyMetadata:
        """
        전략 메타데이터 조회
        
        Args:
            name: 전략 이름
            
        Returns:
            전략 메타데이터
        """
        if name not in cls._strategies:
            raise ValueError(f"Strategy '{name}' not found in registry")
        
        return cls._strategies[name]
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        """
        등록된 전략 목록
        
        Returns:
            전략 이름 리스트
        """
        return list(cls._strategies.keys())
    
    @classmethod
    def list_metadata(cls) -> List[dict]:
        """
        전략 메타데이터 목록
        
        Returns:
            메타데이터 리스트
        """
        return [meta.to_dict() for meta in cls._strategies.values()]
    
    @classmethod
    def create_instance(cls, name: str, **kwargs) -> BaseStrategy:
        """
        전략 인스턴스 생성
        
        Args:
            name: 전략 이름
            **kwargs: 전략 파라미터
            
        Returns:
            전략 인스턴스
        """
        strategy_class = cls.get(name)
        return strategy_class(**kwargs)
    
    @classmethod
    def auto_discover(cls, package_path: str = "core.strategy"):
        """
        전략 자동 탐색 및 등록
        
        Args:
            package_path: 패키지 경로
        """
        try:
            # 패키지 임포트
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent
            
            # 모든 .py 파일 탐색
            for py_file in package_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                
                module_name = f"{package_path}.{py_file.stem}"
                
                try:
                    module = importlib.import_module(module_name)
                    
                    # BaseStrategy 상속 클래스 찾기
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseStrategy) and 
                            obj is not BaseStrategy and
                            obj.__module__ == module_name):
                            
                            # 메타데이터 추출
                            strategy_name = getattr(obj, "STRATEGY_NAME", name)
                            description = getattr(obj, "DESCRIPTION", obj.__doc__ or "")
                            author = getattr(obj, "AUTHOR", "")
                            version = getattr(obj, "VERSION", "1.0.0")
                            parameters = getattr(obj, "PARAMETERS", {})
                            
                            cls.register(
                                name=strategy_name,
                                strategy_class=obj,
                                description=description,
                                author=author,
                                version=version,
                                parameters=parameters
                            )
                
                except Exception as e:
                    logger.error(f"Failed to load module {module_name}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to auto-discover strategies: {e}")
    
    @classmethod
    def clear(cls):
        """모든 전략 등록 해제"""
        cls._strategies.clear()
        logger.info("All strategies cleared from registry")


def strategy(
    name: str = None,
    description: str = "",
    author: str = "",
    version: str = "1.0.0",
    parameters: Dict[str, Any] = None
):
    """
    전략 등록 데코레이터
    
    Args:
        name: 전략 이름 (기본값: 클래스명)
        description: 설명
        author: 작성자
        version: 버전
        parameters: 파라미터 정의
        
    Example:
        @strategy(
            name="MomentumStrategy",
            description="모멘텀 기반 전략",
            author="John Doe",
            version="1.0.0",
            parameters={
                "lookback": {"type": "int", "default": 20, "min": 5, "max": 100},
                "threshold": {"type": "float", "default": 0.02, "min": 0.0, "max": 0.1}
            }
        )
        class MomentumStrategy(BaseStrategy):
            pass
    """
    def decorator(cls):
        strategy_name = name or cls.__name__
        
        StrategyRegistry.register(
            name=strategy_name,
            strategy_class=cls,
            description=description or cls.__doc__ or "",
            author=author,
            version=version,
            parameters=parameters
        )
        
        return cls
    
    return decorator
