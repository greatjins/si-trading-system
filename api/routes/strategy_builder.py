"""
전략 빌더 API - 노코드 전략 생성 및 관리
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth.security import get_current_active_user
from api.dependencies import get_db
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# 스키마

class LogicalNode(BaseModel):
    """
    논리 트리 노드 - 지표 간 연산을 표현
    
    예: MA20 > MA60
    {
        "operator": ">",
        "left": {"type": "indicator", "name": "MA", "params": {"period": 20}},
        "right": {"type": "indicator", "name": "MA", "params": {"period": 60}}
    }
    
    예: (RSI < 30) AND (Volume > Volume_MA)
    {
        "operator": "AND",
        "left": {
            "operator": "<",
            "left": {"type": "indicator", "name": "RSI", "params": {"period": 14}},
            "right": 30
        },
        "right": {
            "operator": ">",
            "left": {"type": "indicator", "name": "Volume"},
            "right": {"type": "indicator", "name": "Volume_MA", "params": {"period": 20}}
        }
    }
    """
    operator: str  # ">", "<", ">=", "<=", "==", "AND", "OR", "NOT"
    left: Any  # LogicalNode, Condition, 또는 값 (int, float, str, dict)
    right: Optional[Any] = None  # AND/OR가 아닌 경우만 사용


class IndicatorConfig(BaseModel):
    """
    지표 설정 - ICT 지표별 옵션 포함
    """
    type: str  # "technical" | "ict"
    name: str  # "rsi" | "ma" | "fvg" | "liquidity" | "order_block" | "mss" | "bos"
    parameters: Dict[str, Any] = {}  # 지표 파라미터
    
    # ICT 지표 전용 옵션
    timeframe: Optional[str] = None  # "1m" | "5m" | "15m" | "1h" | "1d" (ICT 지표용)
    sensitivity: Optional[float] = None  # 민감도 (0.0 ~ 1.0, ICT 지표용)
    enabled: Optional[bool] = True  # 지표 활성화 여부


class Condition(BaseModel):
    """
    조건 - 단순 조건 또는 논리 트리
    """
    id: str
    type: str  # "simple" | "logical" | "indicator" | "price" | "volume" | "ict"
    
    # 단순 조건 (type="simple" 또는 "indicator"/"price"/"volume")
    indicator: Optional[str] = None
    operator: Optional[str] = None  # ">", "<", ">=", "<=", "==", "in_gap", "in_zone", "in_block"
    value: Optional[Any] = None
    period: Optional[int] = None
    
    # 논리 트리 조건 (type="logical")
    logical_tree: Optional[LogicalNode] = None


class StockSelection(BaseModel):
    """종목 선정"""
    # 기본 필터
    marketCap: Optional[Dict[str, float]] = None  # 시가총액 (억원)
    volume: Optional[Dict[str, int]] = None  # 최소 거래량 (주)
    volumeValue: Optional[Dict[str, float]] = None  # 최소 거래대금 (백만원)
    price: Optional[Dict[str, float]] = None  # 가격 범위 (원)
    
    # 시장/업종
    sector: Optional[List[str]] = None  # 업종
    market: Optional[List[str]] = None  # 시장 (KOSPI/KOSDAQ/KONEX)
    
    # 재무 지표
    per: Optional[Dict[str, float]] = None  # PER
    pbr: Optional[Dict[str, float]] = None  # PBR
    roe: Optional[Dict[str, float]] = None  # ROE (%)
    debtRatio: Optional[Dict[str, float]] = None  # 부채비율 (%)
    
    # 기술적 지표
    pricePosition: Optional[Dict[str, Any]] = None  # 52주 최고가/최저가 대비 위치
    
    # 제외 조건
    excludeManaged: Optional[bool] = None  # 관리종목 제외
    excludeClearing: Optional[bool] = None  # 정리매매 제외
    excludePreferred: Optional[bool] = None  # 우선주 제외
    excludeSpac: Optional[bool] = None  # SPAC 제외
    minListingDays: Optional[int] = None  # 최소 상장일수


class TrailingStop(BaseModel):
    """트레일링 스탑 설정"""
    enabled: bool = False
    method: str = "atr"  # atr, percentage, parabolic_sar
    atrMultiple: Optional[float] = None
    percentage: Optional[float] = None
    activationProfit: Optional[float] = None
    updateFrequency: str = "every_bar"  # every_bar, new_high


class StopLoss(BaseModel):
    """손절 설정"""
    enabled: bool = False
    method: str = "fixed"  # fixed, atr, support, time
    fixedPercent: Optional[float] = None
    atrMultiple: Optional[float] = None
    minPercent: Optional[float] = None
    maxPercent: Optional[float] = None
    timeDays: Optional[int] = None


class TakeProfit(BaseModel):
    """익절 설정"""
    enabled: bool = False
    method: str = "fixed"  # fixed, r_multiple, partial
    fixedPercent: Optional[float] = None
    rMultiple: Optional[float] = None
    partialLevels: Optional[list] = None


class PositionManagement(BaseModel):
    """포지션 관리"""
    sizingMethod: str = "fixed"  # fixed, atr_risk, kelly, volatility
    
    # 고정 비율
    positionSize: Optional[float] = None
    
    # ATR 기반
    accountRisk: Optional[float] = None
    atrPeriod: Optional[int] = None
    atrMultiple: Optional[float] = None
    
    # 켈리 공식
    winRate: Optional[float] = None
    winLossRatio: Optional[float] = None
    kellyFraction: Optional[float] = None
    
    # 변동성 기반
    volatilityPeriod: Optional[int] = None
    volatilityTarget: Optional[float] = None
    
    maxPositions: int
    
    # 손절/익절
    stopLoss: Optional[StopLoss] = None
    takeProfit: Optional[TakeProfit] = None
    
    # 트레일링 스탑
    trailingStop: Optional[TrailingStop] = None


class PyramidLevel(BaseModel):
    """피라미딩 레벨"""
    level: int
    condition: str  # initial, price_increase, indicator
    priceChange: Optional[float] = None  # %
    units: float  # 유닛 수
    description: Optional[str] = None


class EntryStrategy(BaseModel):
    """진입 전략"""
    type: str = "single"  # single, pyramid
    pyramidLevels: Optional[List[PyramidLevel]] = None
    maxLevels: Optional[int] = None
    maxPositionSize: Optional[float] = None  # %
    minInterval: Optional[int] = None  # 일


class StrategyConfigRequest(BaseModel):
    """
    전략 설정 요청 - config_json 구조화된 데이터
    
    UI에서 전달받은 설정을 검증하고 config_json으로 저장
    """
    strategy_id: Optional[int] = None  # 수정 시 전략 ID
    name: str
    description: Optional[str] = ""
    
    # 지표 설정
    indicators: List[IndicatorConfig] = []
    
    # 조건 설정 (논리 트리 지원)
    conditions: Dict[str, List[Condition]] = {
        "buy": [],
        "sell": []
    }
    
    # ICT 전용 설정
    ict_config: Optional[Dict[str, Any]] = None
    
    # 전략 파라미터
    parameters: Optional[Dict[str, Any]] = None
    
    # 종목 선정 (포트폴리오 전략용)
    stock_selection: Optional[StockSelection] = None
    
    # 진입 전략
    entry_strategy: Optional[EntryStrategy] = None
    
    # 포지션 관리
    position_management: Optional[PositionManagement] = None
    
    # 리스크 관리
    risk_management: Optional[Dict[str, Any]] = None


class StrategyBuilderRequest(BaseModel):
    """전략 빌더 요청 (기존 호환성 유지)"""
    strategy_id: int = None  # 수정 시 전략 ID
    name: str
    description: str
    is_portfolio: Optional[bool] = None  # 단일 종목(false) vs 포트폴리오(true)
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
    python_code: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None  # 구조화된 설정 (save-config 엔드포인트용)


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
        
        # 수정 모드인지 확인
        if request.strategy_id:
            # 기존 전략 업데이트
            strategy = db.query(StrategyBuilderModel).filter(
                StrategyBuilderModel.id == request.strategy_id,
                StrategyBuilderModel.user_id == current_user["user_id"]
            ).first()
            
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            strategy.name = request.name
            strategy.description = request.description
            config_dict = request.dict()
            strategy.config = config_dict
            strategy.python_code = python_code
            strategy.updated_at = datetime.now()
            
            logger.info(f"Strategy updated: ID={strategy.id}, Name={request.name}, User={current_user['username']}")
            logger.info(f"  Config is_portfolio: {config_dict.get('is_portfolio', 'NOT SET')}")
        else:
            # 새 전략 생성
            config_dict = request.dict()
            strategy = StrategyBuilderModel(
                user_id=current_user["user_id"],
                name=request.name,
                description=request.description,
                config=config_dict,
                python_code=python_code,
                is_active=True
            )
            
            db.add(strategy)
            logger.info(f"Strategy created: Name={request.name}, User={current_user['username']}")
            logger.info(f"  Config is_portfolio: {config_dict.get('is_portfolio', 'NOT SET')}")
        
        db.commit()
        db.refresh(strategy)
        
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


@router.post("/save-config", response_model=StrategyBuilderResponse)
async def save_strategy_config(
    request: StrategyConfigRequest,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    전략 설정 저장 (config_json 기반)
    
    UI에서 전달받은 설정을 검증하고 config_json으로 저장합니다.
    Python 코드를 생성하지 않고, DynamicStrategy가 실행 시점에 config_json을 로드하여 동작합니다.
    
    Args:
        request: 전략 설정 요청
        current_user: 현재 사용자
        db: DB 세션
        
    Returns:
        저장된 전략 정보
    """
    try:
        from data.models import StrategyBuilderModel
        
        # 설정 검증
        validation_errors = _validate_strategy_config(request)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=f"전략 설정 검증 실패: {', '.join(validation_errors)}"
            )
        
        # config_json 구성
        config_json = {
            "indicators": [ind.dict() for ind in request.indicators],
            "conditions": {
                "buy": [cond.dict() for cond in request.conditions.get("buy", [])],
                "sell": [cond.dict() for cond in request.conditions.get("sell", [])]
            }
        }
        
        if request.ict_config:
            config_json["ict_config"] = request.ict_config
        
        if request.parameters:
            config_json["parameters"] = request.parameters
        
        if request.stock_selection:
            config_json["stock_selection"] = request.stock_selection.dict()
        
        if request.entry_strategy:
            config_json["entry_strategy"] = request.entry_strategy.dict()
        
        if request.position_management:
            config_json["position_management"] = request.position_management.dict()
        
        if request.risk_management:
            config_json["risk_management"] = request.risk_management
        
        # 기존 config 필드 (호환성 유지)
        config_dict = {
            "name": request.name,
            "description": request.description,
            "is_portfolio": request.stock_selection is not None,
            "stockSelection": request.stock_selection.dict() if request.stock_selection else {},
            "buyConditions": [cond.dict() for cond in request.conditions.get("buy", [])],
            "sellConditions": [cond.dict() for cond in request.conditions.get("sell", [])],
            "entryStrategy": request.entry_strategy.dict() if request.entry_strategy else {},
            "positionManagement": request.position_management.dict() if request.position_management else {}
        }
        
        # 수정 모드인지 확인
        if request.strategy_id:
            # 기존 전략 업데이트
            strategy = db.query(StrategyBuilderModel).filter(
                StrategyBuilderModel.id == request.strategy_id,
                StrategyBuilderModel.user_id == current_user["user_id"]
            ).first()
            
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            strategy.name = request.name
            strategy.description = request.description
            strategy.config = config_dict
            strategy.config_json = config_json  # 구조화된 설정 저장
            strategy.updated_at = datetime.now()
            
            logger.info(f"Strategy config updated: ID={strategy.id}, Name={request.name}, User={current_user['username']}")
        else:
            # 새 전략 생성
            strategy = StrategyBuilderModel(
                user_id=current_user["user_id"],
                name=request.name,
                description=request.description,
                config=config_dict,
                config_json=config_json,  # 구조화된 설정 저장
                is_active=True
            )
            
            db.add(strategy)
            logger.info(f"Strategy config created: Name={request.name}, User={current_user['username']}")
        
        db.commit()
        db.refresh(strategy)
        
        return StrategyBuilderResponse(
            strategy_id=strategy.id,
            name=strategy.name,
            description=strategy.description,
            created_at=strategy.created_at,
            python_code=None,  # DynamicStrategy는 python_code 불필요
            config_json=config_json
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save strategy config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _validate_strategy_config(request: StrategyConfigRequest) -> List[str]:
    """
    전략 설정 검증
    
    Args:
        request: 전략 설정 요청
    
    Returns:
        검증 오류 리스트 (빈 리스트면 검증 통과)
    """
    errors = []
    
    # 필수 필드 확인
    if not request.name or not request.name.strip():
        errors.append("전략 이름은 필수입니다")
    
    # 지표 검증
    for idx, indicator in enumerate(request.indicators):
        if not indicator.name:
            errors.append(f"지표 {idx+1}: 이름이 필요합니다")
        
        if indicator.type not in ["technical", "ict"]:
            errors.append(f"지표 {idx+1}: 타입은 'technical' 또는 'ict'여야 합니다")
        
        # ICT 지표 타임프레임 검증
        if indicator.type == "ict" and indicator.timeframe:
            valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
            if indicator.timeframe not in valid_timeframes:
                errors.append(f"지표 {idx+1}: 타임프레임은 {valid_timeframes} 중 하나여야 합니다")
        
        # 민감도 검증
        if indicator.sensitivity is not None:
            if not (0.0 <= indicator.sensitivity <= 1.0):
                errors.append(f"지표 {idx+1}: 민감도는 0.0 ~ 1.0 사이여야 합니다")
    
    # 조건 검증
    buy_conditions = request.conditions.get("buy", [])
    sell_conditions = request.conditions.get("sell", [])
    
    if not buy_conditions and not sell_conditions:
        errors.append("매수 또는 매도 조건이 최소 하나는 필요합니다")
    
    for idx, condition in enumerate(buy_conditions + sell_conditions):
        if not condition.id:
            errors.append(f"조건 {idx+1}: ID가 필요합니다")
        
        # 논리 트리 조건 검증
        if condition.type == "logical":
            if not condition.logical_tree:
                errors.append(f"조건 {condition.id}: 논리 트리가 필요합니다")
            else:
                errors.extend(_validate_logical_tree(condition.logical_tree, condition.id))
        
        # 단순 조건 검증
        elif condition.type in ["indicator", "price", "volume", "ict"]:
            if not condition.operator:
                errors.append(f"조건 {condition.id}: 연산자가 필요합니다")
    
    return errors


def _validate_logical_tree(node: LogicalNode, context: str = "") -> List[str]:
    """
    논리 트리 검증
    
    Args:
        node: 논리 트리 노드
        context: 검증 컨텍스트 (디버깅용)
    
    Returns:
        검증 오류 리스트
    """
    errors = []
    
    if not node.operator:
        errors.append(f"{context}: 연산자가 필요합니다")
        return errors
    
    valid_operators = [">", "<", ">=", "<=", "==", "AND", "OR", "NOT"]
    if node.operator not in valid_operators:
        errors.append(f"{context}: 지원하지 않는 연산자 '{node.operator}'")
    
    # 단항 연산자 (NOT)
    if node.operator == "NOT":
        if node.left is None:
            errors.append(f"{context}: NOT 연산자는 left 피연산자가 필요합니다")
        else:
            if isinstance(node.left, dict) and "operator" in node.left:
                # 중첩된 논리 노드
                errors.extend(_validate_logical_tree(LogicalNode(**node.left), f"{context}.left"))
    else:
        # 이항 연산자
        if node.left is None:
            errors.append(f"{context}: left 피연산자가 필요합니다")
        
        if node.right is None and node.operator not in ["NOT"]:
            errors.append(f"{context}: right 피연산자가 필요합니다")
        
        # 중첩된 논리 노드 재귀 검증
        if isinstance(node.left, dict) and "operator" in node.left:
            errors.extend(_validate_logical_tree(LogicalNode(**node.left), f"{context}.left"))
        
        if isinstance(node.right, dict) and "operator" in node.right:
            errors.extend(_validate_logical_tree(LogicalNode(**node.right), f"{context}.right"))
    
    return errors


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
        },
        {
            "id": "bos",
            "name": "BOS (Break of Structure)",
            "category": "ict",
            "type": "ict",
            "parameters": [
                {"name": "swing_lookback", "type": "number", "default": 5, "min": 3, "max": 20}
            ],
            "ict_options": {
                "timeframe": {
                    "type": "select",
                    "options": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                    "default": "1d",
                    "description": "BOS 탐지 타임프레임"
                },
                "sensitivity": {
                    "type": "slider",
                    "min": 0.0,
                    "max": 1.0,
                    "default": 0.5,
                    "step": 0.1,
                    "description": "민감도 (높을수록 더 많은 BOS 탐지)"
                }
            },
            "operators": ["break_high", "break_low", "structure_shift"],
            "description": "ICT 구조적 돌파 - 이전 고점/저점 돌파"
        },
        {
            "id": "fvg",
            "name": "Fair Value Gap",
            "category": "ict",
            "type": "ict",
            "parameters": [
                {"name": "min_gap_size", "type": "number", "default": 0.002, "min": 0.001, "max": 0.01, "step": 0.001},
                {"name": "check_filled", "type": "boolean", "default": True}
            ],
            "ict_options": {
                "timeframe": {
                    "type": "select",
                    "options": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                    "default": "1h",
                    "description": "FVG 탐지 타임프레임"
                },
                "sensitivity": {
                    "type": "slider",
                    "min": 0.0,
                    "max": 1.0,
                    "default": 0.3,
                    "step": 0.1,
                    "description": "민감도 (높을수록 더 작은 갭도 탐지)"
                }
            },
            "operators": ["in_gap", "above_gap", "below_gap"],
            "description": "ICT 공정가치 갭 - 가격 공백 구간"
        },
        {
            "id": "order_block",
            "name": "Order Block",
            "category": "ict",
            "type": "ict",
            "parameters": [
                {"name": "lookback", "type": "number", "default": 20, "min": 5, "max": 100},
                {"name": "volume_multiplier", "type": "number", "default": 1.5, "min": 1.0, "max": 3.0, "step": 0.1}
            ],
            "ict_options": {
                "timeframe": {
                    "type": "select",
                    "options": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                    "default": "1h",
                    "description": "Order Block 탐지 타임프레임"
                },
                "sensitivity": {
                    "type": "slider",
                    "min": 0.0,
                    "max": 1.0,
                    "default": 0.5,
                    "step": 0.1,
                    "description": "민감도 (높을수록 더 많은 Order Block 탐지)"
                }
            },
            "operators": ["in_block", "above_block", "below_block"],
            "description": "ICT 주문 블록 - 기관 주문 집중 구간"
        },
        {
            "id": "liquidity",
            "name": "Liquidity Zones",
            "category": "ict",
            "type": "ict",
            "parameters": [
                {"name": "period", "type": "number", "default": 20, "min": 5, "max": 100},
                {"name": "tolerance", "type": "number", "default": 0.001, "min": 0.0001, "max": 0.01, "step": 0.0001},
                {"name": "min_touches", "type": "number", "default": 2, "min": 1, "max": 10}
            ],
            "ict_options": {
                "timeframe": {
                    "type": "select",
                    "options": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                    "default": "1d",
                    "description": "Liquidity Zone 탐지 타임프레임"
                },
                "sensitivity": {
                    "type": "slider",
                    "min": 0.0,
                    "max": 1.0,
                    "default": 0.4,
                    "step": 0.1,
                    "description": "민감도 (높을수록 더 많은 유동성 구간 탐지)"
                }
            },
            "operators": ["in_zone", "near_zone", "break_zone"],
            "description": "ICT 유동성 구간 - 지지/저항 레벨"
        },
        {
            "id": "mss",
            "name": "Market Structure Shift",
            "category": "ict",
            "type": "ict",
            "parameters": [
                {"name": "swing_lookback", "type": "number", "default": 5, "min": 3, "max": 20}
            ],
            "ict_options": {
                "timeframe": {
                    "type": "select",
                    "options": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                    "default": "1d",
                    "description": "MSS 탐지 타임프레임"
                },
                "sensitivity": {
                    "type": "slider",
                    "min": 0.0,
                    "max": 1.0,
                    "default": 0.5,
                    "step": 0.1,
                    "description": "민감도 (높을수록 더 많은 MSS 탐지)"
                }
            },
            "operators": ["structure_shift", "bullish_shift", "bearish_shift"],
            "description": "ICT 시장 구조 변화 - 상승/하락 구조 전환"
        },
        {
            "id": "smart_money",
            "name": "Smart Money Flow",
            "category": "ict",
            "parameters": [
                {"name": "period", "type": "number", "default": 20, "min": 5, "max": 50}
            ],
            "operators": [">", "<", "bullish", "bearish"],
            "description": "ICT 스마트머니 흐름 - 기관투자자 동향"
        },
        {
            "id": "consecutive_bearish",
            "name": "연속 음봉",
            "category": "pattern",
            "parameters": [
                {"name": "count", "type": "number", "default": 3, "min": 2, "max": 10, "description": "연속 음봉 개수"}
            ],
            "operators": [">=", "=="],
            "description": "연속으로 음봉이 나오는 패턴 감지"
        },
        {
            "id": "price_from_high",
            "name": "고점 대비 하락률",
            "category": "price",
            "parameters": [
                {"name": "lookback", "type": "number", "default": 20, "min": 5, "max": 100, "description": "고점 기준 기간"}
            ],
            "operators": [">", ">=", "<", "<="],
            "description": "최근 고점 대비 현재가 하락률 (%)"
        },
        {
            "id": "ma_cross_down",
            "name": "이동평균선 이탈 (하락)",
            "category": "trend",
            "parameters": [
                {"name": "fast", "type": "number", "default": 5, "min": 1, "max": 50},
                {"name": "slow", "type": "number", "default": 20, "min": 1, "max": 200}
            ],
            "operators": ["cross_below"],
            "description": "단기선이 장기선 아래로 교차 (데드크로스)"
        }
    ]
    
    return {
        "indicators": indicators,
        "categories": [
            {"id": "trend", "name": "추세", "description": "추세 방향과 강도를 측정"},
            {"id": "momentum", "name": "모멘텀", "description": "가격 변화의 속도와 강도를 측정"},
            {"id": "volatility", "name": "변동성", "description": "가격 변동의 크기를 측정"},
            {"id": "volume", "name": "거래량", "description": "거래량 기반 지표"},
            {"id": "ict", "name": "🎯 ICT 이론", "description": "Inner Circle Trader 기법 - Smart Money Concepts"},
            {"id": "pattern", "name": "패턴", "description": "캔들 패턴 및 가격 패턴"},
            {"id": "price", "name": "가격", "description": "가격 기반 조건"}
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
        
        result = []
        for s in strategies:
            is_portfolio = False
            try:
                # 우선순위 1: config에 명시적으로 is_portfolio 필드가 있으면 사용
                if 'is_portfolio' in s.config:
                    is_portfolio = bool(s.config.get('is_portfolio', False))
                    logger.info(f"Strategy {s.name}: is_portfolio from config = {is_portfolio} (config keys: {list(s.config.keys())})")
                else:
                    # 우선순위 2: 실제 전략 인스턴스를 생성하여 확인 (가장 정확)
                    from core.strategy.factory import StrategyFactory
                    try:
                        db_config = {
                            "config": s.config,
                            "name": s.name
                        }
                        strategy = StrategyFactory.create_from_db_config(db_config)
                        is_portfolio = strategy.is_portfolio_strategy()
                        logger.debug(f"Strategy {s.name}: is_portfolio from instance = {is_portfolio}")
                    except Exception as strategy_error:
                        # 우선순위 3: 전략 생성 실패 시 fallback: config에서 stockSelection 확인
                        logger.debug(f"Could not create strategy instance for {s.name}, using config check: {strategy_error}")
                        stock_selection_data = s.config.get('stockSelection', {})
                        if stock_selection_data:
                            stock_selection = StockSelection(**stock_selection_data)
                            is_portfolio = _has_stock_selection_criteria(stock_selection)
                            logger.debug(f"Strategy {s.name}: is_portfolio from stockSelection = {is_portfolio}")
            except Exception as e:
                logger.warning(f"Failed to check portfolio status for strategy {s.id}: {e}")
            
            result.append({
                "strategy_id": s.id,
                "name": s.name,
                "description": s.description,
                "created_at": s.created_at,
                "is_portfolio": is_portfolio,
            })
            
            logger.info(f"Strategy {s.name}: is_portfolio = {is_portfolio}")
        
        return result
    
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


def _generate_condition_code(condition: Condition, index: int, condition_type: str) -> str:
    """
    개별 조건을 Python 코드로 변환
    
    Args:
        condition: 조건 객체
        index: 조건 인덱스
        condition_type: 'buy' 또는 'sell'
        
    Returns:
        Python 코드 문자열
    """
    if not condition.indicator:
        return ""
    
    # 지표별 코드 생성
    if condition.indicator == "ma":
        # 이동평균
        period = getattr(condition, 'period', 20)
        
        # 비교 대상 결정
        if isinstance(condition.value, str):
            if condition.value == 'close':
                compare_value = "current_price"
            elif condition.value == 'open':
                compare_value = "bars['open'].iloc[-1]"
            elif condition.value == 'high':
                compare_value = "bars['high'].iloc[-1]"
            elif condition.value == 'low':
                compare_value = "bars['low'].iloc[-1]"
            elif condition.value.startswith('MA('):
                # 다른 이동평균과 비교
                other_period = condition.value.replace('MA(', '').replace(')', '')
                compare_value = f"sum(closes[-{other_period}:]) / {other_period}"
            elif condition.value.startswith('EMA('):
                # 지수이동평균과 비교 (간단 근사)
                other_period = condition.value.replace('EMA(', '').replace(')', '')
                compare_value = f"_calculate_ema(closes, {other_period})"
            elif condition.value.startswith('RSI('):
                # RSI와 비교
                other_period = condition.value.replace('RSI(', '').replace(')', '')
                compare_value = f"_calculate_rsi(closes, {other_period})"
            else:
                compare_value = str(condition.value)
        else:
            compare_value = str(condition.value)
        
        if condition_type == "buy":
            return (
                f"        # 조건 {index+1}: MA({period}) {condition.operator} {condition.value}\n"
                f"        ma_{index} = sum(closes[-{period}:]) / {period}\n"
                f"        if not (ma_{index} {condition.operator} {compare_value}):\n"
                f"            return signals"
            )
        else:  # sell
            return (
                f"        # 조건 {index+1}: MA({period}) {condition.operator} {condition.value}\n"
                f"        ma_{index} = sum(closes[-{period}:]) / {period}\n"
                f"        if ma_{index} {condition.operator} {compare_value}:\n"
                f"            should_sell = True"
            )
    
    elif condition.indicator == "rsi":
        # RSI
        period = getattr(condition, 'period', 14)
        
        # 비교 대상 결정
        if isinstance(condition.value, str):
            if condition.value == 'close':
                compare_value = "current_price"
            elif condition.value.startswith('RSI('):
                other_period = condition.value.replace('RSI(', '').replace(')', '')
                compare_value = f"_calculate_rsi(closes, {other_period})"
            else:
                compare_value = str(condition.value)
        else:
            compare_value = str(condition.value)
        
        if condition_type == "buy":
            return (
                f"        # 조건 {index+1}: RSI({period}) {condition.operator} {condition.value}\n"
                f"        rsi_{index} = _calculate_rsi(closes, {period})\n"
                f"        if not (rsi_{index} {condition.operator} {compare_value}):\n"
                f"            return signals"
            )
        else:  # sell
            return (
                f"        # 조건 {index+1}: RSI({period}) {condition.operator} {condition.value}\n"
                f"        rsi_{index} = _calculate_rsi(closes, {period})\n"
                f"        if rsi_{index} {condition.operator} {compare_value}:\n"
                f"            should_sell = True"
            )
    
    elif condition.indicator == "volume_ma":
        # 거래량 이동평균
        period = getattr(condition, 'period', 20)
        
        if condition_type == "buy":
            return (
                f"        # 조건 {index+1}: 거래량 > 거래량 MA({period})\n"
                f"        volume_ma_{index} = sum(bars['volume'].iloc[-{period}:]) / {period}\n"
                f"        current_volume = bars['volume'].iloc[-1]\n"
                f"        if not (current_volume > volume_ma_{index}):\n"
                f"            return signals"
            )
        else:  # sell
            return (
                f"        # 조건 {index+1}: 거래량 < 거래량 MA({period})\n"
                f"        volume_ma_{index} = sum(bars['volume'].iloc[-{period}:]) / {period}\n"
                f"        current_volume = bars['volume'].iloc[-1]\n"
                f"        if current_volume < volume_ma_{index}:\n"
                f"            should_sell = True"
            )
    
    elif condition.indicator == "bos":
        # Break of Structure
        lookback = getattr(condition, 'lookback', 20)
        
        if condition_type == "buy":
            return (
                f"        # 조건 {index+1}: BOS 상승 돌파 확인\n"
                f"        recent_high = bars['high'].tail({lookback}).max()\n"
                f"        if not (current_price > recent_high * 1.001):  # 0.1% 여유\n"
                f"            return signals"
            )
        else:  # sell
            return (
                f"        # 조건 {index+1}: BOS 하락 돌파 확인\n"
                f"        recent_low = bars['low'].tail({lookback}).min()\n"
                f"        if current_price < recent_low * 0.999:  # 0.1% 여유\n"
                f"            should_sell = True"
            )
    
    elif condition.indicator == "smart_money":
        # Smart Money Flow
        period = getattr(condition, 'period', 20)
        
        if condition_type == "buy":
            return (
                f"        # 조건 {index+1}: Smart Money 상승 흐름\n"
                f"        volume_ma = bars['volume'].tail({period}).mean()\n"
                f"        current_volume = bars['volume'].iloc[-1]\n"
                f"        rsi_val = _calculate_rsi(closes, 14)\n"
                f"        # 높은 거래량 + 상승 모멘텀\n"
                f"        if not (current_volume > volume_ma * 1.5 and rsi_val > 50):\n"
                f"            return signals"
            )
        else:  # sell
            return (
                f"        # 조건 {index+1}: Smart Money 하락 흐름\n"
                f"        volume_ma = bars['volume'].tail({period}).mean()\n"
                f"        current_volume = bars['volume'].iloc[-1]\n"
                f"        rsi_val = _calculate_rsi(closes, 14)\n"
                f"        # 높은 거래량 + 하락 모멘텀\n"
                f"        if current_volume > volume_ma * 1.5 and rsi_val < 50:\n"
                f"            should_sell = True"
            )
    
    elif condition.indicator == "fvg":
        # Fair Value Gap
        min_gap = getattr(condition, 'min_gap', 0.002)
        
        if condition_type == "buy":
            return (
                f"        # 조건 {index+1}: Fair Value Gap 상승 진입\n"
                f"        # 3봉 패턴으로 FVG 감지\n"
                f"        if len(bars) >= 3:\n"
                f"            prev_high = bars['high'].iloc[-3]\n"
                f"            next_low = bars['low'].iloc[-1]\n"
                f"            gap_size = (next_low - prev_high) / prev_high\n"
                f"            # Bullish FVG: 이전 고점 < 현재 저점\n"
                f"            if not (prev_high < next_low and gap_size >= {min_gap}):\n"
                f"                return signals"
            )
        else:  # sell
            return (
                f"        # 조건 {index+1}: Fair Value Gap 하락 진입\n"
                f"        if len(bars) >= 3:\n"
                f"            prev_low = bars['low'].iloc[-3]\n"
                f"            next_high = bars['high'].iloc[-1]\n"
                f"            gap_size = (prev_low - next_high) / next_high\n"
                f"            # Bearish FVG: 이전 저점 > 현재 고점\n"
                f"            if prev_low > next_high and gap_size >= {min_gap}:\n"
                f"                should_sell = True"
            )
    
    elif condition.indicator == "order_block":
        # Order Block
        volume_multiplier = getattr(condition, 'volume_multiplier', 1.5)
        
        if condition_type == "buy":
            return (
                f"        # 조건 {index+1}: Order Block 상승 리테스트\n"
                f"        # 높은 거래량 + 큰 몸통 확인\n"
                f"        if len(bars) >= 20:\n"
                f"            avg_volume = bars['volume'].tail(20).mean()\n"
                f"            current_volume = bars['volume'].iloc[-1]\n"
                f"            body_size = abs(bars['close'].iloc[-1] - bars['open'].iloc[-1]) / bars['open'].iloc[-1]\n"
                f"            # Order Block 조건: 높은 거래량 + 2% 이상 몸통\n"
                f"            if not (current_volume > avg_volume * {volume_multiplier} and body_size > 0.02):\n"
                f"                return signals"
            )
        else:  # sell
            return (
                f"        # 조건 {index+1}: Order Block 하락 리테스트\n"
                f"        if len(bars) >= 20:\n"
                f"            avg_volume = bars['volume'].tail(20).mean()\n"
                f"            current_volume = bars['volume'].iloc[-1]\n"
                f"            body_size = abs(bars['close'].iloc[-1] - bars['open'].iloc[-1]) / bars['open'].iloc[-1]\n"
                f"            # Bearish Order Block\n"
                f"            if (current_volume > avg_volume * {volume_multiplier} and \n"
                f"                body_size > 0.02 and bars['close'].iloc[-1] < bars['open'].iloc[-1]):\n"
                f"                should_sell = True"
            )
    
    elif condition.indicator == "liquidity_pool":
        # Liquidity Pool
        cluster_threshold = getattr(condition, 'cluster_threshold', 0.015)
        
        if condition_type == "buy":
            return (
                f"        # 조건 {index+1}: Liquidity Pool 지지선 테스트\n"
                f"        # 최근 저점들의 클러스터 확인\n"
                f"        if len(bars) >= 50:\n"
                f"            recent_lows = bars['low'].tail(50)\n"
                f"            # 현재가 근처의 저점 클러스터 찾기\n"
                f"            nearby_lows = [low for low in recent_lows if abs(current_price - low) / low <= {cluster_threshold}]\n"
                f"            # 3개 이상의 저점이 근처에 있으면 유동성 풀\n"
                f"            if not (len(nearby_lows) >= 3):\n"
                f"                return signals"
            )
        else:  # sell
            return (
                f"        # 조건 {index+1}: Liquidity Pool 저항선 테스트\n"
                f"        if len(bars) >= 50:\n"
                f"            recent_highs = bars['high'].tail(50)\n"
                f"            nearby_highs = [high for high in recent_highs if abs(current_price - high) / high <= {cluster_threshold}]\n"
                f"            # 고점 클러스터에서 저항 확인\n"
                f"            if len(nearby_highs) >= 3:\n"
                f"                should_sell = True"
            )
    
    elif condition.indicator == "consecutive_bearish":
        # 연속 음봉 패턴
        count = getattr(condition, 'count', 3)
        if condition_type == "sell":
            return (
                f"        # 조건 {index+1}: 연속 음봉 {count}개 이상\n"
                f"        if len(bars) >= {count}:\n"
                f"            recent_bars = bars.tail({count})\n"
                f"            bearish_count = sum(recent_bars['close'] < recent_bars['open'])\n"
                f"            if bearish_count >= {count}:\n"
                f"                should_sell = True"
            )
    
    elif condition.indicator == "price_from_high":
        # 고점 대비 하락률
        lookback = getattr(condition, 'lookback', 20)
        threshold = float(condition.value) if isinstance(condition.value, (int, float)) else 5.0
        if condition_type == "sell":
            return (
                f"        # 조건 {index+1}: 고점 대비 하락률 {threshold}% 이상\n"
                f"        if len(bars) >= {lookback}:\n"
                f"            recent_high = bars['high'].tail({lookback}).max()\n"
                f"            decline_pct = ((recent_high - current_price) / recent_high) * 100\n"
                f"            if decline_pct >= {threshold}:\n"
                f"                should_sell = True"
            )
    
    elif condition.indicator == "ma_cross_down":
        # 이동평균선 데드크로스
        fast_period = getattr(condition, 'fast', 5)
        slow_period = getattr(condition, 'slow', 20)
        if condition_type == "sell":
            return (
                f"        # 조건 {index+1}: 데드크로스 발생\n"
                f"        if len(bars) >= {slow_period} + 1:\n"
                f"            ma_fast = sum(closes[-{fast_period}:]) / {fast_period}\n"
                f"            ma_slow = sum(closes[-{slow_period}:]) / {slow_period}\n"
                f"            prev_ma_fast = sum(closes[-{fast_period}-1:-1]) / {fast_period}\n"
                f"            prev_ma_slow = sum(closes[-{slow_period}-1:-1]) / {slow_period}\n"
                f"            if prev_ma_fast > prev_ma_slow and ma_fast < ma_slow:\n"
                f"                should_sell = True"
            )
    
    # 기본 처리 (기존 방식)
    return ""


def _has_stock_selection_criteria(stock_selection: StockSelection) -> bool:
    """
    종목 선정 조건이 있는지 확인
    
    Args:
        stock_selection: 종목 선정 조건
        
    Returns:
        조건이 있으면 True
    """
    # 기본 필터
    if stock_selection.marketCap and (stock_selection.marketCap.get('min') or stock_selection.marketCap.get('max')):
        return True
    if stock_selection.volume and stock_selection.volume.get('min'):
        return True
    if stock_selection.volumeValue and stock_selection.volumeValue.get('min'):
        return True
    if stock_selection.price and (stock_selection.price.get('min') or stock_selection.price.get('max')):
        return True
    
    # 시장/업종
    if stock_selection.sector and len(stock_selection.sector) > 0:
        return True
    if stock_selection.market and len(stock_selection.market) > 0:
        return True
    
    # 재무 지표
    if stock_selection.per and (stock_selection.per.get('min') or stock_selection.per.get('max')):
        return True
    if stock_selection.pbr and (stock_selection.pbr.get('min') or stock_selection.pbr.get('max')):
        return True
    if stock_selection.roe and stock_selection.roe.get('min'):
        return True
    if stock_selection.debtRatio and stock_selection.debtRatio.get('max'):
        return True
    
    # 기술적 지표
    if stock_selection.pricePosition:
        if stock_selection.pricePosition.get('from52WeekHigh'):
            return True
        if stock_selection.pricePosition.get('from52WeekLow'):
            return True
    
    return False


def _generate_select_universe_method(stock_selection: StockSelection) -> str:
    """
    select_universe() 메서드 코드 생성
    
    Args:
        stock_selection: 종목 선정 조건
        
    Returns:
        Python 코드
    """
    conditions = []
    
    # 시가총액 (DB는 백만원 단위, 입력은 억원 단위)
    if stock_selection.marketCap:
        if stock_selection.marketCap.get('min'):
            conditions.append(f"StockMasterModel.market_cap >= {stock_selection.marketCap['min'] * 100}")
        if stock_selection.marketCap.get('max'):
            conditions.append(f"StockMasterModel.market_cap <= {stock_selection.marketCap['max'] * 100}")
    
    # 거래량
    if stock_selection.volume and stock_selection.volume.get('min'):
        conditions.append(f"StockMasterModel.volume_amount >= {stock_selection.volume['min']}")
    
    # 거래대금 (DB는 원 단위, 입력은 억원 단위)
    if stock_selection.volumeValue and stock_selection.volumeValue.get('min'):
        conditions.append(f"StockMasterModel.volume_amount >= {stock_selection.volumeValue['min'] * 100_000_000}")
    
    # 가격
    if stock_selection.price:
        if stock_selection.price.get('min'):
            conditions.append(f"StockMasterModel.current_price >= {stock_selection.price['min']}")
        if stock_selection.price.get('max'):
            conditions.append(f"StockMasterModel.current_price <= {stock_selection.price['max']}")
    
    # 시장
    if stock_selection.market and len(stock_selection.market) > 0:
        markets_str = ", ".join([f"'{m}'" for m in stock_selection.market])
        conditions.append(f"StockMasterModel.market.in_([{markets_str}])")
    
    # PER
    if stock_selection.per:
        if stock_selection.per.get('min'):
            conditions.append(f"StockMasterModel.per >= {stock_selection.per['min']}")
        if stock_selection.per.get('max'):
            conditions.append(f"StockMasterModel.per <= {stock_selection.per['max']}")
    
    # PBR
    if stock_selection.pbr:
        if stock_selection.pbr.get('min'):
            conditions.append(f"StockMasterModel.pbr >= {stock_selection.pbr['min']}")
        if stock_selection.pbr.get('max'):
            conditions.append(f"StockMasterModel.pbr <= {stock_selection.pbr['max']}")
    
    # ROE
    if stock_selection.roe and stock_selection.roe.get('min'):
        conditions.append(f"StockMasterModel.roe >= {stock_selection.roe['min']}")
    
    # 52주 위치
    if stock_selection.pricePosition:
        if stock_selection.pricePosition.get('from52WeekHigh'):
            pos = stock_selection.pricePosition['from52WeekHigh']
            if pos.get('min'):
                conditions.append(f"StockMasterModel.price_position >= {pos['min'] / 100}")
            if pos.get('max'):
                conditions.append(f"StockMasterModel.price_position <= {pos['max'] / 100}")
    
    # 제외 조건
    if stock_selection.excludeManaged:
        conditions.append("StockMasterModel.is_active == True")
    
    # 조건 문자열 생성 - 각 filter를 별도 라인으로
    filter_lines = []
    for cond in conditions:
        filter_lines.append(f"            query = query.filter({cond})")
    filter_conditions = "\n".join(filter_lines)
    
    code = f'''
    def select_universe(self, date: datetime, repository) -> List[str]:
        """
        종목 유니버스 선정
        
        Args:
            date: 기준일
            repository: 데이터 저장소
            
        Returns:
            종목 코드 리스트
        """
        from data.models import StockMasterModel
        from data.repository import get_db_session
        
        db = get_db_session()
        
        try:
            # 종목 선정 조건
            query = db.query(StockMasterModel.symbol)
{filter_conditions}
            
            # 최대 종목 수 제한
            max_stocks = self.get_param("max_positions", {stock_selection.market and len(stock_selection.market) * 20 or 50})
            
            # PER 기준 정렬 (낮은 순)
            if hasattr(StockMasterModel, 'per'):
                query = query.filter(StockMasterModel.per.isnot(None))
                query = query.order_by(StockMasterModel.per.asc())
            
            symbols = [row.symbol for row in query.limit(max_stocks).all()]
            
            return symbols
        finally:
            db.close()
'''
    
    return code


def generate_strategy_code(request: StrategyBuilderRequest) -> str:
    """
    전략 설정을 Python 코드로 변환
    
    Args:
        request: 전략 빌더 요청
        
    Returns:
        Python 코드
    """
    from api.services.strategy_code_generator import generate_strategy_code as _generate_strategy_code
    return _generate_strategy_code(request)


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
