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
                "id": int,  # StrategyBuilderModel.id (선택)
                "config": {...},  # JSON 설정 (기존 호환성)
                "config_json": {...},  # 구조화된 설정 (우선 사용)
                "python_code": "...",  # 기존 코드 (사용 안 함)
                "name": "..."
            }
        
        Returns:
            전략 인스턴스 (DynamicStrategy 또는 기존 전략)
        """
        # config_json이 있으면 DynamicStrategy 사용
        config_json = db_config.get("config_json")
        strategy_id = db_config.get("id")
        
        if config_json and strategy_id:
            logger.info(f"Creating DynamicStrategy from config_json: strategy_id={strategy_id}")
            from core.strategy.dynamic import DynamicStrategy
            
            params = {
                "strategy_id": strategy_id,
                "config_json": config_json,
                "name": db_config.get("name", "DynamicStrategy")
            }
            
            # parameters 추가 (config_json에서)
            if isinstance(config_json, dict):
                params.update(config_json.get("parameters", {}))
            
            return DynamicStrategy(params=params)
        
        # 기존 방식 (config 필드 사용)
        config_data = db_config.get("config")
        
        if config_data is None:
            raise ValueError("config or config_json field is required in db_config")
        
        if isinstance(config_data, str):
            try:
                config_data = json.loads(config_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in config field: {e}") from e
        
        if not isinstance(config_data, dict):
            raise ValueError(f"config must be a dict, got {type(config_data)}")
        
        # strategy_type이 config 안에 있는지 확인
        if "strategy_type" not in config_data:
            # 전략 빌더로 생성된 전략인지 확인 (stockSelection, buyConditions 등이 있으면 DynamicStrategy)
            has_builder_fields = any(key in config_data for key in [
                "stockSelection", "buyConditions", "sellConditions", 
                "entryStrategy", "positionManagement"
            ])
            
            if has_builder_fields:
                # 전략 빌더로 생성된 전략: DynamicStrategy 사용
                logger.info(f"Detected strategy builder config, using DynamicStrategy: {db_config.get('name', 'Unknown')}")
                from core.strategy.dynamic import DynamicStrategy
                
                # config에서 config_json 형태로 변환
                config_json = {
                    "indicators": [],  # 기존 config에는 지표 정보가 없을 수 있음
                    "conditions": {
                        "buy": config_data.get("buyConditions", []),
                        "sell": config_data.get("sellConditions", [])
                    }
                }
                
                if config_data.get("stockSelection"):
                    config_json["stock_selection"] = config_data["stockSelection"]
                
                if config_data.get("entryStrategy"):
                    config_json["entry_strategy"] = config_data["entryStrategy"]
                
                if config_data.get("positionManagement"):
                    config_json["position_management"] = config_data["positionManagement"]
                
                # parameters 초기화
                if "parameters" not in config_json:
                    config_json["parameters"] = {}
                
                # config_data의 parameters 병합
                if "parameters" in config_data:
                    config_json["parameters"].update(config_data["parameters"])
                
                # is_portfolio를 parameters에 추가
                if "is_portfolio" in config_data:
                    config_json["parameters"]["is_portfolio"] = config_data["is_portfolio"]
                
                params = {
                    "config_json": config_json,
                    "name": db_config.get("name", "DynamicStrategy")
                }
                
                # strategy_id가 있으면 추가
                if strategy_id:
                    params["strategy_id"] = strategy_id
                
                return DynamicStrategy(params=params)
            
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
