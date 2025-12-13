"""
포지션 관리
"""
from typing import Dict, List, Optional
from datetime import datetime

from utils.types import Position, Trade, OrderSide
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PositionManager:
    """
    포지션 추적 및 관리
    
    - 진입, 청산, 피라미딩 처리
    - 미실현/실현 손익 계산
    - 거래 내역 기록
    """
    
    def __init__(self, commission: float = 0.0015):
        """
        Args:
            commission: 수수료율 (기본: 0.15%)
        """
        self.commission = commission
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[Trade] = []
        
        logger.info(f"PositionManager initialized with commission: {commission:.4%}")
    
    def open_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
        timestamp: datetime
    ) -> Trade:
        """
        포지션 진입 (신규 또는 피라미딩)
        
        Args:
            symbol: 종목코드
            quantity: 수량
            price: 진입가
            timestamp: 시간
        
        Returns:
            거래 기록
        """
        commission_cost = quantity * price * self.commission
        
        if symbol in self.positions:
            # 피라미딩 (기존 포지션에 추가)
            position = self.positions[symbol]
            
            # 평균 단가 재계산
            total_cost = (position.avg_price * position.quantity) + (price * quantity)
            total_quantity = position.quantity + quantity
            position.avg_price = total_cost / total_quantity
            position.quantity = total_quantity
            
            logger.info(f"피라미딩: {symbol}, +{quantity}주 @ {price:,.0f}, 총 {total_quantity}주")
        else:
            # 신규 포지션
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                current_price=price,
                unrealized_pnl=0.0,
                realized_pnl=0.0
            )
            
            logger.info(f"포지션 진입: {symbol}, {quantity}주 @ {price:,.0f}")
        
        # 거래 기록
        trade = Trade(
            trade_id=f"{symbol}_{timestamp.strftime('%Y%m%d%H%M%S')}",
            order_id="",
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            price=price,
            commission=commission_cost,
            timestamp=timestamp
        )
        
        return trade
    
    def close_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
        timestamp: datetime
    ) -> Optional[Trade]:
        """
        포지션 청산 (전체 또는 부분)
        
        Args:
            symbol: 종목코드
            quantity: 청산 수량
            price: 청산가
            timestamp: 시간
        
        Returns:
            거래 기록 (포지션이 없으면 None)
        """
        if symbol not in self.positions:
            logger.warning(f"청산 실패: {symbol} 포지션 없음")
            return None
        
        position = self.positions[symbol]
        
        if quantity > position.quantity:
            logger.warning(f"청산 수량 초과: 요청 {quantity}, 보유 {position.quantity}")
            quantity = position.quantity
        
        # 손익 계산
        pnl = (price - position.avg_price) * quantity
        commission_cost = quantity * price * self.commission
        net_pnl = pnl - commission_cost
        
        # 포지션 업데이트
        position.quantity -= quantity
        position.realized_pnl += net_pnl
        
        logger.info(
            f"포지션 청산: {symbol}, {quantity}주 @ {price:,.0f}, "
            f"손익: {net_pnl:,.0f}원 ({net_pnl/position.avg_price/quantity:.2%})"
        )
        
        # 포지션 완전 청산 시 제거
        if position.quantity == 0:
            del self.positions[symbol]
            logger.info(f"포지션 완전 청산: {symbol}")
        
        # 거래 기록
        trade = Trade(
            trade_id=f"{symbol}_{timestamp.strftime('%Y%m%d%H%M%S')}",
            order_id="",
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            price=price,
            commission=commission_cost,
            timestamp=timestamp
        )
        
        self.closed_trades.append(trade)
        
        return trade
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        현재가 업데이트 및 미실현 손익 재계산
        
        Args:
            prices: {종목코드: 현재가} 딕셔너리
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_price(prices[symbol])
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """포지션 조회"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """모든 포지션 조회"""
        return list(self.positions.values())
    
    def get_total_unrealized_pnl(self) -> float:
        """총 미실현 손익"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def get_total_realized_pnl(self) -> float:
        """총 실현 손익"""
        return sum(pos.realized_pnl for pos in self.positions.values())
    
    def get_closed_trades(self) -> List[Trade]:
        """청산된 거래 내역"""
        return self.closed_trades
    
    def get_portfolio_weights(self, total_equity: float) -> Dict[str, float]:
        """
        현재 포트폴리오 비중 계산
        
        Args:
            total_equity: 총 자산
        
        Returns:
            {종목코드: 비중} 딕셔너리
        """
        if total_equity <= 0:
            return {}
        
        weights = {}
        for symbol, position in self.positions.items():
            position_value = position.quantity * position.current_price
            weights[symbol] = position_value / total_equity
        
        return weights
    
    def calculate_rebalance_orders(
        self,
        target_weights: Dict[str, float],
        current_prices: Dict[str, float],
        total_equity: float
    ) -> Dict[str, int]:
        """
        리밸런싱에 필요한 주문 수량 계산
        
        Args:
            target_weights: 목표 비중 {종목코드: 비중}
            current_prices: 현재가 {종목코드: 가격}
            total_equity: 총 자산
        
        Returns:
            {종목코드: 수량} 딕셔너리 (양수: 매수, 음수: 매도)
        """
        orders = {}
        
        # 현재 보유 종목
        current_symbols = set(self.positions.keys())
        target_symbols = set(target_weights.keys())
        
        # 1. 목표에 없는 종목 청산
        for symbol in current_symbols - target_symbols:
            position = self.positions[symbol]
            orders[symbol] = -position.quantity  # 전량 매도
        
        # 2. 목표 비중에 맞춰 조정
        for symbol, target_weight in target_weights.items():
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            target_value = total_equity * target_weight
            target_quantity = int(target_value / current_price)
            
            # 현재 보유 수량
            current_quantity = 0
            if symbol in self.positions:
                current_quantity = self.positions[symbol].quantity
            
            # 수량 차이
            quantity_diff = target_quantity - current_quantity
            
            if quantity_diff != 0:
                orders[symbol] = quantity_diff
        
        return orders
    
    def clear(self) -> None:
        """모든 포지션 및 거래 내역 초기화"""
        self.positions.clear()
        self.closed_trades.clear()
        logger.info("PositionManager cleared")
