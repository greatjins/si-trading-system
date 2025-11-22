"""
LS증권 OHLC 데이터 조회
"""
from typing import List
from datetime import datetime

from broker.ls.client import LSClient
from broker.ls.models import LSOHLC
from utils.types import OHLC
from utils.logger import setup_logger

logger = setup_logger(__name__)


class LSOHLCService:
    """LS증권 OHLC 데이터 서비스"""
    
    def __init__(self, client: LSClient):
        self.client = client
    
    async def get_daily_ohlc(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[OHLC]:
        """
        일봉 데이터 조회
        
        Args:
            symbol: 종목코드 (6자리)
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            OHLC 데이터 리스트
        """
        logger.info(f"Fetching daily OHLC for {symbol}")
        
        # TODO: 실제 LS증권 API 엔드포인트 호출
        # 예시 엔드포인트: /uapi/domestic-stock/v1/quotations/inquire-daily-price
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분 (J: 주식)
            "FID_INPUT_ISCD": symbol,
            "FID_PERIOD_DIV_CODE": "D",  # 기간구분 (D: 일봉)
            "FID_ORG_ADJ_PRC": "0",  # 수정주가 (0: 원주가)
        }
        
        try:
            # response = await self.client.get("/uapi/domestic-stock/v1/quotations/inquire-daily-price", params=params)
            # data = response.get("output", [])
            
            # Mock 데이터 반환 (개발용)
            logger.warning("Using MOCK data - implement actual API call")
            return []
        
        except Exception as e:
            logger.error(f"Failed to fetch daily OHLC: {e}")
            raise
    
    async def get_minute_ohlc(
        self,
        symbol: str,
        interval: int,  # 1, 5, 10, 30
        start_date: datetime,
        end_date: datetime
    ) -> List[OHLC]:
        """
        분봉 데이터 조회
        
        Args:
            symbol: 종목코드
            interval: 분봉 간격 (1, 5, 10, 30)
            start_date: 시작일시
            end_date: 종료일시
        
        Returns:
            OHLC 데이터 리스트
        """
        logger.info(f"Fetching {interval}min OHLC for {symbol}")
        
        # TODO: 실제 LS증권 분봉 API 엔드포인트 호출
        
        try:
            # Mock 데이터 반환 (개발용)
            logger.warning("Using MOCK data - implement actual API call")
            return []
        
        except Exception as e:
            logger.error(f"Failed to fetch minute OHLC: {e}")
            raise
    
    def _parse_ohlc_data(self, data: List[LSOHLC], symbol: str) -> List[OHLC]:
        """LS API 응답을 OHLC 타입으로 변환"""
        ohlc_list: List[OHLC] = []
        
        for item in data:
            try:
                ohlc = OHLC(
                    symbol=symbol,
                    timestamp=datetime.strptime(item.stck_bsop_date, "%Y%m%d"),
                    open=float(item.stck_oprc),
                    high=float(item.stck_hgpr),
                    low=float(item.stck_lwpr),
                    close=float(item.stck_clpr),
                    volume=int(item.acml_vol)
                )
                ohlc_list.append(ohlc)
            except Exception as e:
                logger.warning(f"Failed to parse OHLC data: {e}")
                continue
        
        return ohlc_list
