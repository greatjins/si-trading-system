"""
주문 관련 API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime

from api.schemas import OrderRequest, OrderResponse, MessageResponse
from api.auth.security import get_current_active_user
from broker.mock.adapter import MockBroker
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# TODO: 실제 브로커 인스턴스로 교체
broker = MockBroker()


@router.post("/", response_model=OrderResponse)
async def create_order(order: OrderRequest, current_user: dict = Depends(get_current_active_user)):
    """
    주문 생성 (인증 필요)
    
    Args:
        order: 주문 요청
        current_user: 현재 사용자
        
    Returns:
        주문 정보
    """
    try:
        # Order 객체 생성
        from utils.types import Order, OrderSide, OrderType, OrderStatus
        
        order_obj = Order(
            order_id="",  # place_order에서 생성됨
            symbol=order.symbol,
            side=OrderSide(order.side),
            order_type=OrderType(order.order_type),
            quantity=order.quantity,
            price=order.price,
            filled_quantity=0,
            status=OrderStatus.PENDING,
            created_at=datetime.now()
        )
        
        # 주문 실행
        order_id = await broker.place_order(order_obj)
        
        logger.info(f"Order created: {order_id} - {order.side} {order.quantity} {order.symbol}")
        
        return OrderResponse(
            order_id=order_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
            status="submitted",
            created_at=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Failed to create order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """
    주문 조회
    
    Args:
        order_id: 주문 ID
        
    Returns:
        주문 정보
    """
    try:
        # TODO: 실제 주문 조회 구현
        raise HTTPException(status_code=501, detail="Not implemented yet")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{order_id}", response_model=MessageResponse)
async def cancel_order(order_id: str):
    """
    주문 취소
    
    Args:
        order_id: 주문 ID
        
    Returns:
        취소 결과
    """
    try:
        await broker.cancel_order(order_id)
        
        return MessageResponse(
            message=f"Order {order_id} cancelled successfully",
            success=True
        )
    
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[OrderResponse])
async def get_orders():
    """
    주문 목록 조회
    
    Returns:
        주문 리스트
    """
    try:
        # TODO: 실제 주문 목록 조회 구현
        return []
    
    except Exception as e:
        logger.error(f"Failed to get orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))
