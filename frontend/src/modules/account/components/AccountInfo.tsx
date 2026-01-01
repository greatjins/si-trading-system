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
    
    // 토큰이 있는지 확인
    const hasToken = () => {
      try {
        const authData = sessionStorage.getItem('auth_data');
        if (!authData) return false;
        const tokenData = JSON.parse(authData);
        // 만료 시간에 여유를 둠 (30초 전부터 만료로 간주)
        return tokenData.access_token && Date.now() < (tokenData.expires_at - 30000);
      } catch {
        return false;
      }
    };
    
    let intervalId: NodeJS.Timeout | null = null;
    let retryCount = 0;
    const MAX_RETRIES = 3;
    
    // 계좌 잔고 조회
    const loadBalance = async () => {
      // 토큰이 없으면 요청하지 않음
      if (!hasToken()) {
        console.debug('계좌 잔고 조회 건너뜀: 토큰 없음');
        setError('로그인이 필요합니다');
        setLoading(false);
        retryCount++;
        // 연속으로 3번 실패하면 interval 중지
        if (retryCount >= MAX_RETRIES && intervalId) {
          console.debug('계좌 잔고 조회 중지: 토큰 없음 (3회 연속)');
          clearInterval(intervalId);
          intervalId = null;
        }
        return;
      }
      
      // 성공하면 retryCount 리셋
      retryCount = 0;
      
      setLoading(true);
      try {
        const response = await httpClient.get(`/api/accounts/${selectedAccountId}/balance`);
        setAccountBalance(response.data);
      } catch (error: any) {
        // 403 에러는 인증 문제이므로 조용히 무시
        if (error.response?.status === 403) {
          console.debug('계좌 잔고 조회 실패 (인증 필요):', error.response?.data?.detail);
          setError('로그인이 필요합니다');
          retryCount++;
          // 연속으로 3번 실패하면 interval 중지
          if (retryCount >= MAX_RETRIES && intervalId) {
            console.debug('계좌 잔고 조회 중지: 인증 실패 (3회 연속)');
            clearInterval(intervalId);
            intervalId = null;
          }
          return;
        }
        console.error('계좌 잔고 조회 실패:', error);
        setError('계좌 정보를 불러올 수 없습니다');
      } finally {
        setLoading(false);
      }
    };
    
    // 초기 요청은 약간 지연 (토큰 로드 대기)
    const timeoutId = setTimeout(() => {
      loadBalance();
      // interval 시작 (30초마다)
      intervalId = setInterval(loadBalance, 30000);
    }, 100);
    
    return () => {
      clearTimeout(timeoutId);
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [selectedAccountId, setAccountBalance, setLoading, setError]);
  
  // 연결 상태 조회
  useEffect(() => {
    if (!selectedAccountId) return;
    
    // 토큰이 있는지 확인
    const hasToken = () => {
      try {
        const authData = sessionStorage.getItem('auth_data');
        if (!authData) return false;
        const tokenData = JSON.parse(authData);
        // 만료 시간에 여유를 둠 (30초 전부터 만료로 간주)
        return tokenData.access_token && Date.now() < (tokenData.expires_at - 30000);
      } catch {
        return false;
      }
    };
    
    let intervalId: NodeJS.Timeout | null = null;
    let retryCount = 0;
    const MAX_RETRIES = 3;
    
    const checkConnection = async () => {
      // 토큰이 없으면 요청하지 않음
      if (!hasToken()) {
        console.debug('연결 상태 조회 건너뜀: 토큰 없음');
        retryCount++;
        // 연속으로 3번 실패하면 interval 중지
        if (retryCount >= MAX_RETRIES && intervalId) {
          console.debug('연결 상태 조회 중지: 토큰 없음 (3회 연속)');
          clearInterval(intervalId);
          intervalId = null;
        }
        return;
      }
      
      // 성공하면 retryCount 리셋
      retryCount = 0;
      
      try {
        const response = await httpClient.get(`/api/accounts/${selectedAccountId}/connection-status`);
        setConnectionStatus(response.data);
      } catch (error: any) {
        // 403 에러는 인증 문제이므로 조용히 무시
        if (error.response?.status === 403) {
          console.debug('연결 상태 조회 실패 (인증 필요):', error.response?.data?.detail);
          retryCount++;
          // 연속으로 3번 실패하면 interval 중지
          if (retryCount >= MAX_RETRIES && intervalId) {
            console.debug('연결 상태 조회 중지: 인증 실패 (3회 연속)');
            clearInterval(intervalId);
            intervalId = null;
          }
          return;
        }
        console.error('연결 상태 조회 실패:', error);
      }
    };
    
    // 초기 요청은 약간 지연 (토큰 로드 대기)
    const timeoutId = setTimeout(() => {
      checkConnection();
      // interval 시작 (10초마다)
      intervalId = setInterval(checkConnection, 10000);
    }, 100);
    
    return () => {
      clearTimeout(timeoutId);
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
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
