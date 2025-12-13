"""
가치주 포트폴리오 전략

PER, PBR이 낮은 종목을 선택하여 균등 분배하는 전략
"""
from typing import List, Dict
from datetime import datetime
import pandas as pd

from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy
from utils.types import Position, Account, OrderSignal, OrderSide, OrderType


@strategy(
    name="ValuePortfolioStrategy",
    version="1.0.0",
    description="PER/PBR 기반 가치주 포트폴리오 전략",
    parameters={
        "per_max": {
            "type": "float",
            "default": 10.0,
            "description": "최대 PER"
        },
        "pbr_max": {
            "type": "float",
            "default": 1.0,
            "description": "최대 PBR"
        },
        "roe_min": {
            "type": "float",
            "default": 10.0,
            "description": "최소 ROE"
        },
        "max_stocks": {
            "type": "int",
            "default": 20,
            "description": "최대 보유 종목 수"
        },
        "rebalance_days": {
            "type": "int",
            "default": 30,
            "description": "리밸런싱 주기 (일)"
        }
    }
)
class ValuePortfolioStrategy(BaseStrategy):
    """
    가치주 포트폴리오 전략
    
    - PER < per_max
    - PBR < pbr_max
    - ROE > roe_min
    - 거래대금 상위 N개 선택
    - 균등 분배
    """
    
    def __init__(self, params: Dict):
        super().__init__(params)
        self.last_rebalance_date = None
    
    def select_universe(
        self,
        date: datetime,
        market_data: pd.DataFrame
    ) -> List[str]:
        """
        가치주 종목 선택
        
        Args:
            date: 현재 날짜
            market_data: 시장 데이터
        
        Returns:
            선택된 종목 리스트
        """
        per_max = self.get_param("per_max", 10.0)
        pbr_max = self.get_param("pbr_max", 1.0)
        roe_min = self.get_param("roe_min", 10.0)
        max_stocks = self.get_param("max_stocks", 20)
        
        # 재무 조건 필터링
        filtered = market_data[
            (market_data['per'] > 0) &
            (market_data['per'] < per_max) &
            (market_data['pbr'] > 0) &
            (market_data['pbr'] < pbr_max) &
            (market_data['roe'] > roe_min)
        ].copy()
        
        if filtered.empty:
            return []
        
        # 거래대금 상위 N개
        top_stocks = filtered.nlargest(max_stocks, 'volume_amount')
        
        return top_stocks.index.tolist()
    
    def get_target_weights(
        self,
        universe: List[str],
        market_data: pd.DataFrame,
        account: Account
    ) -> Dict[str, float]:
        """
        균등 분배
        
        Args:
            universe: 선택된 종목
            market_data: 시장 데이터
            account: 계좌 상태
        
        Returns:
            종목별 목표 비중
        """
        if not universe:
            return {}
        
        # 균등 분배
        weight = 1.0 / len(universe)
        return {symbol: weight for symbol in universe}
    
    def on_bar(
        self,
        bars: pd.DataFrame,
        positions: List[Position],
        account: Account
    ) -> List[OrderSignal]:
        """
        매매 신호 생성
        
        Note:
            포트폴리오 전략에서는 백테스트 엔진이 리밸런싱을 처리하므로
            이 메서드는 비워둡니다.
        """
        return []
    
    def on_fill(self, order, position) -> None:
        """주문 체결 콜백"""
        pass
