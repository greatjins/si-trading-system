"""
전략 빌더 API - 노코드 전략 생성 및 관리
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth.security import get_current_active_user
from api.dependencies import get_db
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# 스키마
class Condition(BaseModel):
    """조건"""
    id: str
    type: str  # indicator, price, volume
    indicator: str = None
    operator: str
    value: Any
    period: int = None


class StockSelection(BaseModel):
    """종목 선정"""
    # 기본 필터
    marketCap: Dict[str, float] = None  # 시가총액 (억원)
    volume: Dict[str, int] = None  # 최소 거래량 (주)
    volumeValue: Dict[str, float] = None  # 최소 거래대금 (백만원)
    price: Dict[str, float] = None  # 가격 범위 (원)
    
    # 시장/업종
    sector: List[str] = None  # 업종
    market: List[str] = None  # 시장 (KOSPI/KOSDAQ/KONEX)
    
    # 재무 지표
    per: Dict[str, float] = None  # PER
    pbr: Dict[str, float] = None  # PBR
    roe: Dict[str, float] = None  # ROE (%)
    debtRatio: Dict[str, float] = None  # 부채비율 (%)
    
    # 기술적 지표
    pricePosition: Dict[str, Any] = None  # 52주 최고가/최저가 대비 위치
    
    # 제외 조건
    excludeManaged: bool = None  # 관리종목 제외
    excludeClearing: bool = None  # 정리매매 제외
    excludePreferred: bool = None  # 우선주 제외
    excludeSpac: bool = None  # SPAC 제외
    minListingDays: int = None  # 최소 상장일수


class TrailingStop(BaseModel):
    """트레일링 스탑 설정"""
    enabled: bool = False
    method: str = "atr"  # atr, percentage, parabolic_sar
    atrMultiple: float = None
    percentage: float = None
    activationProfit: float = None
    updateFrequency: str = "every_bar"  # every_bar, new_high


class StopLoss(BaseModel):
    """손절 설정"""
    enabled: bool = False
    method: str = "fixed"  # fixed, atr, support, time
    fixedPercent: float = None
    atrMultiple: float = None
    minPercent: float = None
    maxPercent: float = None
    timeDays: int = None


class TakeProfit(BaseModel):
    """익절 설정"""
    enabled: bool = False
    method: str = "fixed"  # fixed, r_multiple, partial
    fixedPercent: float = None
    rMultiple: float = None
    partialLevels: list = None


class PositionManagement(BaseModel):
    """포지션 관리"""
    sizingMethod: str = "fixed"  # fixed, atr_risk, kelly, volatility
    
    # 고정 비율
    positionSize: float = None
    
    # ATR 기반
    accountRisk: float = None
    atrPeriod: int = None
    atrMultiple: float = None
    
    # 켈리 공식
    winRate: float = None
    winLossRatio: float = None
    kellyFraction: float = None
    
    # 변동성 기반
    volatilityPeriod: int = None
    volatilityTarget: float = None
    
    maxPositions: int
    
    # 손절/익절
    stopLoss: StopLoss = None
    takeProfit: TakeProfit = None
    
    # 트레일링 스탑
    trailingStop: TrailingStop = None


class PyramidLevel(BaseModel):
    """피라미딩 레벨"""
    level: int
    condition: str  # initial, price_increase, indicator
    priceChange: float = None  # %
    units: float  # 유닛 수
    description: str = None


class EntryStrategy(BaseModel):
    """진입 전략"""
    type: str = "single"  # single, pyramid
    pyramidLevels: List[PyramidLevel] = None
    maxLevels: int = None
    maxPositionSize: float = None  # %
    minInterval: int = None  # 일


class StrategyBuilderRequest(BaseModel):
    """전략 빌더 요청"""
    name: str
    description: str
    stockSelection: StockSelection
    buyConditions: List[Condition]
    sellConditions: List[Condition]
    entryStrategy: EntryStrategy
    positionManagement: PositionManagement


class StrategyBuilderResponse(BaseModel):
    """전략 빌더 응답"""
    strategy_id: int
    name: str
    description: str
    created_at: datetime
    python_code: str = None


@router.post("/save", response_model=StrategyBuilderResponse)
async def save_strategy(
    request: StrategyBuilderRequest,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    전략 저장
    
    Args:
        request: 전략 빌더 요청
        current_user: 현재 사용자
        db: DB 세션
        
    Returns:
        저장된 전략 정보
    """
    try:
        from data.models import StrategyBuilderModel
        from sqlalchemy.orm import Session
        
        # Python 코드 생성
        python_code = generate_strategy_code(request)
        
        # DB에 저장
        strategy = StrategyBuilderModel(
            user_id=current_user["user_id"],
            name=request.name,
            description=request.description,
            config=request.dict(),
            python_code=python_code,
            is_active=True
        )
        
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        
        logger.info(f"Strategy saved: ID={strategy.id}, Name={request.name}, User={current_user['username']}")
        
        return StrategyBuilderResponse(
            strategy_id=strategy.id,
            name=request.name,
            description=request.description,
            created_at=strategy.created_at,
            python_code=python_code,
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save strategy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators")
async def get_available_indicators():
    """
    사용 가능한 기술적 지표 목록 조회
    
    Returns:
        지표 목록 및 설정 정보
    """
    indicators = [
        {
            "id": "ma",
            "name": "이동평균 (MA)",
            "category": "trend",
            "parameters": [
                {"name": "period", "type": "number", "default": 20, "min": 1, "max": 200}
            ],
            "operators": [">", "<", ">=", "<="],
            "description": "단순 이동평균선"
        },
        {
            "id": "ema",
            "name": "지수이동평균 (EMA)",
            "category": "trend",
            "parameters": [
                {"name": "period", "type": "number", "default": 20, "min": 1, "max": 200}
            ],
            "operators": [">", "<", ">=", "<="],
            "description": "지수 이동평균선"
        },
        {
            "id": "rsi",
            "name": "RSI",
            "category": "momentum",
            "parameters": [
                {"name": "period", "type": "number", "default": 14, "min": 2, "max": 50}
            ],
            "operators": [">", "<", ">=", "<="],
            "description": "상대강도지수 (0-100)"
        },
        {
            "id": "macd",
            "name": "MACD",
            "category": "momentum",
            "parameters": [
                {"name": "fast", "type": "number", "default": 12, "min": 2, "max": 50},
                {"name": "slow", "type": "number", "default": 26, "min": 2, "max": 100},
                {"name": "signal", "type": "number", "default": 9, "min": 2, "max": 50}
            ],
            "operators": [">", "<", "cross_above", "cross_below"],
            "description": "MACD 라인과 시그널 라인"
        },
        {
            "id": "bollinger",
            "name": "볼린저 밴드",
            "category": "volatility",
            "parameters": [
                {"name": "period", "type": "number", "default": 20, "min": 2, "max": 100},
                {"name": "std_dev", "type": "number", "default": 2.0, "min": 0.5, "max": 4.0, "step": 0.1}
            ],
            "operators": [">", "<", "cross_above", "cross_below"],
            "description": "볼린저 밴드 (상단/중단/하단)"
        },
        {
            "id": "atr",
            "name": "ATR",
            "category": "volatility",
            "parameters": [
                {"name": "period", "type": "number", "default": 14, "min": 2, "max": 50}
            ],
            "operators": [">", "<", ">=", "<="],
            "description": "평균 진폭 (Average True Range)"
        },
        {
            "id": "stochastic",
            "name": "스토캐스틱",
            "category": "momentum",
            "parameters": [
                {"name": "period", "type": "number", "default": 14, "min": 2, "max": 50}
            ],
            "operators": [">", "<", ">=", "<="],
            "description": "스토캐스틱 오실레이터 (0-100)"
        },
        {
            "id": "adx",
            "name": "ADX",
            "category": "trend",
            "parameters": [
                {"name": "period", "type": "number", "default": 14, "min": 2, "max": 50}
            ],
            "operators": [">", "<", ">=", "<="],
            "description": "추세 강도 지표 (0-100)"
        },
        {
            "id": "cci",
            "name": "CCI",
            "category": "momentum",
            "parameters": [
                {"name": "period", "type": "number", "default": 20, "min": 2, "max": 50}
            ],
            "operators": [">", "<", ">=", "<="],
            "description": "상품채널지수"
        },
        {
            "id": "williams_r",
            "name": "Williams %R",
            "category": "momentum",
            "parameters": [
                {"name": "period", "type": "number", "default": 14, "min": 2, "max": 50}
            ],
            "operators": [">", "<", ">=", "<="],
            "description": "윌리엄스 %R (-100 ~ 0)"
        },
        {
            "id": "mfi",
            "name": "MFI",
            "category": "volume",
            "parameters": [
                {"name": "period", "type": "number", "default": 14, "min": 2, "max": 50}
            ],
            "operators": [">", "<", ">=", "<="],
            "description": "자금흐름지수 (0-100)"
        },
        {
            "id": "obv",
            "name": "OBV",
            "category": "volume",
            "parameters": [],
            "operators": [">", "<", "cross_above", "cross_below"],
            "description": "거래량 누적 지표"
        },
        {
            "id": "volume_ma",
            "name": "거래량 이동평균",
            "category": "volume",
            "parameters": [
                {"name": "period", "type": "number", "default": 20, "min": 1, "max": 200}
            ],
            "operators": [">", "<", ">=", "<="],
            "description": "거래량 이동평균"
        },
        {
            "id": "vwap",
            "name": "VWAP",
            "category": "volume",
            "parameters": [],
            "operators": [">", "<", "cross_above", "cross_below"],
            "description": "거래량 가중 평균 가격"
        },
        {
            "id": "ichimoku",
            "name": "일목균형표",
            "category": "trend",
            "parameters": [],
            "operators": ["cloud_above", "cloud_below", "cross_above", "cross_below"],
            "description": "일목균형표 (전환선/기준선/구름)"
        }
    ]
    
    return {
        "indicators": indicators,
        "categories": [
            {"id": "trend", "name": "추세", "description": "추세 방향과 강도를 측정"},
            {"id": "momentum", "name": "모멘텀", "description": "가격 변화의 속도와 강도를 측정"},
            {"id": "volatility", "name": "변동성", "description": "가격 변동의 크기를 측정"},
            {"id": "volume", "name": "거래량", "description": "거래량 기반 지표"}
        ]
    }


@router.get("/list")
async def list_strategies(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 전략 목록 조회
    
    Args:
        current_user: 현재 사용자
        db: DB 세션
        
    Returns:
        전략 목록
    """
    try:
        from data.models import StrategyBuilderModel
        
        strategies = db.query(StrategyBuilderModel).filter(
            StrategyBuilderModel.user_id == current_user["user_id"],
            StrategyBuilderModel.is_active == True
        ).order_by(StrategyBuilderModel.created_at.desc()).all()
        
        return [
            {
                "strategy_id": s.id,
                "name": s.name,
                "description": s.description,
                "created_at": s.created_at,
            }
            for s in strategies
        ]
    
    except Exception as e:
        logger.error(f"Failed to list strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}")
async def get_strategy(
    strategy_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    전략 상세 조회
    
    Args:
        strategy_id: 전략 ID
        current_user: 현재 사용자
        db: DB 세션
        
    Returns:
        전략 상세 정보
    """
    try:
        from data.models import StrategyBuilderModel
        
        strategy = db.query(StrategyBuilderModel).filter(
            StrategyBuilderModel.id == strategy_id,
            StrategyBuilderModel.user_id == current_user["user_id"]
        ).first()
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "id": strategy.id,
            "name": strategy.name,
            "description": strategy.description,
            "user_id": strategy.user_id,
            "config": strategy.config,
            "python_code": strategy.python_code,
            "created_at": strategy.created_at,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    전략 삭제
    
    Args:
        strategy_id: 전략 ID
        current_user: 현재 사용자
        db: DB 세션
        
    Returns:
        삭제 결과
    """
    try:
        from data.models import StrategyBuilderModel
        
        strategy = db.query(StrategyBuilderModel).filter(
            StrategyBuilderModel.id == strategy_id,
            StrategyBuilderModel.user_id == current_user["user_id"]
        ).first()
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        db.delete(strategy)
        db.commit()
        
        logger.info(f"Strategy deleted: ID={strategy_id}, User={current_user['username']}")
        
        return {"success": True, "message": "Strategy deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_strategy_code(request: StrategyBuilderRequest) -> str:
    """
    전략 설정을 Python 코드로 변환
    
    Args:
        request: 전략 빌더 요청
        
    Returns:
        Python 코드
    """
    import re
    
    # 클래스명: 영문자, 숫자, 언더스코어만 허용
    class_name = re.sub(r'[^a-zA-Z0-9_]', '', request.name.replace(" ", "_").replace("-", "_"))
    if not class_name:
        class_name = "CustomStrategy"
    # 숫자로 시작하면 안됨
    if class_name[0].isdigit():
        class_name = "Strategy_" + class_name
    
    # 설명에서 따옴표 이스케이프
    description = request.description.replace('"', '\\"').replace("'", "\\'") if request.description else ""
    
    # stop_loss와 take_profit을 딕셔너리로 변환
    stop_loss_dict = {}
    if request.positionManagement.stopLoss:
        stop_loss_dict = request.positionManagement.stopLoss.dict(exclude_none=True)
    
    take_profit_dict = {}
    if request.positionManagement.takeProfit:
        take_profit_dict = request.positionManagement.takeProfit.dict(exclude_none=True)
    
    trailing_stop_dict = {}
    if request.positionManagement.trailingStop:
        trailing_stop_dict = request.positionManagement.trailingStop.dict(exclude_none=True)
    
    # Python 코드용 딕셔너리 문자열 생성 (repr 사용)
    stop_loss_str = repr(stop_loss_dict)
    take_profit_str = repr(take_profit_dict)
    trailing_stop_str = repr(trailing_stop_dict)
    
    # 매수 조건 코드 생성
    buy_conditions_code = []
    for i, cond in enumerate(request.buyConditions):
        if cond.indicator == "MA":
            buy_conditions_code.append(
                f"        # 조건 {i+1}: MA({cond.period}) {cond.operator} {cond.value}\n"
                f"        ma_{i} = sum(closes[-{cond.period}:]) / {cond.period}\n"
                f"        if not (ma_{i} {cond.operator} {cond.value}):\n"
                f"            return signals"
            )
    
    # 매도 조건 코드 생성
    sell_conditions_code = []
    for i, cond in enumerate(request.sellConditions):
        if cond.indicator == "MA":
            sell_conditions_code.append(
                f"        # 조건 {i+1}: MA({cond.period}) {cond.operator} {cond.value}\n"
                f"        ma_{i} = sum(closes[-{cond.period}:]) / {cond.period}\n"
                f"        if ma_{i} {cond.operator} {cond.value}:\n"
                f"            should_sell = True"
            )
    
    code = f'''"""
{request.name}

{description}

자동 생성된 전략 - 전략 빌더
"""
from typing import List
from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy
from utils.types import OHLC, Position, Account, OrderSignal, OrderSide, OrderType, Order

@strategy(
    name="{class_name}",
    description="""{description}""",
    author="Strategy Builder",
    version="1.0.0",
    parameters={{
        "entry_type": {{
            "type": "str",
            "default": "{request.entryStrategy.type}",
            "description": "진입 방식 (single/pyramid)"
        }},
        "max_position_size": {{
            "type": "float",
            "default": {request.entryStrategy.maxPositionSize or 40},
            "description": "총 포지션 한도 %"
        }},
        "min_interval": {{
            "type": "int",
            "default": {request.entryStrategy.minInterval or 1},
            "description": "최소 진입 간격 (일)"
        }},
        "sizing_method": {{
            "type": "str",
            "default": "{request.positionManagement.sizingMethod}",
            "description": "포지션 사이징 방식"
        }},
        "position_size": {{
            "type": "float",
            "default": {request.positionManagement.positionSize or 0.1},
            "description": "포지션 크기 (고정 비율)"
        }},
        "account_risk": {{
            "type": "float",
            "default": {request.positionManagement.accountRisk or 1.0},
            "description": "계좌 리스크 % (ATR 기반)"
        }},
        "atr_period": {{
            "type": "int",
            "default": {request.positionManagement.atrPeriod or 20},
            "description": "ATR 기간"
        }},
        "atr_multiple": {{
            "type": "float",
            "default": {request.positionManagement.atrMultiple or 2.0},
            "description": "ATR 배수"
        }},
        "win_rate": {{
            "type": "float",
            "default": {request.positionManagement.winRate or 0.5},
            "description": "승률 (켈리 공식)"
        }},
        "win_loss_ratio": {{
            "type": "float",
            "default": {request.positionManagement.winLossRatio or 2.0},
            "description": "손익비 (켈리 공식)"
        }},
        "kelly_fraction": {{
            "type": "float",
            "default": {request.positionManagement.kellyFraction or 0.25},
            "description": "켈리 비율 조정"
        }},
        "volatility_period": {{
            "type": "int",
            "default": {request.positionManagement.volatilityPeriod or 20},
            "description": "변동성 계산 기간"
        }},
        "volatility_target": {{
            "type": "float",
            "default": {request.positionManagement.volatilityTarget or 2.0},
            "description": "목표 변동성 %"
        }},
        "max_positions": {{
            "type": "int",
            "default": {request.positionManagement.maxPositions},
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
)
class {class_name}(BaseStrategy):
    """
    {request.name}
    
    매수 조건: {len(request.buyConditions)}개
    매도 조건: {len(request.sellConditions)}개
    """
    
    def __init__(self, params: dict):
        super().__init__(params)
        # 진입 전략
        self.entry_type = self.get_param("entry_type", "{request.entryStrategy.type}")
        self.pyramid_levels = {[level.dict() for level in request.entryStrategy.pyramidLevels] if request.entryStrategy.pyramidLevels else []}
        self.max_position_size = self.get_param("max_position_size", {request.entryStrategy.maxPositionSize or 40})
        self.min_interval = self.get_param("min_interval", {request.entryStrategy.minInterval or 1})
        
        # 피라미딩 상태 추적
        self.entry_price = {{}}  # symbol: first_entry_price
        self.current_level = {{}}  # symbol: current_pyramid_level
        self.last_entry_date = {{}}  # symbol: last_entry_date
        self.total_units = {{}}  # symbol: total_units_invested
        
        # 포지션 사이징
        self.sizing_method = self.get_param("sizing_method", "{request.positionManagement.sizingMethod}")
        self.position_size = self.get_param("position_size", {request.positionManagement.positionSize or 0.1})
        self.account_risk = self.get_param("account_risk", {request.positionManagement.accountRisk or 1.0})
        self.atr_period = self.get_param("atr_period", {request.positionManagement.atrPeriod or 20})
        self.atr_multiple = self.get_param("atr_multiple", {request.positionManagement.atrMultiple or 2.0})
        self.win_rate = self.get_param("win_rate", {request.positionManagement.winRate or 0.5})
        self.win_loss_ratio = self.get_param("win_loss_ratio", {request.positionManagement.winLossRatio or 2.0})
        self.kelly_fraction = self.get_param("kelly_fraction", {request.positionManagement.kellyFraction or 0.25})
        self.volatility_period = self.get_param("volatility_period", {request.positionManagement.volatilityPeriod or 20})
        self.volatility_target = self.get_param("volatility_target", {request.positionManagement.volatilityTarget or 2.0})
        self.max_positions = self.get_param("max_positions", {request.positionManagement.maxPositions})
        
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
        self.trailing_stop_price = {{}}  # symbol: stop_price
    
    def on_bar(self, bars: List[OHLC], positions: List[Position], account: Account) -> List[OrderSignal]:
        """새로운 바마다 호출"""
        signals: List[OrderSignal] = []
        
        if len(bars) < 50:  # 최소 데이터 필요
            return signals
        
        closes = [bar.close for bar in bars]
        current_price = bars[-1].close
        symbol = bars[-1].symbol
        position = self.get_position(symbol, positions)
        
        # 매수 조건 체크
        if self.entry_type == "single":
            # 일괄 진입
            if not position and len(positions) < self.max_positions:
{chr(10).join(buy_conditions_code) if buy_conditions_code else "                pass"}
                
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
{chr(10).join(buy_conditions_code) if buy_conditions_code else "                pass"}
                
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
                            highs = [bar.high for bar in bars]
                            lows = [bar.low for bar in bars]
                            closes = [bar.close for bar in bars]
                            
                            true_ranges = []
                            for i in range(1, len(closes)):
                                tr = max(
                                    highs[i] - lows[i],
                                    abs(highs[i] - closes[i-1]),
                                    abs(lows[i] - closes[i-1])
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
            
{chr(10).join(sell_conditions_code) if sell_conditions_code else "            pass"}
            
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
        
        return signals
    
    def on_fill(self, order: Order, position: Position) -> None:
        """주문 체결 시 호출"""
        pass
    
    def _calculate_quantity(self, equity: float, price: float, bars: List[OHLC] = None) -> int:
        """
        매수 수량 계산 - 포지션 사이징 방식에 따라 동적 계산
        
        Args:
            equity: 계좌 자산
            price: 현재 가격
            bars: OHLC 데이터 (ATR/변동성 계산용)
        
        Returns:
            매수 수량
        """
        if self.sizing_method == "fixed":
            # 고정 비율
            position_value = equity * self.position_size
            quantity = int(position_value / price)
            
        elif self.sizing_method == "atr_risk":
            # ATR 기반 리스크 관리
            if bars and len(bars) >= self.atr_period + 1:
                highs = [bar.high for bar in bars]
                lows = [bar.low for bar in bars]
                closes = [bar.close for bar in bars]
                
                # ATR 계산 (간단 버전)
                true_ranges = []
                for i in range(1, len(closes)):
                    tr = max(
                        highs[i] - lows[i],
                        abs(highs[i] - closes[i-1]),
                        abs(lows[i] - closes[i-1])
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
            if bars and len(bars) >= self.volatility_period:
                closes = [bar.close for bar in bars[-self.volatility_period:]]
                returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
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
'''
    
    return code


@router.post("/{strategy_id}/backtest")
async def backtest_custom_strategy(
    strategy_id: int,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 10_000_000,
    current_user: dict = Depends(get_current_active_user)
):
    """
    커스텀 전략 백테스트
    
    Args:
        strategy_id: 전략 ID
        symbol: 종목 코드
        start_date: 시작일
        end_date: 종료일
        initial_capital: 초기 자본
        current_user: 현재 사용자
        
    Returns:
        백테스트 결과
    """
    try:
        if strategy_id not in strategies_db:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        strategy = strategies_db[strategy_id]
        
        # 권한 확인
        if strategy["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # TODO: 동적으로 전략 클래스 생성 및 백테스트 실행
        # 현재는 Python 코드만 반환
        
        return {
            "message": "백테스트 기능 구현 예정",
            "strategy_name": strategy["name"],
            "python_code": strategy["python_code"],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to backtest strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))
