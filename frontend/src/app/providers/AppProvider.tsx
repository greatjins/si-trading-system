/**
 * 앱 전역 Provider
 */
import { RouterProvider } from 'react-router-dom';
import { router } from '../router';
import { WebSocketProvider } from '../../services/websocket.tsx';
import { ErrorBoundary } from '../../components/UI';

export const AppProvider = () => {
  return (
    <ErrorBoundary>
      <WebSocketProvider>
        <RouterProvider router={router} />
      </WebSocketProvider>
    </ErrorBoundary>
  );
};
