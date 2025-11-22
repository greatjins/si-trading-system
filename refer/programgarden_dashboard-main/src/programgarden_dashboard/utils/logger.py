"""
ProgramGarden Dashboard 통합 로그 설정
"""

import logging
import sys
from typing import Optional


class DashboardLogger:
    """ProgramGarden Dashboard 전용 로그 관리자"""
    
    _initialized = False
    _logger_name = "programgarden_dashboard"
    _default_level = logging.WARNING
    
    @classmethod
    def initialize(
        cls, 
        level: int = logging.WARNING,
        format_string: Optional[str] = None,
        enable_console: bool = True
    ) -> None:
        """
        라이브러리 로그 시스템 초기화
        
        Args:
            level: 로그 레벨 (기본: WARNING)
            format_string: 로그 포맷 (기본: 간결한 포맷)
            enable_console: 콘솔 출력 활성화 여부
        """
        if cls._initialized:
            return
            
        # 기본 포맷 설정 (라이브러리용 간결한 포맷)
        if format_string is None:
            format_string = "[%(name)s] %(levelname)s: %(message)s"
            
        # 루트 로거 가져오기
        root_logger = logging.getLogger(cls._logger_name)
        root_logger.setLevel(level)
        
        # 기존 핸들러 제거 (중복 방지)
        root_logger.handlers.clear()
        
        if enable_console:
            # 콘솔 핸들러 추가
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            # 포맷터 설정
            formatter = logging.Formatter(format_string)
            console_handler.setFormatter(formatter)
            
            root_logger.addHandler(console_handler)
        
        # 상위 로거로 전파 방지 (라이브러리 격리)
        root_logger.propagate = False
        
        cls._initialized = True
        cls._default_level = level
        
        # 초기화 완료 메시지 (INFO 레벨로만 출력)
        if level <= logging.INFO:
            root_logger.info("✅ ProgramGarden Dashboard 로그 시스템 초기화 완료")
    
    @classmethod
    def get_logger(cls, name: str = None) -> logging.Logger:
        """
        통합 로거 반환
        
        Args:
            name: 로거 이름 (기본: 호출한 모듈명)
            
        Returns:
            설정된 로거 인스턴스
        """
        # 초기화되지 않은 경우 자동 초기화
        if not cls._initialized:
            cls.initialize()
            
        if name:
            logger_name = f"{cls._logger_name}.{name}"
        else:
            logger_name = cls._logger_name
            
        logger = logging.getLogger(logger_name)
        logger.setLevel(cls._default_level)
        
        return logger
    
    @classmethod
    def set_level(cls, level: int) -> None:
        """
        전체 로그 레벨 변경
        
        Args:
            level: 새로운 로그 레벨
        """
        if not cls._initialized:
            cls.initialize(level)
            return
            
        # 루트 로거 레벨 변경
        root_logger = logging.getLogger(cls._logger_name)
        root_logger.setLevel(level)
        
        # 모든 핸들러 레벨도 변경
        for handler in root_logger.handlers:
            handler.setLevel(level)
            
        cls._default_level = level
    
    @classmethod
    def disable(cls) -> None:
        """라이브러리 로그 완전 비활성화"""
        root_logger = logging.getLogger(cls._logger_name)
        root_logger.disabled = True
    
    @classmethod
    def enable(cls) -> None:
        """라이브러리 로그 다시 활성화"""
        root_logger = logging.getLogger(cls._logger_name)
        root_logger.disabled = False


# 편의 함수들
def get_logger(name: str = None) -> logging.Logger:
    """로거 가져오기 (편의 함수)"""
    return DashboardLogger.get_logger(name)

def set_log_level(level: int) -> None:
    """로그 레벨 설정 (편의 함수)"""
    DashboardLogger.set_level(level)

def disable_logging() -> None:
    """로그 비활성화 (편의 함수)"""
    DashboardLogger.disable()

def enable_logging() -> None:
    """로그 활성화 (편의 함수)"""
    DashboardLogger.enable()


# 레벨 상수들 (사용자 편의용)
class LogLevel:
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG