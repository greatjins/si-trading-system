"""
실시간 실행 엔진
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
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
        
        # 주문 체결 대기 관리
        self.pending_orders: Dict[str, Dict[str, Any]] = {}  # order_id -> {order, event, timeout}
        self.order_execution_events: Dict[str, asyncio.Event] = {}  # order_id -> Event
        
        # WebSocket 체결 알림 콜백 (나중에 확장 가능)
        self.on_order_filled: Optional[Callable[[str, Order], Any]] = None
        
        # 실행 상태 추적 (Phase 3.2)
        self.last_execution_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.error_count: int = 0
        self.strategy_id: Optional[int] = None  # 전략 ID (DB 연동용)
        
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
        self.last_execution_time = datetime.now()
        self.last_error = None
        self.error_count = 0
        
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
            self.last_error = str(e)
            self.error_count += 1
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
            
            # 현재가 조회 (슬리피지 체크용)
            current_price = price  # price_update에서 가져온 가격 사용
            
            # 전략 실행 (OHLCV 바 생성)
            bars = await self._create_bars_from_history(symbol)
            
            if bars is not None and len(bars) > 0:
                try:
                    # DynamicStrategy는 apply_indicators를 on_bar 내부에서 호출하지만,
                    # 다른 전략을 위해 여기서도 호출 가능 (BaseStrategy 메서드)
                    # bars = self.strategy.apply_indicators(bars)
                    
                    signals = self.strategy.on_bar(bars, positions, account)
                    
                    # 주문 신호 처리
                    for signal in signals:
                        await self._execute_signal(signal, account, positions, current_price)
                
                except Exception as e:
                    logger.error(f"Strategy execution error for {symbol}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error processing price update: {e}")
    
    async def _execute_signal(
        self,
        signal: Any,
        account: Account,
        positions: List[Position],
        current_price: Optional[float] = None
    ) -> None:
        """
        주문 신호 실행 (재시도 로직 및 체결 확인 포함)
        
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
        
        # 주문 검증 (슬리피지 체크 포함)
        if not self.risk_manager.validate_order(signal, account, positions, current_price):
            logger.warning(f"리스크 검증 실패: {signal.symbol} {signal.side.value} {signal.quantity}")
            return
        
        # 재시도 로직
        max_retries = 3
        retry_delay = 1.0  # 초
        order_id = None
        
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
                
                # 주문 체결 확인 및 처리
                filled = await self._wait_for_order_execution(order_id, order, timeout_seconds=30)
                
                # 체결 성공 시 거래 기록
                if filled:
                    self.risk_manager.record_trade(signal.symbol)
                
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
    
    async def _wait_for_order_execution(
        self,
        order_id: str,
        order: Order,
        timeout_seconds: int = 30
    ) -> bool:
        """
        주문 체결 대기 (Polling + WebSocket 이벤트 지원)
        
        Args:
            order_id: 주문 ID
            order: 주문 객체
            timeout_seconds: 타임아웃 시간 (초)
        """
        logger.info(f"Waiting for order execution: {order_id}")
        
        # 체결 이벤트 생성
        execution_event = asyncio.Event()
        self.order_execution_events[order_id] = execution_event
        
        # 주문 정보 저장
        self.pending_orders[order_id] = {
            'order': order,
            'event': execution_event,
            'timeout': datetime.now() + timedelta(seconds=timeout_seconds),
            'created_at': datetime.now()
        }
        
        # Polling 간격 (초)
        polling_interval = 1.0
        
        try:
            # 타임아웃까지 체결 확인
            while datetime.now() < self.pending_orders[order_id]['timeout']:
                # WebSocket 이벤트 확인 (우선)
                if execution_event.is_set():
                    logger.info(f"Order filled via WebSocket event: {order_id}")
                    await self._handle_order_filled(order_id)
                    return True
                
                # Polling으로 주문 상태 확인
                order_status = await self._check_order_status(order_id)
                
                if order_status == OrderStatus.FILLED:
                    logger.info(f"Order filled via polling: {order_id}")
                    await self._handle_order_filled(order_id)
                    return True
                elif order_status in [OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                    logger.warning(f"Order cancelled/rejected: {order_id}, status={order_status.value}")
                    self._cleanup_order(order_id)
                    return False
                
                # 다음 확인까지 대기
                await asyncio.sleep(polling_interval)
            
            # 타임아웃: 미체결 주문 취소
            logger.warning(f"Order timeout ({timeout_seconds}s): {order_id}, cancelling...")
            await self._cancel_pending_order(order_id)
            return False
        
        except asyncio.CancelledError:
            logger.warning(f"Order execution wait cancelled: {order_id}")
            self._cleanup_order(order_id)
            return False
        except Exception as e:
            logger.error(f"Error waiting for order execution: {e}", exc_info=True)
            self._cleanup_order(order_id)
            return False
    
    async def _check_order_status(self, order_id: str) -> OrderStatus:
        """
        주문 상태 확인 (Polling)
        
        Args:
            order_id: 주문 ID
        
        Returns:
            주문 상태
        """
        try:
            # 미체결 주문 목록 조회
            open_orders = await self.broker.get_open_orders()
            
            # 해당 주문 찾기
            for open_order in open_orders:
                if open_order.order_id == order_id:
                    return open_order.status
            
            # 미체결 목록에 없으면 체결된 것으로 간주
            # (더 정확한 확인을 위해 체결 내역 조회 가능)
            return OrderStatus.FILLED
        
        except Exception as e:
            logger.error(f"Failed to check order status: {e}")
            return OrderStatus.PENDING
    
    async def _cancel_pending_order(self, order_id: str) -> None:
        """
        미체결 주문 취소
        
        Args:
            order_id: 주문 ID
        """
        try:
            success = await self.broker.cancel_order(order_id)
            if success:
                logger.info(f"Order cancelled successfully: {order_id}")
            else:
                logger.warning(f"Failed to cancel order: {order_id}")
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}", exc_info=True)
        finally:
            self._cleanup_order(order_id)
    
    async def _handle_order_filled(self, order_id: str) -> None:
        """
        주문 체결 처리
        
        Args:
            order_id: 주문 ID
        """
        try:
            # 주문 정보 가져오기
            if order_id not in self.pending_orders:
                logger.warning(f"Order not found in pending orders: {order_id}")
                return
            
            order = self.pending_orders[order_id]['order']
            
            # 포지션 및 계좌 정보 최신화
            logger.info(f"Updating positions and account after order fill: {order_id}")
            
            try:
                # 포지션 정보 최신화
                positions = await self.broker.get_positions()
                logger.debug(f"Updated positions: {len(positions)} positions")
                
                # 계좌 정보 최신화
                account = await self.broker.get_account()
                logger.debug(f"Updated account: equity={account.equity:,.0f}")
                
                # 리스크 관리자 업데이트
                self.risk_manager.update_equity(account.equity, datetime.now())
                
            except Exception as e:
                logger.error(f"Failed to update positions/account: {e}", exc_info=True)
            
            # WebSocket 콜백 호출 (확장 가능)
            if self.on_order_filled:
                try:
                    result = self.on_order_filled(order_id, order)
                    # 비동기 함수인 경우 await
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Error in order filled callback: {e}", exc_info=True)
            
            # 정리
            self._cleanup_order(order_id)
            
            logger.info(f"Order execution completed: {order_id}")
        
        except Exception as e:
            logger.error(f"Error handling order fill: {e}", exc_info=True)
            self._cleanup_order(order_id)
    
    def _cleanup_order(self, order_id: str) -> None:
        """
        주문 정보 정리
        
        Args:
            order_id: 주문 ID
        """
        if order_id in self.pending_orders:
            del self.pending_orders[order_id]
        if order_id in self.order_execution_events:
            del self.order_execution_events[order_id]
    
    def notify_order_filled(self, order_id: str) -> None:
        """
        WebSocket 체결 알림 수신 (외부에서 호출)
        
        Args:
            order_id: 체결된 주문 ID
        """
        if order_id in self.order_execution_events:
            logger.info(f"Received WebSocket fill notification: {order_id}")
            self.order_execution_events[order_id].set()
    
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
    
    async def _create_bars_from_history(
        self, 
        symbol: str, 
        lookback: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        가격 히스토리에서 OHLCV 바 생성 (타임스탬프 연속성 및 데이터 무결성 검증 포함)
        
        Args:
            symbol: 종목 코드
            lookback: 조회할 바 개수
        
        Returns:
            OHLCV DataFrame (timestamp 인덱스, ['open', 'high', 'low', 'close', 'volume', 'value'] 컬럼)
            데이터가 부족하거나 오염되었으면 None 반환
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
            
            if bars is None or len(bars) == 0:
                return None
            
            # 데이터 검증
            bars = validate_bars(bars, symbol)
            
            if len(bars) == 0:
                return None
            
            # 타임스탬프 연속성 확인 및 간격 복구
            bars = await self._check_and_fix_timestamp_gaps(bars, symbol)
            
            if bars is None or len(bars) == 0:
                return None
            
            # 데이터 오염 가능성 체크
            if not self._check_data_integrity(bars, symbol):
                logger.warning(f"Data integrity check failed for {symbol}, skipping strategy execution")
                return None
            
            logger.debug(f"Created {len(bars)} bars for {symbol} (timeframe={self.timeframe})")
            return bars
        
        except Exception as e:
            logger.error(f"Failed to create bars for {symbol}: {e}", exc_info=True)
            return None
    
    async def _check_and_fix_timestamp_gaps(
        self,
        bars: pd.DataFrame,
        symbol: str
    ) -> Optional[pd.DataFrame]:
        """
        타임스탬프 연속성 확인 및 간격 복구
        
        Args:
            bars: OHLCV DataFrame
            symbol: 종목 코드
        
        Returns:
            복구된 DataFrame 또는 None (복구 실패 시)
        """
        if len(bars) < 2:
            return bars
        
        # 타임스탬프 정렬
        bars = bars.sort_index()
        
        # 예상 간격 (타임프레임)
        expected_gap = pd.Timedelta(seconds=self.timeframe_seconds)
        
        # 허용 오차 (예상 간격의 10%)
        tolerance = expected_gap * 0.1
        
        # 간격 확인
        gaps = []
        for i in range(len(bars) - 1):
            current_time = bars.index[i]
            next_time = bars.index[i + 1]
            actual_gap = next_time - current_time
            
            # 예상 간격보다 크게 벗어난 경우 (간격 발견)
            if actual_gap > expected_gap + tolerance:
                gaps.append({
                    'start': current_time,
                    'end': next_time,
                    'gap_size': actual_gap,
                    'expected_bars': int(actual_gap.total_seconds() / self.timeframe_seconds)
                })
        
        if not gaps:
            logger.debug(f"No timestamp gaps found for {symbol}")
            return bars
        
        # 간격 발견 로그
        total_missing_bars = sum(g['expected_bars'] for g in gaps)
        logger.warning(
            f"Found {len(gaps)} timestamp gaps for {symbol}, "
            f"missing approximately {total_missing_bars} bars"
        )
        
        # 간격 복구 시도
        try:
            # 서버에서 누락된 데이터 재조회
            filled_bars = await self._fill_missing_bars(bars, gaps, symbol)
            
            if filled_bars is not None and len(filled_bars) > len(bars):
                logger.info(
                    f"Filled {len(filled_bars) - len(bars)} missing bars for {symbol} "
                    f"from server"
                )
                return filled_bars
            else:
                # 복구 실패 시 간격이 있는 바 제거 (안전한 선택)
                logger.warning(
                    f"Failed to fill gaps for {symbol}, "
                    f"removing bars with gaps"
                )
                return self._remove_bars_with_gaps(bars, gaps)
        
        except Exception as e:
            logger.error(f"Error fixing timestamp gaps for {symbol}: {e}", exc_info=True)
            # 복구 실패 시 간격이 있는 바 제거
            return self._remove_bars_with_gaps(bars, gaps)
    
    async def _fill_missing_bars(
        self,
        bars: pd.DataFrame,
        gaps: List[Dict[str, Any]],
        symbol: str
    ) -> Optional[pd.DataFrame]:
        """
        서버에서 누락된 바 데이터 재조회
        
        Args:
            bars: 현재 바 DataFrame
            gaps: 간격 정보 리스트
            symbol: 종목 코드
        
        Returns:
            복구된 DataFrame 또는 None
        """
        try:
            # 가장 큰 간격의 시작과 끝 시간 찾기
            if not gaps:
                return bars
            
            # 모든 간격을 포함하는 시간 범위
            min_time = min(g['start'] for g in gaps)
            max_time = max(g['end'] for g in gaps)
            
            # 서버에서 데이터 재조회
            logger.info(
                f"Fetching missing data from server for {symbol} "
                f"({min_time} ~ {max_time})"
            )
            
            # 타임프레임을 interval 문자열로 변환
            interval_map = {
                60: "1m", 300: "5m", 900: "15m", 1800: "30m",
                3600: "1h", 14400: "4h", 86400: "1d"
            }
            interval = interval_map.get(self.timeframe_seconds, "1m")
            
            # 서버에서 OHLC 데이터 조회
            ohlc_list = await self.broker.get_ohlc(
                symbol=symbol,
                interval=interval,
                start_date=min_time,
                end_date=max_time
            )
            
            if not ohlc_list:
                logger.warning(f"No data retrieved from server for {symbol}")
                return None
            
            # OHLC 리스트를 DataFrame으로 변환
            from utils.bar_utils import ohlc_list_to_dataframe
            server_bars = ohlc_list_to_dataframe(ohlc_list)
            
            if len(server_bars) == 0:
                return None
            
            # 기존 바와 병합
            # 서버 데이터가 더 정확하므로 우선 사용
            combined_bars = pd.concat([bars, server_bars])
            combined_bars = combined_bars[~combined_bars.index.duplicated(keep='last')]
            combined_bars = combined_bars.sort_index()
            
            # 중복 제거 및 정렬
            return combined_bars
        
        except Exception as e:
            logger.error(f"Failed to fill missing bars for {symbol}: {e}", exc_info=True)
            return None
    
    def _remove_bars_with_gaps(
        self,
        bars: pd.DataFrame,
        gaps: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        간격이 있는 바 제거 (안전한 선택)
        
        Args:
            bars: 바 DataFrame
            gaps: 간격 정보 리스트
        
        Returns:
            간격이 없는 바만 포함한 DataFrame
        """
        if not gaps:
            return bars
        
        # 간격 이후의 바 제거 (데이터 불완전성 방지)
        first_gap_start = min(g['start'] for g in gaps)
        
        # 첫 번째 간격 이전의 바만 유지
        safe_bars = bars[bars.index < first_gap_start]
        
        logger.warning(
            f"Removed {len(bars) - len(safe_bars)} bars with gaps, "
            f"keeping {len(safe_bars)} safe bars"
        )
        
        return safe_bars
    
    def _check_data_integrity(self, bars: pd.DataFrame, symbol: str) -> bool:
        """
        데이터 무결성 확인
        
        Args:
            bars: OHLCV DataFrame
            symbol: 종목 코드
        
        Returns:
            데이터가 정상이면 True
        """
        if len(bars) == 0:
            return False
        
        # 1. 가격 이상치 확인 (변동률이 너무 큰 경우)
        price_changes = bars['close'].pct_change().abs()
        extreme_changes = price_changes > 0.20  # 20% 이상 변동
        
        if extreme_changes.any():
            extreme_count = extreme_changes.sum()
            logger.warning(
                f"Found {extreme_count} bars with extreme price changes (>20%) for {symbol}"
            )
            # 여러 개면 오염 가능성 높음
            if extreme_count > len(bars) * 0.1:  # 10% 이상
                logger.error(
                    f"Too many extreme price changes for {symbol} "
                    f"({extreme_count}/{len(bars)}), data may be corrupted"
                )
                return False
        
        # 2. 거래량 이상치 확인 (거래량이 0인 바가 너무 많은 경우)
        zero_volume_ratio = (bars['volume'] == 0).sum() / len(bars)
        if zero_volume_ratio > 0.5:  # 50% 이상
            logger.warning(
                f"Too many zero-volume bars for {symbol} "
                f"({zero_volume_ratio:.1%}), data may be incomplete"
            )
            # 일봉이 아닌 경우 거래량 0은 비정상
            if self.timeframe_seconds < 86400:  # 일봉이 아닌 경우
                return False
        
        # 3. 타임스탬프 중복 확인
        if bars.index.duplicated().any():
            logger.error(f"Found duplicate timestamps for {symbol}, data may be corrupted")
            return False
        
        # 4. 가격 범위 확인 (high >= low, high >= close, low <= close)
        invalid_ohlc = (
            (bars['high'] < bars['low']) |
            (bars['high'] < bars['close']) |
            (bars['low'] > bars['close'])
        )
        
        if invalid_ohlc.any():
            invalid_count = invalid_ohlc.sum()
            logger.warning(
                f"Found {invalid_count} bars with invalid OHLC relationships for {symbol}"
            )
            # 여러 개면 오염 가능성 높음
            if invalid_count > len(bars) * 0.05:  # 5% 이상
                logger.error(
                    f"Too many invalid OHLC bars for {symbol} "
                    f"({invalid_count}/{len(bars)}), data may be corrupted"
                )
                return False
        
        logger.debug(f"Data integrity check passed for {symbol}")
        return True
    
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
