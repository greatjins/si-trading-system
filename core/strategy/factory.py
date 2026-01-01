"""
전략 팩토리 - JSON 설정 기반 전략 인스턴스 생성
"""
from typing import Dict, Any, Optional
import json

from core.strategy.base import BaseStrategy
from core.strategy.registry import StrategyRegistry
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StrategyFactory:
    """
    JSON 설정을 기반으로 전략 인스턴스를 생성하는 팩토리
    
    exec() 방식 대신 JSON 설정을 파싱하여 전략을 생성합니다.
    """
    
    @staticmethod
    def create_from_json(config: Dict[str, Any]) -> BaseStrategy:
        """
        JSON 설정으로부터 전략 인스턴스 생성
        
        Args:
            config: 전략 설정 딕셔너리 {
                "strategy_type": "ict_pyramiding" | "ma_cross" | ...,
                "parameters": {...},
                "name": "strategy_name"
            }
        
        Returns:
            전략 인스턴스
        
        Raises:
            ValueError: 전략 타입이 지원되지 않거나 설정이 잘못된 경우
        """
        strategy_type = config.get("strategy_type")
        parameters = config.get("parameters", {})
        name = config.get("name", "Unknown")
        
        if not strategy_type:
            raise ValueError("strategy_type is required in config")
        
        # config의 is_portfolio를 parameters에 포함 (전략 인스턴스에서 사용)
        if "is_portfolio" in config:
            parameters["is_portfolio"] = config.get("is_portfolio")
            logger.info(f"Added is_portfolio={config.get('is_portfolio')} to parameters from config")
        
        logger.info(f"Creating strategy: {strategy_type} with name: {name}")
        logger.info(f"  Parameters: {parameters}")
        
        # 레지스트리에서 전략 클래스 가져오기
        try:
            strategy_class = StrategyRegistry.get(strategy_type)
            strategy = strategy_class(params=parameters)
            logger.info(f"✓ Strategy created: {strategy_type}")
            return strategy
        except (ValueError, KeyError) as e:
            logger.error(f"Strategy not found in registry: {strategy_type}")
            raise ValueError(f"Unsupported strategy type: {strategy_type}") from e
    
    @staticmethod
    def create_from_db_config(db_config: Dict[str, Any]) -> BaseStrategy:
        """
        DB의 StrategyBuilderModel 설정으로부터 전략 생성
        
        Args:
            db_config: DB 설정 {
                "config": {...},  # JSON 설정
                "python_code": "...",  # 기존 코드 (사용 안 함)
                "name": "..."
            }
        
        Returns:
            전략 인스턴스
        """
        # config 필드가 JSON 문자열인 경우 파싱
        config_data = db_config.get("config")
        
        if config_data is None:
            raise ValueError("config field is required in db_config")
        
        if isinstance(config_data, str):
            try:
                config_data = json.loads(config_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in config field: {e}") from e
        
        if not isinstance(config_data, dict):
            raise ValueError(f"config must be a dict, got {type(config_data)}")
        
        # strategy_type이 config 안에 있는지 확인
        if "strategy_type" not in config_data:
            # 기존 전략 빌더 호환성: name에서 추론 시도
            name = db_config.get("name", "")
            if "ict" in name.lower():
                config_data["strategy_type"] = "ict_pyramiding"
            else:
                raise ValueError(f"Cannot infer strategy_type from name: {name}")
        
        # is_portfolio가 config 최상위에 있으면 parameters에도 포함
        if "is_portfolio" in config_data:
            if "parameters" not in config_data:
                config_data["parameters"] = {}
            config_data["parameters"]["is_portfolio"] = config_data["is_portfolio"]
            logger.info(f"Copied is_portfolio={config_data['is_portfolio']} from config to parameters")
        
        return StrategyFactory.create_from_json(config_data)
    
    @staticmethod
    def create_ict_pyramiding_strategy(parameters: Dict[str, Any]) -> BaseStrategy:
        """
        ICT Pyramiding 전략 생성 (편의 메서드)
        
        Args:
            parameters: 전략 파라미터
        
        Returns:
            ICT Pyramiding 전략 인스턴스
        """
        # 레지스트리에서 가져오기
        strategy_class = StrategyRegistry.get("ict_pyramiding")
        return strategy_class(params=parameters)
