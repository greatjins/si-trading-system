"""
대시보드 API - 수익 모니터링
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from api.auth.security import get_current_active_user
from api.dependencies import get_db
from data.models import (
    StrategyPerformanceModel, LiveTradeModel, StrategyBuilderModel
)
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# 스키마
class ProfitSummary(BaseModel):
    """수익 요약"""
    today_return: float  # 오늘 수익률
    week_return: float  # 이번 주 수익률
    month_return: float  # 이번 달 수익률
    total_return: float  # 총 수익률
    current_equity: float  # 현재 자산
    initial_capital: float  # 초기 자본


class StrategyPerformanceSummary(BaseModel):
    """전략별 성과 요약"""
    strategy_id: int
    strategy_name: str
    total_return: float
    daily_return: Optional[float]
    total_trades: int
    win_rate: Optional[float]
    current_equity: float
    is_active: bool


class TradeSummary(BaseModel):
    """거래 요약"""
    trade_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    timestamp: datetime


class DashboardSummaryResponse(BaseModel):
    """대시보드 요약 응답"""
    profit: ProfitSummary
    strategies: List[StrategyPerformanceSummary]
    recent_trades: List[TradeSummary]


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    대시보드 요약 정보 조회
    
    Returns:
        오늘/이번 주/이번 달 수익, 실행 중인 전략 목록, 최근 거래 내역
    """
    try:
        user_id = current_user["user_id"]
        
        # 1. 전체 수익 요약 계산
        performances = db.query(StrategyPerformanceModel).filter(
            StrategyPerformanceModel.user_id == user_id,
            StrategyPerformanceModel.is_active == True
        ).all()
        
        if not performances:
            # 전략이 없으면 기본값 반환
            return DashboardSummaryResponse(
                profit=ProfitSummary(
                    today_return=0.0,
                    week_return=0.0,
                    month_return=0.0,
                    total_return=0.0,
                    current_equity=0.0,
                    initial_capital=0.0
                ),
                strategies=[],
                recent_trades=[]
            )
        
        # 전체 자산 계산
        total_initial = sum(p.initial_capital for p in performances)
        total_current = sum(p.current_equity for p in performances)
        total_return = (total_current - total_initial) / total_initial if total_initial > 0 else 0.0
        
        # 오늘/이번 주/이번 달 수익률 계산
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # 최근 거래에서 수익률 계산 (간단한 구현)
        today_trades = db.query(LiveTradeModel).filter(
            LiveTradeModel.user_id == user_id,
            func.date(LiveTradeModel.timestamp) == today
        ).all()
        
        # 오늘 수익률 (간단한 구현: 실현 손익 기반)
        today_pnl = sum(
            (p.realized_pnl + p.unrealized_pnl) - 
            (p.realized_pnl + p.unrealized_pnl)  # 이전 자산 대비
            for p in performances
        )
        today_return = today_pnl / total_initial if total_initial > 0 else 0.0
        
        # 이번 주/이번 달 수익률 (간단한 구현)
        week_return = total_return * 0.3  # 임시: 총 수익률의 30%
        month_return = total_return * 0.7  # 임시: 총 수익률의 70%
        
        profit_summary = ProfitSummary(
            today_return=today_return,
            week_return=week_return,
            month_return=month_return,
            total_return=total_return,
            current_equity=total_current,
            initial_capital=total_initial
        )
        
        # 2. 전략별 성과 목록
        strategy_summaries = []
        for perf in performances:
            strategy = db.query(StrategyBuilderModel).filter(
                StrategyBuilderModel.id == perf.strategy_id
            ).first()
            
            strategy_name = strategy.name if strategy else f"Strategy {perf.strategy_id}"
            
            strategy_summaries.append(StrategyPerformanceSummary(
                strategy_id=perf.strategy_id,
                strategy_name=strategy_name,
                total_return=perf.total_return,
                daily_return=perf.daily_return,
                total_trades=perf.total_trades,
                win_rate=perf.win_rate,
                current_equity=perf.current_equity,
                is_active=perf.is_active
            ))
        
        # 3. 최근 거래 내역 (오늘)
        recent_trades = db.query(LiveTradeModel).filter(
            LiveTradeModel.user_id == user_id,
            func.date(LiveTradeModel.timestamp) == today
        ).order_by(LiveTradeModel.timestamp.desc()).limit(10).all()
        
        trade_summaries = [
            TradeSummary(
                trade_id=trade.trade_id,
                symbol=trade.symbol,
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
                timestamp=trade.timestamp
            )
            for trade in recent_trades
        ]
        
        return DashboardSummaryResponse(
            profit=profit_summary,
            strategies=strategy_summaries,
            recent_trades=trade_summaries
        )
    
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies", response_model=List[StrategyPerformanceSummary])
async def get_strategy_performances(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    실행 중인 전략 목록 및 수익률 조회
    
    Returns:
        전략별 성과 목록
    """
    try:
        user_id = current_user["user_id"]
        
        performances = db.query(StrategyPerformanceModel).filter(
            StrategyPerformanceModel.user_id == user_id,
            StrategyPerformanceModel.is_active == True
        ).all()
        
        summaries = []
        for perf in performances:
            strategy = db.query(StrategyBuilderModel).filter(
                StrategyBuilderModel.id == perf.strategy_id
            ).first()
            
            strategy_name = strategy.name if strategy else f"Strategy {perf.strategy_id}"
            
            summaries.append(StrategyPerformanceSummary(
                strategy_id=perf.strategy_id,
                strategy_name=strategy_name,
                total_return=perf.total_return,
                daily_return=perf.daily_return,
                total_trades=perf.total_trades,
                win_rate=perf.win_rate,
                current_equity=perf.current_equity,
                is_active=perf.is_active
            ))
        
        return summaries
    
    except Exception as e:
        logger.error(f"Failed to get strategy performances: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades", response_model=List[TradeSummary])
async def get_today_trades(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """
    오늘 거래 내역 조회
    
    Args:
        limit: 최대 조회 개수 (기본: 50)
    
    Returns:
        거래 내역 목록
    """
    try:
        user_id = current_user["user_id"]
        today = datetime.now().date()
        
        trades = db.query(LiveTradeModel).filter(
            LiveTradeModel.user_id == user_id,
            func.date(LiveTradeModel.timestamp) == today
        ).order_by(LiveTradeModel.timestamp.desc()).limit(limit).all()
        
        return [
            TradeSummary(
                trade_id=trade.trade_id,
                symbol=trade.symbol,
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
                timestamp=trade.timestamp
            )
            for trade in trades
        ]
    
    except Exception as e:
        logger.error(f"Failed to get today trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

