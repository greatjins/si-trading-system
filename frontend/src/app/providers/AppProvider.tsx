/**
 * 앱 전역 Provider
 */
import { RouterProvider } from 'react-router-dom';
import { router } from '../router';
import { WebSocketProvider } from '../../services/websocket.tsx';

export const AppProvider = () => {
  return (
    <WebSocketProvider>
      <RouterProvider router={router} />
    </WebSocketProvider>
  );
};
