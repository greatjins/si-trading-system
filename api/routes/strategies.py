"""
전략 관리 API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from core.strategy.registry import StrategyRegistry
from api.schemas import StrategyListResponse, StrategyDetailResponse, MessageResponse
from api.dependencies import get_db
from sqlalchemy.orm import Session
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# 전략 실행 상태 스키마
class StrategyStatusResponse(BaseModel):
    """전략 실행 상태 응답"""
    strategy_id: int
    is_running: bool
    last_execution_time: Optional[datetime]
    next_execution_time: Optional[datetime]
    error_count: int
    last_error: Optional[str]
    status: str  # "running", "stopped", "error"


@router.get("/list", response_model=List[StrategyListResponse])
async def list_strategies():
    """
    등록된 전략 목록 조회
    
    Returns:
        전략 목록
    """
    try:
        strategies = StrategyRegistry.list_metadata()
        
        return [
            StrategyListResponse(
                name=s["name"],
                description=s["description"],
                author=s["author"],
                version=s["version"]
            )
            for s in strategies
        ]
    
    except Exception as e:
        logger.error(f"Failed to list strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_name}", response_model=StrategyDetailResponse)
async def get_strategy_detail(strategy_name: str):
    """
    전략 상세 정보 조회
    
    Args:
        strategy_name: 전략 이름
        
    Returns:
        전략 상세 정보
    """
    try:
        metadata = StrategyRegistry.get_metadata(strategy_name)
        
        return StrategyDetailResponse(
            name=metadata.name,
            description=metadata.description,
            author=metadata.author,
            version=metadata.version,
            parameters=metadata.parameters,
            class_name=metadata.strategy_class.__name__,
            module=metadata.strategy_class.__module__
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get strategy detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discover", response_model=MessageResponse)
async def discover_strategies():
    """
    전략 자동 탐색 및 등록
    
    Returns:
        탐색 결과
    """
    try:
        # 기존 전략 클리어
        StrategyRegistry.clear()
        
        # 자동 탐색
        StrategyRegistry.auto_discover("core.strategy.examples")
        
        strategies = StrategyRegistry.list_strategies()
        
        logger.info(f"Discovered {len(strategies)} strategies")
        
        return MessageResponse(
            message=f"Discovered {len(strategies)} strategies: {', '.join(strategies)}",
            success=True
        )
    
    except Exception as e:
        logger.error(f"Failed to discover strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload", response_model=MessageResponse)
async def reload_strategies():
    """
    전략 재로드
    
    Returns:
        재로드 결과
    """
    try:
        # 기존 전략 클리어
        StrategyRegistry.clear()
        
        # 자동 탐색
        StrategyRegistry.auto_discover("core.strategy.examples")
        
        strategies = StrategyRegistry.list_strategies()
        
        logger.info(f"Reloaded {len(strategies)} strategies")
        
        return MessageResponse(
            message=f"Reloaded {len(strategies)} strategies",
            success=True
        )
    
    except Exception as e:
        logger.error(f"Failed to reload strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}/status", response_model=StrategyStatusResponse)
async def get_strategy_status(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """
    전략 실행 상태 조회 (Phase 3.2)
    
    Args:
        strategy_id: 전략 ID
    
    Returns:
        전략 실행 상태
    """
    try:
        # TODO: ExecutionEngine 인스턴스를 전략 ID로 찾는 로직 필요
        # 현재는 간단한 구현으로 DB에서 전략 정보만 조회
        
        from data.models import StrategyBuilderModel
        strategy = db.query(StrategyBuilderModel).filter(
            StrategyBuilderModel.id == strategy_id
        ).first()
        
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # 간단한 구현: 전략이 활성화되어 있으면 실행 중으로 간주
        # 실제로는 ExecutionEngine 인스턴스에서 상태를 가져와야 함
        is_running = strategy.is_active
        
        return StrategyStatusResponse(
            strategy_id=strategy_id,
            is_running=is_running,
            last_execution_time=None,  # TODO: ExecutionEngine에서 가져오기
            next_execution_time=None,  # TODO: 스케줄러에서 가져오기
            error_count=0,  # TODO: ExecutionEngine에서 가져오기
            last_error=None,  # TODO: ExecutionEngine에서 가져오기
            status="running" if is_running else "stopped"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
