"""
데이터 수집기
"""
from typing import List, Optional
from datetime import datetime

from broker.base import BrokerBase
from data.cache import RedisCache
from data.storage import FileStorage
from utils.types import OHLC
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataCollector:
    """
    시장 데이터 수집 및 캐싱
    
    캐시 우선 검색 전략:
    1. Redis 캐시 확인
    2. 파일 저장소 확인
    3. 브로커에서 가져오기
    4. 캐시 및 저장소에 저장
    """
    
    def __init__(
        self,
        broker: BrokerBase,
        cache: Optional[RedisCache] = None,
        storage: Optional[FileStorage] = None
    ):
        """
        Args:
            broker: 브로커 어댑터
            cache: Redis 캐시 (None이면 캐시 비활성화)
            storage: 파일 저장소 (None이면 저장소 비활성화)
        """
        self.broker = broker
        self.cache = cache
        self.storage = storage
        
        logger.info("DataCollector initialized")
    
    async def get_ohlc(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime,
        use_cache: bool = True
    ) -> List[OHLC]:
        """
        OHLC 데이터 가져오기 (캐시 우선)
        
        Args:
            symbol: 종목코드
            interval: 시간 간격
            start_date: 시작일
            end_date: 종료일
            use_cache: 캐시 사용 여부
        
        Returns:
            OHLC 데이터
        """
        logger.info(f"Collecting OHLC: {symbol}, {interval}, {start_date.date()} ~ {end_date.date()}")
        
        # 1. Redis 캐시 확인
        if use_cache and self.cache:
            cached_data = await self.cache.get_ohlc(symbol, interval, start_date, end_date)
            if cached_data:
                logger.info(f"✓ Data from Redis cache ({len(cached_data)} bars)")
                return cached_data
        
        # 2. 파일 저장소 확인
        if use_cache and self.storage:
            stored_data = await self.storage.load_ohlc(symbol, interval, start_date, end_date)
            if stored_data:
                logger.info(f"✓ Data from file storage ({len(stored_data)} bars)")
                
                # Redis 캐시에 저장
                if self.cache:
                    await self.cache.set_ohlc(symbol, interval, stored_data, start_date, end_date)
                
                return stored_data
        
        # 3. 브로커에서 가져오기
        logger.info("Fetching from broker...")
        data = await self.broker.get_ohlc(symbol, interval, start_date, end_date)
        
        if not data:
            logger.warning(f"No data received from broker")
            return []
        
        logger.info(f"✓ Data from broker ({len(data)} bars)")
        
        # 4. 캐시 및 저장소에 저장
        if self.cache:
            await self.cache.set_ohlc(symbol, interval, data, start_date, end_date)
        
        if self.storage:
            await self.storage.save_ohlc(symbol, interval, data)
        
        return data
    
    async def get_current_price(
        self,
        symbol: str,
        use_cache: bool = True,
        cache_ttl: int = 5
    ) -> float:
        """
        현재가 가져오기 (캐시 우선)
        
        Args:
            symbol: 종목코드
            use_cache: 캐시 사용 여부
            cache_ttl: 캐시 TTL (초)
        
        Returns:
            현재가
        """
        # 1. Redis 캐시 확인
        if use_cache and self.cache:
            cached_price = await self.cache.get_price(symbol)
            if cached_price is not None:
                logger.debug(f"Price from cache: {symbol} = {cached_price}")
                return cached_price
        
        # 2. 브로커에서 가져오기
        price = await self.broker.get_current_price(symbol)
        
        # 3. 캐시에 저장
        if self.cache:
            await self.cache.set_price(symbol, price, ttl=cache_ttl)
        
        return price
    
    async def refresh_cache(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> bool:
        """
        캐시 강제 새로고침
        
        Args:
            symbol: 종목코드
            interval: 시간 간격
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            새로고침 성공 여부
        """
        logger.info(f"Refreshing cache: {symbol}, {interval}")
        
        try:
            # 브로커에서 최신 데이터 가져오기
            data = await self.broker.get_ohlc(symbol, interval, start_date, end_date)
            
            if not data:
                return False
            
            # 캐시 및 저장소 업데이트
            if self.cache:
                await self.cache.set_ohlc(symbol, interval, data, start_date, end_date)
            
            if self.storage:
                await self.storage.save_ohlc(symbol, interval, data)
            
            logger.info(f"Cache refreshed: {len(data)} bars")
            return True
        
        except Exception as e:
            logger.error(f"Failed to refresh cache: {e}")
            return False
    
    async def clear_cache(self, pattern: str = "*") -> int:
        """
        캐시 삭제
        
        Args:
            pattern: 삭제할 키 패턴
        
        Returns:
            삭제된 키 개수
        """
        if self.cache:
            return await self.cache.clear(pattern)
        return 0
    
    def get_storage_info(self) -> dict:
        """
        저장소 정보 조회
        
        Returns:
            저장소 정보 딕셔너리
        """
        if not self.storage:
            return {}
        
        symbols = self.storage.list_symbols()
        size_bytes = self.storage.get_storage_size()
        size_mb = size_bytes / (1024 * 1024)
        
        return {
            "symbols_count": len(symbols),
            "symbols": symbols,
            "size_bytes": size_bytes,
            "size_mb": round(size_mb, 2)
        }
