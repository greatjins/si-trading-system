"""
전략 관리 API
"""
from fastapi import APIRouter, HTTPException
from typing import List

from core.strategy.registry import StrategyRegistry
from api.schemas import StrategyListResponse, StrategyDetailResponse, MessageResponse
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


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
