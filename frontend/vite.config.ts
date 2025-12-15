import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    open: false,
    proxy: {
      // API 프록시
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true, // WebSocket 프록시
        rewrite: (path) => path, // 경로 유지
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            // 백엔드 서버가 응답하지 않을 때 에러 로깅만 하고 크래시 방지
            console.log('[Vite Proxy] Backend connection error:', err.message);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('[Vite Proxy] Proxying:', req.method, req.url);
          });
        },
      },
    },
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'zustand',
      'axios',
      'lightweight-charts',
    ],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'chart-vendor': ['lightweight-charts'],
          'state-vendor': ['zustand', 'axios'],
        },
      },
    },
  },
})
