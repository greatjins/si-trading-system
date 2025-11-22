/**
 * 주문 내역 컴포넌트
 */
import { useEffect } from 'react';
import { useOrderStore } from '../../../app/store/orderStore';
import { fetchOrders, cancelOrder } from '../services/orderApi';
import { formatDateTime } from '../../../utils/time';
import { formatNumber } from '../../../utils/formatters';

export const OrderHistory = () => {
  const { orders, setOrders, removeOrder } = useOrderStore();
  
  useEffect(() => {
    const loadOrders = async () => {
      try {
        const data = await fetchOrders();
        setOrders(data);
      } catch (err) {
        console.error('주문 내역 로드 실패:', err);
      }
    };
    
    loadOrders();
  }, [setOrders]);
  
  const handleCancel = async (orderId: string) => {
    if (!confirm('주문을 취소하시겠습니까?')) return;
    
    try {
      await cancelOrder(orderId);
      removeOrder(orderId);
    } catch (err) {
      alert('주문 취소 실패: ' + (err instanceof Error ? err.message : '알 수 없는 오류'));
    }
  };
  
  return (
    <div className="order-history">
      <h3>주문 내역</h3>
      
      {orders.length === 0 ? (
        <div className="empty-state">주문 내역이 없습니다</div>
      ) : (
        <div className="order-table">
          <table>
            <thead>
              <tr>
                <th>시간</th>
                <th>종목</th>
                <th>구분</th>
                <th>유형</th>
                <th>수량</th>
                <th>가격</th>
                <th>상태</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.order_id}>
                  <td>{formatDateTime(order.created_at)}</td>
                  <td>{order.symbol}</td>
                  <td className={order.side === 'buy' ? 'text-buy' : 'text-sell'}>
                    {order.side === 'buy' ? '매수' : '매도'}
                  </td>
                  <td>{order.order_type === 'market' ? '시장가' : '지정가'}</td>
                  <td>{formatNumber(order.quantity)}</td>
                  <td>{order.price ? formatNumber(order.price) : '-'}</td>
                  <td>
                    <span className={`status status-${order.status}`}>
                      {order.status}
                    </span>
                  </td>
                  <td>
                    {(order.status === 'submitted' || order.status === 'pending') && (
                      <button
                        className="btn btn-sm btn-cancel"
                        onClick={() => handleCancel(order.order_id)}
                      >
                        취소
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
