"""
실시간 실행 엔진
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from broker.base import BrokerBase
from core.strategy.base import BaseStrategy
from core.risk.manager import RiskManager
from utils.types import Position, Account, Order, OrderStatus, OrderSide
from utils.logger import setup_logger
from utils.exceptions import RiskLimitError

logger = setup_logger(__name__)


class ExecutionEngine:
    """
    실시간 실행 엔진
    
    WebSocket을 통해 실시간 시장 데이터를 받아
    전략을 실행하고 주문을 제출합니다.
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        broker: BrokerBase,
        risk_manager: RiskManager
    ):
        """
        Args:
            strategy: 실행할 전략
            broker: 브로커 어댑터
            risk_manager: 리스크 관리자
        """
        self.strategy = strategy
        self.broker = broker
        self.risk_manager = risk_manager
        
        self.is_running = False
        self.symbols: List[str] = []
        self.price_history: Dict[str, List[Any]] = {}
        
        logger.info(f"ExecutionEngine initialized: {strategy.name}")
    
    async def start(self, symbols: List[str]) -> None:
        """
        실시간 실행 시작
        
        Args:
            symbols: 구독할 종목 리스트
        """
        if self.is_running:
            logger.warning("Engine is already running")
            return
        
        self.symbols = symbols
        self.is_running = True
        
        logger.info(f"Starting execution engine for {symbols}")
        
        try:
            # 실시간 데이터 스트리밍
            async for price_update in self.broker.stream_realtime(symbols):
                if not self.is_running:
                    break
                
                await self._process_price_update(price_update)
        
        except asyncio.CancelledError:
            logger.info("Execution engine cancelled")
        except Exception as e:
            logger.error(f"Execution engine error: {e}")
        finally:
            self.is_running = False
            logger.info("Execution engine stopped")
    
    async def stop(self) -> None:
        """실행 중단"""
        logger.info("Stopping execution engine...")
        self.is_running = False
    
    async def _process_price_update(self, update: Dict[str, Any]) -> None:
        """
        가격 업데이트 처리
        
        Args:
            update: 가격 업데이트 데이터
        """
        symbol = update.get("symbol")
        price = update.get("price")
        timestamp = update.get("timestamp", datetime.now())
        
        logger.debug(f"Price update: {symbol} = {price:,.0f}")
        
        # 가격 히스토리 저장
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(update)
        
        # 계좌 및 포지션 조회
        try:
            account = await self.broker.get_account()
            positions = await self.broker.get_positions()
            
            # 리스크 한도 확인
            self.risk_manager.update_equity(account.equity, timestamp)
            
            if not self.risk_manager.check_risk_limits(account):
                logger.warning("Risk limits exceeded, skipping strategy execution")
                
                # 긴급 정지 시 모든 포지션 청산
                if self.risk_manager.emergency_stop:
                    await self._emergency_liquidate(positions)
                
                return
            
            # 전략 실행 (간단한 OHLC 바 생성)
            # TODO: 실제로는 더 정교한 바 생성 필요
            bars = self._create_bars_from_history(symbol)
            
            if bars:
                signals = self.strategy.on_bar(bars, positions, account)
                
                # 주문 신호 처리
                for signal in signals:
                    await self._execute_signal(signal, account, positions)
        
        except Exception as e:
            logger.error(f"Error processing price update: {e}")
    
    async def _execute_signal(
        self,
        signal: Any,
        account: Account,
        positions: List[Position]
    ) -> None:
        """
        주문 신호 실행
        
        Args:
            signal: 주문 신호
            account: 계좌 정보
            positions: 현재 포지션
        """
        # 주문 검증
        if not self.risk_manager.validate_order(signal, account, positions):
            logger.warning(f"Order validation failed: {signal}")
            return
        
        try:
            # 주문 생성
            order = signal.to_order(f"RT_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            
            # 주문 제출
            order_id = await self.broker.place_order(order)
            
            logger.info(
                f"Order submitted: {order_id} | "
                f"{signal.side.value} {signal.quantity} {signal.symbol}"
            )
            
            # TODO: 주문 체결 확인 및 전략 콜백
        
        except Exception as e:
            logger.error(f"Failed to execute signal: {e}")
    
    async def _emergency_liquidate(self, positions: List[Position]) -> None:
        """
        긴급 청산
        
        Args:
            positions: 청산할 포지션 리스트
        """
        logger.critical("EMERGENCY LIQUIDATION STARTED")
        
        for position in positions:
            if position.quantity > 0:
                try:
                    # 시장가 매도 주문 생성
                    from utils.types import OrderSignal, OrderSide, OrderType
                    
                    signal = OrderSignal(
                        symbol=position.symbol,
                        side=OrderSide.SELL,
                        quantity=position.quantity,
                        order_type=OrderType.MARKET
                    )
                    
                    order = signal.to_order(f"EMG_{datetime.now().strftime('%Y%m%d%H%M%S')}")
                    order_id = await self.broker.place_order(order)
                    
                    logger.critical(
                        f"Emergency liquidation: {order_id} | "
                        f"SELL {position.quantity} {position.symbol}"
                    )
                
                except Exception as e:
                    logger.error(f"Failed to liquidate {position.symbol}: {e}")
        
        logger.critical("EMERGENCY LIQUIDATION COMPLETED")
    
    def _create_bars_from_history(self, symbol: str, lookback: int = 100) -> List[Any]:
        """
        가격 히스토리에서 OHLC 바 생성
        
        Args:
            symbol: 종목 코드
            lookback: 조회할 바 개수
        
        Returns:
            OHLC 바 리스트
        """
        # TODO: 실제 구현 필요
        # 현재는 빈 리스트 반환
        return []
    
    def get_status(self) -> Dict[str, Any]:
        """
        엔진 상태 조회
        
        Returns:
            상태 딕셔너리
        """
        return {
            "is_running": self.is_running,
            "strategy": self.strategy.name,
            "symbols": self.symbols,
            "risk_status": self.risk_manager.get_risk_status()
        }
