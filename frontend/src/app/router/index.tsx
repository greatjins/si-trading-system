/**
 * React Router 설정
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { LoginPage } from '../../pages/LoginPage';
import { DashboardPage } from '../../pages/DashboardPage';
import { BacktestPage } from '../../pages/BacktestPage';
import { StrategyBuilderPage } from '../../pages/StrategyBuilderPage';

// 인증 체크
const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

// Protected Route
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
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
    path: '/strategy-builder',
    element: (
      <ProtectedRoute>
        <StrategyBuilderPage />
      </ProtectedRoute>
    ),
  },
]);
