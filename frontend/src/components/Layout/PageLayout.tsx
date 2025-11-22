/**
 * 공통 페이지 레이아웃
 */
import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface PageLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
}

export const PageLayout = ({ children, title, description }: PageLayoutProps) => {
  const location = useLocation();
  
  const handleLogout = () => {
    if (confirm('로그아웃 하시겠습니까?')) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
  };
  
  return (
    <div className="page-layout">
      {/* 헤더 */}
      <header className="page-header">
        <div className="header-left">
          <h1>{title || 'LS HTS 플랫폼'}</h1>
          
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
