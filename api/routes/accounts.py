"""
계좌 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from api.dependencies import get_db, get_current_user

from api.repositories.account_repository import AccountRepository
from data.account_models import (
    TradingAccountCreate,
    TradingAccountUpdate,
    TradingAccountResponse,
    TradingAccountDetail
)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: TradingAccountCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 생성"""
    repo = AccountRepository(db)
    account = repo.create_account(current_user["user_id"], account_data)
    return repo.mask_account_for_response(account)


@router.get("", response_model=List[dict])
async def get_accounts(
    active_only: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 모든 계좌 조회"""
    repo = AccountRepository(db)
    accounts = repo.get_accounts(current_user["user_id"], active_only)
    return [repo.mask_account_for_response(acc) for acc in accounts]


@router.get("/default", response_model=dict)
async def get_default_account(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """기본 계좌 조회"""
    repo = AccountRepository(db)
    account = repo.get_default_account(current_user["user_id"])
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기본 계좌가 설정되지 않았습니다"
        )
    return repo.mask_account_for_response(account)


@router.get("/{account_id}", response_model=dict)
async def get_account(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 상세 조회"""
    repo = AccountRepository(db)
    account = repo.get_account(account_id, current_user["user_id"])
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    return repo.mask_account_for_response(account)


@router.put("/{account_id}", response_model=dict)
async def update_account(
    account_id: int,
    update_data: TradingAccountUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 수정"""
    repo = AccountRepository(db)
    account = repo.update_account(account_id, current_user["user_id"], update_data)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    return repo.mask_account_for_response(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 삭제"""
    repo = AccountRepository(db)
    success = repo.delete_account(account_id, current_user["user_id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    return None


@router.post("/{account_id}/set-default", response_model=dict)
async def set_default_account(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """기본 계좌로 설정"""
    repo = AccountRepository(db)
    update_data = TradingAccountUpdate(is_default=True)
    account = repo.update_account(account_id, current_user["user_id"], update_data)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    return repo.mask_account_for_response(account)


@router.get("/{account_id}/connection-status", response_model=dict)
async def get_connection_status(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 연결 상태 조회"""
    from broker.connection_pool import connection_pool
    from datetime import datetime
    
    repo = AccountRepository(db)
    account = repo.get_account(account_id, current_user["user_id"])
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    
    try:
        credentials = repo.get_account_credentials(account_id, current_user["user_id"])
        if not credentials:
            return {
                "connected": False,
                "message": "계좌 인증 정보 없음"
            }
        
        key = f"{account.broker}_{credentials['account_number']}"
        stats = connection_pool.get_stats()
        
        # 해당 계좌의 연결 찾기
        conn_info = None
        for conn in stats["connections"]:
            if conn["key"] == key:
                conn_info = conn
                break
        
        if conn_info:
            last_used = conn_info["last_used"]
            idle_seconds = (datetime.now() - last_used).total_seconds() if last_used else 0
            
            return {
                "connected": conn_info["connected"],
                "last_used": last_used.isoformat() if last_used else None,
                "idle_seconds": int(idle_seconds),
                "max_idle_seconds": connection_pool._max_idle_time,
                "will_disconnect_in": max(0, connection_pool._max_idle_time - idle_seconds),
                "broker": conn_info["broker"],
                "account_number": credentials["account_number"]
            }
        else:
            return {
                "connected": False,
                "message": "연결되지 않음"
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"연결 상태 조회 실패: {str(e)}"
        )


@router.post("/{account_id}/disconnect", response_model=dict)
async def disconnect_account(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 연결 수동 종료"""
    from broker.connection_pool import connection_pool
    
    repo = AccountRepository(db)
    account = repo.get_account(account_id, current_user["user_id"])
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    
    try:
        credentials = repo.get_account_credentials(account_id, current_user["user_id"])
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="계좌 인증 정보를 찾을 수 없습니다"
            )
        
        await connection_pool.close_adapter(
            broker=account.broker,
            account_id=credentials["account_number"]
        )
        
        return {
            "success": True,
            "message": "연결이 종료되었습니다"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"연결 종료 실패: {str(e)}"
        )


@router.post("/{account_id}/keep-alive", response_model=dict)
async def keep_connection_alive(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """연결 유지 (마지막 사용 시간 갱신)"""
    from broker.connection_pool import connection_pool
    
    repo = AccountRepository(db)
    account = repo.get_account(account_id, current_user["user_id"])
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    
    try:
        credentials = repo.get_account_credentials(account_id, current_user["user_id"])
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="계좌 인증 정보를 찾을 수 없습니다"
            )
        
        await connection_pool.release_adapter(
            broker=account.broker,
            account_id=credentials["account_number"]
        )
        
        return {
            "success": True,
            "message": "연결이 갱신되었습니다"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"연결 갱신 실패: {str(e)}"
        )


@router.post("/{account_id}/toggle-active", response_model=dict)
async def toggle_account_active(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 활성화/비활성화 토글"""
    repo = AccountRepository(db)
    account = repo.get_account(account_id, current_user["user_id"])
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    
    update_data = TradingAccountUpdate(is_active=not account.is_active)
    account = repo.update_account(account_id, current_user["user_id"], update_data)
    return repo.mask_account_for_response(account)


@router.get("/{account_id}/balance", response_model=dict)
async def get_account_balance(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """실시간 계좌 잔고 조회 (연결 풀 사용)"""
    from broker.connection_pool import connection_pool
    from utils.config import config
    
    repo = AccountRepository(db)
    account = repo.get_account(account_id, current_user["user_id"])
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    
    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 계좌입니다"
        )
    
    try:
        # 계좌 인증 정보 복호화
        credentials = repo.get_account_credentials(account_id, current_user["user_id"])
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="계좌 인증 정보를 찾을 수 없습니다"
            )
        
        # 브로커별 어댑터 생성 (연결 풀 사용)
        if account.broker == "ls":
            # 연결 풀에서 Adapter 가져오기 (재사용)
            adapter = await connection_pool.get_adapter(
                broker="ls",
                account_id=credentials["account_number"],
                api_key=credentials["api_key"],
                api_secret=credentials["api_secret"],
                paper_trading=(account.account_type == "paper")
            )
            
            try:
                # 계좌 정보 조회
                balance = await adapter.get_account()
                positions = await adapter.get_positions()
                
                return {
                    "account_id": account.id,
                    "account_number": credentials["account_number"],
                    "broker": account.broker,
                    "balance": balance.balance,
                    "equity": balance.equity,
                    "margin_used": balance.margin_used,
                    "margin_available": balance.margin_available,
                    "buying_power": balance.buying_power(),
                    "positions": [
                        {
                            "symbol": pos.symbol,
                            "quantity": pos.quantity,
                            "avg_price": pos.avg_price,
                            "current_price": pos.current_price,
                            "unrealized_pnl": pos.unrealized_pnl,
                            "realized_pnl": pos.realized_pnl
                        }
                        for pos in positions
                    ]
                }
            finally:
                # 연결 반환 (연결은 유지)
                await connection_pool.release_adapter("ls", credentials["account_number"])
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"{account.broker} 브로커는 아직 지원되지 않습니다"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"계좌 정보 조회 실패: {str(e)}"
        )
