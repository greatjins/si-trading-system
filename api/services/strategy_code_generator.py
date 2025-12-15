"""
전략 코드 생성 서비스

전략 빌더 요청을 Python 코드로 변환하는 모듈화된 서비스
"""
import re
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from api.routes.strategy_builder import (
        StrategyBuilderRequest,
        Condition,
        StockSelection,
        PositionManagement,
        EntryStrategy
    )

from utils.logger import setup_logger

logger = setup_logger(__name__)


class StrategyCodeGenerator:
    """
    전략 코드 생성기
    
    전략 빌더 요청을 Python 코드로 변환하는 클래스
    """
    
    def __init__(self, request: "StrategyBuilderRequest"):
        """
        Args:
            request: 전략 빌더 요청
        """
        self.request = request
        self.class_name = self._generate_class_name(request.name)
        self.is_portfolio_strategy = self._check_portfolio_strategy(request.stockSelection)
        self.description = self._escape_description(request.description)
    
    def generate(self) -> str:
        """
        전략 코드 생성
        
        Returns:
            Python 코드 문자열
        """
        # 각 부분 생성
        imports = self._generate_imports()
        decorator = self._generate_decorator()
        class_docstring = self._generate_class_docstring()
        init_method = self._generate_init_method()
        select_universe_method = self._generate_select_universe_method() if self.is_portfolio_strategy else ""
        on_bar_method = self._generate_on_bar_method()
        on_fill_method = self._generate_on_fill_method()
        helper_methods = self._generate_helper_methods()
        
        # 전체 코드 조합
        code = f'''"""
{self.request.name}

{self.request.description}

자동 생성된 전략 - 전략 빌더
"""
{imports}

{decorator}
class {self.class_name}(BaseStrategy):
    """
    {self.request.name}
    
    {'포트폴리오 전략 (종목 자동 선정)' if self.is_portfolio_strategy else '단일 종목 전략'}
    매수 조건: {len(self.request.buyConditions)}개
    매도 조건: {len(self.request.sellConditions)}개
    """
    
{init_method}
{select_universe_method}
{on_bar_method}
{on_fill_method}
{helper_methods}'''
        
        return code
    
    def _generate_class_name(self, name: str) -> str:
        """클래스명 생성"""
        class_name = re.sub(r'[^a-zA-Z0-9_]', '', name.replace(" ", "_").replace("-", "_"))
        if not class_name:
            class_name = "CustomStrategy"
        if class_name[0].isdigit():
            class_name = "Strategy_" + class_name
        return class_name
    
    def _escape_description(self, description: str) -> str:
        """설명 문자열 이스케이프"""
        if not description:
            return ""
        return description.replace('"', '\\"').replace("'", "\\'")
    
    def _check_portfolio_strategy(self, stock_selection: "StockSelection") -> bool:
        """포트폴리오 전략 여부 확인"""
        from api.routes.strategy_builder import _has_stock_selection_criteria
        return _has_stock_selection_criteria(stock_selection)
    
    def _generate_imports(self) -> str:
        """import 문 생성"""
        return """from typing import List
from datetime import datetime
import pandas as pd
from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy
from utils.types import Position, Account, OrderSignal, OrderSide, OrderType, Order"""
    
    def _generate_decorator(self) -> str:
        """@strategy 데코레이터 생성"""
        stop_loss_dict = {}
        if self.request.positionManagement.stopLoss:
            stop_loss_dict = self.request.positionManagement.stopLoss.dict(exclude_none=True)
        
        take_profit_dict = {}
        if self.request.positionManagement.takeProfit:
            take_profit_dict = self.request.positionManagement.takeProfit.dict(exclude_none=True)
        
        trailing_stop_dict = {}
        if self.request.positionManagement.trailingStop:
            trailing_stop_dict = self.request.positionManagement.trailingStop.dict(exclude_none=True)
        
        stop_loss_str = repr(stop_loss_dict)
        take_profit_str = repr(take_profit_dict)
        trailing_stop_str = repr(trailing_stop_dict)
        
        return f'''@strategy(
    name="{self.class_name}",
    description="""{self.description}""",
    author="Strategy Builder",
    version="1.0.0",
    parameters={{
        "entry_type": {{
            "type": "str",
            "default": "{self.request.entryStrategy.type}",
            "description": "진입 방식 (single/pyramid)"
        }},
        "max_position_size": {{
            "type": "float",
            "default": {self.request.entryStrategy.maxPositionSize or 40},
            "description": "총 포지션 한도 %"
        }},
        "min_interval": {{
            "type": "int",
            "default": {self.request.entryStrategy.minInterval or 1},
            "description": "최소 진입 간격 (일)"
        }},
        "sizing_method": {{
            "type": "str",
            "default": "{self.request.positionManagement.sizingMethod}",
            "description": "포지션 사이징 방식"
        }},
        "position_size": {{
            "type": "float",
            "default": {self.request.positionManagement.positionSize or 0.1},
            "description": "포지션 크기 (고정 비율)"
        }},
        "account_risk": {{
            "type": "float",
            "default": {self.request.positionManagement.accountRisk or 1.0},
            "description": "계좌 리스크 % (ATR 기반)"
        }},
        "atr_period": {{
            "type": "int",
            "default": {self.request.positionManagement.atrPeriod or 20},
            "description": "ATR 기간"
        }},
        "atr_multiple": {{
            "type": "float",
            "default": {self.request.positionManagement.atrMultiple or 2.0},
            "description": "ATR 배수"
        }},
        "win_rate": {{
            "type": "float",
            "default": {self.request.positionManagement.winRate or 0.5},
            "description": "승률 (켈리 공식)"
        }},
        "win_loss_ratio": {{
            "type": "float",
            "default": {self.request.positionManagement.winLossRatio or 2.0},
            "description": "손익비 (켈리 공식)"
        }},
        "kelly_fraction": {{
            "type": "float",
            "default": {self.request.positionManagement.kellyFraction or 0.25},
            "description": "켈리 비율 조정"
        }},
        "volatility_period": {{
            "type": "int",
            "default": {self.request.positionManagement.volatilityPeriod or 20},
            "description": "변동성 계산 기간"
        }},
        "volatility_target": {{
            "type": "float",
            "default": {self.request.positionManagement.volatilityTarget or 2.0},
            "description": "목표 변동성 %"
        }},
        "max_positions": {{
            "type": "int",
            "default": {self.request.positionManagement.maxPositions},
            "description": "최대 보유 종목 수"
        }},
        "stop_loss": {{
            "type": "dict",
            "default": {stop_loss_str},
            "description": "손절 설정"
        }},
        "take_profit": {{
            "type": "dict",
            "default": {take_profit_str},
            "description": "익절 설정"
        }},
        "trailing_stop": {{
            "type": "dict",
            "default": {trailing_stop_str},
            "description": "트레일링 스탑 설정"
        }}
    }}
)'''
    
    def _generate_class_docstring(self) -> str:
        """클래스 docstring 생성"""
        return f'''    """
    {self.request.name}
    
    {'포트폴리오 전략 (종목 자동 선정)' if self.is_portfolio_strategy else '단일 종목 전략'}
    매수 조건: {len(self.request.buyConditions)}개
    매도 조건: {len(self.request.sellConditions)}개
    """'''
    
    def _generate_init_method(self) -> str:
        """__init__ 메서드 생성"""
        stop_loss_dict = {}
        if self.request.positionManagement.stopLoss:
            stop_loss_dict = self.request.positionManagement.stopLoss.dict(exclude_none=True)
        
        take_profit_dict = {}
        if self.request.positionManagement.takeProfit:
            take_profit_dict = self.request.positionManagement.takeProfit.dict(exclude_none=True)
        
        trailing_stop_dict = {}
        if self.request.positionManagement.trailingStop:
            trailing_stop_dict = self.request.positionManagement.trailingStop.dict(exclude_none=True)
        
        stop_loss_str = repr(stop_loss_dict)
        take_profit_str = repr(take_profit_dict)
        trailing_stop_str = repr(trailing_stop_dict)
        
        return f'''    def __init__(self, params: dict):
        super().__init__(params)
        # 진입 전략
        self.entry_type = self.get_param("entry_type", "{self.request.entryStrategy.type}")
        self.pyramid_levels = {[level.dict() for level in self.request.entryStrategy.pyramidLevels] if self.request.entryStrategy.pyramidLevels else []}
        self.max_position_size = self.get_param("max_position_size", {self.request.entryStrategy.maxPositionSize or 40})
        self.min_interval = self.get_param("min_interval", {self.request.entryStrategy.minInterval or 1})
        
        # 피라미딩 상태 추적
        self.entry_price = {{}}  # symbol: first_entry_price
        self.current_level = {{}}  # symbol: current_pyramid_level
        self.last_entry_date = {{}}  # symbol: last_entry_date
        self.total_units = {{}}  # symbol: total_units_invested
        
        # 포지션 사이징
        self.sizing_method = self.get_param("sizing_method", "{self.request.positionManagement.sizingMethod}")
        self.position_size = self.get_param("position_size", {self.request.positionManagement.positionSize or 0.1})
        self.account_risk = self.get_param("account_risk", {self.request.positionManagement.accountRisk or 1.0})
        self.atr_period = self.get_param("atr_period", {self.request.positionManagement.atrPeriod or 20})
        self.atr_multiple = self.get_param("atr_multiple", {self.request.positionManagement.atrMultiple or 2.0})
        self.win_rate = self.get_param("win_rate", {self.request.positionManagement.winRate or 0.5})
        self.win_loss_ratio = self.get_param("win_loss_ratio", {self.request.positionManagement.winLossRatio or 2.0})
        self.kelly_fraction = self.get_param("kelly_fraction", {self.request.positionManagement.kellyFraction or 0.25})
        self.volatility_period = self.get_param("volatility_period", {self.request.positionManagement.volatilityPeriod or 20})
        self.volatility_target = self.get_param("volatility_target", {self.request.positionManagement.volatilityTarget or 2.0})
        self.max_positions = self.get_param("max_positions", {self.request.positionManagement.maxPositions})
        
        # 손절/익절 설정
        stop_loss_config = self.get_param("stop_loss", {stop_loss_str})
        self.stop_loss_enabled = stop_loss_config.get("enabled", False) if isinstance(stop_loss_config, dict) else False
        self.stop_loss_method = stop_loss_config.get("method", "fixed") if isinstance(stop_loss_config, dict) else "fixed"
        self.stop_loss_percent = stop_loss_config.get("fixedPercent", 5.0) if isinstance(stop_loss_config, dict) else 5.0
        
        take_profit_config = self.get_param("take_profit", {take_profit_str})
        self.take_profit_enabled = take_profit_config.get("enabled", False) if isinstance(take_profit_config, dict) else False
        self.take_profit_method = take_profit_config.get("method", "fixed") if isinstance(take_profit_config, dict) else "fixed"
        self.take_profit_percent = take_profit_config.get("fixedPercent", 10.0) if isinstance(take_profit_config, dict) else 10.0
        
        # 트레일링 스탑
        trailing_config = self.get_param("trailing_stop", {trailing_stop_str})
        self.trailing_stop_enabled = trailing_config.get("enabled", False) if isinstance(trailing_config, dict) else False
        self.trailing_method = trailing_config.get("method", "atr") if isinstance(trailing_config, dict) else "atr"
        self.trailing_atr_multiple = trailing_config.get("atrMultiple", 3.0) if isinstance(trailing_config, dict) else 3.0
        self.trailing_percentage = trailing_config.get("percentage", 5.0) if isinstance(trailing_config, dict) else 5.0
        self.trailing_activation = trailing_config.get("activationProfit", 5.0) if isinstance(trailing_config, dict) else 5.0
        self.trailing_update_freq = trailing_config.get("updateFrequency", "every_bar") if isinstance(trailing_config, dict) else "every_bar"
        
        # 트레일링 스탑 상태 추적
        self.highest_price = {{}}  # symbol: highest_price
        self.trailing_stop_price = {{}}  # symbol: stop_price'''
    
    def _generate_select_universe_method(self) -> str:
        """select_universe 메서드 생성"""
        # 순환 import 방지를 위해 함수 내부에서 import
        from api.routes.strategy_builder import _generate_select_universe_method
        return "\n" + _generate_select_universe_method(self.request.stockSelection)
    
    def _generate_on_bar_method(self) -> str:
        """on_bar 메서드 생성"""
        # 조건 코드 생성
        buy_conditions_code = []
        for i, cond in enumerate(self.request.buyConditions):
            condition_code = self._generate_condition_code(cond, i, "buy")
            if condition_code:
                buy_conditions_code.append(condition_code)
        
        sell_conditions_code = []
        for i, cond in enumerate(self.request.sellConditions):
            condition_code = self._generate_condition_code(cond, i, "sell")
            if condition_code:
                sell_conditions_code.append(condition_code)
        
        # 들여쓰기 추가: 조건 코드는 8칸 들여쓰기로 시작하지만, 삽입 위치는 16칸이 필요
        # 각 줄에 8칸 추가 들여쓰기 적용
        def add_indent(code: str, extra_spaces: int = 8) -> str:
            """코드 블록에 들여쓰기 추가"""
            if not code or not code.strip():
                return ""
            lines = code.split("\n")
            indented_lines = []
            for line in lines:
                if line.strip():  # 빈 줄이 아닌 경우
                    indented_lines.append(" " * extra_spaces + line)
                # 빈 줄은 제거 (여러 조건 사이에 불필요한 빈 줄 방지)
            return "\n".join(indented_lines)
        
        if buy_conditions_code:
            # 매수 조건은 16칸 들여쓰기 위치에 삽입 (기본 8칸 + 추가 8칸)
            indented_codes = []
            for code in buy_conditions_code:
                indented = add_indent(code, 8)
                if indented:
                    indented_codes.append(indented)
            buy_conditions_str = "\n".join(indented_codes) if indented_codes else "                pass"
        else:
            # 조건이 없을 때는 pass로 안전하게 처리
            buy_conditions_str = "                pass"
        
        if sell_conditions_code:
            # 매도 조건은 12칸 들여쓰기 위치에 삽입 (기본 8칸 + 추가 4칸)
            indented_codes = []
            for code in sell_conditions_code:
                indented = add_indent(code, 4)
                if indented:
                    indented_codes.append(indented)
            sell_conditions_str = "\n".join(indented_codes) if indented_codes else "            pass"
        else:
            # 조건이 없을 때는 pass로 안전하게 처리
            sell_conditions_str = "            pass"
        
        return f'''    def on_bar(self, bars: pd.DataFrame, positions: List[Position], account: Account) -> List[OrderSignal]:
        """
        새로운 바마다 호출
        
        Args:
            bars: OHLCV DataFrame (timestamp 인덱스, ['open', 'high', 'low', 'close', 'volume', 'value'] 컬럼)
            positions: 현재 포지션 리스트
            account: 계좌 정보
        
        Returns:
            주문 신호 리스트
        """
        signals: List[OrderSignal] = []
        
        if len(bars) < 50:  # 최소 데이터 필요
            return signals
        
        # DataFrame에서 데이터 추출
        closes = bars['close'].values
        current_price = bars['close'].iloc[-1]
        
        # 종목 코드는 파라미터에서 가져오거나 기본값 사용
        symbol = self.get_param("symbol", "005930")
        position = self.get_position(symbol, positions)
        
        # 매수 조건 체크
        if self.entry_type == "single":
            # 일괄 진입
            if not position and len(positions) < self.max_positions:
                # 매수 조건 확인
{buy_conditions_str}
                
                # 모든 매수 조건 만족 시 매수
                quantity = self._calculate_quantity(account.equity, current_price, bars)
                if quantity > 0:
                    signals.append(OrderSignal(
                        symbol=symbol,
                        side=OrderSide.BUY,
                        quantity=quantity,
                        order_type=OrderType.MARKET
                    ))
        
        elif self.entry_type == "pyramid":
            # 피라미딩 진입
            # 날짜를 바 인덱스로 사용 (간단하고 안정적)
            current_bar_index = len(bars) - 1
            
            # 1차 진입 (초기 진입)
            if symbol not in self.entry_price:
                # 매수 조건 확인
{buy_conditions_str}
                
                # 매수 조건 만족 시 1차 진입
                if len(positions) < self.max_positions:
                    base_quantity = self._calculate_quantity(account.equity, current_price, bars)
                    first_level = self.pyramid_levels[0] if self.pyramid_levels else {{"units": 1.0}}
                    quantity = int(base_quantity * first_level.get("units", 1.0))
                    
                    if quantity > 0:
                        self.entry_price[symbol] = current_price
                        self.current_level[symbol] = 1
                        self.last_entry_date[symbol] = current_bar_index
                        self.total_units[symbol] = first_level.get("units", 1.0)
                        
                        signals.append(OrderSignal(
                            symbol=symbol,
                            side=OrderSide.BUY,
                            quantity=quantity,
                            order_type=OrderType.MARKET
                        ))
            
            # 추가 진입 (2차 이상)
            elif position and symbol in self.entry_price:
                current_level_num = self.current_level.get(symbol, 1)
                
                # 최대 레벨 체크
                if current_level_num < len(self.pyramid_levels):
                    # 최소 간격 체크 (바 인덱스 기준)
                    last_bar_index = self.last_entry_date.get(symbol, 0)
                    if current_bar_index - last_bar_index >= self.min_interval:
                        # 가격 변화율 계산
                        price_change_pct = ((current_price - self.entry_price[symbol]) / self.entry_price[symbol]) * 100
                        
                        # 다음 레벨 조건 확인
                        next_level = self.pyramid_levels[current_level_num]
                        required_change = next_level.get("priceChange", 0)
                        
                        if price_change_pct >= required_change:
                            # 총 포지션 한도 체크
                            total_units = self.total_units.get(symbol, 0)
                            next_units = next_level.get("units", 1.0)
                            
                            if (total_units + next_units) * self.position_size * 100 <= self.max_position_size:
                                base_quantity = self._calculate_quantity(account.equity, current_price, bars)
                                quantity = int(base_quantity * next_units)
                                
                                if quantity > 0:
                                    self.current_level[symbol] = current_level_num + 1
                                    self.last_entry_date[symbol] = current_bar_index
                                    self.total_units[symbol] = total_units + next_units
                                    
                                    signals.append(OrderSignal(
                                        symbol=symbol,
                                        side=OrderSide.BUY,
                                        quantity=quantity,
                                        order_type=OrderType.MARKET
                                    ))
        
        # 매도 조건 체크
        if position and position.quantity > 0:
            should_sell = False
            
            # 트레일링 스탑 체크
            if self.trailing_stop_enabled:
                # 수익률 계산
                pnl_pct = ((current_price - position.avg_price) / position.avg_price) * 100
                
                # 활성화 조건 확인
                if pnl_pct >= self.trailing_activation:
                    # 최고가 업데이트
                    if symbol not in self.highest_price:
                        self.highest_price[symbol] = current_price
                    
                    if self.trailing_update_freq == "every_bar":
                        self.highest_price[symbol] = max(self.highest_price[symbol], current_price)
                    elif self.trailing_update_freq == "new_high" and current_price > self.highest_price[symbol]:
                        self.highest_price[symbol] = current_price
                    
                    # 트레일링 스탑 가격 계산
                    if self.trailing_method == "atr":
                        # ATR 계산
                        if len(bars) >= self.atr_period + 1:
                            highs = bars['high'].values
                            lows = bars['low'].values
                            closes_arr = bars['close'].values
                            
                            true_ranges = []
                            for i in range(1, len(closes_arr)):
                                tr = max(
                                    highs[i] - lows[i],
                                    abs(highs[i] - closes_arr[i-1]),
                                    abs(lows[i] - closes_arr[i-1])
                                )
                                true_ranges.append(tr)
                            
                            atr = sum(true_ranges[-self.atr_period:]) / self.atr_period
                            self.trailing_stop_price[symbol] = self.highest_price[symbol] - (atr * self.trailing_atr_multiple)
                        else:
                            # ATR 계산 불가 시 고정 % 사용
                            self.trailing_stop_price[symbol] = self.highest_price[symbol] * (1 - self.trailing_percentage / 100)
                    
                    elif self.trailing_method == "percentage":
                        self.trailing_stop_price[symbol] = self.highest_price[symbol] * (1 - self.trailing_percentage / 100)
                    
                    elif self.trailing_method == "parabolic_sar":
                        # 간단한 Parabolic SAR 근사
                        # 실제로는 더 복잡한 계산 필요
                        acceleration = 0.02
                        sar = position.avg_price + (self.highest_price[symbol] - position.avg_price) * acceleration
                        self.trailing_stop_price[symbol] = sar
                    
                    # 트레일링 스탑 터치 확인
                    if symbol in self.trailing_stop_price and current_price <= self.trailing_stop_price[symbol]:
                        should_sell = True
            
            # 기본 손절/익절 체크
            if not should_sell and self.stop_loss_enabled:
                pnl_pct = (current_price - position.avg_price) / position.avg_price
                if pnl_pct <= -(self.stop_loss_percent / 100):
                    should_sell = True
            
            if not should_sell and self.take_profit_enabled:
                pnl_pct = (current_price - position.avg_price) / position.avg_price
                if pnl_pct >= (self.take_profit_percent / 100):
                    should_sell = True
            
            # 추가 매도 조건
{sell_conditions_str}
            
            if should_sell:
                # 매도 시 상태 초기화
                if symbol in self.highest_price:
                    del self.highest_price[symbol]
                if symbol in self.trailing_stop_price:
                    del self.trailing_stop_price[symbol]
                if symbol in self.entry_price:
                    del self.entry_price[symbol]
                if symbol in self.current_level:
                    del self.current_level[symbol]
                if symbol in self.last_entry_date:
                    del self.last_entry_date[symbol]
                if symbol in self.total_units:
                    del self.total_units[symbol]
                
                signals.append(OrderSignal(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                ))
        
        return signals'''
    
    def _generate_on_fill_method(self) -> str:
        """on_fill 메서드 생성"""
        return '''    def on_fill(self, order: Order, position: Position) -> None:
        """주문 체결 시 호출"""
        pass'''
    
    def _generate_helper_methods(self) -> str:
        """헬퍼 메서드 생성 (_calculate_quantity, _calculate_ema, _calculate_rsi)"""
        return '''    def _calculate_quantity(self, equity: float, price: float, bars: pd.DataFrame = None) -> int:
        """
        매수 수량 계산 - 포지션 사이징 방식에 따라 동적 계산
        
        Args:
            equity: 계좌 자산
            price: 현재 가격
            bars: OHLCV DataFrame (ATR/변동성 계산용)
        
        Returns:
            매수 수량
        """
        if self.sizing_method == "fixed":
            # 고정 비율
            position_value = equity * self.position_size
            quantity = int(position_value / price)
            
        elif self.sizing_method == "atr_risk":
            # ATR 기반 리스크 관리
            if bars is not None and len(bars) >= self.atr_period + 1:
                highs = bars['high'].values
                lows = bars['low'].values
                closes_arr = bars['close'].values
                
                # ATR 계산 (간단 버전)
                true_ranges = []
                for i in range(1, len(closes_arr)):
                    tr = max(
                        highs[i] - lows[i],
                        abs(highs[i] - closes_arr[i-1]),
                        abs(lows[i] - closes_arr[i-1])
                    )
                    true_ranges.append(tr)
                
                atr = sum(true_ranges[-self.atr_period:]) / self.atr_period
                
                # 포지션 크기 = (계좌 × 리스크%) / (ATR × 배수)
                risk_amount = equity * (self.account_risk / 100)
                stop_distance = atr * self.atr_multiple
                
                if stop_distance > 0:
                    quantity = int(risk_amount / stop_distance)
                else:
                    quantity = 0
            else:
                # ATR 계산 불가 시 고정 비율 사용
                position_value = equity * 0.1
                quantity = int(position_value / price)
                
        elif self.sizing_method == "kelly":
            # 켈리 공식
            # Kelly % = (승률 × 손익비 - (1 - 승률)) / 손익비
            kelly_pct = (self.win_rate * self.win_loss_ratio - (1 - self.win_rate)) / self.win_loss_ratio
            kelly_pct = max(0, kelly_pct)  # 음수 방지
            
            # 켈리 비율 조정 (보통 1/4 켈리 사용)
            adjusted_kelly = kelly_pct * self.kelly_fraction
            
            position_value = equity * adjusted_kelly
            quantity = int(position_value / price)
            
        elif self.sizing_method == "volatility":
            # 변동성 기반
            if bars is not None and len(bars) >= self.volatility_period:
                closes_arr = bars['close'].iloc[-self.volatility_period:].values
                returns = [(closes_arr[i] - closes_arr[i-1]) / closes_arr[i-1] for i in range(1, len(closes_arr))]
                volatility = (sum([r**2 for r in returns]) / len(returns)) ** 0.5
                
                if volatility > 0:
                    # 목표 변동성 / 실제 변동성 비율로 포지션 조정
                    target_vol = self.volatility_target / 100
                    position_ratio = min(target_vol / volatility, 1.0)  # 최대 100%
                    position_value = equity * position_ratio
                    quantity = int(position_value / price)
                else:
                    position_value = equity * 0.1
                    quantity = int(position_value / price)
            else:
                position_value = equity * 0.1
                quantity = int(position_value / price)
        else:
            # 기본값
            position_value = equity * 0.1
            quantity = int(position_value / price)
        
        return max(1, quantity)  # 최소 1주
    
    def _calculate_ema(self, prices: list, period: int) -> float:
        """지수이동평균 계산"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # 초기 SMA
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_rsi(self, prices: list, period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50.0  # 기본값
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi'''
    
    def _generate_condition_code(self, condition: "Condition", index: int, condition_type: str) -> str:
        """조건 코드 생성 (기존 함수 재사용)"""
        from api.routes.strategy_builder import _generate_condition_code
        return _generate_condition_code(condition, index, condition_type)


def generate_strategy_code(request) -> str:
    """
    전략 코드 생성 (기존 함수 호환성 유지)
    
    Args:
        request: 전략 빌더 요청 (StrategyBuilderRequest)
        
    Returns:
        Python 코드 문자열
    """
    # 순환 import 방지를 위해 함수 내부에서 import
    from api.routes.strategy_builder import StrategyBuilderRequest
    generator = StrategyCodeGenerator(request)
    return generator.generate()
