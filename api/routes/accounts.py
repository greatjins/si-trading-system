"""
계좌 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from api.dependencies import get_db, get_current_user
from api.auth.models import User
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 생성"""
    repo = AccountRepository(db)
    account = repo.create_account(current_user.id, account_data)
    return repo.mask_account_for_response(account)


@router.get("", response_model=List[dict])
async def get_accounts(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 모든 계좌 조회"""
    repo = AccountRepository(db)
    accounts = repo.get_accounts(current_user.id, active_only)
    return [repo.mask_account_for_response(acc) for acc in accounts]


@router.get("/default", response_model=dict)
async def get_default_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """기본 계좌 조회"""
    repo = AccountRepository(db)
    account = repo.get_default_account(current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기본 계좌가 설정되지 않았습니다"
        )
    return repo.mask_account_for_response(account)


@router.get("/{account_id}", response_model=dict)
async def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 상세 조회"""
    repo = AccountRepository(db)
    account = repo.get_account(account_id, current_user.id)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 수정"""
    repo = AccountRepository(db)
    account = repo.update_account(account_id, current_user.id, update_data)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    return repo.mask_account_for_response(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 삭제"""
    repo = AccountRepository(db)
    success = repo.delete_account(account_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    return None


@router.post("/{account_id}/set-default", response_model=dict)
async def set_default_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """기본 계좌로 설정"""
    repo = AccountRepository(db)
    update_data = TradingAccountUpdate(is_default=True)
    account = repo.update_account(account_id, current_user.id, update_data)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    return repo.mask_account_for_response(account)


@router.post("/{account_id}/toggle-active", response_model=dict)
async def toggle_account_active(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """계좌 활성화/비활성화 토글"""
    repo = AccountRepository(db)
    account = repo.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계좌를 찾을 수 없습니다"
        )
    
    update_data = TradingAccountUpdate(is_active=not account.is_active)
    account = repo.update_account(account_id, current_user.id, update_data)
    return repo.mask_account_for_response(account)
