import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
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
                rewrite: function (path) { return path; }, // 경로 유지
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
});
