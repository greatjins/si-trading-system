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
class Condition(BaseModel):
    """조건"""
    id: str
    type: str  # indicator, price, volume
    indicator: Optional[str] = None
    operator: str
    value: Any
    period: Optional[int] = None


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


class StrategyBuilderRequest(BaseModel):
    """전략 빌더 요청"""
    strategy_id: int = None  # 수정 시 전략 ID
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
            strategy.config = request.dict()
            strategy.python_code = python_code
            strategy.updated_at = datetime.now()
            
            logger.info(f"Strategy updated: ID={strategy.id}, Name={request.name}, User={current_user['username']}")
        else:
            # 새 전략 생성
            strategy = StrategyBuilderModel(
                user_id=current_user["user_id"],
                name=request.name,
                description=request.description,
                config=request.dict(),
                python_code=python_code,
                is_active=True
            )
            
            db.add(strategy)
            logger.info(f"Strategy created: Name={request.name}, User={current_user['username']}")
        
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
            "parameters": [
                {"name": "lookback", "type": "number", "default": 20, "min": 5, "max": 100}
            ],
            "operators": [">", "<", "break_high", "break_low"],
            "description": "ICT 구조적 돌파 - 이전 고점/저점 돌파"
        },
        {
            "id": "fvg",
            "name": "Fair Value Gap",
            "category": "ict",
            "parameters": [
                {"name": "min_gap", "type": "number", "default": 0.002, "min": 0.001, "max": 0.01, "step": 0.001}
            ],
            "operators": ["in_gap", "above_gap", "below_gap"],
            "description": "ICT 공정가치 갭 - 가격 공백 구간"
        },
        {
            "id": "order_block",
            "name": "Order Block",
            "category": "ict",
            "parameters": [
                {"name": "volume_multiplier", "type": "number", "default": 1.5, "min": 1.0, "max": 3.0, "step": 0.1}
            ],
            "operators": ["in_block", "above_block", "below_block"],
            "description": "ICT 주문 블록 - 기관 주문 집중 구간"
        },
        {
            "id": "liquidity_pool",
            "name": "Liquidity Pool",
            "category": "ict",
            "parameters": [
                {"name": "cluster_threshold", "type": "number", "default": 0.015, "min": 0.005, "max": 0.05, "step": 0.005}
            ],
            "operators": ["near_pool", "sweep_pool"],
            "description": "ICT 유동성 풀 - 고점/저점 클러스터"
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
        }
    ]
    
    return {
        "indicators": indicators,
        "categories": [
            {"id": "trend", "name": "추세", "description": "추세 방향과 강도를 측정"},
            {"id": "momentum", "name": "모멘텀", "description": "가격 변화의 속도와 강도를 측정"},
            {"id": "volatility", "name": "변동성", "description": "가격 변동의 크기를 측정"},
            {"id": "volume", "name": "거래량", "description": "거래량 기반 지표"},
            {"id": "ict", "name": "🎯 ICT 이론", "description": "Inner Circle Trader 기법 - Smart Money Concepts"}
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
                # config에서 stockSelection 추출
                stock_selection_data = s.config.get('stockSelection', {})
                if stock_selection_data:
                    stock_selection = StockSelection(**stock_selection_data)
                    is_portfolio = _has_stock_selection_criteria(stock_selection)
            except Exception as e:
                logger.warning(f"Failed to check portfolio status for strategy {s.id}: {e}")
            
            result.append({
                "strategy_id": s.id,
                "name": s.name,
                "description": s.description,
                "created_at": s.created_at,
                "is_portfolio": is_portfolio,
            })
        
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
    import re
    
    # 클래스명: 영문자, 숫자, 언더스코어만 허용
    class_name = re.sub(r'[^a-zA-Z0-9_]', '', request.name.replace(" ", "_").replace("-", "_"))
    if not class_name:
        class_name = "CustomStrategy"
    # 숫자로 시작하면 안됨
    if class_name[0].isdigit():
        class_name = "Strategy_" + class_name
    
    # 종목 선정 조건이 있는지 확인 (포트폴리오 전략 여부)
    has_stock_selection = _has_stock_selection_criteria(request.stockSelection)
    is_portfolio_strategy = has_stock_selection
    
    # 설명에서 따옴표 이스케이프
    description = request.description.replace('"', '\\"').replace("'", "\\'") if request.description else ""
    
    # 종목 선정 조건 확인 (포트폴리오 전략 여부)
    has_stock_selection = _has_stock_selection_criteria(request.stockSelection)
    is_portfolio_strategy = has_stock_selection
    
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
    
    # select_universe 메서드 생성 (포트폴리오 전략인 경우)
    select_universe_method = ""
    if is_portfolio_strategy:
        select_universe_method = _generate_select_universe_method(request.stockSelection)
    
    # 매수 조건 코드 생성
    buy_conditions_code = []
    for i, cond in enumerate(request.buyConditions):
        condition_code = _generate_condition_code(cond, i, "buy")
        if condition_code:
            buy_conditions_code.append(condition_code)
    
    # 매도 조건 코드 생성
    sell_conditions_code = []
    for i, cond in enumerate(request.sellConditions):
        condition_code = _generate_condition_code(cond, i, "sell")
        if condition_code:
            sell_conditions_code.append(condition_code)
    
    code = f'''"""
{request.name}

{description}

자동 생성된 전략 - 전략 빌더
"""
from typing import List
from datetime import datetime
import pandas as pd
from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy
from utils.types import Position, Account, OrderSignal, OrderSide, OrderType, Order

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
    
    {'포트폴리오 전략 (종목 자동 선정)' if is_portfolio_strategy else '단일 종목 전략'}
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
    {select_universe_method if is_portfolio_strategy else ""}
    def on_bar(self, bars: pd.DataFrame, positions: List[Position], account: Account) -> List[OrderSignal]:
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
{chr(10).join(buy_conditions_code) if buy_conditions_code else "                # 조건 없음"}
                
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
{chr(10).join(buy_conditions_code) if buy_conditions_code else "                # 조건 없음"}
                
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
{chr(10).join(sell_conditions_code) if sell_conditions_code else "            # 조건 없음"}
            
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
    
    def _calculate_quantity(self, equity: float, price: float, bars: pd.DataFrame = None) -> int:
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
        
        return rsi
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
