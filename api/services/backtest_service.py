"""
백테스트 실행 서비스
"""
from typing import Dict, Any
from datetime import datetime
import pandas as pd

from core.backtest.engine import BacktestEngine
from core.backtest.result import BacktestResult
from data.repository import DataRepository
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BacktestService:
    """백테스트 실행 관리 서비스"""
    
    def __init__(self):
        self.data_repo = DataRepository()
    
    async def run_backtest(
        self,
        strategy_name: str,
        parameters: Dict[str, Any],
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10_000_000
    ) -> BacktestResult:
        """
        백테스트 실행
        
        Args:
            strategy_name: 전략 이름
            parameters: 전략 파라미터
            symbol: 종목 코드
            interval: 시간 간격
            start_date: 시작일
            end_date: 종료일
            initial_capital: 초기 자본
            
        Returns:
            백테스트 결과
        """
        try:
            # 데이터 로드
            data = self.data_repo.get_ohlc(
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date
            )
            
            if data.empty:
                raise ValueError(f"No data found for {symbol}")
            
            # TODO: 전략 레지스트리에서 전략 클래스 가져오기
            # strategy_class = StrategyRegistry.get(strategy_name)
            # strategy = strategy_class(**parameters)
            
            # 백테스트 엔진 생성
            engine = BacktestEngine(
                initial_capital=initial_capital,
                commission=0.00015
            )
            
            # 백테스트 실행
            # result = engine.run(strategy, data)
            
            # TODO: 결과를 DB에 저장
            
            logger.info(f"Backtest completed for {strategy_name} on {symbol}")
            
            # 임시 결과 반환
            raise NotImplementedError("Backtest execution not fully implemented")
        
        except Exception as e:
            logger.error(f"Failed to run backtest: {e}")
            raise
    
    def get_backtest_result(self, backtest_id: int) -> Dict[str, Any]:
        """
        백테스트 결과 조회
        
        Args:
            backtest_id: 백테스트 ID
            
        Returns:
            백테스트 결과
        """
        # TODO: DB에서 결과 조회
        raise NotImplementedError("Not implemented yet")
    
    def get_all_results(self) -> list:
        """
        모든 백테스트 결과 조회
        
        Returns:
            백테스트 결과 리스트
        """
        # TODO: DB에서 결과 조회
        return []
