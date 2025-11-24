"""
브로커 연결 풀 관리
"""
from typing import Dict, Optional
import asyncio
from datetime import datetime, timedelta

from broker.ls.adapter import LSAdapter
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BrokerConnectionPool:
    """브로커 연결 풀 - 싱글톤"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._connections: Dict[str, Dict] = {}  # key: f"{broker}_{account_id}"
        self._last_used: Dict[str, datetime] = {}
        
        # 설정 (config.yaml 또는 환경변수 또는 기본값)
        import os
        from utils.config import config
        
        self._cleanup_interval = int(
            os.getenv("CONNECTION_CLEANUP_INTERVAL") or 
            config.get("connection_pool.cleanup_interval", 120)
        )  # 기본 2분
        
        self._max_idle_time = int(
            os.getenv("CONNECTION_MAX_IDLE_TIME") or 
            config.get("connection_pool.max_idle_time", 300)
        )  # 기본 5분
        
        self._initialized = True
        
        logger.info(f"BrokerConnectionPool initialized (cleanup: {self._cleanup_interval}s, max_idle: {self._max_idle_time}s)")
    
    def _get_key(self, broker: str, account_id: str) -> str:
        """연결 키 생성"""
        return f"{broker}_{account_id}"
    
    async def get_adapter(
        self,
        broker: str,
        account_id: str,
        api_key: str,
        api_secret: str,
        paper_trading: bool = False
    ) -> LSAdapter:
        """
        Adapter 가져오기 (재사용 또는 새로 생성)
        
        Args:
            broker: 브로커 이름
            account_id: 계좌번호
            api_key: API 키
            api_secret: API 시크릿
            paper_trading: 모의투자 여부
            
        Returns:
            Adapter 인스턴스
        """
        async with self._lock:
            key = self._get_key(broker, account_id)
            
            # 기존 연결 확인
            if key in self._connections:
                conn_info = self._connections[key]
                adapter = conn_info["adapter"]
                
                # 연결 상태 확인
                if conn_info["connected"]:
                    self._last_used[key] = datetime.now()
                    logger.debug(f"Reusing connection: {key}")
                    return adapter
                else:
                    # 연결이 끊어진 경우 재연결
                    logger.info(f"Reconnecting: {key}")
                    await adapter.__aenter__()
                    conn_info["connected"] = True
                    self._last_used[key] = datetime.now()
                    return adapter
            
            # 새 연결 생성
            logger.info(f"Creating new connection: {key}")
            
            if broker == "ls":
                adapter = LSAdapter(
                    api_key=api_key,
                    api_secret=api_secret,
                    account_id=account_id,
                    paper_trading=paper_trading
                )
                
                # 연결
                await adapter.__aenter__()
                
                # 풀에 저장
                self._connections[key] = {
                    "adapter": adapter,
                    "connected": True,
                    "broker": broker,
                    "account_id": account_id,
                }
                self._last_used[key] = datetime.now()
                
                return adapter
            else:
                raise ValueError(f"Unsupported broker: {broker}")
    
    async def release_adapter(self, broker: str, account_id: str):
        """
        Adapter 반환 (연결은 유지)
        
        Args:
            broker: 브로커 이름
            account_id: 계좌번호
        """
        key = self._get_key(broker, account_id)
        self._last_used[key] = datetime.now()
        logger.debug(f"Released connection: {key}")
    
    async def close_adapter(self, broker: str, account_id: str):
        """
        Adapter 연결 종료
        
        Args:
            broker: 브로커 이름
            account_id: 계좌번호
        """
        async with self._lock:
            key = self._get_key(broker, account_id)
            
            if key in self._connections:
                conn_info = self._connections[key]
                adapter = conn_info["adapter"]
                
                if conn_info["connected"]:
                    await adapter.__aexit__(None, None, None)
                    conn_info["connected"] = False
                
                del self._connections[key]
                if key in self._last_used:
                    del self._last_used[key]
                
                logger.info(f"Closed connection: {key}")
    
    async def cleanup_idle_connections(self):
        """유휴 연결 정리"""
        async with self._lock:
            now = datetime.now()
            keys_to_remove = []
            
            for key, last_used in self._last_used.items():
                idle_time = (now - last_used).total_seconds()
                
                if idle_time > self._max_idle_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                conn_info = self._connections[key]
                adapter = conn_info["adapter"]
                
                if conn_info["connected"]:
                    await adapter.__aexit__(None, None, None)
                
                del self._connections[key]
                del self._last_used[key]
                
                logger.info(f"Cleaned up idle connection: {key}")
    
    async def close_user_connections(self, user_account_ids: list):
        """
        특정 사용자의 모든 연결 종료
        
        Args:
            user_account_ids: 사용자의 계좌번호 리스트
        """
        async with self._lock:
            keys_to_remove = []
            
            for key, conn_info in self._connections.items():
                if conn_info["account_id"] in user_account_ids:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                conn_info = self._connections[key]
                adapter = conn_info["adapter"]
                
                if conn_info["connected"]:
                    await adapter.__aexit__(None, None, None)
                
                del self._connections[key]
                if key in self._last_used:
                    del self._last_used[key]
                
                logger.info(f"Closed user connection: {key}")
    
    async def close_all(self):
        """모든 연결 종료"""
        async with self._lock:
            for key, conn_info in self._connections.items():
                adapter = conn_info["adapter"]
                
                if conn_info["connected"]:
                    await adapter.__aexit__(None, None, None)
                
                logger.info(f"Closed connection: {key}")
            
            self._connections.clear()
            self._last_used.clear()
    
    def get_stats(self) -> Dict:
        """연결 풀 통계"""
        return {
            "total_connections": len(self._connections),
            "active_connections": sum(1 for c in self._connections.values() if c["connected"]),
            "connections": [
                {
                    "key": key,
                    "broker": info["broker"],
                    "account_id": info["account_id"],
                    "connected": info["connected"],
                    "last_used": self._last_used.get(key),
                }
                for key, info in self._connections.items()
            ]
        }


# 싱글톤 인스턴스
connection_pool = BrokerConnectionPool()
