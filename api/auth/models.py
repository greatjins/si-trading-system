"""
사용자 인증 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from utils.logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user")  # user, trader, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIKey(Base):
    """API 키 모델"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class UserRepository:
    """사용자 저장소"""
    
    def __init__(self, db_url: str = None):
        """
        Args:
            db_url: 데이터베이스 URL (None이면 config에서 가져옴)
        """
        if db_url is None:
            from utils.config import config
            db_config = config.get("database", {})
            db_type = db_config.get("type", "sqlite")
            
            if db_type == "postgresql":
                db_url = (
                    f"postgresql+pg8000://{db_config['user']}:{db_config['password']}"
                    f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
                )
            else:
                db_path = db_config.get("path", "data/hts.db")
                db_url = f"sqlite:///{db_path}"
        
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_user(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: str = None,
        role: str = "user"
    ) -> User:
        """
        사용자 생성
        
        Args:
            username: 사용자명
            email: 이메일
            hashed_password: 해시된 비밀번호
            full_name: 전체 이름
            role: 역할
            
        Returns:
            생성된 사용자
        """
        session = self.Session()
        try:
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                role=role
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            logger.info(f"User created: {username}")
            return user
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
        
        finally:
            session.close()
    
    def get_user_by_username(self, username: str) -> User:
        """
        사용자명으로 사용자 조회
        
        Args:
            username: 사용자명
            
        Returns:
            사용자 또는 None
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(username=username).first()
            return user
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> User:
        """
        이메일로 사용자 조회
        
        Args:
            email: 이메일
            
        Returns:
            사용자 또는 None
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(email=email).first()
            return user
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: int) -> User:
        """
        ID로 사용자 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            사용자 또는 None
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            return user
        finally:
            session.close()
    
    def update_user(self, user_id: int, **kwargs) -> User:
        """
        사용자 정보 업데이트
        
        Args:
            user_id: 사용자 ID
            **kwargs: 업데이트할 필드
            
        Returns:
            업데이트된 사용자
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            user.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(user)
            
            logger.info(f"User updated: {user.username}")
            return user
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update user: {e}")
            raise
        
        finally:
            session.close()
    
    def delete_user(self, user_id: int) -> None:
        """
        사용자 삭제
        
        Args:
            user_id: 사용자 ID
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                session.delete(user)
                session.commit()
                logger.info(f"User deleted: {user.username}")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete user: {e}")
            raise
        
        finally:
            session.close()
