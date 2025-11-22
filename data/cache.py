"""
Redis 캐시 구현
"""
import json
import pickle
from typing import List, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis

from utils.types import OHLC
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


class RedisCache:
    """
    Redis 기반 캐시
    
    OHLC 데이터 및 실시간 가격을 캐싱합니다.
    """
    
    def __init__(
        self,
        redis_url: str = None,
        ttl_seconds: int = None
    ):
        """
        Args:
            redis_url: Redis 연결 URL (None이면 config에서 로드)
            ttl_seconds: 캐시 TTL (초, None이면 config에서 로드)
        """
        self.redis_url = redis_url or config.get("cache.redis_url", "redis://localhost:6379")
        self.ttl_seconds = ttl_seconds or config.get("cache.ttl_seconds", 300)
        
        self.client: Optional[redis.Redis] = None
        
        logger.info(f"RedisCache initialized with TTL: {self.ttl_seconds}s")
    
    async def connect(self) -> None:
        """Redis 연결"""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False
            )
            await self.client.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            logger.warning("Cache will be disabled")
            self.client = None
    
    async def close(self) -> None:
        """Redis 연결 종료"""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Redis disconnected")
    
    async def __aenter__(self) -> "RedisCache":
        """비동기 컨텍스트 매니저 진입"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """비동기 컨텍스트 매니저 종료"""
        await self.close()
    
    def _make_ohlc_key(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """OHLC 캐시 키 생성"""
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        return f"ohlc:{symbol}:{interval}:{start_str}:{end_str}"
    
    def _make_price_key(self, symbol: str) -> str:
        """현재가 캐시 키 생성"""
        return f"price:{symbol}"
    
    async def get_ohlc(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[List[OHLC]]:
        """
        OHLC 데이터 조회
        
        Args:
            symbol: 종목코드
            interval: 시간 간격
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            캐시된 OHLC 데이터 (없으면 None)
        """
        if not self.client:
            return None
        
        key = self._make_ohlc_key(symbol, interval, start_date, end_date)
        
        try:
            data = await self.client.get(key)
            if data:
                ohlc_list = pickle.loads(data)
                logger.debug(f"Cache HIT: {key}")
                return ohlc_list
            
            logger.debug(f"Cache MISS: {key}")
            return None
        
        except Exception as e:
            logger.warning(f"Failed to get from cache: {e}")
            return None
    
    async def set_ohlc(
        self,
        symbol: str,
        interval: str,
        ohlc_data: List[OHLC],
        start_date: datetime = None,
        end_date: datetime = None
    ) -> bool:
        """
        OHLC 데이터 저장
        
        Args:
            symbol: 종목코드
            interval: 시간 간격
            ohlc_data: OHLC 데이터
            start_date: 시작일 (None이면 데이터에서 추출)
            end_date: 종료일 (None이면 데이터에서 추출)
        
        Returns:
            저장 성공 여부
        """
        if not self.client or not ohlc_data:
            return False
        
        # 날짜 추출
        if start_date is None:
            start_date = ohlc_data[0].timestamp
        if end_date is None:
            end_date = ohlc_data[-1].timestamp
        
        key = self._make_ohlc_key(symbol, interval, start_date, end_date)
        
        try:
            data = pickle.dumps(ohlc_data)
            await self.client.setex(key, self.ttl_seconds, data)
            logger.debug(f"Cache SET: {key}")
            return True
        
        except Exception as e:
            logger.warning(f"Failed to set cache: {e}")
            return False
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """
        현재가 조회
        
        Args:
            symbol: 종목코드
        
        Returns:
            캐시된 현재가 (없으면 None)
        """
        if not self.client:
            return None
        
        key = self._make_price_key(symbol)
        
        try:
            data = await self.client.get(key)
            if data:
                price = float(data)
                logger.debug(f"Price cache HIT: {symbol}")
                return price
            
            return None
        
        except Exception as e:
            logger.warning(f"Failed to get price from cache: {e}")
            return None
    
    async def set_price(self, symbol: str, price: float, ttl: int = None) -> bool:
        """
        현재가 저장
        
        Args:
            symbol: 종목코드
            price: 현재가
            ttl: TTL (초, None이면 기본값 사용)
        
        Returns:
            저장 성공 여부
        """
        if not self.client:
            return False
        
        key = self._make_price_key(symbol)
        ttl = ttl or self.ttl_seconds
        
        try:
            await self.client.setex(key, ttl, str(price))
            logger.debug(f"Price cache SET: {symbol} = {price}")
            return True
        
        except Exception as e:
            logger.warning(f"Failed to set price cache: {e}")
            return False
    
    async def clear(self, pattern: str = "*") -> int:
        """
        캐시 삭제
        
        Args:
            pattern: 삭제할 키 패턴
        
        Returns:
            삭제된 키 개수
        """
        if not self.client:
            return 0
        
        try:
            keys = await self.client.keys(pattern)
            if keys:
                deleted = await self.client.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys")
                return deleted
            return 0
        
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
            return 0
