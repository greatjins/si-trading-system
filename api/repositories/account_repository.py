"""
계좌 관리 Repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from data.account_models import TradingAccount, TradingAccountCreate, TradingAccountUpdate
from cryptography.fernet import Fernet
import os


class AccountRepository:
    """계좌 관리 Repository"""
    
    def __init__(self, db: Session):
        self.db = db
        # 암호화 키 (환경변수에서 가져오거나 생성)
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            # 개발용 기본 키 (프로덕션에서는 반드시 환경변수 사용!)
            encryption_key = Fernet.generate_key()
        self.cipher = Fernet(encryption_key)
    
    def _encrypt(self, value: Optional[str]) -> Optional[str]:
        """문자열 암호화"""
        if not value:
            return None
        return self.cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, value: Optional[str]) -> Optional[str]:
        """문자열 복호화"""
        if not value:
            return None
        try:
            return self.cipher.decrypt(value.encode()).decode()
        except Exception:
            return None
    
    def _mask_string(self, value: Optional[str], show_last: int = 4) -> str:
        """문자열 마스킹"""
        if not value:
            return "****"
        if len(value) <= show_last:
            return "*" * len(value)
        return "*" * (len(value) - show_last) + value[-show_last:]
    
    def create_account(self, user_id: int, account_data: TradingAccountCreate) -> TradingAccount:
        """계좌 생성"""
        # 기본 계좌로 설정 시 기존 기본 계좌 해제
        if account_data.is_default:
            self.db.query(TradingAccount).filter(
                TradingAccount.user_id == user_id,
                TradingAccount.is_default == True
            ).update({"is_default": False})
        
        # 민감정보 암호화
        account = TradingAccount(
            user_id=user_id,
            name=account_data.name,
            broker=account_data.broker,
            account_type=account_data.account_type,
            account_number=self._encrypt(account_data.account_number),
            api_key=self._encrypt(account_data.api_key),
            api_secret=self._encrypt(account_data.api_secret),
            app_key=self._encrypt(account_data.app_key),
            app_secret=self._encrypt(account_data.app_secret),
            is_active=True,
            is_default=account_data.is_default
        )
        
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def get_account(self, account_id: int, user_id: int) -> Optional[TradingAccount]:
        """계좌 조회"""
        return self.db.query(TradingAccount).filter(
            TradingAccount.id == account_id,
            TradingAccount.user_id == user_id
        ).first()
    
    def get_accounts(self, user_id: int, active_only: bool = False) -> List[TradingAccount]:
        """사용자의 모든 계좌 조회"""
        query = self.db.query(TradingAccount).filter(TradingAccount.user_id == user_id)
        if active_only:
            query = query.filter(TradingAccount.is_active == True)
        return query.order_by(TradingAccount.is_default.desc(), TradingAccount.created_at.desc()).all()
    
    def get_default_account(self, user_id: int) -> Optional[TradingAccount]:
        """기본 계좌 조회"""
        return self.db.query(TradingAccount).filter(
            TradingAccount.user_id == user_id,
            TradingAccount.is_default == True,
            TradingAccount.is_active == True
        ).first()
    
    def update_account(self, account_id: int, user_id: int, update_data: TradingAccountUpdate) -> Optional[TradingAccount]:
        """계좌 수정"""
        account = self.get_account(account_id, user_id)
        if not account:
            return None
        
        # 기본 계좌로 설정 시 기존 기본 계좌 해제
        if update_data.is_default:
            self.db.query(TradingAccount).filter(
                TradingAccount.user_id == user_id,
                TradingAccount.id != account_id,
                TradingAccount.is_default == True
            ).update({"is_default": False})
        
        # 업데이트할 필드만 수정
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # 민감정보 암호화
        if "account_number" in update_dict and update_dict["account_number"]:
            update_dict["account_number"] = self._encrypt(update_dict["account_number"])
        if "api_key" in update_dict and update_dict["api_key"]:
            update_dict["api_key"] = self._encrypt(update_dict["api_key"])
        if "api_secret" in update_dict and update_dict["api_secret"]:
            update_dict["api_secret"] = self._encrypt(update_dict["api_secret"])
        if "app_key" in update_dict and update_dict["app_key"]:
            update_dict["app_key"] = self._encrypt(update_dict["app_key"])
        if "app_secret" in update_dict and update_dict["app_secret"]:
            update_dict["app_secret"] = self._encrypt(update_dict["app_secret"])
        
        for key, value in update_dict.items():
            setattr(account, key, value)
        
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def delete_account(self, account_id: int, user_id: int) -> bool:
        """계좌 삭제"""
        account = self.get_account(account_id, user_id)
        if not account:
            return False
        
        self.db.delete(account)
        self.db.commit()
        return True
    
    def get_account_credentials(self, account_id: int, user_id: int) -> Optional[dict]:
        """계좌 인증 정보 조회 (복호화)"""
        account = self.get_account(account_id, user_id)
        if not account:
            return None
        
        return {
            "account_number": self._decrypt(account.account_number),
            "api_key": self._decrypt(account.api_key),
            "api_secret": self._decrypt(account.api_secret),
            "app_key": self._decrypt(account.app_key),
            "app_secret": self._decrypt(account.app_secret),
        }
    
    def mask_account_for_response(self, account: TradingAccount) -> dict:
        """응답용 계좌 정보 (마스킹)"""
        return {
            "id": account.id,
            "user_id": account.user_id,
            "name": account.name,
            "broker": account.broker.value,
            "account_type": account.account_type.value,
            "account_number_masked": self._mask_string(self._decrypt(account.account_number)),
            "api_key_masked": self._mask_string(self._decrypt(account.api_key)),
            "has_api_secret": bool(account.api_secret),
            "has_app_key": bool(account.app_key),
            "has_app_secret": bool(account.app_secret),
            "is_active": account.is_active,
            "is_default": account.is_default,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
            "last_connected_at": account.last_connected_at,
        }
