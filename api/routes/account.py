"""
계좌 관련 API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from api.schemas import AccountResponse, PositionResponse
from api.auth.security import get_current_active_user
from broker.mock.adapter import MockBroker
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# TODO: 실제 브로커 인스턴스로 교체
broker = MockBroker()


@router.get("/summary", response_model=AccountResponse)
async def get_account_summary(current_user: dict = Depends(get_current_active_user)):
    """
    계좌 요약 정보 조회 (인증 필요)
    
    Args:
        current_user: 현재 사용자
    
    Returns:
        계좌 정보
    """
    try:
        account = await broker.get_account()
        
        return AccountResponse(
            account_id=account.account_id,
            balance=account.balance,
            equity=account.equity,
            margin_used=account.margin_used,
            margin_available=account.margin_available
        )
    
    except Exception as e:
        logger.error(f"Failed to get account summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(current_user: dict = Depends(get_current_active_user)):
    """
    보유 포지션 조회 (인증 필요)
    
    Args:
        current_user: 현재 사용자
    
    Returns:
        포지션 리스트
    """
    try:
        positions = await broker.get_positions()
        
        return [
            PositionResponse(
                symbol=pos.symbol,
                quantity=pos.quantity,
                avg_price=pos.avg_price,
                current_price=pos.current_price,
                unrealized_pnl=pos.unrealized_pnl,
                realized_pnl=pos.realized_pnl
            )
            for pos in positions
        ]
    
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
