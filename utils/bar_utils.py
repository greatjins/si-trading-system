"""
OHLCV 바 생성 및 검증 유틸리티
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from utils.types import OHLC
from utils.logger import setup_logger

logger = setup_logger(__name__)


def validate_bars(bars: pd.DataFrame, symbol: str = "UNKNOWN") -> pd.DataFrame:
    """
    바 데이터 유효성 검증 및 정리
    
    Args:
        bars: OHLCV DataFrame
        symbol: 종목 코드 (로깅용)
    
    Returns:
        검증된 DataFrame
    
    Raises:
        ValueError: 필수 컬럼이 없는 경우
    """
    # 필수 컬럼 확인
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in bars.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for {symbol}: {missing_cols}")
    
    if len(bars) == 0:
        logger.warning(f"Empty DataFrame for {symbol}")
        return bars
    
    # high/low 검증
    invalid_hl = bars['high'] < bars['low']
    if invalid_hl.any():
        logger.warning(f"Found {invalid_hl.sum()} bars with high < low for {symbol}, fixing...")
        # high와 low를 교환
        bars.loc[invalid_hl, ['high', 'low']] = bars.loc[invalid_hl, ['low', 'high']].values
    
    # 음수 가격 제거
    negative_prices = (bars[['open', 'high', 'low', 'close']] < 0).any(axis=1)
    if negative_prices.any():
        logger.warning(f"Found {negative_prices.sum()} bars with negative prices for {symbol}, removing...")
        bars = bars[~negative_prices]
    
    # NaN 처리 (forward fill)
    if bars.isna().any().any():
        nan_count = bars.isna().sum().sum()
        logger.warning(f"Found {nan_count} NaN values for {symbol}, forward filling...")
        bars = bars.fillna(method='ffill')
        # 첫 행에 NaN이 남아있으면 제거
        bars = bars.dropna()
    
    # value 컬럼 처리
    if 'value' not in bars.columns or bars['value'].isna().all():
        bars['value'] = bars['volume'] * bars['close']
        logger.debug(f"Calculated 'value' column for {symbol}")
    
    # Zero volume 처리
    zero_volume = bars['volume'] == 0
    if zero_volume.any():
        logger.debug(f"Found {zero_volume.sum()} bars with zero volume for {symbol}")
        # value도 0으로 설정
        bars.loc[zero_volume, 'value'] = 0
    
    return bars


def create_bars_from_ticks(
    ticks: List[Dict[str, Any]],
    timeframe_seconds: int,
    lookback: int = 100
) -> Optional[pd.DataFrame]:
    """
    틱 데이터에서 OHLCV 바 생성
    
    Args:
        ticks: 틱 데이터 리스트
            각 틱은 {'timestamp': datetime, 'price': float, 'volume': int|float, 'value': float|None} 형태
        timeframe_seconds: 타임프레임 (초)
        lookback: 반환할 최대 바 개수
    
    Returns:
        OHLCV DataFrame (timestamp 인덱스) 또는 None
    """
    if not ticks:
        return None
    
    try:
        # DataFrame으로 변환
        df = pd.DataFrame(ticks)
        
        # timestamp 컬럼 처리
        if 'timestamp' not in df.columns:
            logger.warning("No timestamp in ticks")
            return None
        
        # timestamp를 datetime으로 변환
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # 필수 컬럼 확인
        if 'price' not in df.columns:
            logger.error("No price column in ticks")
            return None
        
        # volume이 없으면 0으로 채움
        if 'volume' not in df.columns:
            df['volume'] = 0
            logger.warning("No volume in ticks, using 0")
        
        # value 계산 (없으면 volume * price)
        if 'value' not in df.columns or df['value'].isna().all():
            df['value'] = df['volume'] * df['price']
        
        # 타임프레임에 맞춰 리샘플링
        bars = df.resample(f'{timeframe_seconds}S').agg({
            'price': ['first', 'max', 'min', 'last'],
            'volume': 'sum',
            'value': 'sum'
        })
        
        # 컬럼명 정리
        bars.columns = ['open', 'high', 'low', 'close', 'volume', 'value']
        
        # NaN 제거 (거래가 없는 구간)
        bars = bars.dropna(subset=['close'])
        
        if len(bars) == 0:
            logger.debug("No valid bars after resampling")
            return None
        
        # lookback 적용
        if len(bars) > lookback:
            bars = bars.iloc[-lookback:]
        
        return bars
    
    except Exception as e:
        logger.error(f"Failed to create bars from ticks: {e}", exc_info=True)
        return None


def ohlc_list_to_dataframe(ohlc_list: List[OHLC]) -> pd.DataFrame:
    """
    OHLC 객체 리스트를 DataFrame으로 변환
    
    Args:
        ohlc_list: OHLC 객체 리스트
    
    Returns:
        OHLCV DataFrame (timestamp 인덱스)
    """
    if not ohlc_list:
        return pd.DataFrame()
    
    data = {
        'timestamp': [bar.timestamp for bar in ohlc_list],
        'open': [bar.open for bar in ohlc_list],
        'high': [bar.high for bar in ohlc_list],
        'low': [bar.low for bar in ohlc_list],
        'close': [bar.close for bar in ohlc_list],
        'volume': [bar.volume for bar in ohlc_list],
        'value': [bar.value if bar.value is not None else bar.volume * bar.close for bar in ohlc_list]
    }
    
    df = pd.DataFrame(data)
    df = df.set_index('timestamp')
    
    return df


def dataframe_to_ohlc_list(df: pd.DataFrame, symbol: str) -> List[OHLC]:
    """
    DataFrame을 OHLC 객체 리스트로 변환
    
    Args:
        df: OHLCV DataFrame (timestamp 인덱스)
        symbol: 종목 코드
    
    Returns:
        OHLC 객체 리스트
    """
    ohlc_list = []
    
    for timestamp, row in df.iterrows():
        ohlc = OHLC(
            symbol=symbol,
            timestamp=timestamp,
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=int(row['volume']),
            value=row.get('value')
        )
        ohlc_list.append(ohlc)
    
    return ohlc_list
