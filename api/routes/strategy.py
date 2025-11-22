"""
전략 관련 API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
import uuid

from api.schemas import StrategyStartRequest, StrategyResponse, MessageResponse
from api.auth.security import get_current_active_user
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# 실행 중인 전략 저장 (실제로는 DB나 Redis 사용)
running_strategies = {}


@router.post("/start", response_model=StrategyResponse)
async def start_strategy(request: StrategyStartRequest, current_user: dict = Depends(get_current_active_user)):
    """
    전략 시작 (인증 필요)
    
    Args:
        request: 전략 시작 요청
        current_user: 현재 사용자
        
    Returns:
        전략 정보
    """
    try:
        strategy_id = str(uuid.uuid4())
        
        # TODO: 실제 전략 실행 로직 구현
        # ExecutionEngine을 사용하여 전략 시작
        
        strategy_info = {
            "strategy_id": strategy_id,
            "strategy_name": request.strategy_name,
            "parameters": request.parameters,
            "symbols": request.symbols,
            "is_running": True,
            "created_at": datetime.now()
        }
        
        running_strategies[strategy_id] = strategy_info
        
        logger.info(f"Strategy {strategy_id} started: {request.strategy_name}")
        
        return StrategyResponse(**strategy_info)
    
    except Exception as e:
        logger.error(f"Failed to start strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/stop", response_model=MessageResponse)
async def stop_strategy(strategy_id: str):
    """
    전략 중지
    
    Args:
        strategy_id: 전략 ID
        
    Returns:
        중지 결과
    """
    try:
        if strategy_id not in running_strategies:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # TODO: 실제 전략 중지 로직 구현
        
        running_strategies[strategy_id]["is_running"] = False
        
        logger.info(f"Strategy {strategy_id} stopped")
        
        return MessageResponse(
            message=f"Strategy {strategy_id} stopped successfully",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: str):
    """
    전략 조회
    
    Args:
        strategy_id: 전략 ID
        
    Returns:
        전략 정보
    """
    try:
        if strategy_id not in running_strategies:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return StrategyResponse(**running_strategies[strategy_id])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[StrategyResponse])
async def get_strategies():
    """
    전략 목록 조회
    
    Returns:
        전략 리스트
    """
    try:
        return [
            StrategyResponse(**strategy)
            for strategy in running_strategies.values()
        ]
    
    except Exception as e:
        logger.error(f"Failed to get strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
