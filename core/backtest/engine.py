"""
백테스트 엔진
"""
from typing import List, Dict, Any
from datetime import datetime
from copy import deepcopy
import pandas as pd

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
        slippage: float = 0.001,
        rebalance_days: int = 5,
        execution_delay: float = 1.5,
        use_dynamic_slippage: bool = True,
        use_tiered_commission: bool = True
    ):
        """
        Args:
            strategy: 백테스트할 전략
            initial_capital: 초기 자본
            commission: 수수료율 (기본: 0.15%, 고정 수수료 모드)
            slippage: 기본 슬리피지 (기본: 0.1%, 동적 슬리피지의 기준값)
            rebalance_days: 리밸런싱 주기 (일, 기본: 5일 = 주간)
            execution_delay: 체결 지연 시간 (초, 기본: 1.5초)
            use_dynamic_slippage: 동적 슬리피지 사용 여부 (기본: True)
            use_tiered_commission: 거래대금별 차등 수수료 사용 여부 (기본: True)
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.base_slippage = slippage  # 기본 슬리피지 (동적 계산의 기준)
        self.rebalance_days = rebalance_days
        self.execution_delay = execution_delay
        self.use_dynamic_slippage = use_dynamic_slippage
        self.use_tiered_commission = use_tiered_commission
        
        # 포지션 관리자
        self.position_manager = PositionManager(commission=commission)
        
        # 계좌 상태
        self.cash = initial_capital
        self.equity = initial_capital
        
        # 기록
        self.equity_curve: List[float] = [initial_capital]
        self.equity_timestamps: List[datetime] = []
        self.all_trades: List[Trade] = []
        
        # 리밸런싱 추적
        self.last_rebalance_date: datetime = None
        
        # 체결 지연 큐 (Phase 1.2용)
        self.pending_orders: List[Dict[str, Any]] = []
        
        logger.info(f"BacktestEngine initialized: {strategy.name}")
        logger.info(f"Initial capital: {initial_capital:,.0f}, Commission: {commission:.4%}, Base slippage: {slippage:.4%}")
        logger.info(f"Execution delay: {execution_delay}s, Dynamic slippage: {use_dynamic_slippage}, Tiered commission: {use_tiered_commission}")
    
    async def run(
        self,
        ohlc_data: List[OHLC] = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> BacktestResult:
        """
        백테스트 시뮬레이션 실행
        
        Args:
            ohlc_data: OHLC 데이터 리스트 (단일 종목 전략용, 시간순 정렬)
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            백테스트 결과
        
        Note:
            - 포트폴리오 전략: ohlc_data=None, start_date/end_date 필수
            - 단일 종목 전략: ohlc_data 필수
        """
        # 포트폴리오 전략 여부 확인
        if self.strategy.is_portfolio_strategy():
            return await self.run_portfolio(start_date, end_date)
        else:
            return await self.run_single(ohlc_data, start_date, end_date)
    
    async def run_single(
        self,
        ohlc_data: List[OHLC],
        start_date: datetime = None,
        end_date: datetime = None
    ) -> BacktestResult:
        """
        단일 종목 백테스트 (기존 방식)
        
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
        
        logger.info(f"Starting single-symbol backtest: {len(ohlc_data)} bars")
        logger.info(f"Period: {ohlc_data[0].timestamp.date()} ~ {ohlc_data[-1].timestamp.date()}")
        
        # 초기화
        self._reset()
        
        # [성능 최적화] 루프 밖에서 전체 데이터를 DataFrame으로 변환 (1회 수행)
        full_df = self._convert_to_dataframe(ohlc_data)
        
        # OHLC 바 반복
        for i in range(len(ohlc_data)):
            current_bar = ohlc_data[i]
            
            # [성능 최적화] 이미 변환된 DataFrame에서 슬라이싱만 수행 (메모리 복사 최소화)
            historical_bars = full_df.iloc[:i+1]
            
            # 현재 계좌 상태
            account = self._get_account_state()
            
            # 현재 포지션
            positions = self.position_manager.get_all_positions()
            
            # 포지션 현재가 업데이트
            self.position_manager.update_prices({current_bar.symbol: current_bar.close})
            
            # 전략 호출 - 주문 신호 생성
            try:
                signals = self.strategy.on_bar(historical_bars, positions, account)
            except Exception as e:
                logger.error(f"Strategy error at {current_bar.timestamp}: {e}", exc_info=True)
                signals = []
            
            # 주문 신호 처리 (체결 지연 시뮬레이션)
            for signal in signals:
                if self.execution_delay > 0:
                    # 체결 지연: 주문을 큐에 저장
                    self._queue_order(signal, current_bar, historical_bars)
                else:
                    # 즉시 체결
                    self._process_signal(signal, current_bar, historical_bars)
            
            # 체결 지연 큐에서 만료된 주문 처리
            self._process_pending_orders(current_bar, historical_bars)
            
            # 자산 기록
            self._update_equity(current_bar.timestamp)
        
        # 결과 생성
        result = self._generate_result(ohlc_data[0].timestamp, ohlc_data[-1].timestamp)
        
        logger.info(f"Backtest completed: {result.total_trades} trades")
        logger.info(f"Final equity: {result.final_equity:,.0f} ({result.total_return:.2%})")
        
        return result
    
    async def run_portfolio(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """
        포트폴리오 백테스트 (여러 종목)
        
        Args:
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            백테스트 결과
        """
        if not start_date or not end_date:
            raise BacktestError("start_date and end_date are required for portfolio backtest")
        
        logger.info(f"Starting portfolio backtest")
        logger.info(f"Period: {start_date.date()} ~ {end_date.date()}")
        
        # 초기화
        self._reset()
        
        # 데이터 로더 임포트
        from data.repository import DataRepository
        repo = DataRepository()
        
        # 거래일 목록 생성 (임시: 모든 날짜, 실제로는 영업일만)
        from datetime import timedelta
        current_date = start_date
        trading_days = []
        while current_date <= end_date:
            trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        logger.info(f"Total trading days: {len(trading_days)}")
        
        # 각 거래일마다 실행
        for date in trading_days:
            try:
                # 1. 리밸런싱 필요 여부 확인
                should_rebalance = False
                if self.last_rebalance_date is None:
                    # 첫 리밸런싱
                    should_rebalance = True
                else:
                    # 리밸런싱 주기 확인
                    days_since_rebalance = (date - self.last_rebalance_date).days
                    if days_since_rebalance >= self.rebalance_days:
                        should_rebalance = True
                
                if should_rebalance:
                    # 2. 전략이 종목 선택
                    # 전략 빌더 생성 전략은 repository를 받고, 기존 전략은 market_data를 받음
                    import inspect
                    sig = inspect.signature(self.strategy.select_universe)
                    params = list(sig.parameters.keys())
                    
                    # 두 번째 파라미터 이름으로 판단 (date 다음)
                    if len(params) > 1 and params[1] in ['repository', 'repo']:
                        # 전략 빌더 생성 전략 (DB 직접 조회)
                        universe = self.strategy.select_universe(date, repo)
                    else:
                        # 기존 포트폴리오 전략 (market_data 필요)
                        market_data = await self._load_market_snapshot(date, repo)
                        universe = self.strategy.select_universe(date, market_data)
                    
                    if universe:
                        logger.info(f"{date.date()}: Rebalancing - Selected {len(universe)} stocks")
                        
                        # 3. 선택된 종목의 가격 조회 (간단한 쿼리)
                        prices = await self._get_prices_for_symbols(universe, date, repo)
                        
                        if not prices:
                            logger.warning(f"{date.date()}: No price data available")
                            self._update_equity(date)
                            continue
                        
                        # 4. 목표 비중 계산
                        account = self._get_account_state()
                        # get_target_weights는 Dict 또는 DataFrame을 받을 수 있음
                        # 기본적으로 prices Dict를 전달 (균등 분배 전략에 충분)
                        target_weights = self.strategy.get_target_weights(universe, prices, account)
                        
                        # 5. 리밸런싱 (목표 비중에 맞춰 매매)
                        await self._rebalance_portfolio(universe, target_weights, prices, date, repo)
                        
                        # 리밸런싱 날짜 기록
                        self.last_rebalance_date = date
                else:
                    # 리밸런싱 없이 포지션 가격만 업데이트
                    positions = self.position_manager.get_all_positions()
                    if positions:
                        # 보유 종목의 가격만 조회
                        symbols = [p.symbol for p in positions]
                        prices = await self._get_prices_for_symbols(symbols, date, repo)
                        
                        if prices:
                            price_updates = {}
                            for pos in positions:
                                if pos.symbol in prices:
                                    price_updates[pos.symbol] = prices[pos.symbol]
                            
                            if price_updates:
                                self.position_manager.update_prices(price_updates)
                
                # 6. 자산 기록
                self._update_equity(date)
                
            except Exception as e:
                logger.error(f"Error on {date.date()}: {e}", exc_info=True)
                continue
        
        # 결과 생성
        result = self._generate_result(start_date, end_date)
        
        logger.info(f"Portfolio backtest completed: {result.total_trades} trades")
        logger.info(f"Final equity: {result.final_equity:,.0f} ({result.total_return:.2%})")
        
        return result
    
    async def _load_market_snapshot(
        self,
        date: datetime,
        repo
    ) -> pd.DataFrame:
        """
        특정 날짜의 시장 스냅샷 로드
        
        Args:
            date: 날짜
            repo: 데이터 저장소
        
        Returns:
            시장 데이터 DataFrame (index: symbol)
        """
        return repo.get_market_snapshot(date)
    
    async def _get_prices_for_symbols(
        self,
        symbols: List[str],
        date: datetime,
        repo
    ) -> Dict[str, float]:
        """
        특정 종목들의 특정 날짜 종가 조회
        
        Args:
            symbols: 종목 코드 리스트
            date: 날짜
            repo: 데이터 저장소
        
        Returns:
            {symbol: close_price} 딕셔너리
        """
        prices = {}
        
        for symbol in symbols:
            try:
                # 해당 날짜의 OHLC 데이터 조회
                ohlc_data = repo.get_ohlc(
                    symbol=symbol,
                    interval='1d',
                    start_date=date,
                    end_date=date
                )
                
                # DataFrame인 경우
                if isinstance(ohlc_data, pd.DataFrame):
                    if not ohlc_data.empty:
                        # timestamp가 인덱스인 경우
                        if ohlc_data.index.name == 'timestamp':
                            matching_rows = ohlc_data[ohlc_data.index.date == date.date()]
                            if not matching_rows.empty:
                                prices[symbol] = float(matching_rows.iloc[0]['close'])
                        # timestamp가 컬럼인 경우
                        elif 'timestamp' in ohlc_data.columns:
                            matching_rows = ohlc_data[ohlc_data['timestamp'].dt.date == date.date()]
                            if not matching_rows.empty:
                                prices[symbol] = float(matching_rows.iloc[0]['close'])
                # List[OHLC]인 경우
                elif isinstance(ohlc_data, list) and len(ohlc_data) > 0:
                    prices[symbol] = ohlc_data[0].close
            except Exception as e:
                logger.warning(f"Failed to get price for {symbol} on {date.date()}: {e}")
                continue
        
        return prices
    
    async def _rebalance_portfolio(
        self,
        universe: List[str],
        target_weights: Dict[str, float],
        prices: Dict[str, float],
        date: datetime,
        repo
    ) -> None:
        """
        포트폴리오 리밸런싱
        
        Args:
            universe: 선택된 종목 리스트
            target_weights: 목표 비중
            prices: 종목별 가격 {symbol: price}
            date: 현재 날짜
            repo: 데이터 저장소
        """
        # 현재 포지션
        positions = self.position_manager.get_all_positions()
        current_symbols = {p.symbol for p in positions}
        
        # 목표 포트폴리오 가치
        total_equity = self._get_account_state().equity
        
        # 1. 유니버스에서 제외된 종목 청산
        for symbol in current_symbols:
            if symbol not in universe:
                position = self.position_manager.get_position(symbol)
                if position and position.quantity > 0:
                    # 현재가 조회
                    current_price = prices.get(symbol, position.current_price)
                    
                    # 청산 신호 생성
                    signal = OrderSignal(
                        symbol=symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=position.quantity
                    )
                    
                    # 가상 OHLC 바 생성
                    fake_bar = OHLC(
                        symbol=symbol,
                        timestamp=date,
                        open=current_price,
                        high=current_price,
                        low=current_price,
                        close=current_price,
                        volume=0
                    )
                    
                    # 포트폴리오 백테스트는 historical_bars 없이 처리
                    self._process_signal(signal, fake_bar, None)
        
        # 2. 목표 비중에 맞춰 매수/매도
        for symbol, target_weight in target_weights.items():
            if symbol not in prices:
                continue
            
            current_price = prices[symbol]
            target_value = total_equity * target_weight
            target_quantity = int(target_value / current_price)
            
            # 현재 보유 수량
            position = self.position_manager.get_position(symbol)
            current_quantity = position.quantity if position else 0
            
            # 수량 차이
            quantity_diff = target_quantity - current_quantity
            
            if quantity_diff == 0:
                continue
            
            # 매수/매도 신호 생성
            if quantity_diff > 0:
                # 매수
                signal = OrderSignal(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=quantity_diff
                )
            else:
                # 매도
                signal = OrderSignal(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(quantity_diff)
                )
            
            # 가상 OHLC 바 생성
            fake_bar = OHLC(
                symbol=symbol,
                timestamp=date,
                open=current_price,
                high=current_price,
                low=current_price,
                close=current_price,
                volume=0
            )
            
            self._process_signal(signal, fake_bar)

    
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
    
    def _calculate_dynamic_slippage(
        self,
        current_bar: OHLC,
        historical_bars: pd.DataFrame = None,
        order_quantity: int = 0
    ) -> float:
        """
        동적 슬리피지 계산 (변동성/거래량 기반)
        
        Args:
            current_bar: 현재 OHLC 바
            historical_bars: 과거 데이터 (ATR 계산용)
            order_quantity: 주문 수량 (거래량 비교용)
        
        Returns:
            계산된 슬리피지 비율
        """
        if not self.use_dynamic_slippage:
            return self.base_slippage
        
        slippage = self.base_slippage
        
        try:
            # 1. 변동성 기반 조정 (ATR)
            if historical_bars is not None and len(historical_bars) >= 14:
                # ATR 계산
                atr = self._calculate_atr(historical_bars)
                if atr > 0 and current_bar.close > 0:
                    # ATR 대비 가격 비율 (변동성이 클수록 높은 슬리피지)
                    volatility_ratio = atr / current_bar.close
                    # 변동성 기반 슬리피지 증가 (최대 2배)
                    volatility_multiplier = min(1.0 + volatility_ratio * 10, 2.0)
                    slippage *= volatility_multiplier
            
            # 2. 거래량 기반 조정
            if current_bar.volume > 0 and order_quantity > 0:
                # 주문 수량이 거래량 대비 비율
                volume_ratio = order_quantity / current_bar.volume
                # 거래량이 적을수록 높은 슬리피지 (최대 3배)
                if volume_ratio > 0.01:  # 주문이 거래량의 1% 초과
                    volume_multiplier = min(1.0 + volume_ratio * 20, 3.0)
                    slippage *= volume_multiplier
            
            # 3. 시장 상황별 조정 (상승장/하락장/횡보)
            if historical_bars is not None and len(historical_bars) >= 20:
                # 최근 20일 평균 수익률로 시장 상황 판단
                recent_returns = historical_bars['close'].pct_change().tail(20)
                avg_return = recent_returns.mean()
                
                if avg_return > 0.001:  # 상승장
                    slippage *= 0.9  # 상승장에서는 슬리피지 약간 감소
                elif avg_return < -0.001:  # 하락장
                    slippage *= 1.2  # 하락장에서는 슬리피지 증가
            
            # 최소/최대 슬리피지 제한
            slippage = max(self.base_slippage * 0.5, min(slippage, self.base_slippage * 5.0))
        
        except Exception as e:
            logger.warning(f"Error calculating dynamic slippage: {e}, using base slippage")
            slippage = self.base_slippage
        
        return slippage
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """ATR 계산 (캐시 사용)"""
        if len(df) < period:
            return 0.0
        
        # 캐시 키 생성
        cache_key = f"{df.index[-1]}_{period}"
        if cache_key in self._atr_cache:
            return self._atr_cache[cache_key]
        
        # ATR 계산
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        atr_value = float(atr) if pd.notna(atr) else 0.0
        self._atr_cache[cache_key] = atr_value
        
        return atr_value
    
    def _calculate_commission(
        self,
        order_value: float,
        is_round_trip: bool = False
    ) -> float:
        """
        수수료 계산 (거래대금별 차등)
        
        Args:
            order_value: 주문 금액
            is_round_trip: 왕복 거래 여부 (매수+매도)
        
        Returns:
            수수료 금액
        """
        if not self.use_tiered_commission:
            # 고정 수수료
            commission = order_value * self.commission
            if is_round_trip:
                commission *= 2  # 매수+매도
            return commission
        
        # 거래대금별 차등 수수료
        # 일반적으로 거래대금이 클수록 낮은 수수료율
        if order_value < 1_000_000:  # 100만원 미만
            rate = self.commission * 1.2  # 0.18%
        elif order_value < 10_000_000:  # 1000만원 미만
            rate = self.commission  # 0.15%
        elif order_value < 100_000_000:  # 1억원 미만
            rate = self.commission * 0.8  # 0.12%
        else:  # 1억원 이상
            rate = self.commission * 0.6  # 0.09%
        
        commission = order_value * rate
        if is_round_trip:
            commission *= 2  # 매수+매도
        
        return commission
    
    def _check_liquidity(
        self,
        signal: OrderSignal,
        current_bar: OHLC,
        historical_bars: pd.DataFrame = None
    ) -> bool:
        """
        유동성 체크 (거래량 부족 시 주문 실패)
        
        Args:
            signal: 주문 신호
            current_bar: 현재 OHLC 바
            historical_bars: 과거 데이터 (평균 거래량 계산용)
        
        Returns:
            유동성이 충분하면 True, 부족하면 False
        """
        if current_bar.volume <= 0:
            logger.warning(f"Liquidity check failed: {signal.symbol} has zero volume")
            return False
        
        # 주문 수량이 거래량 대비 비율
        volume_ratio = signal.quantity / current_bar.volume
        
        # 임계값: 주문 수량이 일일 거래량의 10% 초과 시 실패
        LIQUIDITY_THRESHOLD = 0.10
        
        if volume_ratio > LIQUIDITY_THRESHOLD:
            logger.warning(
                f"Liquidity check failed: {signal.symbol} "
                f"order quantity ({signal.quantity}) exceeds {LIQUIDITY_THRESHOLD:.1%} "
                f"of daily volume ({current_bar.volume})"
            )
            return False
        
        # 추가 체크: 평균 거래량 대비 현재 거래량이 너무 낮으면 경고
        if historical_bars is not None and len(historical_bars) >= 20:
            avg_volume = historical_bars['volume'].tail(20).mean()
            if current_bar.volume < avg_volume * 0.3:  # 평균의 30% 미만
                logger.warning(
                    f"Low liquidity warning: {signal.symbol} "
                    f"current volume ({current_bar.volume:,.0f}) is below 30% "
                    f"of 20-day average ({avg_volume:,.0f})"
                )
                # 경고만 하고 주문은 진행 (선택적)
        
        return True
    
    def _process_signal(self, signal: OrderSignal, current_bar: OHLC, historical_bars: pd.DataFrame = None) -> None:
        """
        주문 신호 처리 (리스크 관리 강화, 동적 슬리피지/수수료 적용, 유동성 체크)
        
        Args:
            signal: 주문 신호
            current_bar: 현재 OHLC 바
            historical_bars: 과거 데이터 (동적 슬리피지 계산용)
        """
        # 유동성 체크
        if not self._check_liquidity(signal, current_bar, historical_bars):
            logger.warning(f"Order rejected due to insufficient liquidity: {signal.symbol} {signal.side.value} {signal.quantity}")
            return
        
        # 동적 슬리피지 계산
        slippage = self._calculate_dynamic_slippage(
            current_bar,
            historical_bars,
            signal.quantity
        )
        
        # 실행 가격 계산 (슬리피지 적용)
        if signal.order_type == OrderType.MARKET:
            if signal.side == OrderSide.BUY:
                execution_price = current_bar.close * (1 + slippage)
            else:
                execution_price = current_bar.close * (1 - slippage)
        else:
            execution_price = signal.price or current_bar.close
        
        # 매수 처리
        if signal.side == OrderSide.BUY:
            order_value = signal.quantity * execution_price
            commission_cost = self._calculate_commission(order_value, is_round_trip=False)
            total_cost = order_value + commission_cost
            
            # 🔒 강화된 리스크 관리: 잔액 확인 및 자동 수량 조정
            available_cash = max(0, self.cash)
            
            # 잔액 부족 시 자동 수량 조정
            if total_cost > available_cash:
                # 사용 가능한 현금의 80%로 수량 조정 (기존 95%에서 축소)
                max_investment = available_cash * 0.8
                # 수수료를 고려한 최대 수량 계산 (반복 계산으로 정확도 향상)
                estimated_commission_rate = self.commission if not self.use_tiered_commission else self.commission * 0.8
                adjusted_quantity = int(max_investment / (execution_price * (1 + estimated_commission_rate)))
                
                if adjusted_quantity <= 0:
                    logger.debug(f"투자 가능 수량 없음: {signal.symbol} (현금: {available_cash:,.0f})")
                    return
                
                # 수량 조정 적용
                original_quantity = signal.quantity
                signal.quantity = adjusted_quantity
                order_value = signal.quantity * execution_price
                commission_cost = self._calculate_commission(order_value, is_round_trip=False)
                total_cost = order_value + commission_cost
                
                logger.debug(f"수량 자동 조정: {signal.symbol} {original_quantity}주 → {adjusted_quantity}주")
            
            # 🚨 추가 안전장치: 단일 거래 최대 투자 한도
            max_single_investment = self.initial_capital * 0.1  # 초기 자본의 10%
            if total_cost > max_single_investment:
                estimated_commission_rate = self.commission if not self.use_tiered_commission else self.commission * 0.8
                safe_quantity = int(max_single_investment / (execution_price * (1 + estimated_commission_rate)))
                if safe_quantity < signal.quantity:
                    logger.warning(f"단일 거래 한도 초과로 수량 조정: {signal.quantity}주 → {safe_quantity}주")
                    signal.quantity = safe_quantity
                    order_value = signal.quantity * execution_price
                    commission_cost = self._calculate_commission(order_value, is_round_trip=False)
                    total_cost = order_value + commission_cost
            
            # 포지션 진입
            trade = self.position_manager.open_position(
                symbol=signal.symbol,
                quantity=signal.quantity,
                price=execution_price,
                timestamp=current_bar.timestamp
            )
            
            # 현금 차감 (마이너스 방지)
            self.cash = max(0, self.cash - total_cost)
            self.all_trades.append(trade)
            
            logger.debug(f"매수 체결: {signal.symbol}, {signal.quantity}주 @ {execution_price:,.0f}, 잔액: {self.cash:,.0f}")
            
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
            
            # 매도 수량 조정 (보유 수량 초과 방지)
            sell_quantity = min(signal.quantity, position.quantity)
            
            # 포지션 청산
            trade = self.position_manager.close_position(
                symbol=signal.symbol,
                quantity=sell_quantity,
                price=execution_price,
                timestamp=current_bar.timestamp
            )
            
            if trade:
                # 현금 증가
                order_value = sell_quantity * execution_price
                commission_cost = self._calculate_commission(order_value, is_round_trip=False)
                net_proceeds = order_value - commission_cost
                self.cash += net_proceeds
                self.all_trades.append(trade)
                
                logger.debug(f"매도 체결: {signal.symbol}, {sell_quantity}주 @ {execution_price:,.0f}, 잔액: {self.cash:,.0f}")
                
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
    
    def _convert_to_dataframe(self, ohlc_list: List[OHLC]) -> pd.DataFrame:
        """
        OHLC 리스트를 DataFrame으로 변환
        
        Args:
            ohlc_list: OHLC 객체 리스트
        
        Returns:
            OHLCV DataFrame (timestamp 인덱스)
        """
        if not ohlc_list:
            return pd.DataFrame()
        
        data = {
            'timestamp': [bar.timestamp for bar in ohlc_list],
            'open': [bar.open for bar in ohlc_list],
            'high': [bar.high for bar in ohlc_list],
            'low': [bar.low for bar in ohlc_list],
            'close': [bar.close for bar in ohlc_list],
            'volume': [bar.volume for bar in ohlc_list],
            'value': [bar.value if bar.value is not None else bar.volume * bar.close for bar in ohlc_list]
        }
        
        df = pd.DataFrame(data)
        df = df.set_index('timestamp')
        
        return df
    
    def _update_equity(self, timestamp: datetime) -> None:
        """자산 곡선 업데이트 (정확한 MDD 계산을 위한 수정)"""
        # 포지션 가치 계산
        position_value = self.position_manager.get_total_position_value()
        
        # 실제 자산 = 현금 + 포지션 가치 (음수 허용)
        self.equity = self.cash + position_value
        
        # 자산 곡선에 실제 값 기록 (MDD 계산의 정확성을 위해)
        self.equity_curve.append(self.equity)
        self.equity_timestamps.append(timestamp)
        
        # 🚨 위험 신호 감지 (로깅용)
        if self.equity < self.initial_capital * 0.5:  # 50% 이상 손실
            logger.warning(f"⚠️ 큰 손실 발생: {timestamp.date()}, 자산: {self.equity:,.0f} ({(self.equity/self.initial_capital-1)*100:.1f}%)")
        
        if self.cash < 0:
            logger.warning(f"⚠️ 마이너스 현금: {timestamp.date()}, 현금: {self.cash:,.0f}")
        
        # 극단적 손실 체크 (99% 이상 손실 시 백테스트 중단)
        if self.equity < self.initial_capital * 0.01:
            logger.error(f"🚨 극단적 손실로 백테스트 중단: {timestamp.date()}, 자산: {self.equity:,.0f}")
            raise RuntimeError(f"Extreme loss detected: {self.equity/self.initial_capital:.1%}")
        
        logger.debug(f"자산 업데이트: {timestamp.date()}, 현금: {self.cash:,.0f}, 포지션가치: {position_value:,.0f}, 총자산: {self.equity:,.0f}")
    
    def _generate_result(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """백테스트 결과 생성 (검증 로직 포함)"""
        from core.backtest.metrics import calculate_metrics
        
        # 자산 곡선 검증
        logger.info(f"=== 백테스트 결과 생성 ===")
        logger.info(f"자산 곡선 길이: {len(self.equity_curve)}")
        logger.info(f"초기 자본: {self.initial_capital:,.0f}")
        logger.info(f"최종 자산: {self.equity:,.0f}")
        
        if self.equity_curve:
            min_equity = min(self.equity_curve)
            max_equity = max(self.equity_curve)
            logger.info(f"자산 범위: {min_equity:,.0f} ~ {max_equity:,.0f}")
            
            # 비정상적인 자산 곡선 감지
            if min_equity <= 0:
                logger.warning(f"⚠️ 음수 자산 감지: 최소값 {min_equity:,.0f}")
            
            if max_equity > self.initial_capital * 10:
                logger.warning(f"⚠️ 과도한 수익 감지: 최대값 {max_equity:,.0f} (초기 자본의 {max_equity/self.initial_capital:.1f}배)")
        
        # 메트릭 계산
        metrics = calculate_metrics(
            equity_curve=self.equity_curve,
            trades=self.all_trades,
            initial_capital=self.initial_capital
        )
        
        # MDD 검증
        if metrics["mdd"] > 0.8:  # 80% 이상 MDD
            logger.error(f"🚨 비정상적인 MDD 감지: {metrics['mdd']:.2%}")
            logger.error(f"자산 곡선 샘플: {self.equity_curve[:5]} ... {self.equity_curve[-5:]}")
        
        logger.info(f"계산된 메트릭: 총수익률={metrics['total_return']:.2%}, MDD={metrics['mdd']:.2%}, 샤프={metrics['sharpe_ratio']:.2f}")
        
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
            equity_timestamps=self.equity_timestamps,
            trades=self.all_trades
        )
