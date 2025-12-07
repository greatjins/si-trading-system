/**
 * 계좌 정보 컴포넌트
 */
import { useEffect, useState } from 'react';
import { useAccountStore } from '../../../app/store/accountStore';
import { httpClient } from '../../../services/http';
import { formatCurrency } from '../../../utils/formatters';

export const AccountInfo = () => {
  const { selectedAccountId, accountBalance, isLoading, setAccountBalance, setLoading, setError } = useAccountStore();
  const [connectionStatus, setConnectionStatus] = useState<any>(null);
  
  useEffect(() => {
    if (!selectedAccountId) return;
    
    // 계좌 잔고 조회
    const loadBalance = async () => {
      setLoading(true);
      try {
        const response = await httpClient.get(`/api/accounts/${selectedAccountId}/balance`);
        setAccountBalance(response.data);
      } catch (error) {
        console.error('계좌 잔고 조회 실패:', error);
        setError('계좌 정보를 불러올 수 없습니다');
      }
    };
    
    loadBalance();
    
    // 주기적으로 업데이트 (30초마다)
    const interval = setInterval(() => {
      loadBalance();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [selectedAccountId, setAccountBalance, setLoading, setError]);
  
  // 연결 상태 조회
  useEffect(() => {
    if (!selectedAccountId) return;
    
    const checkConnection = async () => {
      try {
        const response = await httpClient.get(`/api/accounts/${selectedAccountId}/connection-status`);
        setConnectionStatus(response.data);
      } catch (error) {
        console.error('연결 상태 조회 실패:', error);
      }
    };
    
    checkConnection();
    const interval = setInterval(checkConnection, 10000); // 10초마다
    
    return () => clearInterval(interval);
  }, [selectedAccountId]);
  
  // 연결 종료 핸들러 (향후 사용 예정)
  // const handleDisconnect = async () => {
  //   if (!selectedAccountId) return;
  //   
  //   try {
  //     await httpClient.post(`/api/accounts/${selectedAccountId}/disconnect`);
  //     setConnectionStatus({ connected: false });
  //     alert('연결이 종료되었습니다');
  //   } catch (error) {
  //     console.error('연결 종료 실패:', error);
  //     alert('연결 종료에 실패했습니다');
  //   }
  // };
  
  const handleKeepAlive = async () => {
    if (!selectedAccountId) return;
    
    try {
      await httpClient.post(`/api/accounts/${selectedAccountId}/keep-alive`);
      alert('연결이 갱신되었습니다');
    } catch (error) {
      console.error('연결 갱신 실패:', error);
    }
  };
  
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}분 ${secs}초`;
  };
  
  if (!selectedAccountId) {
    return (
      <div className="account-info">
        <h3>계좌 정보</h3>
        <div className="empty">계좌를 선택해주세요</div>
      </div>
    );
  }
  
  if (isLoading && !accountBalance) {
    return (
      <div className="account-info">
        <h3>계좌 정보</h3>
        <div className="loading">로딩 중...</div>
      </div>
    );
  }
  
  if (!accountBalance) {
    return (
      <div className="account-info">
        <h3>계좌 정보</h3>
        <div className="error">계좌 정보를 불러올 수 없습니다</div>
      </div>
    );
  }
  
  return (
    <div className="account-info">
      <div className="account-header">
        <h3>계좌 정보</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {connectionStatus && (
            <>
              <span 
                className="connection-status" 
                style={{ 
                  fontSize: '12px', 
                  color: connectionStatus.connected ? '#10b981' : '#6b7280',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <span style={{ 
                  width: '8px', 
                  height: '8px', 
                  borderRadius: '50%', 
                  backgroundColor: connectionStatus.connected ? '#10b981' : '#6b7280',
                  display: 'inline-block'
                }} />
                {connectionStatus.connected ? '연결됨' : '연결 안됨'}
                {connectionStatus.connected && connectionStatus.will_disconnect_in > 0 && (
                  <span style={{ marginLeft: '4px', color: '#6b7280' }}>
                    ({formatTime(Math.floor(connectionStatus.will_disconnect_in))} 후)
                  </span>
                )}
              </span>
              {connectionStatus.connected && (
                <button
                  onClick={handleKeepAlive}
                  style={{
                    fontSize: '11px',
                    padding: '2px 8px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    background: 'white',
                    cursor: 'pointer',
                    color: '#6b7280'
                  }}
                  title="연결 유지"
                >
                  🔄
                </button>
              )}
            </>
          )}
          {isLoading && <span className="loading-indicator">🔄</span>}
        </div>
      </div>
      
      <div className="account-grid">
        <div className="account-item">
          <label>계좌번호</label>
          <div className="value">{accountBalance.account_number}</div>
        </div>
        
        <div className="account-item">
          <label>예수금</label>
          <div className="value">{formatCurrency(accountBalance.balance)}원</div>
        </div>
        
        <div className="account-item">
          <label>순자산</label>
          <div className="value highlight">{formatCurrency(accountBalance.equity)}원</div>
        </div>
        
        <div className="account-item">
          <label>매수가능</label>
          <div className="value">{formatCurrency(accountBalance.buying_power)}원</div>
        </div>
        
        <div className="account-item">
          <label>보유종목</label>
          <div className="value">{accountBalance.positions.length}개</div>
        </div>
      </div>
    </div>
  );
};
