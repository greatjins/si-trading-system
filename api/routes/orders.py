"""
주문 관련 API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime

from api.schemas import OrderRequest, OrderResponse, MessageResponse
from api.auth.security import get_current_active_user
from broker.mock.adapter import MockBroker
from broker.connection_pool import connection_pool
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)
router = APIRouter()


async def get_broker():
    """
    브로커 인스턴스 가져오기 (의존성 주입)
    config.yaml의 broker.type 설정에 따라 적절한 브로커 반환
    """
    broker_type = config.get("broker.type", "mock")
    
    if broker_type == "ls":
        # LSAdapter 사용 (연결 풀에서 가져오기)
        api_key = config.get("broker.api_key") or config.get("ls.appkey")
        api_secret = config.get("broker.api_secret") or config.get("ls.appsecretkey")
        account_id = config.get("broker.account_id") or config.get("ls.account_id")
        paper_trading = config.get("ls.paper_trading", False)
        
        if not all([api_key, api_secret, account_id]):
            logger.warning("LS broker credentials not found, falling back to MockBroker")
            return MockBroker()
        
        try:
            broker = await connection_pool.get_adapter(
                broker="ls",
                account_id=account_id,
                api_key=api_key,
                api_secret=api_secret,
                paper_trading=paper_trading
            )
            return broker
        except Exception as e:
            logger.error(f"Failed to get LSAdapter: {e}, falling back to MockBroker")
            return MockBroker()
    else:
        # MockBroker 사용 (기본값)
        return MockBroker()


@router.post("/", response_model=OrderResponse)
async def create_order(
    order: OrderRequest, 
    current_user: dict = Depends(get_current_active_user),
    broker = Depends(get_broker)
):
    """
    주문 생성 (인증 필요)
    
    Args:
        order: 주문 요청
        current_user: 현재 사용자
        broker: 브로커 인스턴스 (의존성 주입)
        
    Returns:
        주문 정보
    """
    try:
        # Order 객체 생성
        from utils.types import Order, OrderSide, OrderType, OrderStatus
        from datetime import timezone, timedelta, time
        
        # 시장 구분 결정 (ExecutionEngine의 determine_market 로직과 동일)
        def determine_market() -> str:
            """현재 시간에 따라 시장 구분 결정"""
            kst = timezone(timedelta(hours=9))
            now_kst = datetime.now(kst)
            current_time = now_kst.time()
            
            # 08:00 ~ 08:50: NXT (장전 시간외)
            if time(8, 0) <= current_time < time(8, 50):
                return "NXT"
            # 09:00 ~ 15:30: KRX (정규장)
            if time(9, 0) <= current_time <= time(15, 30):
                return "KRX"
            # 15:40 ~ 20:00: NXT (장후 시간외)
            if time(15, 40) <= current_time <= time(20, 0):
                return "NXT"
            # 그 외 시간은 기본값 KRX (에러 방지)
            logger.warning(f"주문 불가 시간대이지만 기본값 KRX 사용: {current_time.strftime('%H:%M:%S')} (KST)")
            return "KRX"
        
        mbr_no = determine_market()
        
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
        
        # mbr_no를 metadata로 추가
        if not hasattr(order_obj, 'metadata'):
            order_obj.metadata = {}
        order_obj.metadata['mbr_no'] = mbr_no
        
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
async def cancel_order(
    order_id: str,
    broker = Depends(get_broker)
):
    """
    주문 취소
    
    Args:
        order_id: 주문 ID
        broker: 브로커 인스턴스 (의존성 주입)
        
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
async def get_orders(
    broker = Depends(get_broker)
):
    """
    주문 목록 조회 (체결/미체결 포함)
    
    Args:
        broker: 브로커 인스턴스 (의존성 주입)
    
    Returns:
        주문 리스트
    """
    try:
        # 브로커에서 주문 내역 가져오기
        orders = await broker.get_orders()
        
        # Order를 OrderResponse로 변환
        order_responses = []
        for order in orders:
            order_responses.append(OrderResponse(
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side.value if hasattr(order.side, 'value') else str(order.side),
                order_type=order.order_type.value if hasattr(order.order_type, 'value') else str(order.order_type),
                quantity=order.quantity,
                price=order.price,
                status=order.status.value if hasattr(order.status, 'value') else str(order.status),
                created_at=order.created_at
            ))
        
        return order_responses
    
    except Exception as e:
        logger.error(f"Failed to get orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
