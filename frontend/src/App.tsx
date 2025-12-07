/**
 * 메인 앱 컴포넌트
 * 
 * Note: 현재 main.tsx에서 AppProvider를 직접 사용하므로
 * 이 파일은 사용되지 않습니다.
 * 
 * 향후 개선 시 다음과 같이 구조를 변경할 수 있습니다:
 * - main.tsx: <App /> 렌더링
 * - App.tsx: WebSocketProvider + RouterProvider 포함
 */

import { WebSocketProvider } from './services/websocket'
import { RouterProvider } from 'react-router-dom'
import { router } from './app/router'

export default function App() {
  return (
    <WebSocketProvider>
      <RouterProvider router={router} />
    </WebSocketProvider>
  )
}
