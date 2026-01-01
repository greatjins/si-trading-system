/**
 * 알림 API 서비스
 */
import { httpClient } from '../../../services/http';

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  metadata: Record<string, any>;
}

export interface NotificationListResponse {
  notifications: Notification[];
  unread_count: number;
}

/**
 * 알림 목록 조회
 */
export const getNotifications = async (
  limit: number = 50,
  unread_only: boolean = false,
  type_filter?: string
): Promise<NotificationListResponse> => {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  params.append('unread_only', unread_only.toString());
  if (type_filter) {
    params.append('type_filter', type_filter);
  }
  
  const response = await httpClient.get<NotificationListResponse>(
    `/api/notifications?${params.toString()}`
  );
  return response.data;
};

/**
 * 알림 읽음 처리
 */
export const markNotificationAsRead = async (notificationId: string): Promise<void> => {
  await httpClient.post(`/api/notifications/${notificationId}/read`);
};

/**
 * 모든 알림 읽음 처리
 */
export const markAllNotificationsAsRead = async (): Promise<number> => {
  const response = await httpClient.post<{ count: number }>('/api/notifications/read-all');
  return response.data.count;
};

/**
 * 읽지 않은 알림 개수 조회
 */
export const getUnreadCount = async (): Promise<number> => {
  const response = await httpClient.get<{ unread_count: number }>('/api/notifications/unread-count');
  return response.data.unread_count;
};

