"""
전략 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from utils.types import OHLC, Position, Account, OrderSignal, Order
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseStrategy(ABC):
    """
    모든 트레이딩 전략의 기본 클래스
    
    전략은 브로커 API를 직접 호출하지 않고,
    엔진으로부터 데이터를 받아 주문 신호만 반환합니다.
    
    이를 통해 전략 코드가 브로커 구현으로부터 완전히 분리됩니다.
    """
    
    def __init__(self, params: Dict[str, Any]):
        """
        Args:
            params: 전략 파라미터 딕셔너리
        """
        self.params = params
        self.name = self.__class__.__name__
        
        logger.info(f"Strategy initialized: {self.name}")
        logger.debug(f"Parameters: {params}")
    
    @abstractmethod
    def on_bar(
        self,
        bars: pd.DataFrame,
        positions: List[Position],
        account: Account
    ) -> List[OrderSignal]:
        """
        새로운 바마다 호출됨 (백테스트) 또는 가격 업데이트마다 호출됨 (실시간)
        
        Args:
            bars: OHLCV DataFrame
                - Index: timestamp (datetime)
                - Columns: ['open', 'high', 'low', 'close', 'volume', 'value']
                - 가장 최근 바가 마지막 행
            positions: 현재 보유 포지션 리스트
            account: 현재 계좌 상태
        
        Returns:
            주문 신호 리스트 (매수/매도/청산)
        
        Note:
            - 전략은 브로커 API를 직접 호출하지 않습니다
            - 엔진이 제공한 데이터만 사용합니다
            - 주문 신호만 반환하며, 실제 주문은 엔진이 처리합니다
            - bars DataFrame은 최소 ['open', 'high', 'low', 'close', 'volume'] 컬럼을 포함합니다
            - 'value' 컬럼이 없으면 volume * close로 계산됩니다
        
        Example:
            ```python
            def on_bar(self, bars, positions, account):
                if len(bars) < 20:
                    return []
                
                # 기술적 지표 계산
                ma20 = bars['close'].rolling(20).mean()
                current_price = bars['close'].iloc[-1]
                
                # 매수 신호
                if current_price > ma20.iloc[-1]:
                    return [OrderSignal(...)]
                
                return []
            ```
        """
        pass
    
    @abstractmethod
    def on_fill(self, order: Order, position: Position) -> None:
        """
        주문이 체결될 때 호출됨
        
        Args:
            order: 체결된 주문
            position: 업데이트된 포지션
        
        Note:
            전략 상태 업데이트나 로깅에 사용
        """
        pass
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """
        파라미터 조회
        
        Args:
            key: 파라미터 키
            default: 기본값
        
        Returns:
            파라미터 값
        """
        return self.params.get(key, default)
    
    def set_param(self, key: str, value: Any) -> None:
        """
        파라미터 설정
        
        Args:
            key: 파라미터 키
            value: 파라미터 값
        """
        self.params[key] = value
    
    def get_position(self, symbol: str, positions: List[Position]) -> Optional[Position]:
        """
        특정 종목의 포지션 조회
        
        Args:
            symbol: 종목코드
            positions: 포지션 리스트
        
        Returns:
            포지션 (없으면 None)
        """
        for position in positions:
            if position.symbol == symbol:
                return position
        return None
    
    def has_position(self, symbol: str, positions: List[Position]) -> bool:
        """
        특정 종목의 포지션 보유 여부
        
        Args:
            symbol: 종목코드
            positions: 포지션 리스트
        
        Returns:
            보유 여부
        """
        return self.get_position(symbol, positions) is not None
    
    def select_universe(
        self,
        date: datetime,
        market_data: pd.DataFrame
    ) -> List[str]:
        """
        매일 거래할 종목 유니버스 선택 (포트폴리오 전략용)
        
        Args:
            date: 현재 날짜
            market_data: 전체 시장 데이터
                - Index: symbol (종목코드)
                - Columns: ['close', 'volume', 'per', 'pbr', 'roe', 'market_cap', ...]
        
        Returns:
            선택된 종목 코드 리스트
        
        Note:
            - 기본 구현은 빈 리스트 반환 (단일 종목 전략 하위 호환)
            - 포트폴리오 전략은 이 메서드를 오버라이드하여 종목 선택 로직 구현
            - 반환된 종목들에 대해 on_bar()가 호출됨
        
        Example:
            ```python
            def select_universe(self, date, market_data):
                # PER < 10, PBR < 1.0 종목 선택
                filtered = market_data[
                    (market_data['per'] < 10) & 
                    (market_data['pbr'] < 1.0)
                ]
                # 거래대금 상위 20개
                top20 = filtered.nlargest(20, 'volume_amount')
                return top20.index.tolist()
            ```
        """
        return []
    
    def get_target_weights(
        self,
        universe: List[str],
        market_data,  # Union[pd.DataFrame, Dict[str, float]]
        account: Account
    ) -> Dict[str, float]:
        """
        각 종목의 목표 비중 계산 (포트폴리오 전략용)
        
        Args:
            universe: 선택된 종목 리스트
            market_data: 시장 데이터 (DataFrame 또는 Dict[symbol, price])
            account: 계좌 상태
        
        Returns:
            종목별 목표 비중 (합계 1.0)
            예: {"005930": 0.2, "000660": 0.3, "035420": 0.5}
        
        Note:
            - 기본 구현은 균등 분배
            - 포트폴리오 전략은 이 메서드를 오버라이드하여 비중 로직 구현
            - market_data는 DataFrame(전체 시장 데이터) 또는 Dict(가격만)일 수 있음
        
        Example:
            ```python
            def get_target_weights(self, universe, market_data, account):
                # DataFrame인 경우
                if isinstance(market_data, pd.DataFrame):
                    market_caps = market_data.loc[universe, 'market_cap']
                    total_cap = market_caps.sum()
                    return {symbol: cap / total_cap for symbol, cap in market_caps.items()}
                # Dict인 경우 (균등 분배)
                else:
                    weight = 1.0 / len(universe)
                    return {symbol: weight for symbol in universe}
            ```
        """
        if not universe:
            return {}
        
        # 기본: 균등 분배
        weight = 1.0 / len(universe)
        return {symbol: weight for symbol in universe}
    
    def is_portfolio_strategy(self) -> bool:
        """
        포트폴리오 전략 여부 확인
        
        Returns:
            True: 포트폴리오 전략 (여러 종목)
            False: 단일 종목 전략
        """
        # select_universe가 오버라이드되었는지 확인
        return self.__class__.select_universe != BaseStrategy.select_universe
    
    def __repr__(self) -> str:
        return f"{self.name}({self.params})"
