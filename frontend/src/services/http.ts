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
  timeout: 60000, // 60초로 증가 (백테스트용)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor - 보안 강화된 토큰 관리
httpClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    console.log('📤 API 요청:', config.method?.toUpperCase(), config.url);
    console.log('  - baseURL:', config.baseURL);
    console.log('  - 전체 URL:', (config.baseURL || '') + (config.url || ''));
    
    // 새로운 인증 서비스에서 토큰 가져오기
    const getToken = () => {
      try {
        const authData = sessionStorage.getItem('auth_data');
        if (!authData) return null;
        
        const tokenData = JSON.parse(authData);
        
        // 토큰 만료 확인
        if (Date.now() > tokenData.expires_at) {
          console.log('⚠️ 토큰 만료됨');
          sessionStorage.removeItem('auth_data');
          return null;
        }
        
        return tokenData.access_token;
      } catch (error) {
        console.error('❌ 토큰 조회 실패:', error);
        return null;
      }
    };
    
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('  - 토큰: 있음 (보안 강화)');
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
    
    // 401 에러 시 토큰 갱신 시도 (보안 강화)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const authData = sessionStorage.getItem('auth_data');
        if (!authData) {
          throw new Error('No auth data');
        }
        
        const tokenData = JSON.parse(authData);
        if (!tokenData.refresh_token) {
          throw new Error('No refresh token');
        }
        
        const refreshUrl = API_BASE ? `${API_BASE}/api/auth/refresh` : '/api/auth/refresh';
        const response = await axios.post(refreshUrl, {
          refresh_token: tokenData.refresh_token,
        });
        
        const newTokenData = response.data;
        
        // 새 토큰 저장 (만료 시간 포함)
        const expiresAt = Date.now() + (30 * 60 * 1000); // 30분
        const updatedAuthData = {
          access_token: newTokenData.access_token,
          refresh_token: tokenData.refresh_token,
          expires_at: expiresAt,
          token_type: newTokenData.token_type || 'bearer',
        };
        
        sessionStorage.setItem('auth_data', JSON.stringify(updatedAuthData));
        
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newTokenData.access_token}`;
        }
        
        console.log('✅ 토큰 자동 갱신 성공');
        return httpClient(originalRequest);
      } catch (refreshError) {
        // 토큰 갱신 실패 시 세션 정리 및 로그아웃
        console.log('❌ 토큰 갱신 실패 - 로그아웃');
        sessionStorage.removeItem('auth_data');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
