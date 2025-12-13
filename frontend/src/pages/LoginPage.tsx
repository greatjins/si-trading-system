/**
 * 로그인 페이지
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';

export const LoginPage = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 이미 로그인된 경우 대시보드로 리다이렉트
  useEffect(() => {
    if (authService.isAuthenticated()) {
      console.log('✅ 이미 로그인됨 - 대시보드로 이동');
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('🔐 로그인 시도:', username);
      
      // 새로운 보안 강화된 인증 서비스 사용
      const user = await authService.login(username, password);
      
      console.log('✅ 로그인 성공:', user.username);
      
      // 저장된 리다이렉트 경로가 있으면 해당 경로로, 없으면 대시보드로
      const redirectPath = sessionStorage.getItem('redirectPath') || '/dashboard';
      sessionStorage.removeItem('redirectPath'); // 사용 후 제거
      
      console.log('🔄 리다이렉트:', redirectPath);
      navigate(redirectPath, { replace: true });
      
    } catch (err) {
      console.error('❌ 로그인 실패:', err);
      setError(err instanceof Error ? err.message : '로그인에 실패했습니다. 사용자명과 비밀번호를 확인해주세요.');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="login-page">
      <div className="login-container">
        <h1>HTS</h1>
        <p className="subtitle">국내주식 자동매매 시스템</p>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>사용자명</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="사용자명을 입력하세요"
              className="form-input"
              required
            />
          </div>
          
          <div className="form-group">
            <label>비밀번호</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호를 입력하세요"
              className="form-input"
              required
            />
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={isLoading}
          >
            {isLoading ? '로그인 중...' : '로그인'}
          </button>
        </form>
      </div>
    </div>
  );
};
