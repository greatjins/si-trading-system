"""
종목 필터링 엔진
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, desc, and_
from sqlalchemy.orm import sessionmaker

from data.models import StockMasterModel, StockUniverseModel
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


class StockFilter:
    """종목 필터링 엔진"""
    
    def __init__(self, db_url: str = None):
        """
        Args:
            db_url: 데이터베이스 URL (None이면 config에서 로드)
        """
        if db_url is None:
            db_type = config.get("database.type", "sqlite")
            if db_type == "sqlite":
                db_path = config.get("database.path", "data/hts.db")
                db_url = f"sqlite:///{db_path}"
            else:
                # PostgreSQL
                host = config.get("database.host", "localhost")
                port = config.get("database.port", 5432)
                database = config.get("database.database", "hts")
                username = config.get("database.user", "hts_user")
                password = config.get("database.password", "")
                db_url = f"postgresql+pg8000://{username}:{password}@{host}:{port}/{database}"
        
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info("StockFilter initialized")
    
    def filter_by_liquidity(
        self,
        min_volume_amount: int = 100_000_000_000  # 1000억원
    ) -> List[str]:
        """
        거래대금 필터
        
        Args:
            min_volume_amount: 최소 거래대금 (기본: 1000억원)
        
        Returns:
            종목 코드 리스트
        """
        session = self.SessionLocal()
        
        try:
            results = session.query(StockMasterModel.symbol).filter(
                and_(
                    StockMasterModel.volume_amount >= min_volume_amount,
                    StockMasterModel.is_active == True
                )
            ).order_by(desc(StockMasterModel.volume_amount)).all()
            
            symbols = [r.symbol for r in results]
            logger.info(f"Liquidity filter: {len(symbols)} symbols (>= {min_volume_amount:,}원)")
            return symbols
        
        finally:
            session.close()
    
    def filter_by_price_position(
        self,
        max_position: float = 0.5  # 52주 최고가 대비 50% 이하
    ) -> List[str]:
        """
        가격 위치 필터 (저점 매수용)
        
        Args:
            max_position: 최대 가격 위치 (0.5 = 52주 최고가 대비 50%)
        
        Returns:
            종목 코드 리스트
        """
        session = self.SessionLocal()
        
        try:
            results = session.query(StockMasterModel.symbol).filter(
                and_(
                    StockMasterModel.price_position <= max_position,
                    StockMasterModel.price_position.isnot(None),
                    StockMasterModel.is_active == True
                )
            ).order_by(StockMasterModel.price_position).all()
            
            symbols = [r.symbol for r in results]
            logger.info(f"Price position filter: {len(symbols)} symbols (<= {max_position:.0%})")
            return symbols
        
        finally:
            session.close()
    
    def filter_by_momentum(
        self,
        min_position: float = 0.7,  # 52주 최고가 대비 70% 이상
        max_position: float = 1.0   # 52주 최고가 대비 100% 이하
    ) -> List[str]:
        """
        모멘텀 필터 (추세 추종용)
        
        Args:
            min_position: 최소 가격 위치
            max_position: 최대 가격 위치
        
        Returns:
            종목 코드 리스트
        """
        session = self.SessionLocal()
        
        try:
            results = session.query(StockMasterModel.symbol).filter(
                and_(
                    StockMasterModel.price_position >= min_position,
                    StockMasterModel.price_position <= max_position,
                    StockMasterModel.price_position.isnot(None),
                    StockMasterModel.is_active == True
                )
            ).order_by(desc(StockMasterModel.price_position)).all()
            
            symbols = [r.symbol for r in results]
            logger.info(f"Momentum filter: {len(symbols)} symbols ({min_position:.0%} ~ {max_position:.0%})")
            return symbols
        
        finally:
            session.close()
    
    def get_universe(
        self,
        strategy_type: str = "mean_reversion",
        min_volume_amount: int = 100_000_000_000,  # 1000억원
        limit: int = 200
    ) -> List[str]:
        """
        전략별 종목 유니버스 생성
        
        Args:
            strategy_type: 전략 타입 (mean_reversion, momentum)
            min_volume_amount: 최소 거래대금
            limit: 최대 종목 수
        
        Returns:
            종목 코드 리스트
        """
        logger.info(f"Building universe for {strategy_type}")
        
        # 1. 거래대금 필터 (공통)
        liquid_symbols = set(self.filter_by_liquidity(min_volume_amount))
        
        if strategy_type == "mean_reversion":
            # 2. 평균회귀: 저점 종목
            low_price_symbols = set(self.filter_by_price_position(max_position=0.5))
            symbols = list(liquid_symbols & low_price_symbols)
        
        elif strategy_type == "momentum":
            # 2. 모멘텀: 고점 근처 종목
            high_price_symbols = set(self.filter_by_momentum(min_position=0.7))
            symbols = list(liquid_symbols & high_price_symbols)
        
        else:
            # 기본: 거래대금만
            symbols = list(liquid_symbols)
        
        # 3. 제한
        symbols = symbols[:limit]
        
        logger.info(f"Universe built: {len(symbols)} symbols for {strategy_type}")
        return symbols
    
    def save_universe(
        self,
        strategy_type: str,
        symbols: List[str],
        scores: Dict[str, float] = None
    ) -> int:
        """
        유니버스를 DB에 저장
        
        Args:
            strategy_type: 전략 타입
            symbols: 종목 코드 리스트
            scores: 종목별 점수 (선택)
        
        Returns:
            저장된 레코드 수
        """
        session = self.SessionLocal()
        
        try:
            # 기존 유니버스 삭제
            session.query(StockUniverseModel).filter_by(
                strategy_type=strategy_type
            ).delete()
            
            # 새 유니버스 저장
            for rank, symbol in enumerate(symbols, 1):
                score = scores.get(symbol) if scores else None
                
                model = StockUniverseModel(
                    strategy_type=strategy_type,
                    symbol=symbol,
                    rank=rank,
                    score=score
                )
                session.add(model)
            
            session.commit()
            logger.info(f"Saved {len(symbols)} symbols to {strategy_type} universe")
            return len(symbols)
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save universe: {e}")
            return 0
        finally:
            session.close()
    
    def load_universe(self, strategy_type: str) -> List[str]:
        """
        저장된 유니버스 로드
        
        Args:
            strategy_type: 전략 타입
        
        Returns:
            종목 코드 리스트
        """
        session = self.SessionLocal()
        
        try:
            results = session.query(StockUniverseModel).filter_by(
                strategy_type=strategy_type
            ).order_by(StockUniverseModel.rank).all()
            
            symbols = [r.symbol for r in results]
            logger.info(f"Loaded {len(symbols)} symbols from {strategy_type} universe")
            return symbols
        
        finally:
            session.close()
    
    def get_all_symbols(self) -> List[str]:
        """
        전체 종목 코드 조회
        
        Returns:
            종목 코드 리스트
        """
        session = self.SessionLocal()
        
        try:
            results = session.query(StockMasterModel.symbol).filter_by(
                is_active=True
            ).all()
            
            return [r.symbol for r in results]
        
        finally:
            session.close()
