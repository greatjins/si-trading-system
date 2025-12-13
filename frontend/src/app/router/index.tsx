/**
 * React Router 설정
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import React from 'react';
import { LoginPage } from '../../pages/LoginPage';
import { DashboardPage } from '../../pages/DashboardPage';
import { BacktestPage } from '../../pages/BacktestPage';
import { BacktestResultPage } from '../../pages/BacktestResultPage';
import { BacktestComparisonPage } from '../../pages/BacktestComparisonPage';
import StrategyBuilderPage from '../../pages/StrategyBuilderPage';
import { StrategyBuilderPageV2 } from '../../pages/StrategyBuilderPageV2';
import StrategyListPage from '../../pages/StrategyListPage';
import SettingsPage from '../../pages/SettingsPage';
import DataCollection from '../../pages/DataCollection';
import { authService } from '../../services/auth';

// JWT 기반 즉시 인증 체크 (서버 호출 없음)
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  // 개발 모드 인증 우회
  const isDev = import.meta.env.DEV;
  const bypassAuth = isDev && localStorage.getItem('dev_bypass_auth') === 'true';
  
  if (bypassAuth) {
    console.log('🚧 개발 모드 - 인증 우회');
    return <>{children}</>;
  }

  // JWT 기반 즉시 인증 체크 (동기)
  const isAuthenticated = authService.isAuthenticated();
  
  if (!isAuthenticated) {
    console.log('🔒 JWT 인증 실패 - 로그인 리다이렉트:', window.location.pathname);
    // 현재 경로 저장
    sessionStorage.setItem('redirectPath', window.location.pathname + window.location.search);
    return <Navigate to="/login" replace />;
  }

  // 백그라운드에서 서버 검증 (UI 블로킹 없음)
  React.useEffect(() => {
    authService.validateWithServer().then(isValid => {
      if (!isValid) {
        console.warn('⚠️ 백그라운드 서버 검증 실패 - 토큰 갱신 필요할 수 있음');
      }
    });
  }, []);

  // 즉시 렌더링 (로딩 없음)
  return <>{children}</>;
};

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <DashboardPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/backtest',
    element: (
      <ProtectedRoute>
        <BacktestPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/backtest/results/:backtestId',
    element: (
      <ProtectedRoute>
        <BacktestResultPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/backtest/compare',
    element: (
      <ProtectedRoute>
        <BacktestComparisonPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/strategy-builder',
    element: (
      <ProtectedRoute>
        <StrategyBuilderPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/strategy-builder-v2',
    element: (
      <ProtectedRoute>
        <StrategyBuilderPageV2 />
      </ProtectedRoute>
    ),
  },
  {
    path: '/strategies',
    element: (
      <ProtectedRoute>
        <StrategyListPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/settings',
    element: (
      <ProtectedRoute>
        <SettingsPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/data-collection',
    element: (
      <ProtectedRoute>
        <DataCollection />
      </ProtectedRoute>
    ),
  },
]);
