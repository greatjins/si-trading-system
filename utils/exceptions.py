"""
커스텀 예외 클래스
"""


class BrokerError(Exception):
    """브로커 에러의 기본 예외"""
    pass


class AuthenticationError(BrokerError):
    """인증 실패"""
    pass


class InsufficientFundsError(BrokerError):
    """주문에 대한 잔액 부족"""
    pass


class InvalidOrderError(BrokerError):
    """주문 파라미터가 유효하지 않음"""
    pass


class ConnectionError(BrokerError):
    """네트워크 또는 연결 문제"""
    pass


class DataNotFoundError(BrokerError):
    """요청한 데이터를 찾을 수 없음"""
    pass


class RiskLimitError(Exception):
    """리스크 한도 초과"""
    pass


class StrategyError(Exception):
    """전략 실행 에러"""
    pass


class BacktestError(Exception):
    """백테스트 실행 에러"""
    pass
