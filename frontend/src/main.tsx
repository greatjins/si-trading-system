import { createRoot } from 'react-dom/client'
import './index.css'
import './styles/common.css'
import { AppProvider } from './app/providers/AppProvider'

// StrictMode는 개발 중 이중 렌더링을 유발하므로 WebSocket 연결 시 제거
createRoot(document.getElementById('root')!).render(
  <AppProvider />
)
