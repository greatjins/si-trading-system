"""
동적 전략 클래스 - DB의 config_json을 실행 시점에 로드하여 동작
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from core.strategy.base import BaseStrategy
from utils.types import Position, Account, OrderSignal, Order, OrderSide, OrderType
from utils.logger import setup_logger
from data.models import StrategyBuilderModel
from data.repository import get_db_session

logger = setup_logger(__name__)


class DynamicStrategy(BaseStrategy):
    """
    동적 전략 클래스
    
    실행 시점에 DB에서 config_json을 로드하여 동작합니다.
    파이썬 파일을 생성하지 않고, DB 설정만 업데이트하면 즉시 반영됩니다.
    
    config_json 구조:
    {
        "indicators": [...],  # 지표 설정
        "conditions": {
            "buy": [...],     # 매수 조건
            "sell": [...]     # 매도 조건
        },
        "parameters": {...}   # 전략 파라미터
    }
    """
    
    def __init__(self, params: Dict[str, Any]):
        """
        Args:
            params: 전략 파라미터 {
                "strategy_id": int,  # StrategyBuilderModel.id (필수)
                "config_json": Dict,  # 직접 전달 가능 (선택)
                ...
            }
        """
        super().__init__(params)
        
        self.strategy_id = params.get('strategy_id')
        
        # config_json 로드 (직접 전달되었거나 DB에서 로드)
        self.config_json = params.get('config_json')
        if not self.config_json:
            # config_json이 없으면 DB에서 로드 (strategy_id 필수)
            if not self.strategy_id:
                raise ValueError("Either strategy_id or config_json is required for DynamicStrategy")
            self._load_config_from_db()
        
        # 지표 설정 추출
        self.indicators = self.config_json.get('indicators', [])
        
        # 조건 추출
        conditions = self.config_json.get('conditions', {})
        self.buy_conditions = conditions.get('buy', [])
        self.sell_conditions = conditions.get('sell', [])
        
        # 전략 파라미터
        self.strategy_params = self.config_json.get('parameters', {})
        
        # is_portfolio를 self.params에 추가 (BaseStrategy.is_portfolio_strategy()에서 사용)
        if 'is_portfolio' in self.strategy_params:
            self.params['is_portfolio'] = self.strategy_params['is_portfolio']
        elif 'stock_selection' in self.config_json:
            # stock_selection이 있으면 포트폴리오 전략
            self.params['is_portfolio'] = True
        
        logger.info(f"DynamicStrategy initialized: strategy_id={self.strategy_id if self.strategy_id else 'N/A (config_json provided)'}")
        logger.debug(f"  Indicators: {len(self.indicators)}")
        logger.debug(f"  Buy conditions: {len(self.buy_conditions)}")
        logger.debug(f"  Sell conditions: {len(self.sell_conditions)}")
        logger.debug(f"  Is portfolio: {self.params.get('is_portfolio', False)}")
    
    def _load_config_from_db(self) -> None:
        """DB에서 config_json 로드"""
        db = get_db_session()
        try:
            strategy = db.query(StrategyBuilderModel).filter(
                StrategyBuilderModel.id == self.strategy_id,
                StrategyBuilderModel.is_active == True
            ).first()
            
            if not strategy:
                raise ValueError(f"Strategy not found: strategy_id={self.strategy_id}")
            
            if not strategy.config_json:
                raise ValueError(f"config_json is not set for strategy_id={self.strategy_id}")
            
            self.config_json = strategy.config_json
            self.name = strategy.name  # 전략 이름 업데이트
            
            # 전략 파라미터 업데이트
            self.strategy_params = self.config_json.get('parameters', {})
            
            # is_portfolio를 self.params에 추가
            if 'is_portfolio' in self.strategy_params:
                self.params['is_portfolio'] = self.strategy_params['is_portfolio']
            elif 'stock_selection' in self.config_json:
                # stock_selection이 있으면 포트폴리오 전략
                self.params['is_portfolio'] = True
            
            logger.info(f"Loaded config_json from DB: strategy_id={self.strategy_id}, name={strategy.name}")
        
        finally:
            db.close()
    
    def on_bar(
        self,
        bars: pd.DataFrame,
        positions: List[Position],
        account: Account
    ) -> List[OrderSignal]:
        """
        새로운 바마다 호출됨
        
        Args:
            bars: OHLCV DataFrame (지표가 추가된 상태)
            positions: 현재 보유 포지션 리스트
            account: 현재 계좌 상태
        
        Returns:
            주문 신호 리스트
        """
        if len(bars) == 0:
            return []
        
        # 지표 계산 (config_json 기반)
        bars = self.apply_indicators(bars, self.config_json)
        
        signals = []
        
        # 현재 가격
        current_price = bars['close'].iloc[-1]
        current_symbol = bars.index[-1] if hasattr(bars.index[-1], '__str__') else None
        
        # 심볼이 없으면 첫 번째 컬럼의 이름에서 추론 시도
        if current_symbol is None:
            # DataFrame의 인덱스가 timestamp인 경우, symbol은 별도로 관리
            # 여기서는 params에서 symbol을 가져오거나, positions에서 추론
            if positions:
                current_symbol = positions[0].symbol
            else:
                current_symbol = self.params.get('symbol')
        
        if not current_symbol:
            logger.warning("Cannot determine symbol, skipping signal generation")
            return []
        
        # 현재 포지션 확인
        current_position = self.get_position(current_symbol, positions)
        has_position = current_position is not None and current_position.quantity > 0
        
        # 매수 조건 확인 (포지션이 없을 때만)
        if not has_position:
            if self._check_conditions(bars, self.buy_conditions):
                # 매수 신호 생성
                quantity = self._calculate_quantity(account, current_price, bars)
                if quantity > 0:
                    signal = OrderSignal(
                        symbol=current_symbol,
                        side=OrderSide.BUY,
                        quantity=quantity,
                        order_type=OrderType.MARKET
                    )
                    signals.append(signal)
                    logger.info(f"Buy signal generated: {current_symbol} x {quantity}")
        
        # 매도 조건 확인 (포지션이 있을 때만)
        if has_position:
            if self._check_conditions(bars, self.sell_conditions):
                # 매도 신호 생성 (전량 매도)
                signal = OrderSignal(
                    symbol=current_symbol,
                    side=OrderSide.SELL,
                    quantity=current_position.quantity,
                    order_type=OrderType.MARKET
                )
                signals.append(signal)
                logger.info(f"Sell signal generated: {current_symbol} x {current_position.quantity}")
        
        return signals
    
    def _check_conditions(self, bars: pd.DataFrame, conditions: List[Dict[str, Any]]) -> bool:
        """
        조건 리스트 확인 (AND 조건: 모든 조건이 True여야 함)
        
        Args:
            bars: OHLCV DataFrame (지표 포함)
            conditions: 조건 리스트
        
        Returns:
            모든 조건이 만족되면 True
        """
        if not conditions:
            return False
        
        for condition in conditions:
            if not self._evaluate_condition(bars, condition):
                return False
        
        return True
    
    def _evaluate_logical_tree(self, bars: pd.DataFrame, node: Dict[str, Any], depth: int = 0) -> bool:
        """
        논리 트리 평가
        
        Args:
            bars: OHLCV DataFrame (지표 포함)
            node: 논리 트리 노드 {
                "operator": ">" | "<" | "AND" | "OR" | "NOT",
                "left": {...} | 값,
                "right": {...} | 값
            }
            depth: 현재 재귀 깊이 (기본값: 0, 최대: 20)
        
        Returns:
            논리 트리 평가 결과
        
        Raises:
            ValueError: 재귀 깊이 초과 또는 잘못된 노드 구조
        """
        # 재귀 깊이 제한 (무한 재귀 방지)
        MAX_DEPTH = 20
        if depth > MAX_DEPTH:
            logger.error(f"논리 트리 재귀 깊이 초과 (최대: {MAX_DEPTH})")
            raise ValueError(f"논리 트리 재귀 깊이가 {MAX_DEPTH}를 초과했습니다")
        
        operator = node.get("operator")
        if not operator:
            logger.warning("논리 트리 노드에 연산자가 없습니다")
            return False
        
        try:
            # 단항 연산자 (NOT)
            if operator == "NOT":
                left_value = self._get_node_value(bars, node.get("left"), depth + 1)
                return not bool(left_value)
            
            # 이항 연산자
            left_value = self._get_node_value(bars, node.get("left"), depth + 1)
            right_value = self._get_node_value(bars, node.get("right"), depth + 1)
            
            if operator == "AND":
                return bool(left_value) and bool(right_value)
            elif operator == "OR":
                return bool(left_value) or bool(right_value)
            elif operator == ">":
                return float(left_value) > float(right_value)
            elif operator == ">=":
                return float(left_value) >= float(right_value)
            elif operator == "<":
                return float(left_value) < float(right_value)
            elif operator == "<=":
                return float(left_value) <= float(right_value)
            elif operator == "==" or operator == "=":
                return abs(float(left_value) - float(right_value)) < 0.0001
            else:
                logger.warning(f"지원하지 않는 연산자: {operator}")
                return False
        
        except (ValueError, TypeError) as e:
            logger.error(f"논리 트리 평가 중 오류: {e}, node={node}")
            return False
        except Exception as e:
            logger.error(f"논리 트리 평가 중 예상치 못한 오류: {e}", exc_info=True)
            return False
    
    def _get_node_value(self, bars: pd.DataFrame, node: Any, depth: int = 0) -> Any:
        """
        논리 트리 노드에서 값 추출
        
        Args:
            bars: OHLCV DataFrame
            node: 노드 (dict, 값, 또는 None)
            depth: 현재 재귀 깊이
        
        Returns:
            노드 값 (None이면 0 반환)
        """
        if node is None:
            return 0
        
        # 이미 값인 경우 (int, float, str)
        if isinstance(node, (int, float, str, bool)):
            return node
        
        # 딕셔너리인 경우
        if isinstance(node, dict):
            # 논리 노드인 경우
            if "operator" in node:
                return self._evaluate_logical_tree(bars, node, depth)
            
            # 지표 참조인 경우
            if "type" in node and node["type"] == "indicator":
                indicator_name = node.get("name", "").upper()
                params = node.get("params", {})
                period = params.get("period", 14)
                
                value = self._get_indicator_value(bars, indicator_name, period)
                return value if value is not None else 0
            
            # 가격 참조인 경우
            if "type" in node and node["type"] == "price":
                try:
                    return float(bars['close'].iloc[-1])
                except (IndexError, KeyError):
                    logger.warning("가격 데이터를 가져올 수 없습니다")
                    return 0
            
            # 거래량 참조인 경우
            if "type" in node and node["type"] == "volume":
                try:
                    return float(bars['volume'].iloc[-1])
                except (IndexError, KeyError):
                    logger.warning("거래량 데이터를 가져올 수 없습니다")
                    return 0
        
        logger.warning(f"알 수 없는 노드 타입: {type(node)}")
        return 0
    
    def _evaluate_condition(self, bars: pd.DataFrame, condition: Dict[str, Any]) -> bool:
        """
        개별 조건 평가
        
        Args:
            bars: OHLCV DataFrame
            condition: 조건 딕셔너리 {
                "type": "logical" | "indicator" | "price" | "volume" | "ict",
                "indicator": "rsi" | "fvg" | ...,
                "operator": ">" | "<" | ">=" | "<=" | "==" | "in_gap" | "in_zone",
                "value": 70 | "bullish" | ...,
                "period": 14,
                "logical_tree": {...}  # type="logical"인 경우
            }
        
        Returns:
            조건이 만족되면 True
        """
        condition_type = condition.get('type', 'indicator')
        
        # 논리 트리 조건 평가
        if condition_type == "logical":
            logical_tree = condition.get('logical_tree')
            if not logical_tree:
                return False
            
            # Pydantic 모델인 경우 dict로 변환
            if hasattr(logical_tree, 'dict'):
                logical_tree = logical_tree.dict()
            
            return self._evaluate_logical_tree(bars, logical_tree)
        
        operator = condition.get('operator', '>')
        value = condition.get('value')
        
        try:
            if condition_type == 'indicator':
                # 기술적 지표 조건
                indicator_name = condition.get('indicator', '').upper()
                period = condition.get('period', 14)
                
                # DataFrame에서 지표 값 찾기
                indicator_value = self._get_indicator_value(bars, indicator_name, period)
                
                if indicator_value is None:
                    return False
                
                # 연산자로 비교
                return self._compare_values(indicator_value, operator, value)
            
            elif condition_type == 'ict':
                # ICT 지표 조건
                indicator_name = condition.get('indicator', '').lower()
                
                if indicator_name == 'fvg':
                    # FVG 조건: in_gap, bullish/bearish
                    return self._check_fvg_condition(bars, operator, value)
                
                elif indicator_name == 'liquidity' or indicator_name == 'liquidity_zones':
                    # Liquidity Zone 조건: in_zone
                    return self._check_liquidity_condition(bars, operator, value)
                
                elif indicator_name == 'order_block' or indicator_name == 'ob':
                    # Order Block 조건: in_block
                    return self._check_order_block_condition(bars, operator, value)
                
                elif indicator_name == 'mss' or indicator_name == 'bos':
                    # MSS/BOS 조건
                    return self._check_mss_bos_condition(bars, operator, value)
            
            elif condition_type == 'price':
                # 가격 조건
                current_price = bars['close'].iloc[-1]
                return self._compare_values(current_price, operator, value)
            
            elif condition_type == 'volume':
                # 거래량 조건
                current_volume = bars['volume'].iloc[-1]
                return self._compare_values(current_volume, operator, value)
        
        except Exception as e:
            logger.error(f"Error evaluating condition: {condition}, error: {e}", exc_info=True)
            return False
        
        return False
    
    def _get_indicator_value(self, bars: pd.DataFrame, indicator_name: str, period: int) -> Optional[float]:
        """DataFrame에서 지표 값 가져오기"""
        # 컬럼 이름 패턴 매칭
        # 예: RSI_14, MA_20, EMA_20, MACD_12_26 등
        
        if indicator_name == 'RSI':
            col_name = f'RSI_{period}'
        elif indicator_name == 'MA' or indicator_name == 'SMA':
            col_name = f'MA_{period}'
        elif indicator_name == 'EMA':
            col_name = f'EMA_{period}'
        elif indicator_name == 'MACD':
            col_name = f'MACD_12_26'  # 기본값
        else:
            # 일반적인 패턴: {INDICATOR}_{period}
            col_name = f'{indicator_name}_{period}'
        
        if col_name in bars.columns:
            return float(bars[col_name].iloc[-1])
        
        # 정확한 매칭 실패 시 부분 매칭 시도
        matching_cols = [col for col in bars.columns if indicator_name.upper() in col.upper()]
        if matching_cols:
            return float(bars[matching_cols[0]].iloc[-1])
        
        return None
    
    def _compare_values(self, left: float, operator: str, right: Any) -> bool:
        """값 비교"""
        try:
            right_value = float(right) if isinstance(right, (int, float, str)) else right
            
            if operator == '>':
                return left > right_value
            elif operator == '>=':
                return left >= right_value
            elif operator == '<':
                return left < right_value
            elif operator == '<=':
                return left <= right_value
            elif operator == '==' or operator == '=':
                return abs(left - right_value) < 0.0001  # 부동소수점 오차 고려
            else:
                logger.warning(f"Unsupported operator: {operator}")
                return False
        except (ValueError, TypeError) as e:
            logger.error(f"Error comparing values: {left} {operator} {right}, error: {e}")
            return False
    
    def _check_fvg_condition(self, bars: pd.DataFrame, operator: str, value: Any) -> bool:
        """FVG 조건 확인"""
        if operator != 'in_gap':
            return False
        
        # 최근 FVG 확인
        if 'fvg_type' in bars.columns:
            recent_fvg = bars['fvg_type'].iloc[-5:].dropna()
            if len(recent_fvg) > 0:
                last_fvg = recent_fvg.iloc[-1]
                if value == 'bullish':
                    return last_fvg == 'bullish'
                elif value == 'bearish':
                    return last_fvg == 'bearish'
        
        return False
    
    def _check_liquidity_condition(self, bars: pd.DataFrame, operator: str, value: Any) -> bool:
        """Liquidity Zone 조건 확인"""
        if operator != 'in_zone':
            return False
        
        current_price = bars['close'].iloc[-1]
        
        # 최근 Liquidity Zone 확인
        if 'liquidity_zone_type' in bars.columns:
            recent_zones = bars[['liquidity_zone_type', 'liquidity_zone_top', 'liquidity_zone_bottom']].iloc[-20:].dropna()
            for _, zone in recent_zones.iterrows():
                zone_type = zone['liquidity_zone_type']
                zone_top = zone['liquidity_zone_top']
                zone_bottom = zone['liquidity_zone_bottom']
                
                if zone_type == value and zone_bottom <= current_price <= zone_top:
                    return True
        
        return False
    
    def _check_order_block_condition(self, bars: pd.DataFrame, operator: str, value: Any) -> bool:
        """Order Block 조건 확인"""
        if operator != 'in_block':
            return False
        
        current_price = bars['close'].iloc[-1]
        
        # 최근 Order Block 확인
        if 'order_block_type' in bars.columns:
            recent_blocks = bars[['order_block_type', 'order_block_top', 'order_block_bottom']].iloc[-20:].dropna()
            for _, block in recent_blocks.iterrows():
                block_type = block['order_block_type']
                block_top = block['order_block_top']
                block_bottom = block['order_block_bottom']
                
                if block_type == value and block_bottom <= current_price <= block_top:
                    return True
        
        return False
    
    def _check_mss_bos_condition(self, bars: pd.DataFrame, operator: str, value: Any) -> bool:
        """MSS/BOS 조건 확인"""
        current_price = bars['close'].iloc[-1]
        
        if operator == 'break_high':
            # BOS 상승 돌파
            if 'bos_type' in bars.columns:
                recent_bos = bars['bos_type'].iloc[-5:].dropna()
                if len(recent_bos) > 0:
                    return recent_bos.iloc[-1] == 'bullish'
        
        elif operator == 'break_low':
            # BOS 하락 돌파
            if 'bos_type' in bars.columns:
                recent_bos = bars['bos_type'].iloc[-5:].dropna()
                if len(recent_bos) > 0:
                    return recent_bos.iloc[-1] == 'bearish'
        
        elif operator == 'structure_shift':
            # MSS 발생
            if 'mss_type' in bars.columns:
                recent_mss = bars['mss_type'].iloc[-5:].dropna()
                if len(recent_mss) > 0:
                    return recent_mss.iloc[-1] == value
        
        return False
    
    def _calculate_quantity(self, account: Account, price: float, bars: pd.DataFrame) -> int:
        """매수 수량 계산"""
        # 기본: 계좌 자산의 10% 사용
        position_size_ratio = self.strategy_params.get('position_size', 0.1)
        position_value = account.equity * position_size_ratio
        quantity = int(position_value / price)
        
        return max(1, quantity)  # 최소 1주
    
    def select_universe(
        self,
        date: datetime,
        repository = None
    ) -> List[str]:
        """
        종목 유니버스 선정 (포트폴리오 전략용)
        
        Args:
            date: 기준일
            repository: 데이터 저장소 (DataRepository 인스턴스)
            
        Returns:
            종목 코드 리스트
        """
        # stock_selection이 없으면 빈 리스트 반환
        if 'stock_selection' not in self.config_json:
            logger.warning("No stock_selection in config_json, returning empty universe")
            return []
        
        stock_selection = self.config_json.get('stock_selection', {})
        if not stock_selection:
            return []
        
        try:
            from data.models import StockMasterModel
            from data.repository import get_db_session
            
            db = get_db_session()
            
            try:
                # 종목 선정 조건
                query = db.query(StockMasterModel.symbol)
                
                # 기본: 활성 종목만
                query = query.filter(StockMasterModel.is_active == True)
                
                # 시가총액 필터 (DB는 백만원 단위, 입력은 억원 단위)
                if stock_selection.get('marketCap'):
                    market_cap = stock_selection['marketCap']
                    if market_cap.get('min'):
                        query = query.filter(StockMasterModel.market_cap >= market_cap['min'] * 100)
                    if market_cap.get('max'):
                        query = query.filter(StockMasterModel.market_cap <= market_cap['max'] * 100)
                
                # 거래량 필터
                if stock_selection.get('volume') and stock_selection['volume'].get('min'):
                    query = query.filter(StockMasterModel.volume_amount >= stock_selection['volume']['min'])
                
                # 거래대금 필터 (DB는 원 단위, 입력은 억원 단위)
                if stock_selection.get('volumeValue') and stock_selection['volumeValue'].get('min'):
                    query = query.filter(StockMasterModel.volume_amount >= stock_selection['volumeValue']['min'] * 100_000_000)
                
                # 가격 필터
                if stock_selection.get('price'):
                    price = stock_selection['price']
                    if price.get('min'):
                        query = query.filter(StockMasterModel.current_price >= price['min'])
                    if price.get('max'):
                        query = query.filter(StockMasterModel.current_price <= price['max'])
                
                # 시장 필터
                if stock_selection.get('market') and len(stock_selection['market']) > 0:
                    query = query.filter(StockMasterModel.market.in_(stock_selection['market']))
                
                # 업종 필터
                if stock_selection.get('sector') and len(stock_selection['sector']) > 0:
                    query = query.filter(StockMasterModel.sector.in_(stock_selection['sector']))
                
                # PER 필터
                if stock_selection.get('per'):
                    per = stock_selection['per']
                    if per.get('min'):
                        query = query.filter(
                            StockMasterModel.per.isnot(None),
                            StockMasterModel.per >= per['min']
                        )
                    if per.get('max'):
                        query = query.filter(
                            StockMasterModel.per.isnot(None),
                            StockMasterModel.per <= per['max']
                        )
                
                # PBR 필터
                if stock_selection.get('pbr'):
                    pbr = stock_selection['pbr']
                    if pbr.get('min'):
                        query = query.filter(
                            StockMasterModel.pbr.isnot(None),
                            StockMasterModel.pbr >= pbr['min']
                        )
                    if pbr.get('max'):
                        query = query.filter(
                            StockMasterModel.pbr.isnot(None),
                            StockMasterModel.pbr <= pbr['max']
                        )
                
                # ROE 필터
                if stock_selection.get('roe'):
                    roe = stock_selection['roe']
                    if roe.get('min'):
                        query = query.filter(
                            StockMasterModel.roe.isnot(None),
                            StockMasterModel.roe >= roe['min']
                        )
                    if roe.get('max'):
                        query = query.filter(
                            StockMasterModel.roe.isnot(None),
                            StockMasterModel.roe <= roe['max']
                        )
                
                # 부채비율 필터
                if stock_selection.get('debtRatio'):
                    debt_ratio = stock_selection['debtRatio']
                    if debt_ratio.get('max'):
                        query = query.filter(
                            StockMasterModel.debt_ratio.isnot(None),
                            StockMasterModel.debt_ratio <= debt_ratio['max']
                        )
                
                # 52주 위치 필터
                if stock_selection.get('pricePosition'):
                    price_pos = stock_selection['pricePosition']
                    if price_pos.get('from52WeekHigh'):
                        pos = price_pos['from52WeekHigh']
                        if pos.get('min'):
                            query = query.filter(
                                StockMasterModel.price_position.isnot(None),
                                StockMasterModel.price_position >= pos['min'] / 100
                            )
                        if pos.get('max'):
                            query = query.filter(
                                StockMasterModel.price_position.isnot(None),
                                StockMasterModel.price_position <= pos['max'] / 100
                            )
                
                # 제외 조건
                if stock_selection.get('excludeManaged'):
                    query = query.filter(StockMasterModel.is_active == True)
                
                if stock_selection.get('excludeClearing'):
                    # 정리매매 제외 (is_active로 대체)
                    query = query.filter(StockMasterModel.is_active == True)
                
                if stock_selection.get('excludePreferred'):
                    # 우선주 제외 (symbol에 'P'가 없거나, 별도 필드가 있으면 사용)
                    # 현재는 symbol 패턴으로 판단 (예: '005930P' 같은 우선주)
                    # 실제 구현은 DB 스키마에 따라 다를 수 있음
                    pass
                
                if stock_selection.get('excludeSpac'):
                    # SPAC 제외 (별도 필드가 있으면 사용)
                    pass
                
                # 최소 상장일수 필터
                if stock_selection.get('minListingDays'):
                    # 상장일 필드가 있으면 사용, 없으면 스킵
                    pass
                
                # 최대 종목 수 제한
                max_stocks = self.strategy_params.get('max_stocks', 20)
                if 'max_stocks' in self.params:
                    max_stocks = self.params.get('max_stocks', max_stocks)
                
                # PER 기준 정렬 (낮은 순, 값이 있는 것만)
                query = query.filter(StockMasterModel.per.isnot(None))
                query = query.order_by(StockMasterModel.per.asc())
                
                symbols = [row.symbol for row in query.limit(max_stocks).all()]
                
                logger.info(f"Selected {len(symbols)} stocks for universe on {date.date()}")
                logger.debug(f"  Filters: market={stock_selection.get('market')}, max_stocks={max_stocks}")
                
                return symbols
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to select universe: {e}", exc_info=True)
            return []
    
    def is_portfolio_strategy(self) -> bool:
        """
        포트폴리오 전략 여부 확인 (DynamicStrategy 오버라이드)
        
        Returns:
            True: 포트폴리오 전략 (여러 종목)
            False: 단일 종목 전략
        """
        # 우선순위 1: params에 명시적으로 is_portfolio가 있으면 사용
        if 'is_portfolio' in self.params:
            return bool(self.params.get('is_portfolio', False))
        
        # 우선순위 2: config_json의 parameters에서 확인
        if 'is_portfolio' in self.strategy_params:
            return bool(self.strategy_params.get('is_portfolio', False))
        
        # 우선순위 3: stock_selection이 있으면 포트폴리오 전략
        if 'stock_selection' in self.config_json:
            stock_selection = self.config_json.get('stock_selection', {})
            # stock_selection이 비어있지 않으면 포트폴리오 전략
            if stock_selection and isinstance(stock_selection, dict):
                # 최소한 하나의 필터 조건이 있으면 포트폴리오 전략
                has_filter = any(
                    stock_selection.get(key) is not None and stock_selection.get(key) != []
                    for key in ['market', 'sector', 'marketCap', 'volume', 'price', 'per', 'pbr', 'roe']
                )
                if has_filter:
                    return True
        
        # 우선순위 4: BaseStrategy의 기본 로직 (select_universe 오버라이드 확인)
        return super().is_portfolio_strategy()
    
    def on_fill(self, order: Order, position: Position) -> None:
        """주문 체결 시 호출"""
        logger.info(f"Order filled: {order.side.value} {order.quantity} {order.symbol} @ {order.price}")

