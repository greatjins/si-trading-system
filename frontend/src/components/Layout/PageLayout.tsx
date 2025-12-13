/**
 * 공통 페이지 레이아웃
 */
import { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { authService } from '../../services/auth';

interface PageLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
}

export const PageLayout = ({ children, title, description }: PageLayoutProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const handleLogout = async () => {
    if (confirm('로그아웃 하시겠습니까?')) {
      try {
        console.log('🚪 로그아웃 시작...');
        await authService.logout();
        console.log('✅ 로그아웃 완료');
        navigate('/login', { replace: true });
      } catch (error) {
        console.error('❌ 로그아웃 오류:', error);
        // 오류가 발생해도 클라이언트 세션은 정리됨
        navigate('/login', { replace: true });
      }
    }
  };
  
  return (
    <div className="page-layout">
      {/* 헤더 */}
      <header className="page-header">
        <div className="header-left">
          <h1>{title || 'HTS'}</h1>
          
          {/* 네비게이션 */}
          <nav className="nav-links">
            <Link 
              to="/dashboard" 
              className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
            >
              📊 트레이딩
            </Link>
            <Link 
              to="/backtest" 
              className={`nav-link ${location.pathname === '/backtest' ? 'active' : ''}`}
            >
              🧪 백테스트
            </Link>
            <Link 
              to="/strategy-builder" 
              className={`nav-link ${location.pathname === '/strategy-builder' ? 'active' : ''}`}
            >
              🔧 전략 빌더
            </Link>
            <Link 
              to="/strategies" 
              className={`nav-link ${location.pathname === '/strategies' ? 'active' : ''}`}
            >
              📋 내 전략
            </Link>
            <Link 
              to="/data-collection" 
              className={`nav-link ${location.pathname === '/data-collection' ? 'active' : ''}`}
            >
              💾 데이터 수집
            </Link>
            <Link 
              to="/settings" 
              className={`nav-link ${location.pathname === '/settings' ? 'active' : ''}`}
            >
              ⚙️ 설정
            </Link>
          </nav>
          
          {description && <p className="page-description">{description}</p>}
        </div>
        
        <div className="header-right">
          <button onClick={handleLogout} className="btn btn-logout">
            🚪 로그아웃
          </button>
        </div>
      </header>
      
      {/* 컨텐츠 */}
      <main className="page-content">
        {children}
      </main>
    </div>
  );
};
