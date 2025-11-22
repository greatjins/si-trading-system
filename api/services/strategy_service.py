"""
전략 실행 서비스
"""
from typing import Dict, Any, List
from datetime import datetime
import uuid

from core.execution.engine import ExecutionEngine
from broker.base import BrokerBase
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StrategyService:
    """전략 실행 관리 서비스"""
    
    def __init__(self, broker: BrokerBase):
        """
        Args:
            broker: 브로커 인스턴스
        """
        self.broker = broker
        self.engines: Dict[str, ExecutionEngine] = {}
    
    async def start_strategy(
        self,
        strategy_name: str,
        parameters: Dict[str, Any],
        symbols: List[str]
    ) -> Dict[str, Any]:
        """
        전략 시작
        
        Args:
            strategy_name: 전략 이름
            parameters: 전략 파라미터
            symbols: 종목 리스트
            
        Returns:
            전략 정보
        """
        strategy_id = str(uuid.uuid4())
        
        try:
            # TODO: 전략 레지스트리에서 전략 클래스 가져오기
            # strategy_class = StrategyRegistry.get(strategy_name)
            # strategy = strategy_class(**parameters)
            
            # ExecutionEngine 생성 및 시작
            engine = ExecutionEngine(
                broker=self.broker,
                strategy=None,  # TODO: 실제 전략 인스턴스
                symbols=symbols
            )
            
            # TODO: engine.start() 구현 필요
            # await engine.start()
            
            self.engines[strategy_id] = engine
            
            logger.info(f"Strategy {strategy_id} started: {strategy_name}")
            
            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
                "parameters": parameters,
                "symbols": symbols,
                "is_running": True,
                "created_at": datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Failed to start strategy: {e}")
            raise
    
    async def stop_strategy(self, strategy_id: str) -> None:
        """
        전략 중지
        
        Args:
            strategy_id: 전략 ID
        """
        if strategy_id not in self.engines:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        try:
            engine = self.engines[strategy_id]
            # TODO: engine.stop() 구현 필요
            # await engine.stop()
            
            del self.engines[strategy_id]
            
            logger.info(f"Strategy {strategy_id} stopped")
        
        except Exception as e:
            logger.error(f"Failed to stop strategy: {e}")
            raise
    
    def get_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """
        전략 정보 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            전략 정보
        """
        if strategy_id not in self.engines:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        engine = self.engines[strategy_id]
        
        # TODO: 실제 전략 정보 반환
        return {
            "strategy_id": strategy_id,
            "is_running": True,
            "created_at": datetime.now()
        }
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """
        모든 전략 조회
        
        Returns:
            전략 리스트
        """
        return [
            self.get_strategy(strategy_id)
            for strategy_id in self.engines.keys()
        ]
