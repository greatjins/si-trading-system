"""
간단한 포트폴리오 전략 (테스트용)

거래대금 상위 종목을 균등 분배
"""
from typing import List, Dict
from datetime import datetime
import pandas as pd

from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy
from utils.types import Position, Account, OrderSignal


@strategy(
    name="SimplePortfolioStrategy",
    version="1.0.0",
    description="거래대금 상위 종목 균등 분배 (테스트용)",
    parameters={
        "max_stocks": {
            "type": "int",
            "default": 10,
            "description": "최대 보유 종목 수"
        }
    }
)
class SimplePortfolioStrategy(BaseStrategy):
    """
    간단한 포트폴리오 전략 (테스트용)
    
    - 거래대금 상위 N개 선택
    - 균등 분배
    - 재무 조건 없음
    """
    
    def select_universe(
        self,
        date: datetime,
        market_data: pd.DataFrame
    ) -> List[str]:
        """
        거래대금 상위 종목 선택
        """
        max_stocks = self.get_param("max_stocks", 10)
        
        if market_data.empty:
            return []
        
        # 거래대금이 있는 종목만
        valid = market_data[market_data['volume_amount'] > 0].copy()
        
        if valid.empty:
            return []
        
        # 거래대금 상위 N개
        top_stocks = valid.nlargest(max_stocks, 'volume_amount')
        
        return top_stocks.index.tolist()
    
    def on_bar(self, bars, positions, account):
        """포트폴리오 전략은 비워둠"""
        return []
    
    def on_fill(self, order, position):
        """주문 체결 콜백"""
        pass
