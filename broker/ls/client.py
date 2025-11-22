"""
LS증권 API 클라이언트
"""
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

from broker.ls.oauth import LSOAuth, LSTokenManager
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


class LSClient:
    """LS증권 API 클라이언트"""
    
    def __init__(
        self,
        appkey: str = None,
        appsecretkey: str = None,
        account_id: str = None,
        base_url: str = None,
        paper_trading: bool = False,
        use_token_manager: bool = True
    ):
        """
        Args:
            appkey: 앱 키 (LS증권 용어)
            appsecretkey: 앱 시크릿 키 (LS증권 용어)
            account_id: 계좌번호
            base_url: API 베이스 URL
            paper_trading: 모의투자 여부
            use_token_manager: 토큰 매니저 사용 여부 (파일 기반 영속성)
        """
        self.appkey = appkey or config.get("ls.appkey")
        self.appsecretkey = appsecretkey or config.get("ls.appsecretkey")
        self.account_id = account_id or config.get("ls.account_id")
        self.paper_trading = paper_trading or config.get("ls.paper_trading", False)
        
        # REST API는 실거래/모의투자 동일한 URL 사용 (포트 8080)
        self.base_url = base_url or config.get("ls.base_url", "https://openapi.ls-sec.co.kr:8080")
        
        # OAuth 인증
        if use_token_manager:
            self.token_manager = LSTokenManager()
            self.oauth: Optional[LSOAuth] = None
        else:
            self.oauth = LSOAuth(
                appkey=self.appkey,
                appsecretkey=self.appsecretkey,
                base_url=self.base_url,
                paper_trading=self.paper_trading
            )
            self.token_manager = None
        
        # HTTP 클라이언트
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0
        )
        
        self.is_connected = False
        
        logger.info(f"LSClient initialized for account: {self.account_id}")
    
    async def connect(self):
        """API 연결 및 인증"""
        try:
            if self.token_manager:
                # 토큰 매니저 사용
                self.oauth = await self.token_manager.initialize(
                    appkey=self.appkey,
                    appsecretkey=self.appsecretkey
                )
            else:
                # 직접 토큰 발급
                await self.oauth.get_access_token()
            
            self.is_connected = True
            logger.info("LSClient connected successfully")
        
        except Exception as e:
            logger.error(f"Failed to connect LSClient: {e}")
            raise
    
    async def close(self):
        """API 연결 종료"""
        try:
            if self.oauth:
                await self.oauth.close()
            
            await self.client.aclose()
            self.is_connected = False
            
            logger.info("LSClient closed")
        
        except Exception as e:
            logger.error(f"Failed to close LSClient: {e}")
    
    async def _ensure_connected(self):
        """연결 상태 확인"""
        if not self.is_connected:
            await self.connect()
    
    async def _get_valid_token(self) -> str:
        """유효한 토큰 획득"""
        await self._ensure_connected()
        
        if self.token_manager:
            return await self.token_manager.get_valid_token()
        else:
            return await self.oauth.ensure_valid_token()
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        API 요청
        
        Args:
            method: HTTP 메서드 (GET, POST, PUT, DELETE)
            endpoint: API 엔드포인트
            params: 쿼리 파라미터
            data: 요청 바디
            headers: 추가 헤더
            
        Returns:
            응답 데이터
            
        Raises:
            Exception: API 요청 실패
        """
        try:
            # 유효한 토큰 획득
            token = await self._get_valid_token()
            
            # LS증권 API 헤더 구성 (ProgramGarden 방식)
            request_headers = {
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",  # Bearer 포함
            }
            
            # 추가 헤더 병합 (tr_id, tr_cont 등)
            if headers:
                # tr_id를 tr_cd로도 추가 (LS증권 API 호환)
                if "tr_id" in headers:
                    request_headers["tr_cd"] = headers["tr_id"]
                request_headers.update(headers)
            
            # 기본 TR 헤더 추가 (없으면)
            if "tr_cont" not in request_headers:
                request_headers["tr_cont"] = "N"
            if "tr_cont_key" not in request_headers:
                request_headers["tr_cont_key"] = ""
            if "mac_address" not in request_headers:
                request_headers["mac_address"] = ""
            
            # 디버깅: 요청 정보 로그
            logger.info(f"Request to {endpoint}")
            logger.info(f"Request method: {method}")
            logger.info(f"Request headers: {request_headers}")
            logger.info(f"Request params: {params}")
            logger.info(f"Request body: {data}")
            
            # 요청 실행
            response = await self.client.request(
                method=method,
                url=endpoint,
                params=params,
                json=data,
                headers=request_headers
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except httpx.HTTPStatusError as e:
            logger.error(f"API request failed: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API error: {e.response.text}")
        
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise
    
    async def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """GET 요청"""
        return await self.request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """POST 요청"""
        return await self.request("POST", endpoint, data=data)
    
    async def put(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """PUT 요청"""
        return await self.request("PUT", endpoint, data=data)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE 요청"""
        return await self.request("DELETE", endpoint)
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()
