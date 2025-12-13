"""
데이터 로더 모듈
"""
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

from data.repository import get_db_session
from data.models import OHLCModel, StockMasterModel
from utils.types import OHLC
from utils.logger import setup_logger

logger = setup_logger(__name__)


class OHLCLoader:
    """OHLC 데이터 로더"""
    
    def __init__(self):
        self.db_session = None
    
    async def load_ohlc(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[OHLC]:
        """
        OHLC 데이터 로드
        
        Args:
            symbol: 종목 코드
            start_date: 시작일
            end_date: 종료일
            interval: 시간 간격
            
        Returns:
            OHLC 데이터 리스트
        """
        try:
            db = get_db_session()
            
            # DB에서 OHLC 데이터 조회
            query = db.query(OHLCModel).filter(
                OHLCModel.symbol == symbol,
                OHLCModel.timestamp >= start_date,
                OHLCModel.timestamp <= end_date
            ).order_by(OHLCModel.timestamp)
            
            ohlc_records = query.all()
            
            if not ohlc_records:
                logger.warning(f"No OHLC data found for {symbol} from {start_date} to {end_date}")
                # 샘플 데이터 생성
                return self._generate_sample_data(symbol, start_date, end_date)
            
            # OHLC 객체로 변환
            ohlc_data = []
            for record in ohlc_records:
                ohlc = OHLC(
                    symbol=record.symbol,
                    timestamp=record.timestamp,
                    open=record.open,
                    high=record.high,
                    low=record.low,
                    close=record.close,
                    volume=record.volume,
                    value=record.value
                )
                ohlc_data.append(ohlc)
            
            logger.info(f"Loaded {len(ohlc_data)} OHLC records for {symbol}")
            return ohlc_data
            
        except Exception as e:
            logger.error(f"Failed to load OHLC data for {symbol}: {e}")
            # 에러 시 샘플 데이터 반환
            return self._generate_sample_data(symbol, start_date, end_date)
        finally:
            if db:
                db.close()
    
    def _generate_sample_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[OHLC]:
        """샘플 OHLC 데이터 생성"""
        import random
        import numpy as np
        
        logger.info(f"Generating sample OHLC data for {symbol}")
        
        # 기본 가격 설정
        base_prices = {
            "005930": 70000,  # 삼성전자
            "000660": 130000,  # SK하이닉스
            "035420": 300000,  # NAVER
            "051910": 900000,  # LG화학
            "006400": 35000,   # 삼성SDI
        }
        
        base_price = base_prices.get(symbol, 50000)
        current_price = base_price
        
        ohlc_data = []
        current_date = start_date
        
        while current_date <= end_date:
            # 일일 변동률 (-3% ~ +3%)
            daily_return = random.uniform(-0.03, 0.03)
            
            # OHLC 생성
            open_price = current_price
            close_price = open_price * (1 + daily_return)
            
            # High/Low 생성 (Open/Close 기준)
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.02)
            low_price = min(open_price, close_price) * random.uniform(0.98, 1.0)
            
            # 거래량 생성
            volume = random.randint(100000, 1000000)
            value = volume * close_price
            
            ohlc = OHLC(
                symbol=symbol,
                timestamp=current_date,
                open=round(open_price),
                high=round(high_price),
                low=round(low_price),
                close=round(close_price),
                volume=volume,
                value=value
            )
            
            ohlc_data.append(ohlc)
            current_price = close_price
            current_date += timedelta(days=1)
        
        return ohlc_data


class MarketDataLoader:
    """시장 데이터 로더"""
    
    async def load_market_data(self, date: datetime) -> pd.DataFrame:
        """
        특정 날짜의 전체 시장 데이터 로드
        
        Args:
            date: 기준일
            
        Returns:
            시장 데이터 DataFrame
        """
        try:
            db = get_db_session()
            
            # 종목 마스터 데이터 조회
            query = db.query(StockMasterModel).filter(
                StockMasterModel.is_active == True
            )
            
            stock_records = query.all()
            
            if not stock_records:
                logger.warning("No stock master data found")
                return pd.DataFrame()
            
            # DataFrame으로 변환
            data = []
            for record in stock_records:
                data.append({
                    'symbol': record.symbol,
                    'name': record.name,
                    'market': record.market,
                    'close': record.current_price or 50000,
                    'volume': record.volume or 100000,
                    'volume_amount': record.volume_amount or 5000000000,
                    'market_cap': record.market_cap or 1000000,
                    'per': record.per or 15.0,
                    'pbr': record.pbr or 1.5,
                    'roe': record.roe or 10.0,
                    'debt_ratio': record.debt_ratio or 50.0,
                    'price_position': record.price_position or 0.5
                })
            
            df = pd.DataFrame(data)
            df.set_index('symbol', inplace=True)
            
            logger.info(f"Loaded market data for {len(df)} stocks")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load market data: {e}")
            return self._generate_sample_market_data()
        finally:
            if db:
                db.close()
    
    def _generate_sample_market_data(self) -> pd.DataFrame:
        """샘플 시장 데이터 생성"""
        import random
        
        logger.info("Generating sample market data")
        
        # 샘플 종목들
        symbols = [
            "005930", "000660", "035420", "051910", "006400",
            "028260", "207940", "005380", "068270", "035720",
            "003670", "096770", "017670", "034020", "018260"
        ]
        
        data = []
        for symbol in symbols:
            data.append({
                'symbol': symbol,
                'name': f"종목{symbol}",
                'market': random.choice(['KOSPI', 'KOSDAQ']),
                'close': random.randint(10000, 100000),
                'volume': random.randint(100000, 1000000),
                'volume_amount': random.randint(1000000000, 50000000000),
                'market_cap': random.randint(500000, 50000000),
                'per': random.uniform(5.0, 30.0),
                'pbr': random.uniform(0.5, 3.0),
                'roe': random.uniform(5.0, 25.0),
                'debt_ratio': random.uniform(20.0, 80.0),
                'price_position': random.uniform(0.2, 0.8)
            })
        
        df = pd.DataFrame(data)
        df.set_index('symbol', inplace=True)
        
        return df


class UniverseLoader:
    """종목 유니버스 로더"""
    
    async def load_universe(
        self,
        date: datetime,
        filters: dict = None
    ) -> List[str]:
        """
        종목 유니버스 로드
        
        Args:
            date: 기준일
            filters: 필터 조건
            
        Returns:
            종목 코드 리스트
        """
        try:
            market_loader = MarketDataLoader()
            market_data = await market_loader.load_market_data(date)
            
            if market_data.empty:
                return []
            
            # 필터 적용
            if filters:
                filtered_data = market_data.copy()
                
                # 시가총액 필터
                if 'market_cap_min' in filters:
                    filtered_data = filtered_data[
                        filtered_data['market_cap'] >= filters['market_cap_min']
                    ]
                
                # 거래대금 필터
                if 'volume_amount_min' in filters:
                    filtered_data = filtered_data[
                        filtered_data['volume_amount'] >= filters['volume_amount_min']
                    ]
                
                # PER 필터
                if 'per_max' in filters:
                    filtered_data = filtered_data[
                        filtered_data['per'] <= filters['per_max']
                    ]
                
                return filtered_data.index.tolist()
            
            return market_data.index.tolist()
            
        except Exception as e:
            logger.error(f"Failed to load universe: {e}")
            return []