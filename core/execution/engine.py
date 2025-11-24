"""
실시간 실행 엔진
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from broker.base import BrokerBase
from core.strategy.base import BaseStrategy
from core.risk.manager import RiskManager
from utils.types import Position, Account, Order, OrderStatus, OrderSide
from utils.logger import setup_logger
from utils.exceptions import RiskLimitError
from utils.config import config
from utils.bar_utils import create_bars_from_ticks, validate_bars
from utils.signal_logger import get_signal_logger, SignalType

logger = setup_logger(__name__)
signal_logger = get_signal_logger()


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
        risk_manager: RiskManager,
        timeframe: str = None
    ):
        """
        Args:
            strategy: 실행할 전략
            broker: 브로커 어댑터
            risk_manager: 리스크 관리자
            timeframe: 타임프레임 (예: "1m", "5m", "1h") - None이면 config에서 로드
        """
        self.strategy = strategy
        self.broker = broker
        self.risk_manager = risk_manager
        
        # 타임프레임 설정 (config 또는 파라미터)
        self.timeframe = timeframe or config.get("execution.timeframe", "1m")
        self._parse_timeframe()
        
        self.is_running = False
        self.symbols: List[str] = []
        self.price_history: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info(f"ExecutionEngine initialized: {strategy.name}, timeframe={self.timeframe}")
    
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
            
            # 전략 실행 (OHLCV 바 생성)
            bars = self._create_bars_from_history(symbol)
            
            if bars is not None and len(bars) > 0:
                try:
                    signals = self.strategy.on_bar(bars, positions, account)
                    
                    # 주문 신호 처리
                    for signal in signals:
                        await self._execute_signal(signal, account, positions)
                
                except Exception as e:
                    logger.error(f"Strategy execution error for {symbol}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error processing price update: {e}")
    
    async def _execute_signal(
        self,
        signal: Any,
        account: Account,
        positions: List[Position]
    ) -> None:
        """
        주문 신호 실행 (재시도 로직 포함)
        
        Args:
            signal: 주문 신호
            account: 계좌 정보
            positions: 현재 포지션
        """
        # 중복 진입 방지
        if signal.side == OrderSide.BUY:
            existing_position = next((p for p in positions if p.symbol == signal.symbol), None)
            if existing_position and existing_position.quantity > 0:
                logger.warning(
                    f"중복 진입 방지: {signal.symbol}에 이미 포지션 보유 중 "
                    f"(수량: {existing_position.quantity})"
                )
                return
        
        # 주문 검증
        if not self.risk_manager.validate_order(signal, account, positions):
            logger.warning(f"리스크 검증 실패: {signal.symbol} {signal.side.value} {signal.quantity}")
            return
        
        # 재시도 로직
        max_retries = 3
        retry_delay = 1.0  # 초
        
        for attempt in range(max_retries):
            try:
                # 주문 생성
                order = signal.to_order(f"RT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{attempt}")
                
                # 주문 제출
                order_id = await self.broker.place_order(order)
                
                logger.info(
                    f"주문 제출 성공: {order_id} | "
                    f"{signal.side.value} {signal.quantity} {signal.symbol}"
                )
                
                # TODO: 주문 체결 확인 및 전략 콜백
                return  # 성공 시 종료
            
            except asyncio.TimeoutError:
                logger.warning(
                    f"주문 제출 타임아웃 (시도 {attempt + 1}/{max_retries}): "
                    f"{signal.symbol} {signal.side.value}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
            
            except ConnectionError as e:
                logger.error(
                    f"네트워크 오류 (시도 {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
            
            except Exception as e:
                logger.error(
                    f"주문 실행 실패: {signal.symbol} {signal.side.value} - {e}",
                    exc_info=True
                )
                break  # 다른 예외는 재시도하지 않음
        
        # 모든 재시도 실패
        logger.error(
            f"주문 제출 최종 실패: {signal.symbol} {signal.side.value} {signal.quantity}"
        )
    
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
    
    def _parse_timeframe(self) -> None:
        """타임프레임 파싱 (예: "1m" -> 1분, "5m" -> 5분)"""
        timeframe_map = {
            "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
            "1h": 3600, "4h": 14400, "1d": 86400
        }
        
        self.timeframe_seconds = timeframe_map.get(self.timeframe)
        if self.timeframe_seconds is None:
            logger.warning(f"Unknown timeframe: {self.timeframe}, defaulting to 1m")
            self.timeframe = "1m"
            self.timeframe_seconds = 60
    
    def _create_bars_from_history(
        self, 
        symbol: str, 
        lookback: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        가격 히스토리에서 OHLCV 바 생성
        
        Args:
            symbol: 종목 코드
            lookback: 조회할 바 개수
        
        Returns:
            OHLCV DataFrame (timestamp 인덱스, ['open', 'high', 'low', 'close', 'volume', 'value'] 컬럼)
            데이터가 부족하면 None 반환
        """
        if symbol not in self.price_history or not self.price_history[symbol]:
            return None
        
        try:
            # bar_utils 사용
            bars = create_bars_from_ticks(
                self.price_history[symbol],
                self.timeframe_seconds,
                lookback
            )
            
            if bars is None:
                return None
            
            # 데이터 검증
            bars = validate_bars(bars, symbol)
            
            logger.debug(f"Created {len(bars)} bars for {symbol} (timeframe={self.timeframe})")
            return bars
        
        except Exception as e:
            logger.error(f"Failed to create bars for {symbol}: {e}", exc_info=True)
            return None
    
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
