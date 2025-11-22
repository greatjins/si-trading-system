"""
WebSocket 라우터
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json

from api.websocket.manager import manager
from api.websocket.handlers import handler
from api.websocket.streams import price_streamer
from api.auth.security import decode_token
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket 엔드포인트
    
    Args:
        websocket: WebSocket 연결
        token: JWT 액세스 토큰
    """
    # 토큰 검증
    try:
        payload = decode_token(token)
        user_id = str(payload.get("user_id"))
        username = payload.get("sub")
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # 연결 수락
    await manager.connect(websocket, user_id)
    
    # 환영 메시지
    await manager.send_personal_message({
        "type": "connected",
        "message": f"Welcome {username}!",
        "user_id": user_id
    }, user_id)
    
    # 가격 스트리머 시작 (첫 연결 시)
    if not price_streamer.is_running:
        await price_streamer.start()
    
    try:
        while True:
            # 메시지 수신
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handler.handle_message(message, user_id)
            
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, user_id)
            
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": str(e)
                }, user_id)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected: user={username}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


@router.get("/ws/status")
async def websocket_status():
    """
    WebSocket 상태 조회
    
    Returns:
        활성 연결 정보
    """
    active_users = manager.get_active_users()
    
    return {
        "active_connections": len(active_users),
        "active_users": active_users,
        "subscriptions": {
            topic: manager.get_topic_subscribers(topic)
            for topic in manager.subscriptions.keys()
        },
        "price_streamer_running": price_streamer.is_running
    }
