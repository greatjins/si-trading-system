/**
 * HTTP 클라이언트 (Axios)
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// API 베이스 URL 자동 감지
const getApiBaseUrl = () => {
  console.log('🔍 API URL 감지 시작');
  console.log('  - 현재 URL:', window.location.href);
  console.log('  - 호스트:', window.location.hostname);
  console.log('  - 포트:', window.location.port);
  
  // 1. 환경변수가 있으면 사용 (강제 지정)
  const envUrl = (import.meta as any).env?.VITE_API_URL;
  if (envUrl) {
    console.log('✅ API_BASE:', envUrl, '(환경변수 사용)');
    return envUrl;
  }
  
  // 2. 현재 호스트가 localhost면 상대주소 (Vite 프록시 사용)
  const currentHost = window.location.hostname;
  if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
    console.log('✅ API_BASE: "" (상대주소 - Vite 프록시)');
    return '';
  }
  
  // 3. 외부 접근 (Tailscale 등)이면 현재 호스트:8000 사용
  const protocol = window.location.protocol;
  const apiUrl = `${protocol}//${currentHost}:8000`;
  console.log('✅ API_BASE:', apiUrl, '(현재 호스트 자동 감지)');
  return apiUrl;
};

const API_BASE = getApiBaseUrl();

// Axios 인스턴스 생성
export const httpClient = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor
httpClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    console.log('📤 API 요청:', config.method?.toUpperCase(), config.url);
    console.log('  - baseURL:', config.baseURL);
    console.log('  - 전체 URL:', config.baseURL + config.url);
    
    // 토큰 추가
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('  - 토큰: 있음');
    } else {
      console.log('  - 토큰: 없음');
    }
    return config;
  },
  (error: AxiosError) => {
    console.error('❌ 요청 에러:', error);
    return Promise.reject(error);
  }
);

// Response Interceptor
httpClient.interceptors.response.use(
  (response) => {
    console.log('📥 API 응답:', response.status, response.config.url);
    return response;
  },
  async (error: AxiosError) => {
    console.error('❌ API 에러:', error.message);
    console.error('  - URL:', error.config?.url);
    console.error('  - 상태:', error.response?.status);
    console.error('  - 응답:', error.response?.data);
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // 401 에러 시 토큰 갱신 시도
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }
        
        const refreshUrl = API_BASE ? `${API_BASE}/api/auth/refresh` : '/api/auth/refresh';
        const response = await axios.post(refreshUrl, {
          refresh_token: refreshToken,
        });
        
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        
        return httpClient(originalRequest);
      } catch (refreshError) {
        // 토큰 갱신 실패 시 로그아웃
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
