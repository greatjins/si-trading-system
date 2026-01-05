"""
서버 시간 동기화 모듈
"""
from typing import Optional
from datetime import datetime, timezone, timedelta
import asyncio

from broker.ls.services.market import LSMarketService
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 전역 변수: 서버 시간과 로컬 시간의 차이 (초 단위)
time_offset: Optional[float] = None
_last_sync_time: Optional[datetime] = None
_sync_interval = 3600  # 1시간마다 동기화 (초)


async def sync_server_time(market_service: LSMarketService) -> None:
    """
    서버 시간과 로컬 시간 동기화
    
    Args:
        market_service: LSMarketService 인스턴스
    """
    global time_offset, _last_sync_time
    
    try:
        # 서버 시간 조회
        server_time = await market_service.get_server_time()
        
        # 로컬 시간 (KST)
        kst = timezone(timedelta(hours=9))
        local_time = datetime.now(kst)
        
        # 시간 차이 계산 (초 단위)
        time_offset = (server_time - local_time).total_seconds()
        
        _last_sync_time = datetime.now()
        
        logger.info(
            f"Server time synced: offset={time_offset:.3f}s "
            f"(server={server_time.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"local={local_time.strftime('%Y-%m-%d %H:%M:%S')})"
        )
    
    except Exception as e:
        logger.error(f"Failed to sync server time: {e}")
        # 동기화 실패 시 time_offset을 None으로 유지 (로컬 시간 사용)


def get_exchange_time() -> datetime:
    """
    거래소 시간 반환 (로컬 시간 + time_offset)
    
    Returns:
        거래소 시간 (datetime 객체, KST)
    """
    global time_offset
    
    kst = timezone(timedelta(hours=9))
    local_time = datetime.now(kst)
    
    # time_offset이 설정되지 않았으면 로컬 시간 반환
    if time_offset is None:
        logger.debug("Time offset not synced, using local time")
        return local_time
    
    # 거래소 시간 = 로컬 시간 + offset
    exchange_time = local_time + timedelta(seconds=time_offset)
    return exchange_time


def is_sync_needed() -> bool:
    """
    시간 동기화가 필요한지 확인
    
    Returns:
        동기화가 필요하면 True
    """
    global _last_sync_time
    
    if _last_sync_time is None:
        return True
    
    elapsed = (datetime.now() - _last_sync_time).total_seconds()
    return elapsed >= _sync_interval


async def ensure_synced(market_service: LSMarketService) -> None:
    """
    시간 동기화 상태 확인 및 필요시 동기화
    
    Args:
        market_service: LSMarketService 인스턴스
    """
    if is_sync_needed():
        await sync_server_time(market_service)

