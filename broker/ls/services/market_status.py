"""
장운영정보 관리 모듈
"""
from typing import Optional, Dict
from datetime import datetime
from threading import Lock

from utils.logger import setup_logger

logger = setup_logger(__name__)


class MarketStatusManager:
    """
    장운영정보(JIF) 상태 관리자 (싱글톤)
    
    jangubun 1,2 (코스피/코스닥)의 jstatus가 21~41 사이면 krx_active = True
    jangubun 6 (NXT)의 jstatus가 21~41 사이면 nxt_active = True
    """
    
    _instance: Optional['MarketStatusManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        """싱글톤 패턴"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """초기화 (싱글톤이므로 한 번만 실행)"""
        if self._initialized:
            return
        
        self.krx_active = False  # KRX (코스피/코스닥) 활성 상태
        self.nxt_active = False  # NXT (넥스트레이드) 활성 상태
        
        # 서킷브레이크/사이드카 상태
        self.krx_circuit_breaker = False  # KRX 서킷브레이크 발동
        self.krx_sidecar = False  # KRX 사이드카 발동
        self.nxt_circuit_breaker = False  # NXT 서킷브레이크 발동
        self.nxt_sidecar = False  # NXT 사이드카 발동
        
        # 장 상태 코드 저장
        self.krx_status: Optional[str] = None
        self.nxt_status: Optional[str] = None
        
        self._lock = Lock()
        self._initialized = True
        
        logger.info("MarketStatusManager initialized")
    
    def update_jif(self, jangubun: str, jstatus: str) -> None:
        """
        JIF 데이터 업데이트
        
        Args:
            jangubun: 장구분 (1:코스피, 2:코스닥, 6:NXT)
            jstatus: 장상태 코드
        """
        with self._lock:
            # KRX (jangubun 1,2)
            if jangubun in ("1", "2"):
                self.krx_status = jstatus
                
                # 장 활성 상태 확인 (21~41: 장개시 ~ 장마감)
                try:
                    status_num = int(jstatus)
                    self.krx_active = 21 <= status_num <= 41
                except (ValueError, TypeError):
                    # 숫자가 아닌 경우 (예: "A2", "B2" 등)
                    # 프리마켓/에프터마켓 상태는 활성으로 간주하지 않음
                    self.krx_active = False
                
                # 서킷브레이크 확인 (61~63, 68~71)
                # 해제 신호(62, 70)가 오면 False, 발동 신호(61, 63, 68, 69, 71)가 오면 True
                if jstatus in ("61", "63", "68", "69", "71"):
                    self.krx_circuit_breaker = True
                    logger.warning(f"KRX 서킷브레이크 발동: jstatus={jstatus}")
                elif jstatus in ("62", "70"):
                    self.krx_circuit_breaker = False
                    logger.info(f"KRX 서킷브레이크 해제: jstatus={jstatus}")
                
                # 사이드카 확인 (64~67)
                # 해제 신호(65, 67)가 오면 False, 발동 신호(64, 66)가 오면 True
                if jstatus in ("64", "66"):
                    self.krx_sidecar = True
                    logger.warning(f"KRX 사이드카 발동: jstatus={jstatus}")
                elif jstatus in ("65", "67"):
                    self.krx_sidecar = False
                    logger.info(f"KRX 사이드카 해제: jstatus={jstatus}")
                
                logger.debug(
                    f"KRX 상태 업데이트: jangubun={jangubun}, jstatus={jstatus}, "
                    f"active={self.krx_active}, circuit_breaker={self.krx_circuit_breaker}, "
                    f"sidecar={self.krx_sidecar}"
                )
            
            # NXT (jangubun 6)
            elif jangubun == "6":
                self.nxt_status = jstatus
                
                # 장 활성 상태 확인 (21~41: 장개시 ~ 장마감)
                try:
                    status_num = int(jstatus)
                    self.nxt_active = 21 <= status_num <= 41
                except (ValueError, TypeError):
                    # 숫자가 아닌 경우
                    self.nxt_active = False
                
                # NXT 전용 서킷브레이크/사이드카 확인 (동일한 코드 사용)
                # 해제 신호(62, 70)가 오면 False, 발동 신호(61, 63, 68, 69, 71)가 오면 True
                if jstatus in ("61", "63", "68", "69", "71"):
                    self.nxt_circuit_breaker = True
                    logger.warning(f"NXT 서킷브레이크 발동: jstatus={jstatus}")
                elif jstatus in ("62", "70"):
                    self.nxt_circuit_breaker = False
                    logger.info(f"NXT 서킷브레이크 해제: jstatus={jstatus}")
                
                # 해제 신호(65, 67)가 오면 False, 발동 신호(64, 66)가 오면 True
                if jstatus in ("64", "66"):
                    self.nxt_sidecar = True
                    logger.warning(f"NXT 사이드카 발동: jstatus={jstatus}")
                elif jstatus in ("65", "67"):
                    self.nxt_sidecar = False
                    logger.info(f"NXT 사이드카 해제: jstatus={jstatus}")
                
                logger.debug(
                    f"NXT 상태 업데이트: jangubun={jangubun}, jstatus={jstatus}, "
                    f"active={self.nxt_active}, circuit_breaker={self.nxt_circuit_breaker}, "
                    f"sidecar={self.nxt_sidecar}"
                )
            
            # 장마감 확인 (jstatus: 41)
            if jstatus == "41":
                if jangubun in ("1", "2"):
                    logger.info("KRX 장마감")
                elif jangubun == "6":
                    logger.info("NXT 장마감")
    
    def is_market_active(self, market: str) -> bool:
        """
        시장 활성 상태 확인
        
        Args:
            market: 시장 구분 ("KRX" 또는 "NXT")
        
        Returns:
            활성 상태이면 True
        """
        with self._lock:
            if market == "KRX":
                return self.krx_active
            elif market == "NXT":
                return self.nxt_active
            return False
    
    def is_circuit_breaker_active(self, market: str) -> bool:
        """
        서킷브레이크 발동 상태 확인
        
        Args:
            market: 시장 구분 ("KRX" 또는 "NXT")
        
        Returns:
            서킷브레이크가 발동 중이면 True
        """
        with self._lock:
            if market == "KRX":
                return self.krx_circuit_breaker
            elif market == "NXT":
                return self.nxt_circuit_breaker
            return False
    
    def is_sidecar_active(self, market: str) -> bool:
        """
        사이드카 발동 상태 확인
        
        Args:
            market: 시장 구분 ("KRX" 또는 "NXT")
        
        Returns:
            사이드카가 발동 중이면 True
        """
        with self._lock:
            if market == "KRX":
                return self.krx_sidecar
            elif market == "NXT":
                return self.nxt_sidecar
            return False
    
    def is_market_closed(self, market: str) -> bool:
        """
        장마감 상태 확인
        
        Args:
            market: 시장 구분 ("KRX" 또는 "NXT")
        
        Returns:
            장마감이면 True
        """
        with self._lock:
            if market == "KRX":
                return self.krx_status == "41"
            elif market == "NXT":
                return self.nxt_status == "41"
            return False
    
    def get_status(self) -> Dict[str, any]:
        """
        전체 상태 조회
        
        Returns:
            상태 딕셔너리
        """
        with self._lock:
            return {
                "krx_active": self.krx_active,
                "nxt_active": self.nxt_active,
                "krx_circuit_breaker": self.krx_circuit_breaker,
                "krx_sidecar": self.krx_sidecar,
                "nxt_circuit_breaker": self.nxt_circuit_breaker,
                "nxt_sidecar": self.nxt_sidecar,
                "krx_status": self.krx_status,
                "nxt_status": self.nxt_status
            }

