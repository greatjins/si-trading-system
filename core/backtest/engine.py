"""
백테스트 엔진
"""
from typing import List, Dict, Any
from datetime import datetime
from copy import deepcopy

from core.strategy.base import BaseStrategy
from core.backtest.position import PositionManager
from utils.types import (
    OHLC, Account, Order, OrderSignal, OrderSide, 
    OrderType, OrderStatus, BacktestResult, Trade
)
from utils.logger import setup_logger
from utils.exceptions import BacktestError

logger = setup_logger(__name__)


class BacktestEngine:
    """
    과거 데이터로 전략 실행을 시뮬레이션
    
    OHLC 데이터를 시간순으로 반복하며 전략을 실행하고,
    주문 신호를 처리하여 포지션을 관리합니다.
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float,
        commission: float = 0.0015,
        slippage: float = 0.001
    ):
        """
        Args:
            strategy: 백테스트할 전략
            initial_capital: 초기 자본
            commission: 수수료율 (기본: 0.15%)
            slippage: 슬리피지 (기본: 0.1%)
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        # 포지션 관리자
        self.position_manager = PositionManager(commission=commission)
        
        # 계좌 상태
        self.cash = initial_capital
        self.equity = initial_capital
        
        # 기록
        self.equity_curve: List[float] = [initial_capital]
        self.equity_timestamps: List[datetime] = []
        self.all_trades: List[Trade] = []
        
        logger.info(f"BacktestEngine initialized: {strategy.name}")
        logger.info(f"Initial capital: {initial_capital:,.0f}, Commission: {commission:.4%}, Slippage: {slippage:.4%}")
    
    async def run(
        self,
        ohlc_data: List[OHLC],
        start_date: datetime = None,
        end_date: datetime = None
    ) -> BacktestResult:
        """
        백테스트 시뮬레이션 실행
        
        Args:
            ohlc_data: OHLC 데이터 리스트 (시간순 정렬)
            start_date: 시작일 (None이면 데이터 시작)
            end_date: 종료일 (None이면 데이터 끝)
        
        Returns:
            백테스트 결과
        """
        if not ohlc_data:
            raise BacktestError("No OHLC data provided")
        
        # 날짜 필터링
        if start_date:
            ohlc_data = [bar for bar in ohlc_data if bar.timestamp >= start_date]
        if end_date:
            ohlc_data = [bar for bar in ohlc_data if bar.timestamp <= end_date]
        
        if not ohlc_data:
            raise BacktestError("No data in specified date range")
        
        logger.info(f"Starting backtest: {len(ohlc_data)} bars")
        logger.info(f"Period: {ohlc_data[0].timestamp.date()} ~ {ohlc_data[-1].timestamp.date()}")
        
        # 초기화
        self._reset()
        
        # OHLC 바 반복
        for i in range(len(ohlc_data)):
            current_bar = ohlc_data[i]
            
            # 전략에 제공할 과거 데이터 (현재 바까지)
            historical_bars = ohlc_data[:i+1]
            
            # 현재 계좌 상태
            account = self._get_account_state()
            
            # 현재 포지션
            positions = self.position_manager.get_all_positions()
            
            # 포지션 현재가 업데이트
            self.position_manager.update_prices({current_bar.symbol: current_bar.close})
            
            # 전략 호출 - 주문 신호 생성
            signals = self.strategy.on_bar(historical_bars, positions, account)
            
            # 주문 신호 처리
            for signal in signals:
                self._process_signal(signal, current_bar)
            
            # 자산 기록
            self._update_equity(current_bar.timestamp)
        
        # 결과 생성
        result = self._generate_result(ohlc_data[0].timestamp, ohlc_data[-1].timestamp)
        
        logger.info(f"Backtest completed: {result.total_trades} trades")
        logger.info(f"Final equity: {result.final_equity:,.0f} ({result.total_return:.2%})")
        
        return result

    
    def _reset(self) -> None:
        """백테스트 상태 초기화"""
        self.cash = self.initial_capital
        self.equity = self.initial_capital
        self.equity_curve = [self.initial_capital]
        self.equity_timestamps = []
        self.all_trades = []
        self.position_manager.clear()
    
    def _get_account_state(self) -> Account:
        """현재 계좌 상태 반환"""
        unrealized_pnl = self.position_manager.get_total_unrealized_pnl()
        equity = self.cash + unrealized_pnl
        
        return Account(
            account_id="BACKTEST",
            balance=self.cash,
            equity=equity,
            margin_used=0.0,
            margin_available=self.cash
        )
    
    def _process_signal(self, signal: OrderSignal, current_bar: OHLC) -> None:
        """
        주문 신호 처리
        
        Args:
            signal: 주문 신호
            current_bar: 현재 OHLC 바
        """
        # 실행 가격 계산 (슬리피지 적용)
        if signal.order_type == OrderType.MARKET:
            if signal.side == OrderSide.BUY:
                execution_price = current_bar.close * (1 + self.slippage)
            else:
                execution_price = current_bar.close * (1 - self.slippage)
        else:
            execution_price = signal.price or current_bar.close
        
        # 매수 처리
        if signal.side == OrderSide.BUY:
            order_value = signal.quantity * execution_price
            commission_cost = order_value * self.commission
            total_cost = order_value + commission_cost
            
            # 잔액 확인
            if total_cost > self.cash:
                logger.warning(f"잔액 부족: 필요 {total_cost:,.0f}, 보유 {self.cash:,.0f}")
                return
            
            # 포지션 진입
            trade = self.position_manager.open_position(
                symbol=signal.symbol,
                quantity=signal.quantity,
                price=execution_price,
                timestamp=current_bar.timestamp
            )
            
            # 현금 차감
            self.cash -= total_cost
            self.all_trades.append(trade)
            
            # 전략 콜백
            order = self._create_order(signal, execution_price, current_bar.timestamp)
            position = self.position_manager.get_position(signal.symbol)
            if position:
                self.strategy.on_fill(order, position)
        
        # 매도 처리
        elif signal.side == OrderSide.SELL:
            position = self.position_manager.get_position(signal.symbol)
            
            if not position or position.quantity == 0:
                logger.warning(f"매도 실패: {signal.symbol} 포지션 없음")
                return
            
            # 포지션 청산
            trade = self.position_manager.close_position(
                symbol=signal.symbol,
                quantity=signal.quantity,
                price=execution_price,
                timestamp=current_bar.timestamp
            )
            
            if trade:
                # 현금 증가
                order_value = signal.quantity * execution_price
                commission_cost = order_value * self.commission
                net_proceeds = order_value - commission_cost
                self.cash += net_proceeds
                self.all_trades.append(trade)
                
                # 전략 콜백
                order = self._create_order(signal, execution_price, current_bar.timestamp)
                position = self.position_manager.get_position(signal.symbol)
                if position:
                    self.strategy.on_fill(order, position)
    
    def _create_order(self, signal: OrderSignal, price: float, timestamp: datetime) -> Order:
        """신호를 주문으로 변환"""
        return Order(
            order_id=f"BT_{timestamp.strftime('%Y%m%d%H%M%S')}",
            symbol=signal.symbol,
            side=signal.side,
            order_type=signal.order_type,
            quantity=signal.quantity,
            price=price,
            filled_quantity=signal.quantity,
            status=OrderStatus.FILLED,
            created_at=timestamp,
            updated_at=timestamp
        )
    
    def _update_equity(self, timestamp: datetime) -> None:
        """자산 곡선 업데이트"""
        unrealized_pnl = self.position_manager.get_total_unrealized_pnl()
        self.equity = self.cash + unrealized_pnl
        
        self.equity_curve.append(self.equity)
        self.equity_timestamps.append(timestamp)
    
    def _generate_result(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """백테스트 결과 생성"""
        from core.backtest.metrics import calculate_metrics
        
        metrics = calculate_metrics(
            equity_curve=self.equity_curve,
            trades=self.all_trades,
            initial_capital=self.initial_capital
        )
        
        return BacktestResult(
            strategy_name=self.strategy.name,
            parameters=self.strategy.params,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_equity=self.equity,
            total_return=metrics["total_return"],
            mdd=metrics["mdd"],
            sharpe_ratio=metrics["sharpe_ratio"],
            win_rate=metrics["win_rate"],
            profit_factor=metrics["profit_factor"],
            total_trades=len(self.all_trades),
            equity_curve=self.equity_curve,
            trades=self.all_trades
        )
