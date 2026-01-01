"""
비교 분석 API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from api.auth.security import get_current_active_user
from api.dependencies import get_db
from sqlalchemy.orm import Session
from core.analysis.comparison import ComparisonEngine
from data.models import BacktestLiveComparisonModel
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# 스키마
class ComparisonRequest(BaseModel):
    """비교 분석 요청"""
    backtest_id: int
    strategy_id: int
    live_start: datetime
    live_end: datetime


class ComparisonResponse(BaseModel):
    """비교 분석 응답"""
    id: int
    backtest_id: int
    strategy_id: int
    backtest_return: float
    live_return: float
    return_difference: float
    backtest_trades: int
    live_trades: int
    trade_difference: int
    slippage_contribution: Optional[float]
    commission_contribution: Optional[float]
    delay_contribution: Optional[float]
    liquidity_contribution: Optional[float]
    market_change_contribution: Optional[float]
    created_at: datetime


@router.post("/compare", response_model=ComparisonResponse)
async def create_comparison(
    request: ComparisonRequest,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    백테스트-실전 비교 실행
    
    Args:
        request: 비교 분석 요청
    
    Returns:
        비교 결과
    """
    try:
        user_id = current_user["user_id"]
        
        # 비교 엔진 생성
        engine = ComparisonEngine(db)
        
        # 비교 실행
        comparison = engine.compare(
            backtest_id=request.backtest_id,
            strategy_id=request.strategy_id,
            user_id=user_id,
            live_start=request.live_start,
            live_end=request.live_end
        )
        
        return ComparisonResponse(
            id=comparison.id,
            backtest_id=comparison.backtest_id,
            strategy_id=comparison.strategy_id,
            backtest_return=comparison.backtest_return,
            live_return=comparison.live_return,
            return_difference=comparison.return_difference,
            backtest_trades=comparison.backtest_trades,
            live_trades=comparison.live_trades,
            trade_difference=comparison.trade_difference,
            slippage_contribution=comparison.slippage_contribution,
            commission_contribution=comparison.commission_contribution,
            delay_contribution=comparison.delay_contribution,
            liquidity_contribution=comparison.liquidity_contribution,
            market_change_contribution=comparison.market_change_contribution,
            created_at=comparison.created_at
        )
    
    except Exception as e:
        logger.error(f"Failed to create comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparisons", response_model=List[ComparisonResponse])
async def get_comparisons(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    strategy_id: Optional[int] = None,
    limit: int = 50
):
    """
    비교 결과 목록 조회
    
    Args:
        strategy_id: 전략 ID 필터 (선택)
        limit: 최대 조회 개수
    
    Returns:
        비교 결과 목록
    """
    try:
        user_id = current_user["user_id"]
        
        query = db.query(BacktestLiveComparisonModel).filter(
            BacktestLiveComparisonModel.user_id == user_id
        )
        
        if strategy_id:
            query = query.filter(
                BacktestLiveComparisonModel.strategy_id == strategy_id
            )
        
        comparisons = query.order_by(
            BacktestLiveComparisonModel.created_at.desc()
        ).limit(limit).all()
        
        return [
            ComparisonResponse(
                id=c.id,
                backtest_id=c.backtest_id,
                strategy_id=c.strategy_id,
                backtest_return=c.backtest_return,
                live_return=c.live_return,
                return_difference=c.return_difference,
                backtest_trades=c.backtest_trades,
                live_trades=c.live_trades,
                trade_difference=c.trade_difference,
                slippage_contribution=c.slippage_contribution,
                commission_contribution=c.commission_contribution,
                delay_contribution=c.delay_contribution,
                liquidity_contribution=c.liquidity_contribution,
                market_change_contribution=c.market_change_contribution,
                created_at=c.created_at
            )
            for c in comparisons
        ]
    
    except Exception as e:
        logger.error(f"Failed to get comparisons: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparisons/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(
    comparison_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    비교 결과 상세 조회
    
    Args:
        comparison_id: 비교 결과 ID
    
    Returns:
        비교 결과 상세
    """
    try:
        user_id = current_user["user_id"]
        
        comparison = db.query(BacktestLiveComparisonModel).filter(
            BacktestLiveComparisonModel.id == comparison_id,
            BacktestLiveComparisonModel.user_id == user_id
        ).first()
        
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail=f"Comparison not found: {comparison_id}"
            )
        
        return ComparisonResponse(
            id=comparison.id,
            backtest_id=comparison.backtest_id,
            strategy_id=comparison.strategy_id,
            backtest_return=comparison.backtest_return,
            live_return=comparison.live_return,
            return_difference=comparison.return_difference,
            backtest_trades=comparison.backtest_trades,
            live_trades=comparison.live_trades,
            trade_difference=comparison.trade_difference,
            slippage_contribution=comparison.slippage_contribution,
            commission_contribution=comparison.commission_contribution,
            delay_contribution=comparison.delay_contribution,
            liquidity_contribution=comparison.liquidity_contribution,
            market_change_contribution=comparison.market_change_contribution,
            created_at=comparison.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

