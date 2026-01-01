/**
 * 알림 센터 컴포넌트
 */
import { useEffect, useState } from 'react';
import {
  getNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  getUnreadCount,
  Notification
} from '../services/notificationApi';
import { LoadingSpinner } from '../../../components/UI/LoadingSpinner';
import { ErrorMessage } from '../../../components/UI/ErrorMessage';
import './NotificationCenter.css';

export const NotificationCenter = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNotifications();
    // 5초마다 자동 갱신
    const interval = setInterval(loadNotifications, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadNotifications = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [notificationsData, unreadCountData] = await Promise.all([
        getNotifications(50, false),
        getUnreadCount()
      ]);
      setNotifications(notificationsData.notifications);
      setUnreadCount(unreadCountData);
    } catch (err: any) {
      setError(err.message || '알림을 불러오는데 실패했습니다.');
      console.error('Notification load error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await markNotificationAsRead(notificationId);
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err: any) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await markAllNotificationsAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (err: any) {
      console.error('Failed to mark all notifications as read:', err);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'order_filled':
        return '✓';
      case 'profit':
        return '↑';
      case 'loss':
        return '↓';
      case 'error':
        return '⚠';
      case 'risk_limit':
        return '🚨';
      case 'strategy_started':
        return '▶';
      case 'strategy_stopped':
        return '⏸';
      default:
        return '•';
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'order_filled':
        return '#007bff';
      case 'profit':
        return '#28a745';
      case 'loss':
        return '#dc3545';
      case 'error':
        return '#dc3545';
      case 'risk_limit':
        return '#ffc107';
      case 'strategy_started':
        return '#28a745';
      case 'strategy_stopped':
        return '#6c757d';
      default:
        return '#6c757d';
    }
  };

  if (isLoading && notifications.length === 0) {
    return (
      <div className="notification-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error && notifications.length === 0) {
    return (
      <div className="notification-center">
        <ErrorMessage message={error} />
      </div>
    );
  }

  return (
    <div className="notification-center">
      <div className="notification-header">
        <h3>알림</h3>
        <div className="notification-actions">
          {unreadCount > 0 && (
            <button onClick={handleMarkAllAsRead} className="mark-all-read-button">
              모두 읽음 처리
            </button>
          )}
          <button onClick={loadNotifications} className="refresh-button" disabled={isLoading}>
            {isLoading ? '갱신 중...' : '새로고침'}
          </button>
        </div>
      </div>

      {unreadCount > 0 && (
        <div className="unread-badge">
          읽지 않은 알림 {unreadCount}개
        </div>
      )}

      <div className="notification-list">
        {notifications.length === 0 ? (
          <div className="empty-state">
            <p>알림이 없습니다.</p>
          </div>
        ) : (
          notifications.map((notification) => (
            <div
              key={notification.id}
              className={`notification-item ${notification.read ? 'read' : 'unread'}`}
              onClick={() => !notification.read && handleMarkAsRead(notification.id)}
            >
              <div
                className="notification-icon"
                style={{ color: getNotificationColor(notification.type) }}
              >
                {getNotificationIcon(notification.type)}
              </div>
              <div className="notification-content">
                <div className="notification-title">{notification.title}</div>
                <div className="notification-message">{notification.message}</div>
                <div className="notification-time">
                  {new Date(notification.timestamp).toLocaleString()}
                </div>
              </div>
              {!notification.read && <div className="unread-indicator" />}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

