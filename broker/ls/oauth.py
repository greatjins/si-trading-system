"""
LS증권 OAuth 2.0 인증
"""
import httpx
from typing import Optional, Dict
from datetime import datetime, timedelta
import json

from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


class LSOAuth:
    """LS증권 OAuth 2.0 인증 클라이언트"""
    
    def __init__(
        self,
        appkey: str = None,
        appsecretkey: str = None,
        base_url: str = None,
        paper_trading: bool = False
    ):
        """
        Args:
            appkey: 앱 키 (LS증권 용어)
            appsecretkey: 앱 시크릿 키 (LS증권 용어)
            base_url: API 베이스 URL
            paper_trading: 모의투자 여부
        """
        self.appkey = appkey or config.get("ls.appkey")
        self.appsecretkey = appsecretkey or config.get("ls.appsecretkey")
        self.paper_trading = paper_trading or config.get("ls.paper_trading", False)
        
        # REST API URL (실거래/모의투자 모두 포트 8080 사용)
        # 모의투자는 계좌번호로 구분됨
        self.base_url = base_url or "https://openapi.ls-sec.co.kr:8080"
        
        # 토큰 정보
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_type: str = "Bearer"
        self.expires_at: Optional[datetime] = None
        
        # HTTP 클라이언트
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0
        )
        
        logger.info("LSOAuth initialized")
    
    async def get_access_token(
        self,
        grant_type: str = "client_credentials",
        scope: str = "oob"
    ) -> Dict[str, str]:
        """
        접근 토큰 발급
        
        Args:
            grant_type: 인증 방식 (client_credentials, authorization_code 등)
            scope: 권한 범위
            
        Returns:
            토큰 정보 딕셔너리
            
        Raises:
            Exception: 토큰 발급 실패
        """
        try:
            # OAuth 토큰 발급 요청 (LS증권 스펙에 맞춤)
            # ProgramGarden과 동일한 방식 사용
            import aiohttp
            
            url = f"{self.base_url}/oauth2/token"
            data = {
                "grant_type": grant_type,
                "appkey": self.appkey,
                "appsecretkey": self.appsecretkey,
                "scope": scope
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    # 응답 내용 확인 (디버깅)
                    response_text = await response.text()
                    logger.info(f"OAuth Response Status: {response.status}")
                    logger.info(f"OAuth Response Body: {response_text}")
                    
                    response.raise_for_status()
                    data = await response.json()
            
                    # 토큰 정보 저장
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    self.token_type = data.get("token_type", "Bearer")
                    
                    # 만료 시간 계산
                    expires_in = data.get("expires_in", 86400)  # 기본 24시간
                    self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    logger.info(f"Access token issued: expires in {expires_in}s")
                    
                    return {
                        "access_token": self.access_token,
                        "refresh_token": self.refresh_token,
                        "token_type": self.token_type,
                        "expires_in": expires_in,
                        "expires_at": self.expires_at.isoformat()
                    }
        
        except aiohttp.ClientResponseError as e:
            # 에러 응답 본문 확인
            try:
                error_body = await e.response.text() if hasattr(e, 'response') else "No response body"
            except:
                error_body = "Unable to read response body"
            
            logger.error(f"Failed to get access token: {e.status} - {e.message}")
            logger.error(f"Error details: {error_body}")
            raise Exception(f"Token issuance failed: {e.message} - {error_body}")
        
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise
    
    async def refresh_access_token(self) -> Dict[str, str]:
        """
        접근 토큰 갱신
        
        Returns:
            새로운 토큰 정보
            
        Raises:
            Exception: 토큰 갱신 실패
        """
        if not self.refresh_token:
            raise Exception("No refresh token available")
        
        try:
            response = await self.client.post(
                "/oauth2/token",
                data={
                    "grant_type": "refresh_token",
                    "appkey": self.appkey,
                    "appsecretkey": self.appsecretkey,
                    "refresh_token": self.refresh_token
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            # 토큰 정보 업데이트
            self.access_token = data.get("access_token")
            if data.get("refresh_token"):
                self.refresh_token = data.get("refresh_token")
            
            expires_in = data.get("expires_in", 86400)
            self.expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info(f"Access token refreshed: expires in {expires_in}s")
            
            return {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "token_type": self.token_type,
                "expires_in": expires_in,
                "expires_at": self.expires_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise
    
    async def revoke_token(self, token: str = None) -> bool:
        """
        접근 토큰 폐기
        
        Args:
            token: 폐기할 토큰 (None이면 현재 access_token)
            
        Returns:
            폐기 성공 여부
        """
        token_to_revoke = token or self.access_token
        
        if not token_to_revoke:
            logger.warning("No token to revoke")
            return False
        
        try:
            response = await self.client.post(
                "/oauth2/revoke",
                data={
                    "appkey": self.appkey,
                    "appsecretkey": self.appsecretkey,
                    "token": token_to_revoke
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            response.raise_for_status()
            
            # 토큰 정보 초기화
            if token_to_revoke == self.access_token:
                self.access_token = None
                self.refresh_token = None
                self.expires_at = None
            
            logger.info("Token revoked successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False
    
    def is_token_valid(self) -> bool:
        """
        토큰 유효성 확인
        
        Returns:
            토큰이 유효한지 여부
        """
        if not self.access_token:
            return False
        
        if not self.expires_at:
            return True  # 만료 시간 정보 없으면 유효하다고 가정
        
        # 만료 5분 전이면 갱신 필요
        return datetime.now() < (self.expires_at - timedelta(minutes=5))
    
    async def ensure_valid_token(self) -> str:
        """
        유효한 토큰 보장 (필요시 자동 갱신)
        
        Returns:
            유효한 접근 토큰
            
        Raises:
            Exception: 토큰 발급/갱신 실패
        """
        if self.is_token_valid():
            return self.access_token
        
        # 토큰이 없으면 새로 발급
        if not self.access_token:
            await self.get_access_token()
            return self.access_token
        
        # 토큰이 만료되었으면 갱신
        try:
            await self.refresh_access_token()
            return self.access_token
        except Exception as e:
            logger.warning(f"Token refresh failed, getting new token: {e}")
            await self.get_access_token()
            return self.access_token
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        인증 헤더 생성
        
        Returns:
            Authorization 헤더 딕셔너리
        """
        if not self.access_token:
            raise Exception("No access token available")
        
        return {
            "Authorization": f"{self.token_type} {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()
        logger.info("LSOAuth client closed")
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.get_access_token()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()


class LSTokenManager:
    """LS증권 토큰 관리자 (파일 기반 영속성)"""
    
    def __init__(self, token_file: str = "data/ls_token.json"):
        """
        Args:
            token_file: 토큰 저장 파일 경로
        """
        self.token_file = token_file
        self.oauth: Optional[LSOAuth] = None
    
    async def initialize(
        self,
        appkey: str = None,
        appsecretkey: str = None
    ) -> LSOAuth:
        """
        토큰 매니저 초기화
        
        Args:
            appkey: 앱 키
            appsecretkey: 앱 시크릿 키
            
        Returns:
            LSOAuth 인스턴스
        """
        self.oauth = LSOAuth(appkey=appkey, appsecretkey=appsecretkey)
        
        # 저장된 토큰 로드 시도
        if await self.load_token():
            logger.info("Loaded token from file")
        else:
            # 새 토큰 발급
            await self.oauth.get_access_token()
            await self.save_token()
        
        return self.oauth
    
    async def save_token(self) -> bool:
        """
        토큰을 파일에 저장
        
        Returns:
            저장 성공 여부
        """
        if not self.oauth or not self.oauth.access_token:
            return False
        
        try:
            import os
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            
            token_data = {
                "access_token": self.oauth.access_token,
                "refresh_token": self.oauth.refresh_token,
                "token_type": self.oauth.token_type,
                "expires_at": self.oauth.expires_at.isoformat() if self.oauth.expires_at else None
            }
            
            with open(self.token_file, "w") as f:
                json.dump(token_data, f, indent=2)
            
            logger.info(f"Token saved to {self.token_file}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            return False
    
    async def load_token(self) -> bool:
        """
        파일에서 토큰 로드
        
        Returns:
            로드 성공 여부
        """
        try:
            import os
            if not os.path.exists(self.token_file):
                return False
            
            with open(self.token_file, "r") as f:
                token_data = json.load(f)
            
            self.oauth.access_token = token_data.get("access_token")
            self.oauth.refresh_token = token_data.get("refresh_token")
            self.oauth.token_type = token_data.get("token_type", "Bearer")
            
            expires_at_str = token_data.get("expires_at")
            if expires_at_str:
                self.oauth.expires_at = datetime.fromisoformat(expires_at_str)
            
            # 토큰 유효성 확인
            if not self.oauth.is_token_valid():
                logger.info("Loaded token is expired, refreshing...")
                await self.oauth.refresh_access_token()
                await self.save_token()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
            return False
    
    async def get_valid_token(self) -> str:
        """
        유효한 토큰 반환 (자동 갱신)
        
        Returns:
            유효한 접근 토큰
        """
        if not self.oauth:
            raise Exception("TokenManager not initialized")
        
        token = await self.oauth.ensure_valid_token()
        await self.save_token()
        return token
