/**
 * 주문 패널 컴포넌트
 */
import { useState } from 'react';
import { useOrderStore } from '../../../app/store/orderStore';
import { useChartStore } from '../../../app/store/chartStore';
import { createOrder } from '../services/orderApi';
import { ORDER_SIDE, ORDER_TYPE } from '../../../constants/order-types';
import { getSymbolName } from '../../../utils/symbols';

export const OrderPanel = () => {
  const { symbol } = useChartStore();
  const symbolName = getSymbolName(symbol);
  const { addOrder } = useOrderStore();
  
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [quantity, setQuantity] = useState<number>(1);
  const [price, setPrice] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    
    console.log('📝 주문 제출:', { symbol, side, orderType, quantity, price });
    
    try {
      const order = await createOrder({
        symbol,
        side,
        order_type: orderType,
        quantity,
        price: orderType === 'limit' ? price : undefined,
      });
      
      console.log('✅ 주문 성공:', order);
      addOrder(order);
      alert(`주문 성공! 주문ID: ${order.order_id}`);
      
      // 폼 초기화
      setQuantity(1);
      setPrice(0);
    } catch (err) {
      console.error('❌ 주문 실패:', err);
      const errorMsg = err instanceof Error ? err.message : '주문 실패';
      setError(errorMsg);
      alert(`주문 실패: ${errorMsg}`);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="order-panel">
      <h3>주문</h3>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>
            종목: {symbol}
            {symbolName ? ` (${symbolName})` : ''}
          </label>
        </div>
        
        <div className="form-group">
          <div className="button-group">
            <button
              type="button"
              className={`btn ${side === ORDER_SIDE.BUY ? 'btn-buy active' : 'btn-buy'}`}
              onClick={() => setSide(ORDER_SIDE.BUY)}
            >
              매수
            </button>
            <button
              type="button"
              className={`btn ${side === ORDER_SIDE.SELL ? 'btn-sell active' : 'btn-sell'}`}
              onClick={() => setSide(ORDER_SIDE.SELL)}
            >
              매도
            </button>
          </div>
        </div>
        
        <div className="form-group">
          <label>주문 유형</label>
          <select
            value={orderType}
            onChange={(e) => setOrderType(e.target.value as 'market' | 'limit')}
            className="form-select"
          >
            <option value={ORDER_TYPE.MARKET}>시장가</option>
            <option value={ORDER_TYPE.LIMIT}>지정가</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>수량</label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            min="1"
            className="form-input"
            required
          />
        </div>
        
        {orderType === ORDER_TYPE.LIMIT && (
          <div className="form-group">
            <label>가격</label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(Number(e.target.value))}
              min="0"
              step="100"
              className="form-input"
              required
            />
          </div>
        )}
        
        {error && <div className="error-message">{error}</div>}
        
        <button
          type="submit"
          className={`btn btn-submit ${side === ORDER_SIDE.BUY ? 'btn-buy' : 'btn-sell'}`}
          disabled={isSubmitting}
        >
          {isSubmitting ? '주문 중...' : side === ORDER_SIDE.BUY ? '매수 주문' : '매도 주문'}
        </button>
      </form>
    </div>
  );
};
