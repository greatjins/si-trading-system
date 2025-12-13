/**
 * 인증 서비스 - 보안 강화된 세션 관리
 */

interface TokenData {
  access_token: string;
  refresh_token?: string;
  expires_at: number;
  token_type: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
}

class AuthService {
  private static instance: AuthService;
  private tokenCheckInterval: NodeJS.Timeout | null = null;
  private sessionTimeout: NodeJS.Timeout | null = null;
  
  // 세션 타임아웃 (2시간)
  private readonly SESSION_TIMEOUT = 2 * 60 * 60 * 1000;
  
  // 토큰 체크 간격 (1분)
  private readonly TOKEN_CHECK_INTERVAL = 60 * 1000;

  private constructor() {
    this.initializeAuth();
  }

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * 인증 시스템 초기화
   */
  private initializeAuth(): void {
    // 페이지 로드 시 토큰 검증
    this.validateStoredToken();
    
    // 주기적 토큰 검증
    this.startTokenValidation();
    
    // 브라우저 종료 시 세션 정리
    this.setupSessionCleanup();
    
    // 사용자 활동 모니터링
    this.setupActivityMonitoring();
  }

  /**
   * 로그인
   */
  async login(username: string, password: string): Promise<User> {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('로그인 실패');
      }

      const data = await response.json();
      
      // 토큰 저장 (보안 강화)
      this.storeTokenSecurely(data);
      
      // 사용자 정보 조회
      const user = await this.getCurrentUser();
      
      // 세션 타이머 시작
      this.startSessionTimeout();
      
      console.log('✅ 로그인 성공:', user.username);
      
      return user;
    } catch (error) {
      console.error('❌ 로그인 실패:', error);
      throw error;
    }
  }

  /**
   * 로그아웃
   */
  async logout(): Promise<void> {
    try {
      // 서버에 로그아웃 요청
      const token = this.getAccessToken();
      if (token) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('⚠️ 서버 로그아웃 실패:', error);
    } finally {
      // 클라이언트 세션 정리
      this.clearSession();
      console.log('✅ 로그아웃 완료');
    }
  }

  /**
   * JWT 토큰 디코딩 (백엔드 호환)
   */
  private decodeJWT(token: string): any {
    try {
      // JWT 구조: header.payload.signature
      const parts = token.split('.');
      if (parts.length !== 3) {
        throw new Error('Invalid JWT format');
      }

      const payload = parts[1];
      // Base64URL 디코딩
      const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      
      const decoded = JSON.parse(jsonPayload);
      
      // 백엔드 JWT 구조 검증
      if (!decoded.sub || !decoded.exp) {
        throw new Error('Invalid JWT payload structure');
      }
      
      return decoded;
    } catch (error) {
      console.error('JWT 디코딩 실패:', error);
      return null;
    }
  }

  /**
   * 토큰 보안 저장 (JWT 기반)
   */
  private storeTokenSecurely(tokenData: any): void {
    // JWT에서 만료 시간 추출
    const payload = this.decodeJWT(tokenData.access_token);
    const expiresAt = payload?.exp ? payload.exp * 1000 : Date.now() + (2 * 60 * 60 * 1000);
    
    const secureTokenData: TokenData = {
      access_token: tokenData.access_token,
      refresh_token: tokenData.refresh_token,
      expires_at: expiresAt,
      token_type: tokenData.token_type || 'bearer',
    };

    // sessionStorage 사용 (브라우저 종료 시 자동 삭제)
    sessionStorage.setItem('auth_data', JSON.stringify(secureTokenData));
    
    // localStorage에서 기존 토큰 제거
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    console.log('✅ JWT 토큰 저장:', {
      expiresAt: new Date(expiresAt).toLocaleString(),
      payload: payload ? { sub: payload.sub, exp: payload.exp } : null
    });
  }

  /**
   * 액세스 토큰 조회
   */
  getAccessToken(): string | null {
    try {
      const authData = sessionStorage.getItem('auth_data');
      if (!authData) return null;

      const tokenData: TokenData = JSON.parse(authData);
      
      // 토큰 만료 확인
      if (Date.now() > tokenData.expires_at) {
        console.log('⚠️ 토큰 만료됨');
        this.clearSession();
        return null;
      }

      return tokenData.access_token;
    } catch (error) {
      console.error('❌ 토큰 조회 실패:', error);
      return null;
    }
  }

  /**
   * JWT 기반 클라이언트 인증 체크 (서버 호출 없음)
   */
  isAuthenticated(): boolean {
    try {
      const authData = sessionStorage.getItem('auth_data');
      if (!authData) {
        console.log('🔍 인증 체크: 토큰 없음');
        return false;
      }

      const tokenData: TokenData = JSON.parse(authData);
      const now = Date.now();
      
      // JWT 만료 시간 체크
      if (now > tokenData.expires_at) {
        console.log('🔍 인증 체크: JWT 만료됨', {
          now: new Date(now).toLocaleString(),
          expiresAt: new Date(tokenData.expires_at).toLocaleString()
        });
        this.clearSession();
        return false;
      }

      // JWT 페이로드 검증
      const payload = this.decodeJWT(tokenData.access_token);
      if (!payload || !payload.sub) {
        console.log('🔍 인증 체크: JWT 페이로드 무효');
        this.clearSession();
        return false;
      }

      console.log('✅ 인증 체크: 유효한 JWT', {
        user: payload.sub,
        expiresIn: Math.round((tokenData.expires_at - now) / 1000 / 60) + '분'
      });

      return true;
    } catch (error) {
      console.error('❌ 인증 체크 오류:', error);
      this.clearSession();
      return false;
    }
  }

  /**
   * 서버 검증 (백그라운드 전용)
   */
  async validateWithServer(): Promise<boolean> {
    const token = this.getAccessToken();
    if (!token) return false;

    try {
      await this.getCurrentUser();
      return true;
    } catch (error) {
      console.log('⚠️ 서버 검증 실패 (백그라운드):', error);
      // 서버 검증 실패 시에도 클라이언트 토큰이 유효하면 유지
      return this.isAuthenticated();
    }
  }

  /**
   * 현재 사용자 정보 조회
   */
  async getCurrentUser(): Promise<User> {
    const token = this.getAccessToken();
    if (!token) {
      throw new Error('인증되지 않음');
    }

    const response = await fetch('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('사용자 정보 조회 실패');
    }

    return response.json();
  }

  /**
   * 저장된 토큰 검증
   */
  private validateStoredToken(): void {
    const authData = sessionStorage.getItem('auth_data');
    if (!authData) return;

    try {
      const tokenData: TokenData = JSON.parse(authData);
      
      // 만료 확인
      if (Date.now() > tokenData.expires_at) {
        console.log('⚠️ 저장된 토큰이 만료됨');
        this.clearSession();
        return;
      }

      // 서버 검증
      this.validateTokenWithServer();
    } catch (error) {
      console.error('❌ 토큰 검증 실패:', error);
      this.clearSession();
    }
  }

  /**
   * 서버와 토큰 검증
   */
  private async validateTokenWithServer(): Promise<void> {
    try {
      await this.getCurrentUser();
      console.log('✅ 토큰 서버 검증 성공');
    } catch (error) {
      console.log('⚠️ 토큰 서버 검증 실패 - 로그아웃');
      this.clearSession();
    }
  }

  /**
   * 주기적 토큰 검증 시작
   */
  private startTokenValidation(): void {
    this.tokenCheckInterval = setInterval(() => {
      if (this.isAuthenticated()) {
        this.validateTokenWithServer();
      }
    }, this.TOKEN_CHECK_INTERVAL);
  }

  /**
   * 세션 타임아웃 시작
   */
  private startSessionTimeout(): void {
    this.clearSessionTimeout();
    
    this.sessionTimeout = setTimeout(() => {
      console.log('⏰ 세션 타임아웃 - 자동 로그아웃');
      this.logout();
      alert('세션이 만료되었습니다. 다시 로그인해주세요.');
      window.location.href = '/login';
    }, this.SESSION_TIMEOUT);
  }

  /**
   * 세션 타임아웃 초기화
   */
  private clearSessionTimeout(): void {
    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
      this.sessionTimeout = null;
    }
  }

  /**
   * 사용자 활동 모니터링
   */
  private setupActivityMonitoring(): void {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    
    const resetTimeout = () => {
      if (this.isAuthenticated()) {
        this.startSessionTimeout(); // 타임아웃 리셋
      }
    };

    events.forEach(event => {
      document.addEventListener(event, resetTimeout, true);
    });
  }

  /**
   * 브라우저 종료 시 세션 정리
   */
  private setupSessionCleanup(): void {
    // 브라우저 종료/새로고침 시
    window.addEventListener('beforeunload', () => {
      // sessionStorage는 자동으로 정리되지만 명시적으로 정리
      this.clearSession();
    });

    // 탭 포커스 변경 시 토큰 검증
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.isAuthenticated()) {
        this.validateTokenWithServer();
      }
    });
  }

  /**
   * 세션 완전 정리
   */
  private clearSession(): void {
    // 토큰 제거
    sessionStorage.removeItem('auth_data');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // 타이머 정리
    this.clearSessionTimeout();
    
    if (this.tokenCheckInterval) {
      clearInterval(this.tokenCheckInterval);
      this.tokenCheckInterval = null;
    }
  }

  /**
   * 토큰 갱신
   */
  async refreshToken(): Promise<boolean> {
    try {
      const authData = sessionStorage.getItem('auth_data');
      if (!authData) return false;

      const tokenData: TokenData = JSON.parse(authData);
      if (!tokenData.refresh_token) return false;

      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: tokenData.refresh_token,
        }),
      });

      if (!response.ok) return false;

      const newTokenData = await response.json();
      this.storeTokenSecurely(newTokenData);
      
      console.log('✅ 토큰 갱신 성공');
      return true;
    } catch (error) {
      console.error('❌ 토큰 갱신 실패:', error);
      return false;
    }
  }
}

// 싱글톤 인스턴스 내보내기
export const authService = AuthService.getInstance();

// 기존 함수들과의 호환성을 위한 래퍼
export const isAuthenticated = () => authService.isAuthenticated();
export const getAccessToken = () => authService.getAccessToken();
export const logout = () => authService.logout();