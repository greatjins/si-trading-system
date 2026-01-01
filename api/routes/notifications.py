"""
알림 API
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel

from api.auth.security import get_current_active_user
from core.notifications.manager import NotificationManager, NotificationType
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# 전역 알림 관리자 (실제로는 사용자별로 관리해야 함)
_notification_manager = NotificationManager()


# 스키마
class NotificationResponse(BaseModel):
    """알림 응답"""
    id: str
    type: str
    title: str
    message: str
    timestamp: str
    read: bool
    metadata: dict


class NotificationListResponse(BaseModel):
    """알림 목록 응답"""
    notifications: List[NotificationResponse]
    unread_count: int


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    current_user: dict = Depends(get_current_active_user),
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
    type_filter: Optional[str] = Query(None)
):
    """
    알림 목록 조회
    
    Args:
        limit: 최대 조회 개수
        unread_only: 읽지 않은 알림만 조회
        type_filter: 알림 타입 필터 (order_filled, profit, loss, error 등)
    
    Returns:
        알림 목록 및 읽지 않은 알림 개수
    """
    try:
        # 타입 필터 변환
        notification_type = None
        if type_filter:
            try:
                notification_type = NotificationType(type_filter)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid notification type: {type_filter}"
                )
        
        # 알림 조회
        notifications = _notification_manager.get_notifications(
            limit=limit,
            unread_only=unread_only,
            type_filter=notification_type
        )
        
        # 응답 변환
        notification_responses = [
            NotificationResponse(**n.to_dict())
            for n in notifications
        ]
        
        unread_count = _notification_manager.get_unread_count()
        
        return NotificationListResponse(
            notifications=notification_responses,
            unread_count=unread_count
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    알림 읽음 처리
    
    Args:
        notification_id: 알림 ID
    
    Returns:
        성공 여부
    """
    try:
        success = _notification_manager.mark_as_read(notification_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Notification not found: {notification_id}"
            )
        
        return {"success": True, "message": "Notification marked as read"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/read-all")
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_active_user)
):
    """
    모든 알림 읽음 처리
    
    Returns:
        처리된 알림 개수
    """
    try:
        count = _notification_manager.mark_all_as_read()
        
        return {
            "success": True,
            "message": f"Marked {count} notifications as read",
            "count": count
        }
    
    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_active_user)
):
    """
    읽지 않은 알림 개수 조회
    
    Returns:
        읽지 않은 알림 개수
    """
    try:
        count = _notification_manager.get_unread_count()
        
        return {"unread_count": count}
    
    except Exception as e:
        logger.error(f"Failed to get unread count: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

