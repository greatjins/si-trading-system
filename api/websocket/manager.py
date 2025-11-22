"""
WebSocket 연결 관리자
"""
from typing import Dict, Set, List
from fastapi import WebSocket
import json
import asyncio

from utils.logger import setup_logger

logger = setup_logger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 활성 연결: {user_id: Set[WebSocket]}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # 구독 관리: {topic: Set[user_id]}
        self.subscriptions: Dict[str, Set[str]] = {}
        
        # 사용자별 구독: {user_id: Set[topic]}
        self.user_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        WebSocket 연결
        
        Args:
            websocket: WebSocket 인스턴스
            user_id: 사용자 ID
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        logger.info(f"WebSocket connected: user={user_id}, total={len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        WebSocket 연결 해제
        
        Args:
            websocket: WebSocket 인스턴스
            user_id: 사용자 ID
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # 사용자 구독 정리
                if user_id in self.user_subscriptions:
                    for topic in self.user_subscriptions[user_id]:
                        if topic in self.subscriptions:
                            self.subscriptions[topic].discard(user_id)
                    del self.user_subscriptions[user_id]
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def subscribe(self, user_id: str, topic: str):
        """
        토픽 구독
        
        Args:
            user_id: 사용자 ID
            topic: 구독할 토픽 (예: "price:005930", "order:*", "strategy:123")
        """
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        
        self.subscriptions[topic].add(user_id)
        
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        self.user_subscriptions[user_id].add(topic)
        
        logger.info(f"Subscribed: user={user_id}, topic={topic}")
    
    async def unsubscribe(self, user_id: str, topic: str):
        """
        토픽 구독 해제
        
        Args:
            user_id: 사용자 ID
            topic: 구독 해제할 토픽
        """
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(user_id)
            
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(topic)
        
        logger.info(f"Unsubscribed: user={user_id}, topic={topic}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """
        특정 사용자에게 메시지 전송
        
        Args:
            message: 전송할 메시지
            user_id: 사용자 ID
        """
        if user_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        
        # 해당 사용자의 모든 연결에 전송
        disconnected = []
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                disconnected.append(websocket)
        
        # 실패한 연결 제거
        for websocket in disconnected:
            self.disconnect(websocket, user_id)
    
    async def broadcast_to_topic(self, message: dict, topic: str):
        """
        토픽 구독자들에게 브로드캐스트
        
        Args:
            message: 전송할 메시지
            topic: 토픽
        """
        if topic not in self.subscriptions:
            return
        
        # 토픽 구독자들에게 전송
        for user_id in self.subscriptions[topic]:
            await self.send_personal_message(message, user_id)
    
    async def broadcast_all(self, message: dict):
        """
        모든 연결에 브로드캐스트
        
        Args:
            message: 전송할 메시지
        """
        message_json = json.dumps(message)
        
        for user_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.error(f"Failed to broadcast to user {user_id}: {e}")
    
    def get_active_users(self) -> List[str]:
        """
        활성 사용자 목록 조회
        
        Returns:
            사용자 ID 리스트
        """
        return list(self.active_connections.keys())
    
    def get_user_subscriptions(self, user_id: str) -> List[str]:
        """
        사용자 구독 목록 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            구독 토픽 리스트
        """
        if user_id not in self.user_subscriptions:
            return []
        
        return list(self.user_subscriptions[user_id])
    
    def get_topic_subscribers(self, topic: str) -> List[str]:
        """
        토픽 구독자 목록 조회
        
        Args:
            topic: 토픽
            
        Returns:
            구독자 사용자 ID 리스트
        """
        if topic not in self.subscriptions:
            return []
        
        return list(self.subscriptions[topic])


# 전역 연결 관리자
manager = ConnectionManager()
