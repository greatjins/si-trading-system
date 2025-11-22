"""
실시간 데이터 스트림
"""
import asyncio
from datetime import datetime
from typing import List
import random

from api.websocket.manager import manager
from data.repository import DataRepository
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PriceStreamer:
    """시세 스트리머"""
    
    def __init__(self):
        self.data_repo = DataRepository()
        self.is_running = False
        self.task = None
    
    async def start(self):
        """스트리밍 시작"""
        if self.is_running:
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._stream_loop())
        logger.info("Price streamer started")
    
    async def stop(self):
        """스트리밍 중지"""
        self.is_running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Price streamer stopped")
    
    async def _stream_loop(self):
        """스트리밍 루프"""
        while self.is_running:
            try:
                # 구독된 종목들 확인
                price_topics = [
                    topic for topic in manager.subscriptions.keys()
                    if topic.startswith("price:")
                ]
                
                for topic in price_topics:
                    symbol = topic.split(":")[1]
                    await self._send_price_update(symbol, topic)
                
                # 1초 대기
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.error(f"Error in price stream loop: {e}")
                await asyncio.sleep(1)
    
    async def _send_price_update(self, symbol: str, topic: str):
        """
        시세 업데이트 전송
        
        Args:
            symbol: 종목 코드
            topic: 토픽
        """
        try:
            # 최근 데이터 조회
            data = self.data_repo.get_ohlc(symbol=symbol, interval="1d")
            
            if data.empty:
                return
            
            latest = data.iloc[-1]
            
            # 실시간 시뮬레이션 (랜덤 변동)
            base_price = float(latest["close"])
            current_price = base_price * (1 + random.uniform(-0.01, 0.01))
            
            message = {
                "type": "price_update",
                "symbol": symbol,
                "data": {
                    "price": round(current_price, 2),
                    "change": round(current_price - base_price, 2),
                    "change_percent": round((current_price / base_price - 1) * 100, 2),
                    "volume": int(latest["volume"]),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await manager.broadcast_to_topic(message, topic)
        
        except Exception as e:
            logger.error(f"Failed to send price update for {symbol}: {e}")


class OrderStreamer:
    """주문 체결 스트리머"""
    
    def __init__(self):
        self.is_running = False
    
    async def send_order_update(self, user_id: str, order_data: dict):
        """
        주문 체결 알림 전송
        
        Args:
            user_id: 사용자 ID
            order_data: 주문 데이터
        """
        message = {
            "type": "order_update",
            "data": order_data
        }
        
        await manager.send_personal_message(message, user_id)
        logger.info(f"Order update sent to user {user_id}: {order_data['order_id']}")


class StrategyStreamer:
    """전략 실행 상태 스트리머"""
    
    def __init__(self):
        self.is_running = False
    
    async def send_strategy_update(self, strategy_id: str, status_data: dict):
        """
        전략 상태 업데이트 전송
        
        Args:
            strategy_id: 전략 ID
            status_data: 상태 데이터
        """
        topic = f"strategy:{strategy_id}"
        
        message = {
            "type": "strategy_update",
            "strategy_id": strategy_id,
            "data": status_data
        }
        
        await manager.broadcast_to_topic(message, topic)
        logger.info(f"Strategy update sent: {strategy_id}")
    
    async def send_strategy_signal(self, strategy_id: str, signal_data: dict):
        """
        전략 시그널 전송
        
        Args:
            strategy_id: 전략 ID
            signal_data: 시그널 데이터
        """
        topic = f"strategy:{strategy_id}"
        
        message = {
            "type": "strategy_signal",
            "strategy_id": strategy_id,
            "data": signal_data
        }
        
        await manager.broadcast_to_topic(message, topic)
        logger.info(f"Strategy signal sent: {strategy_id}")


# 전역 스트리머
price_streamer = PriceStreamer()
order_streamer = OrderStreamer()
strategy_streamer = StrategyStreamer()
