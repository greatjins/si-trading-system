"""
알림 관리자
"""
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from collections import deque

from utils.logger import setup_logger

logger = setup_logger(__name__)


class NotificationType(Enum):
    """알림 타입"""
    ORDER_FILLED = "order_filled"  # 주문 체결
    PROFIT = "profit"  # 수익 발생
    LOSS = "loss"  # 손실 발생
    ERROR = "error"  # 에러 발생
    RISK_LIMIT = "risk_limit"  # 리스크 한도 초과
    STRATEGY_STARTED = "strategy_started"  # 전략 시작
    STRATEGY_STOPPED = "strategy_stopped"  # 전략 중지


@dataclass
class Notification:
    """알림 데이터 클래스"""
    id: str
    type: NotificationType
    title: str
    message: str
    timestamp: datetime
    read: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read,
            "metadata": self.metadata
        }


class NotificationManager:
    """
    알림 관리자
    
    알림을 저장하고 전송하는 역할을 담당합니다.
    메모리 기반 저장소를 사용하며, 필요시 DB로 확장 가능합니다.
    """
    
    def __init__(self, max_notifications: int = 1000):
        """
        Args:
            max_notifications: 최대 저장 알림 개수 (오래된 알림 자동 삭제)
        """
        self.max_notifications = max_notifications
        self.notifications: deque = deque(maxlen=max_notifications)
        self._notification_id_counter = 0
        
        # 알림 전송 콜백 리스트
        self._send_callbacks: List[Callable[[Notification], None]] = []
        
        logger.info(f"NotificationManager initialized (max: {max_notifications})")
    
    def add_send_callback(self, callback: Callable[[Notification], None]) -> None:
        """
        알림 전송 콜백 추가
        
        Args:
            callback: 알림이 생성될 때 호출될 함수
        """
        self._send_callbacks.append(callback)
        logger.debug(f"Added notification send callback: {callback.__name__}")
    
    def notify(
        self,
        type: NotificationType,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        알림 생성 및 저장
        
        Args:
            type: 알림 타입
            title: 알림 제목
            message: 알림 메시지
            metadata: 추가 메타데이터
        
        Returns:
            생성된 알림 객체
        """
        notification_id = f"notif_{self._notification_id_counter}"
        self._notification_id_counter += 1
        
        notification = Notification(
            id=notification_id,
            type=type,
            title=title,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # 알림 저장
        self.notifications.append(notification)
        
        # 콜백 호출 (WebSocket, Email 등)
        for callback in self._send_callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Error in notification callback {callback.__name__}: {e}")
        
        logger.info(f"Notification created: {type.value} - {title}")
        
        return notification
    
    def notify_order_filled(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: float
    ) -> Notification:
        """주문 체결 알림"""
        return self.notify(
            type=NotificationType.ORDER_FILLED,
            title="주문 체결",
            message=f"{symbol} {side} {quantity}주 @ {price:,.0f}원 체결",
            metadata={
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price
            }
        )
    
    def notify_profit(
        self,
        symbol: str,
        profit: float,
        profit_rate: float
    ) -> Notification:
        """수익 발생 알림"""
        return self.notify(
            type=NotificationType.PROFIT,
            title="수익 발생",
            message=f"{symbol} 수익: {profit:+,.0f}원 ({profit_rate:+.2%})",
            metadata={
                "symbol": symbol,
                "profit": profit,
                "profit_rate": profit_rate
            }
        )
    
    def notify_loss(
        self,
        symbol: str,
        loss: float,
        loss_rate: float
    ) -> Notification:
        """손실 발생 알림"""
        return self.notify(
            type=NotificationType.LOSS,
            title="손실 발생",
            message=f"{symbol} 손실: {loss:+,.0f}원 ({loss_rate:+.2%})",
            metadata={
                "symbol": symbol,
                "loss": loss,
                "loss_rate": loss_rate
            }
        )
    
    def notify_error(
        self,
        strategy_id: Optional[int],
        error_message: str,
        error_type: Optional[str] = None
    ) -> Notification:
        """에러 발생 알림"""
        return self.notify(
            type=NotificationType.ERROR,
            title="전략 에러",
            message=f"전략 {strategy_id or 'Unknown'} 에러: {error_message}",
            metadata={
                "strategy_id": strategy_id,
                "error_message": error_message,
                "error_type": error_type
            }
        )
    
    def notify_risk_limit(
        self,
        limit_type: str,
        current_value: float,
        limit_value: float
    ) -> Notification:
        """리스크 한도 초과 알림"""
        return self.notify(
            type=NotificationType.RISK_LIMIT,
            title="리스크 한도 초과",
            message=f"{limit_type}: {current_value:.2%} > {limit_value:.2%}",
            metadata={
                "limit_type": limit_type,
                "current_value": current_value,
                "limit_value": limit_value
            }
        )
    
    def get_notifications(
        self,
        limit: int = 50,
        unread_only: bool = False,
        type_filter: Optional[NotificationType] = None
    ) -> List[Notification]:
        """
        알림 목록 조회
        
        Args:
            limit: 최대 조회 개수
            unread_only: 읽지 않은 알림만 조회
            type_filter: 특정 타입만 필터링
        
        Returns:
            알림 목록 (최신순)
        """
        notifications = list(self.notifications)
        
        # 필터링
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        if type_filter:
            notifications = [n for n in notifications if n.type == type_filter]
        
        # 최신순 정렬 및 제한
        notifications.sort(key=lambda n: n.timestamp, reverse=True)
        return notifications[:limit]
    
    def mark_as_read(self, notification_id: str) -> bool:
        """
        알림 읽음 처리
        
        Args:
            notification_id: 알림 ID
        
        Returns:
            성공 여부
        """
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                logger.debug(f"Notification marked as read: {notification_id}")
                return True
        
        logger.warning(f"Notification not found: {notification_id}")
        return False
    
    def mark_all_as_read(self) -> int:
        """
        모든 알림 읽음 처리
        
        Returns:
            처리된 알림 개수
        """
        count = 0
        for notification in self.notifications:
            if not notification.read:
                notification.read = True
                count += 1
        
        logger.info(f"Marked {count} notifications as read")
        return count
    
    def get_unread_count(self) -> int:
        """읽지 않은 알림 개수"""
        return sum(1 for n in self.notifications if not n.read)
    
    def clear(self) -> None:
        """모든 알림 삭제"""
        self.notifications.clear()
        logger.info("All notifications cleared")

