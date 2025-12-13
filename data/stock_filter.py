"""
종목 필터링 유틸리티
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from data.models import StockMasterModel
from data.repository import get_db_session
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FinancialFilter:
    """재무 지표 기반 종목 필터"""
    
    def __init__(self):
        """초기화"""
        pass
    
    @staticmethod
    def filter_by_per(
        session: Session,
        min_per: Optional[float] = None,
        max_per: Optional[float] = None
    ) -> List[StockMasterModel]:
        """
        PER 기준 필터링
        
        Args:
            session: DB 세션
            min_per: 최소 PER
            max_per: 최대 PER
            
        Returns:
            필터링된 종목 리스트
        """
        query = session.query(StockMasterModel).filter(
            StockMasterModel.is_active == True,
            StockMasterModel.per.isnot(None)
        )
        
        if min_per is not None:
            query = query.filter(StockMasterModel.per >= min_per)
        if max_per is not None:
            query = query.filter(StockMasterModel.per <= max_per)
        
        return query.all()
    
    @staticmethod
    def filter_by_pbr(
        session: Session,
        min_pbr: Optional[float] = None,
        max_pbr: Optional[float] = None
    ) -> List[StockMasterModel]:
        """
        PBR 기준 필터링
        
        Args:
            session: DB 세션
            min_pbr: 최소 PBR
            max_pbr: 최대 PBR
            
        Returns:
            필터링된 종목 리스트
        """
        query = session.query(StockMasterModel).filter(
            StockMasterModel.is_active == True,
            StockMasterModel.pbr.isnot(None)
        )
        
        if min_pbr is not None:
            query = query.filter(StockMasterModel.pbr >= min_pbr)
        if max_pbr is not None:
            query = query.filter(StockMasterModel.pbr <= max_pbr)
        
        return query.all()
    
    @staticmethod
    def filter_by_roe(
        session: Session,
        min_roe: Optional[float] = None,
        max_roe: Optional[float] = None
    ) -> List[StockMasterModel]:
        """
        ROE 기준 필터링
        
        Args:
            session: DB 세션
            min_roe: 최소 ROE
            max_roe: 최대 ROE
            
        Returns:
            필터링된 종목 리스트
        """
        query = session.query(StockMasterModel).filter(
            StockMasterModel.is_active == True,
            StockMasterModel.roe.isnot(None)
        )
        
        if min_roe is not None:
            query = query.filter(StockMasterModel.roe >= min_roe)
        if max_roe is not None:
            query = query.filter(StockMasterModel.roe <= max_roe)
        
        return query.all()
    
    @staticmethod
    def filter_by_multiple_criteria(
        session: Session,
        criteria: Dict[str, Any]
    ) -> List[StockMasterModel]:
        """
        복합 조건 필터링
        
        Args:
            session: DB 세션
            criteria: 필터 조건 딕셔너리
                {
                    "per_min": 0,
                    "per_max": 15,
                    "pbr_min": 0,
                    "pbr_max": 1.5,
                    "roe_min": 10,
                    "dividend_yield_min": 2.0,
                    "market_cap_min": 1000000000000,  # 1조
                    "foreign_ratio_min": 10.0
                }
            
        Returns:
            필터링된 종목 리스트
        """
        query = session.query(StockMasterModel).filter(
            StockMasterModel.is_active == True
        )
        
        # PER 필터
        if "per_min" in criteria and criteria["per_min"] is not None:
            query = query.filter(
                StockMasterModel.per.isnot(None),
                StockMasterModel.per >= criteria["per_min"]
            )
        if "per_max" in criteria and criteria["per_max"] is not None:
            query = query.filter(
                StockMasterModel.per.isnot(None),
                StockMasterModel.per <= criteria["per_max"]
            )
        
        # PBR 필터
        if "pbr_min" in criteria and criteria["pbr_min"] is not None:
            query = query.filter(
                StockMasterModel.pbr.isnot(None),
                StockMasterModel.pbr >= criteria["pbr_min"]
            )
        if "pbr_max" in criteria and criteria["pbr_max"] is not None:
            query = query.filter(
                StockMasterModel.pbr.isnot(None),
                StockMasterModel.pbr <= criteria["pbr_max"]
            )
        
        # ROE 필터
        if "roe_min" in criteria and criteria["roe_min"] is not None:
            query = query.filter(
                StockMasterModel.roe.isnot(None),
                StockMasterModel.roe >= criteria["roe_min"]
            )
        if "roe_max" in criteria and criteria["roe_max"] is not None:
            query = query.filter(
                StockMasterModel.roe.isnot(None),
                StockMasterModel.roe <= criteria["roe_max"]
            )
        
        # ROA 필터
        if "roa_min" in criteria and criteria["roa_min"] is not None:
            query = query.filter(
                StockMasterModel.roa.isnot(None),
                StockMasterModel.roa >= criteria["roa_min"]
            )
        
        # 배당수익률 필터
        if "dividend_yield_min" in criteria and criteria["dividend_yield_min"] is not None:
            query = query.filter(
                StockMasterModel.dividend_yield.isnot(None),
                StockMasterModel.dividend_yield >= criteria["dividend_yield_min"]
            )
        
        # 시가총액 필터
        if "market_cap_min" in criteria and criteria["market_cap_min"] is not None:
            query = query.filter(
                StockMasterModel.market_cap.isnot(None),
                StockMasterModel.market_cap >= criteria["market_cap_min"]
            )
        if "market_cap_max" in criteria and criteria["market_cap_max"] is not None:
            query = query.filter(
                StockMasterModel.market_cap.isnot(None),
                StockMasterModel.market_cap <= criteria["market_cap_max"]
            )
        
        # 외국인지분율 필터
        if "foreign_ratio_min" in criteria and criteria["foreign_ratio_min"] is not None:
            query = query.filter(
                StockMasterModel.foreign_ratio.isnot(None),
                StockMasterModel.foreign_ratio >= criteria["foreign_ratio_min"]
            )
        
        # 시장 필터
        if "market" in criteria and criteria["market"]:
            query = query.filter(StockMasterModel.market == criteria["market"])
        
        return query.all()
    
    @staticmethod
    def get_value_stocks(
        session: Session,
        per_max: float = 10,
        pbr_max: float = 1.0,
        roe_min: float = 10,
        limit: int = 50
    ) -> List[StockMasterModel]:
        """
        가치주 필터 (저PER, 저PBR, 고ROE)
        
        Args:
            session: DB 세션
            per_max: 최대 PER
            pbr_max: 최대 PBR
            roe_min: 최소 ROE
            limit: 최대 개수
            
        Returns:
            가치주 리스트
        """
        stocks = session.query(StockMasterModel).filter(
            StockMasterModel.is_active == True,
            StockMasterModel.per.isnot(None),
            StockMasterModel.pbr.isnot(None),
            StockMasterModel.roe.isnot(None),
            StockMasterModel.per > 0,
            StockMasterModel.per <= per_max,
            StockMasterModel.pbr > 0,
            StockMasterModel.pbr <= pbr_max,
            StockMasterModel.roe >= roe_min
        ).order_by(
            StockMasterModel.pbr.asc()  # PBR 낮은 순
        ).limit(limit).all()
        
        logger.info(f"Found {len(stocks)} value stocks (PER<={per_max}, PBR<={pbr_max}, ROE>={roe_min})")
        return stocks
    
    @staticmethod
    def get_dividend_stocks(
        session: Session,
        dividend_yield_min: float = 3.0,
        limit: int = 50
    ) -> List[StockMasterModel]:
        """
        배당주 필터 (고배당)
        
        Args:
            session: DB 세션
            dividend_yield_min: 최소 배당수익률
            limit: 최대 개수
            
        Returns:
            배당주 리스트
        """
        stocks = session.query(StockMasterModel).filter(
            StockMasterModel.is_active == True,
            StockMasterModel.dividend_yield.isnot(None),
            StockMasterModel.dividend_yield >= dividend_yield_min
        ).order_by(
            StockMasterModel.dividend_yield.desc()  # 배당수익률 높은 순
        ).limit(limit).all()
        
        logger.info(f"Found {len(stocks)} dividend stocks (yield>={dividend_yield_min}%)")
        return stocks
    
    @staticmethod
    def get_quality_stocks(
        session: Session,
        roe_min: float = 15,
        roa_min: float = 10,
        market_cap_min: float = 1_000_000_000_000,  # 1조
        limit: int = 50
    ) -> List[StockMasterModel]:
        """
        우량주 필터 (고ROE, 고ROA, 대형주)
        
        Args:
            session: DB 세션
            roe_min: 최소 ROE
            roa_min: 최소 ROA
            market_cap_min: 최소 시가총액
            limit: 최대 개수
            
        Returns:
            우량주 리스트
        """
        stocks = session.query(StockMasterModel).filter(
            StockMasterModel.is_active == True,
            StockMasterModel.roe.isnot(None),
            StockMasterModel.roa.isnot(None),
            StockMasterModel.market_cap.isnot(None),
            StockMasterModel.roe >= roe_min,
            StockMasterModel.roa >= roa_min,
            StockMasterModel.market_cap >= market_cap_min
        ).order_by(
            StockMasterModel.roe.desc()  # ROE 높은 순
        ).limit(limit).all()
        
        logger.info(f"Found {len(stocks)} quality stocks (ROE>={roe_min}, ROA>={roa_min})")
        return stocks


# 편의 함수
def get_value_stocks(per_max: float = 10, pbr_max: float = 1.0, roe_min: float = 10, limit: int = 50) -> List[str]:
    """가치주 종목 코드 리스트"""
    session = get_db_session()
    try:
        stocks = FinancialFilter.get_value_stocks(session, per_max, pbr_max, roe_min, limit)
        return [s.symbol for s in stocks]
    finally:
        session.close()


def get_dividend_stocks(dividend_yield_min: float = 3.0, limit: int = 50) -> List[str]:
    """배당주 종목 코드 리스트"""
    session = get_db_session()
    try:
        stocks = FinancialFilter.get_dividend_stocks(session, dividend_yield_min, limit)
        return [s.symbol for s in stocks]
    finally:
        session.close()


def get_quality_stocks(roe_min: float = 15, roa_min: float = 10, market_cap_min: float = 1_000_000_000_000, limit: int = 50) -> List[str]:
    """우량주 종목 코드 리스트"""
    session = get_db_session()
    try:
        stocks = FinancialFilter.get_quality_stocks(session, roe_min, roa_min, market_cap_min, limit)
        return [s.symbol for s in stocks]
    finally:
        session.close()
