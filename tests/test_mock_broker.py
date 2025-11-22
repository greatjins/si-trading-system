"""
MockBroker 테스트
"""
import pytest
from datetime import datetime, timedelta

from broker.mock.adapter import MockBroker
from utils.types import Order, OrderSide, OrderType, OrderStatus


@pytest.mark.asyncio
async def test_mock_broker_initialization():
    """MockBroker 초기화 테스트"""
    broker = MockBroker(initial_balance=10_000_000)
    
    account = await broker.get_account()
    assert account.balance == 10_000_000
    assert account.equity == 10_000_000


@pytest.mark.asyncio
async def test_get_ohlc():
    """OHLC 데이터 조회 테스트"""
    broker = MockBroker()
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 5)
    
    ohlc_data = await broker.get_ohlc(
        symbol="005930",
        interval="1d",
        start_date=start_date,
        end_date=end_date
    )
    
    assert len(ohlc_data) > 0
    assert all(bar.symbol == "005930" for bar in ohlc_data)
    assert all(bar.high >= bar.low for bar in ohlc_data)
    assert all(bar.open > 0 and bar.close > 0 for bar in ohlc_data)


@pytest.mark.asyncio
async def test_get_current_price():
    """현재가 조회 테스트"""
    broker = MockBroker()
    
    price = await broker.get_current_price("005930")
    assert price > 0


@pytest.mark.asyncio
async def test_place_order():
    """주문 제출 테스트"""
    broker = MockBroker()
    
    order = Order(
        order_id="",
        symbol="005930",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=10,
        price=None,
        filled_quantity=0,
        status=OrderStatus.PENDING,
        created_at=datetime.now()
    )
    
    order_id = await broker.place_order(order)
    assert order_id is not None
    assert len(order_id) > 0


@pytest.mark.asyncio
async def test_get_positions():
    """포지션 조회 테스트"""
    broker = MockBroker()
    
    positions = await broker.get_positions()
    assert isinstance(positions, list)


@pytest.mark.asyncio
async def test_get_open_orders():
    """미체결 주문 조회 테스트"""
    broker = MockBroker()
    
    orders = await broker.get_open_orders()
    assert isinstance(orders, list)
