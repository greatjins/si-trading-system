"""
ICT (Inner Circle Trader) 기반 전략
- Smart Money Concepts 적용
- 기관투자자 관점의 시장 분석
- 유동성 기반 진입/청산
- Multi-timeframe 분석: 일봉 FVG/OB + 60분봉 MSS
"""
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy
from utils.types import OHLC, Position, Account, OrderSignal, OrderSide, OrderType, Order
from utils.logger import setup_logger
from utils.indicators import calculate_fvg, calculate_order_block, calculate_mss
from data.repository import DataRepository

logger = setup_logger(__name__)


@strategy(
    name="ICTStrategy",
    description="ICT 이론 기반 Smart Money 전략 - 기관투자자 관점의 시장 분석",
    author="LS HTS Team",
    version="1.0.0",
    parameters={
        "symbol": {
            "type": "str",
            "default": "005930",
            "description": "종목 코드"
        },
        "lookback_period": {
            "type": "int",
            "default": 50,
            "min": 20,
            "max": 200,
            "description": "시장 구조 분석 기간"
        },
        "fvg_threshold": {
            "type": "float",
            "default": 0.002,
            "min": 0.001,
            "max": 0.01,
            "description": "Fair Value Gap 최소 크기 (비율)"
        },
        "liquidity_threshold": {
            "type": "float",
            "default": 0.015,
            "min": 0.005,
            "max": 0.05,
            "description": "유동성 풀 감지 임계값 (비율)"
        },
        "risk_per_trade": {
            "type": "float",
            "default": 0.02,
            "min": 0.01,
            "max": 0.05,
            "description": "거래당 리스크 (계좌 대비 비율)"
        },
        "rr_ratio": {
            "type": "float",
            "default": 2.0,
            "min": 1.0,
            "max": 5.0,
            "description": "Risk-Reward 비율"
        }
    }
)
class ICTStrategy(BaseStrategy):
    """
    ICT (Inner Circle Trader) 전략
    
    핵심 로직:
    1. Market Structure 분석 (BOS, CHoCH 감지)
    2. Liquidity Pool 식별 (고점/저점 클러스터)
    3. Fair Value Gap (FVG) 감지
    4. Order Block 식별
    5. Smart Money 흐름 분석
    6. 유동성 기반 진입/청산
    """
    
    def __init__(self, params: dict):
        super().__init__(params)
        
        self.symbol = self.get_param("symbol", "005930")
        self.lookback_period = self.get_param("lookback_period", 50)
        self.fvg_threshold = self.get_param("fvg_threshold", 0.002)
        self.liquidity_threshold = self.get_param("liquidity_threshold", 0.015)
        self.risk_per_trade = self.get_param("risk_per_trade", 0.02)
        self.rr_ratio = self.get_param("rr_ratio", 2.0)
        
        # 상태 변수
        self.market_structure = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
        self.last_bos = None  # Break of Structure
        self.order_blocks = []  # 식별된 Order Block들
        self.liquidity_pools = {"highs": [], "lows": []}
        self.fair_value_gaps = []
        
        # Multi-timeframe 분석용
        self.daily_fvgs = []  # 일봉 FVG 구간들
        self.daily_obs = []   # 일봉 Order Block 구간들
        self.repository = DataRepository()  # 데이터 로드용
        
        logger.info(f"ICT Strategy initialized: {self.symbol}")
    
    def on_bar(
        self,
        bars: pd.DataFrame,
        positions: List[Position],
        account: Account
    ) -> List[OrderSignal]:
        """
        ICT 분석 및 신호 생성 (Multi-timeframe 강화)
        
        로직:
        1. 일봉(1d) 데이터를 DataRepository를 통해 별도로 로드하여 'Daily OB/FVG' 구간을 먼저 계산
        2. 현재 들어오는 60분봉 가격이 이 'Daily 구간'에 도달했는지 확인
        3. Daily 구간에 도달했을 때만 MSS(Market Structure Shift)를 확인하여 진입 시그널 생성
        """
        signals: List[OrderSignal] = []
        
        if not self._validate_data(bars):
            return signals
        
        # 현재 bars는 60분봉으로 가정 (실행 엔진에서 전달받은 timeframe)
        current_price = bars['close'].iloc[-1]
        current_time = bars.index[-1]
        
        try:
            # ===== 1단계: 일봉 데이터 로드 및 Daily OB/FVG 구간 계산 =====
            daily_bars = self._load_daily_bars(current_time)
            if daily_bars is None or len(daily_bars) < 3:
                logger.warning(f"Daily bars insufficient for {self.symbol}: {len(daily_bars) if daily_bars is not None else 0} bars")
                # Daily 데이터가 없으면 청산 신호만 처리
                exit_signal = self._generate_exit_signal(bars, positions)
                if exit_signal:
                    signals.append(exit_signal)
                return signals
            
            # 일봉에서 FVG 계산
            daily_bars_with_fvg = calculate_fvg(daily_bars.copy())
            self.daily_fvgs = self._extract_fvg_levels(daily_bars_with_fvg)
            
            # 일봉에서 Order Block 계산
            daily_bars_with_ob = calculate_order_block(daily_bars.copy())
            self.daily_obs = self._extract_ob_levels(daily_bars_with_ob)
            
            logger.debug(f"Daily levels calculated - FVGs: {len(self.daily_fvgs)}, OBs: {len(self.daily_obs)}")
            
            # ===== 2단계: 60분봉 현재가가 Daily OB/FVG 구간에 도달했는지 확인 =====
            in_fvg_zone = self._check_price_in_fvg_zone(current_price)
            in_ob_zone = self._check_price_in_ob_zone(current_price)
            in_daily_zone = in_fvg_zone or in_ob_zone
            
            if not in_daily_zone:
                # Daily 구간에 도달하지 않았으면 MSS 확인하지 않고 청산 신호만 처리
                logger.debug(f"Price {current_price:,.0f} not in Daily zone - skipping MSS check")
                exit_signal = self._generate_exit_signal(bars, positions)
                if exit_signal:
                    signals.append(exit_signal)
                return signals
            
            # ===== 3단계: Daily 구간에 도달했을 때만 MSS 확인 =====
            logger.info(f"Price {current_price:,.0f} entered Daily zone (FVG: {in_fvg_zone}, OB: {in_ob_zone}) - checking MSS...")
            
            mss_occurred = False
            if len(bars) >= 10:
                # 60분봉 데이터에서 MSS 계산
                bars_with_mss = calculate_mss(bars.copy(), swing_lookback=5)
                mss_occurred = self._check_mss_occurred(bars_with_mss)
            else:
                logger.warning(f"Insufficient 60m bars for MSS analysis: {len(bars)} bars")
            
            # ===== 4단계: Daily 구간 진입 + MSS 발생 시 진입 시그널 생성 =====
            if mss_occurred:
                entry_signal = self._generate_entry_signal(bars, positions, account, current_price)
                if entry_signal:
                    signals.append(entry_signal)
                    logger.info(f"🟢 ICT Multi-timeframe Entry Signal: {current_price:,.0f} (Daily Zone: ✓, MSS: ✓)")
            else:
                logger.debug(f"MSS not occurred yet - waiting for structure shift")
            
            # ===== 5단계: 청산 신호 생성 =====
            exit_signal = self._generate_exit_signal(bars, positions)
            if exit_signal:
                signals.append(exit_signal)
        
        except Exception as e:
            logger.error(f"Error in ICT strategy on_bar: {e}", exc_info=True)
        
        return signals
    
    def _analyze_market_structure(self, bars: pd.DataFrame) -> None:
        """
        시장 구조 분석 (BOS, CHoCH 감지)
        """
        if len(bars) < 20:
            return
        
        # Swing High/Low 식별
        highs = self._find_swing_points(bars['high'], 'high')
        lows = self._find_swing_points(bars['low'], 'low')
        
        # BOS (Break of Structure) 감지
        current_price = bars['close'].iloc[-1]
        
        # 상승 BOS: 이전 고점 돌파
        if highs and current_price > max(highs[-3:]) * 1.001:
            if self.market_structure != "BULLISH":
                self.market_structure = "BULLISH"
                self.last_bos = {"type": "BULLISH", "price": current_price, "time": bars.index[-1]}
                logger.info(f"🟢 Bullish BOS detected at {current_price:,.0f}")
        
        # 하락 BOS: 이전 저점 하향 돌파
        elif lows and current_price < min(lows[-3:]) * 0.999:
            if self.market_structure != "BEARISH":
                self.market_structure = "BEARISH"
                self.last_bos = {"type": "BEARISH", "price": current_price, "time": bars.index[-1]}
                logger.info(f"🔴 Bearish BOS detected at {current_price:,.0f}")
    
    def _identify_liquidity_pools(self, bars: pd.DataFrame) -> None:
        """
        유동성 풀 식별 (고점/저점 클러스터)
        """
        if len(bars) < 20:
            return
        
        # 최근 N개 봉의 고점/저점 분석
        recent_bars = bars.tail(self.lookback_period)
        
        # 고점 클러스터 (저항선)
        highs = recent_bars['high'].rolling(window=5).max()
        high_clusters = self._find_price_clusters(highs.dropna(), self.liquidity_threshold)
        
        # 저점 클러스터 (지지선)
        lows = recent_bars['low'].rolling(window=5).min()
        low_clusters = self._find_price_clusters(lows.dropna(), self.liquidity_threshold)
        
        self.liquidity_pools = {
            "highs": high_clusters,
            "lows": low_clusters
        }
        
        logger.debug(f"Liquidity pools - Highs: {len(high_clusters)}, Lows: {len(low_clusters)}")
    
    # _detect_fair_value_gaps와 _identify_order_blocks 메서드는 
    # utils/indicators.py의 calculate_fvg와 calculate_order_block 함수로 대체되었습니다.
    # 이 메서드들은 더 이상 사용되지 않으며, 공통 함수를 사용하도록 변경되었습니다.
    
    def _load_daily_bars(self, current_time: datetime) -> Optional[pd.DataFrame]:
        """
        일봉(1d) 데이터를 DataRepository를 통해 별도로 로드
        
        Args:
            current_time: 현재 시간 (60분봉의 타임스탬프)
            
        Returns:
            일봉 DataFrame (없으면 None)
            
        Note:
            - DataRepository는 로컬 캐시(DB/Parquet) 우선 조회
            - 캐시에 없으면 자동으로 브로커 API 호출하여 데이터 수집
        """
        try:
            # 최근 100일 일봉 데이터 로드 (충분한 기간 확보)
            end_date = current_time
            start_date = end_date - timedelta(days=100)
            
            logger.debug(f"Loading daily bars for {self.symbol} from {start_date.date()} to {end_date.date()}")
            
            # DataRepository를 통해 일봉 데이터 로드
            # - DB 우선 조회, 없으면 Parquet 파일, 없으면 브로커 API 호출
            daily_bars = self.repository.get_ohlc(
                symbol=self.symbol,
                interval="1d",
                start_date=start_date,
                end_date=end_date
            )
            
            if daily_bars.empty:
                logger.warning(f"No daily bars found for {self.symbol}")
                return None
            
            logger.debug(f"Loaded {len(daily_bars)} daily bars for {self.symbol}")
            return daily_bars
            
        except Exception as e:
            logger.error(f"Failed to load daily bars for {self.symbol}: {e}", exc_info=True)
            return None
    
    def _extract_fvg_levels(self, daily_bars: pd.DataFrame) -> List[Dict]:
        """
        일봉에서 FVG 구간 추출
        
        Args:
            daily_bars: FVG가 계산된 일봉 DataFrame
            
        Returns:
            FVG 구간 리스트 [{'type': 'bullish'/'bearish', 'top': float, 'bottom': float, 'filled': bool}, ...]
        """
        fvgs = []
        
        for idx, row in daily_bars.iterrows():
            if pd.notna(row.get('fvg_type')):
                fvg = {
                    'type': row['fvg_type'],
                    'top': row['fvg_top'],
                    'bottom': row['fvg_bottom'],
                    'filled': row.get('fvg_filled', False),
                    'timestamp': idx
                }
                fvgs.append(fvg)
        
        # 최근 10개만 유지
        return fvgs[-10:]
    
    def _extract_ob_levels(self, daily_bars: pd.DataFrame) -> List[Dict]:
        """
        일봉에서 Order Block 구간 추출
        
        Args:
            daily_bars: OB가 계산된 일봉 DataFrame
            
        Returns:
            OB 구간 리스트 [{'type': 'bullish'/'bearish', 'top': float, 'bottom': float}, ...]
        """
        obs = []
        
        for idx, row in daily_bars.iterrows():
            if pd.notna(row.get('order_block_type')):
                ob = {
                    'type': row['order_block_type'],
                    'top': row['order_block_top'],
                    'bottom': row['order_block_bottom'],
                    'timestamp': idx
                }
                obs.append(ob)
        
        # 최근 10개만 유지
        return obs[-10:]
    
    def _check_price_in_fvg_zone(self, current_price: float) -> bool:
        """
        60분봉 현재가가 일봉 FVG 구간에 진입했는지 체크
        
        Args:
            current_price: 현재가
            
        Returns:
            FVG 구간 내 진입 여부
        """
        for fvg in self.daily_fvgs:
            if fvg['filled']:
                continue  # 이미 채워진 FVG는 무시
            
            if fvg['type'] == 'bullish':
                # Bullish FVG: bottom <= price <= top
                if fvg['bottom'] <= current_price <= fvg['top']:
                    return True
            elif fvg['type'] == 'bearish':
                # Bearish FVG: bottom <= price <= top
                if fvg['bottom'] <= current_price <= fvg['top']:
                    return True
        
        return False
    
    def _check_price_in_ob_zone(self, current_price: float) -> bool:
        """
        60분봉 현재가가 일봉 Order Block 구간에 진입했는지 체크
        
        Args:
            current_price: 현재가
            
        Returns:
            OB 구간 내 진입 여부
        """
        for ob in self.daily_obs:
            # OB 구간: bottom <= price <= top
            if ob['bottom'] <= current_price <= ob['top']:
                return True
        
        return False
    
    def _check_mss_occurred(self, bars_with_mss: pd.DataFrame) -> bool:
        """
        60분봉에서 MSS(Market Structure Shift) 발생 여부 확인
        
        Args:
            bars_with_mss: MSS가 계산된 60분봉 DataFrame
            
        Returns:
            MSS 발생 여부
        """
        # 최근 5개 캔들에서 MSS 발생 확인
        recent_bars = bars_with_mss.tail(5)
        
        for idx, row in recent_bars.iterrows():
            if pd.notna(row.get('mss_type')):
                # MSS 발생 (상승 구조 전환 또는 하락 구조 전환)
                mss_type = row['mss_type']
                if mss_type == 'bullish':
                    # 상승 구조 전환: 매수 시그널에 유리
                    return True
        
        return False
    
    def _generate_entry_signal(
        self, 
        bars: pd.DataFrame, 
        positions: List[Position], 
        account: Account,
        current_price: float
    ) -> Optional[OrderSignal]:
        """
        ICT 기반 진입 신호 생성 (Multi-timeframe)
        """
        position = self.get_position(self.symbol, positions)
        if position:  # 이미 포지션 보유 중
            return None
        
        # Bullish FVG/OB 구간 진입 + MSS 발생 시 매수
        bullish_fvg = any(fvg['type'] == 'bullish' and fvg['bottom'] <= current_price <= fvg['top'] 
                          for fvg in self.daily_fvgs if not fvg['filled'])
        bullish_ob = any(ob['type'] == 'bullish' and ob['bottom'] <= current_price <= ob['top'] 
                         for ob in self.daily_obs)
        
        if bullish_fvg or bullish_ob:
            quantity = self._calculate_position_size(account.equity, current_price, "BUY")
            
            if quantity > 0:
                return OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    order_type=OrderType.MARKET
                )
        
        return None
    
    def _check_bullish_entry(self, bars: pd.DataFrame, current_price: float) -> bool:
        """
        상승 진입 조건 확인
        """
        # 1. 상승 시장 구조
        if self.market_structure != "BULLISH":
            return False
        
        # 2. FVG 리테스트
        for fvg in self.fair_value_gaps:
            if (fvg["type"] == "BULLISH" and 
                not fvg["filled"] and
                fvg["bottom"] <= current_price <= fvg["top"]):
                return True
        
        # 3. Order Block 리테스트
        for ob in self.order_blocks:
            if (ob["type"] == "BULLISH" and
                ob["bottom"] <= current_price <= ob["top"]):
                return True
        
        # 4. 유동성 풀 테스트 후 반등
        for low_pool in self.liquidity_pools["lows"]:
            if abs(current_price - low_pool) / low_pool < 0.005:  # 0.5% 이내
                # 반등 확인
                if len(bars) >= 3:
                    recent_low = bars['low'].tail(3).min()
                    if current_price > recent_low * 1.002:  # 0.2% 반등
                        return True
        
        return False
    
    def _check_bearish_entry(self, bars: pd.DataFrame, current_price: float) -> bool:
        """
        하락 진입 조건 확인
        """
        # 1. 하락 시장 구조
        if self.market_structure != "BEARISH":
            return False
        
        # 2. FVG 리테스트
        for fvg in self.fair_value_gaps:
            if (fvg["type"] == "BEARISH" and 
                not fvg["filled"] and
                fvg["bottom"] <= current_price <= fvg["top"]):
                return True
        
        # 3. Order Block 리테스트
        for ob in self.order_blocks:
            if (ob["type"] == "BEARISH" and
                ob["bottom"] <= current_price <= ob["top"]):
                return True
        
        # 4. 유동성 풀 테스트 후 하락
        for high_pool in self.liquidity_pools["highs"]:
            if abs(current_price - high_pool) / high_pool < 0.005:  # 0.5% 이내
                # 하락 확인
                if len(bars) >= 3:
                    recent_high = bars['high'].tail(3).max()
                    if current_price < recent_high * 0.998:  # 0.2% 하락
                        return True
        
        return False
    
    def _generate_exit_signal(
        self, 
        bars: pd.DataFrame, 
        positions: List[Position]
    ) -> Optional[OrderSignal]:
        """
        청산 신호 생성
        """
        position = self.get_position(self.symbol, positions)
        if not position:
            return None
        
        current_price = bars['close'].iloc[-1]
        
        # 손절/익절 로직
        if position.quantity > 0:  # 롱 포지션
            # 손절: 최근 저점 하향 돌파
            recent_low = bars['low'].tail(10).min()
            if current_price < recent_low * 0.995:
                logger.info(f"🔴 Long Stop Loss: {current_price:,.0f}")
                return OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
            
            # 익절: 유동성 풀 도달
            for high_pool in self.liquidity_pools["highs"]:
                if current_price >= high_pool * 0.998:
                    logger.info(f"🟢 Long Take Profit: {current_price:,.0f}")
                    return OrderSignal(
                        symbol=self.symbol,
                        side=OrderSide.SELL,
                        quantity=position.quantity,
                        order_type=OrderType.MARKET
                    )
        
        return None
    
    def _calculate_position_size(
        self, 
        equity: float, 
        price: float, 
        direction: str
    ) -> int:
        """
        안전한 포지션 사이징 (MDD 최소화)
        """
        # 🔧 극도로 보수적인 접근 (MDD 94% 문제 해결)
        
        # 1. 최대 투자 금액: 자본의 5% (기존 10%에서 축소)
        max_investment = equity * 0.05
        
        # 2. 리스크 기반 계산
        risk_amount = equity * self.risk_per_trade  # 자본의 2%
        stop_loss_pct = 0.03  # 3% 스탑로스 (기존 2%에서 확대)
        
        # 3. 리스크 기반 포지션 가치 계산
        # 리스크 금액 / 스탑로스 비율 = 최대 포지션 가치
        risk_based_investment = risk_amount / stop_loss_pct
        
        # 4. 더 보수적인 값 선택
        safe_investment = min(max_investment, risk_based_investment)
        
        # 5. 추가 안전장치: 현금 보유량 확인
        # 전체 자본의 80%는 현금으로 보유 (20%만 투자)
        max_total_investment = equity * 0.2
        safe_investment = min(safe_investment, max_total_investment)
        
        # 6. 수수료 고려한 실제 가격
        commission_rate = 0.0015  # 0.15%
        slippage_rate = 0.0005   # 0.05%
        effective_price = price * (1 + commission_rate + slippage_rate)
        
        # 7. 수량 계산
        quantity = int(safe_investment / effective_price)
        
        # 8. 최종 안전장치
        min_quantity = 1
        max_quantity = int((equity * 0.05) / effective_price)  # 절대 5% 초과 금지
        
        final_quantity = max(min_quantity, min(quantity, max_quantity))
        
        # 9. 로깅 (디버깅용)
        investment_ratio = (final_quantity * effective_price) / equity
        logger.debug(f"Position sizing - Equity: {equity:,.0f}, Investment: {final_quantity * effective_price:,.0f} ({investment_ratio:.1%})")
        
        return final_quantity
    
    def _find_swing_points(self, series: pd.Series, point_type: str) -> List[float]:
        """
        Swing High/Low 찾기
        """
        points = []
        window = 5
        
        for i in range(window, len(series) - window):
            if point_type == 'high':
                if series.iloc[i] == series.iloc[i-window:i+window+1].max():
                    points.append(series.iloc[i])
            else:  # low
                if series.iloc[i] == series.iloc[i-window:i+window+1].min():
                    points.append(series.iloc[i])
        
        return points[-10:]  # 최근 10개만
    
    def _find_price_clusters(self, prices: pd.Series, threshold: float) -> List[float]:
        """
        가격 클러스터 찾기 (유동성 풀)
        """
        if len(prices) < 3:
            return []
        
        clusters = []
        sorted_prices = sorted(prices.unique())
        
        for price in sorted_prices:
            # 임계값 내의 가격들 그룹화
            nearby_prices = [p for p in sorted_prices 
                           if abs(p - price) / price <= threshold]
            
            if len(nearby_prices) >= 3:  # 최소 3개 이상
                cluster_price = np.mean(nearby_prices)
                if not any(abs(cluster_price - c) / c <= threshold for c in clusters):
                    clusters.append(cluster_price)
        
        return clusters[-5:]  # 최근 5개만
    
    def _validate_data(self, bars: pd.DataFrame) -> bool:
        """
        데이터 유효성 검증
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        return all(col in bars.columns for col in required_cols) and len(bars) > 0
    
    def on_fill(self, order: Order, position: Position) -> None:
        """주문 체결 시 호출"""
        logger.info(f"[ICT] Order filled: {order.side.value} {order.filled_quantity} @ {order.price}")