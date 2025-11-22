"""
WebSocket 메시지 핸들러
"""
from typing import Dict, Any
import asyncio

from api.websocket.manager import manager
from broker.mock.adapter import MockBroker
from data.repository import DataRepository
from utils.logger import setup_logger

logger = setup_logger(__name__)


class WebSocketHandler:
    """WebSocket 메시지 핸들러"""
    
    def __init__(self):
        self.broker = MockBroker()
        self.data_repo = DataRepository()
        self.handlers = {
            "subscribe": self.handle_subscribe,
            "unsubscribe": self.handle_unsubscribe,
            "ping": self.handle_ping,
            "get_price": self.handle_get_price,
            "get_account": self.handle_get_account,
        }
    
    async def handle_message(self, message: Dict[str, Any], user_id: str):
        """
        메시지 처리
        
        Args:
            message: 수신한 메시지
            user_id: 사용자 ID
        """
        msg_type = message.get("type")
        
        if msg_type not in self.handlers:
            await manager.send_personal_message({
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            }, user_id)
            return
        
        try:
            await self.handlers[msg_type](message, user_id)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await manager.send_personal_message({
                "type": "error",
                "message": str(e)
            }, user_id)
    
    async def handle_subscribe(self, message: Dict[str, Any], user_id: str):
        """
        구독 요청 처리
        
        Args:
            message: {"type": "subscribe", "topic": "price:005930"}
            user_id: 사용자 ID
        """
        topic = message.get("topic")
        
        if not topic:
            await manager.send_personal_message({
                "type": "error",
                "message": "Topic is required"
            }, user_id)
            return
        
        await manager.subscribe(user_id, topic)
        
        await manager.send_personal_message({
            "type": "subscribed",
            "topic": topic,
            "message": f"Successfully subscribed to {topic}"
        }, user_id)
    
    async def handle_unsubscribe(self, message: Dict[str, Any], user_id: str):
        """
        구독 해제 요청 처리
        
        Args:
            message: {"type": "unsubscribe", "topic": "price:005930"}
            user_id: 사용자 ID
        """
        topic = message.get("topic")
        
        if not topic:
            await manager.send_personal_message({
                "type": "error",
                "message": "Topic is required"
            }, user_id)
            return
        
        await manager.unsubscribe(user_id, topic)
        
        await manager.send_personal_message({
            "type": "unsubscribed",
            "topic": topic,
            "message": f"Successfully unsubscribed from {topic}"
        }, user_id)
    
    async def handle_ping(self, message: Dict[str, Any], user_id: str):
        """
        Ping 요청 처리
        
        Args:
            message: {"type": "ping"}
            user_id: 사용자 ID
        """
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": message.get("timestamp")
        }, user_id)
    
    async def handle_get_price(self, message: Dict[str, Any], user_id: str):
        """
        현재가 조회 요청 처리
        
        Args:
            message: {"type": "get_price", "symbol": "005930"}
            user_id: 사용자 ID
        """
        symbol = message.get("symbol")
        
        if not symbol:
            await manager.send_personal_message({
                "type": "error",
                "message": "Symbol is required"
            }, user_id)
            return
        
        try:
            # 최근 데이터 조회
            data = self.data_repo.get_ohlc(symbol=symbol, interval="1d")
            
            if data.empty:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"No data found for {symbol}"
                }, user_id)
                return
            
            latest = data.iloc[-1]
            
            await manager.send_personal_message({
                "type": "price",
                "symbol": symbol,
                "data": {
                    "price": float(latest["close"]),
                    "open": float(latest["open"]),
                    "high": float(latest["high"]),
                    "low": float(latest["low"]),
                    "volume": int(latest["volume"]),
                    "timestamp": latest.name.isoformat()
                }
            }, user_id)
        
        except Exception as e:
            logger.error(f"Failed to get price: {e}")
            await manager.send_personal_message({
                "type": "error",
                "message": str(e)
            }, user_id)
    
    async def handle_get_account(self, message: Dict[str, Any], user_id: str):
        """
        계좌 정보 조회 요청 처리
        
        Args:
            message: {"type": "get_account"}
            user_id: 사용자 ID
        """
        try:
            account = await self.broker.get_account()
            
            await manager.send_personal_message({
                "type": "account",
                "data": {
                    "account_id": account.account_id,
                    "balance": account.balance,
                    "equity": account.equity,
                    "margin_used": account.margin_used,
                    "margin_available": account.margin_available
                }
            }, user_id)
        
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            await manager.send_personal_message({
                "type": "error",
                "message": str(e)
            }, user_id)


# 전역 핸들러
handler = WebSocketHandler()
