"""
RiskManager 테스트
"""
import pytest
from datetime import datetime

from core.risk.manager import RiskManager
from utils.types import Account, Position, OrderSignal, OrderSide, OrderType


def test_risk_manager_initialization():
    """리스크 관리자 초기화 테스트"""
    manager = RiskManager(
        max_mdd=0.20,
        max_position_size=0.10,
        max_daily_loss=0.05,
        initial_capital=10_000_000
    )
    
    assert manager.max_mdd == 0.20
    assert manager.max_position_size == 0.10
    assert manager.max_daily_loss == 0.05
    assert manager.peak_equity == 10_000_000
    assert manager.emergency_stop == False


def test_mdd_calculation():
    """MDD 계산 테스트"""
    manager = RiskManager(
        max_mdd=0.20,
        initial_capital=10_000_000
    )
    
    # 자산 증가
    manager.update_equity(11_000_000)
    assert manager.peak_equity == 11_000_000
    assert manager.current_mdd == 0.0
    
    # 자산 감소
    manager.update_equity(9_000_000)
    expected_mdd = (11_000_000 - 9_000_000) / 11_000_000
    assert abs(manager.current_mdd - expected_mdd) < 0.001


def test_mdd_limit_exceeded():
    """MDD 한도 초과 테스트"""
    manager = RiskManager(
        max_mdd=0.10,  # 10%
        initial_capital=10_000_000
    )
    
    account = Account(
        account_id="TEST",
        balance=8_500_000,
        equity=8_500_000,
        margin_used=0,
        margin_available=8_500_000
    )
    
    # MDD 15% (한도 초과)
    manager.update_equity(8_500_000)
    
    # 리스크 한도 확인 (실패해야 함)
    result = manager.check_risk_limits(account)
    assert result == False
    assert manager.emergency_stop == True


def test_position_size_validation():
    """포지션 크기 검증 테스트"""
    manager = RiskManager(
        max_position_size=0.10,  # 10%
        initial_capital=10_000_000
    )
    
    account = Account(
        account_id="TEST",
        balance=10_000_000,
        equity=10_000_000,
        margin_used=0,
        margin_available=10_000_000
    )
    
    # 포지션 크기 5% (허용)
    signal_ok = OrderSignal(
        symbol="005930",
        side=OrderSide.BUY,
        quantity=10,
        order_type=OrderType.MARKET,
        price=50_000  # 총 500,000원 = 5%
    )
    
    assert manager.validate_order(signal_ok, account, []) == True
    
    # 포지션 크기 15% (초과)
    signal_exceed = OrderSignal(
        symbol="005930",
        side=OrderSide.BUY,
        quantity=30,
        order_type=OrderType.MARKET,
        price=50_000  # 총 1,500,000원 = 15%
    )
    
    assert manager.validate_order(signal_exceed, account, []) == False


def test_daily_loss_tracking():
    """일일 손실 추적 테스트"""
    manager = RiskManager(
        max_daily_loss=0.05,  # 5%
        initial_capital=10_000_000
    )
    
    # 일일 시작
    manager.update_equity(10_000_000)
    
    # 3% 손실 (허용)
    account_ok = Account(
        account_id="TEST",
        balance=9_700_000,
        equity=9_700_000,
        margin_used=0,
        margin_available=9_700_000
    )
    
    manager.update_equity(9_700_000)
    assert manager.check_risk_limits(account_ok) == True
    
    # 6% 손실 (초과)
    account_exceed = Account(
        account_id="TEST",
        balance=9_400_000,
        equity=9_400_000,
        margin_used=0,
        margin_available=9_400_000
    )
    
    manager.update_equity(9_400_000)
    assert manager.check_risk_limits(account_exceed) == False


def test_emergency_stop():
    """긴급 정지 테스트"""
    manager = RiskManager(initial_capital=10_000_000)
    
    assert manager.emergency_stop == False
    
    # 긴급 정지 트리거
    manager.trigger_emergency_stop("Test reason")
    assert manager.emergency_stop == True
    
    # 긴급 정지 해제
    manager.reset_emergency_stop()
    assert manager.emergency_stop == False


def test_risk_status():
    """리스크 상태 조회 테스트"""
    manager = RiskManager(
        max_mdd=0.20,
        max_position_size=0.10,
        max_daily_loss=0.05,
        initial_capital=10_000_000
    )
    
    status = manager.get_risk_status()
    
    assert "emergency_stop" in status
    assert "current_mdd" in status
    assert "max_mdd" in status
    assert "daily_loss" in status
    assert "peak_equity" in status
