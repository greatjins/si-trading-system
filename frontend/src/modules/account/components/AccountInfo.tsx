/**
 * 계좌 정보 컴포넌트
 */
import { useEffect } from 'react';
import { useAccountStore } from '../../../app/store/accountStore';
import { useWebSocket } from '../../../hooks/useWebSocket';
import { WS_EVENTS } from '../../../constants/ws-events';
import { formatCurrency } from '../../../utils/formatters';

export const AccountInfo = () => {
  const { account, setAccount } = useAccountStore();
  const { sendMessage, isConnected } = useWebSocket();
  
  useEffect(() => {
    if (!isConnected) return;
    
    // 계좌 정보 요청
    sendMessage({
      type: WS_EVENTS.GET_ACCOUNT,
    });
    
    // 주기적으로 업데이트 (30초마다)
    const interval = setInterval(() => {
      sendMessage({
        type: WS_EVENTS.GET_ACCOUNT,
      });
    }, 30000);
    
    return () => clearInterval(interval);
  }, [isConnected, sendMessage]);
  
  // WebSocket 메시지 수신
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      const message = JSON.parse(event.data);
      
      if (message.type === WS_EVENTS.ACCOUNT) {
        setAccount(message.data);
      }
    };
    
    if (isConnected) {
      window.addEventListener('message', handleMessage);
      return () => window.removeEventListener('message', handleMessage);
    }
  }, [isConnected, setAccount]);
  
  if (!account) {
    return (
      <div className="account-info">
        <h3>계좌 정보</h3>
        <div className="loading">로딩 중...</div>
      </div>
    );
  }
  
  return (
    <div className="account-info">
      <h3>계좌 정보</h3>
      
      <div className="account-grid">
        <div className="account-item">
          <label>계좌번호</label>
          <div className="value">{account.account_id}</div>
        </div>
        
        <div className="account-item">
          <label>예수금</label>
          <div className="value">{formatCurrency(account.balance)}</div>
        </div>
        
        <div className="account-item">
          <label>총 자산</label>
          <div className="value highlight">{formatCurrency(account.equity)}</div>
        </div>
        
        <div className="account-item">
          <label>사용 증거금</label>
          <div className="value">{formatCurrency(account.margin_used)}</div>
        </div>
        
        <div className="account-item">
          <label>가용 증거금</label>
          <div className="value">{formatCurrency(account.margin_available)}</div>
        </div>
      </div>
    </div>
  );
};
