"""
파일 기반 저장소 구현
"""
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa

from utils.types import OHLC
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)

# 필요한 컬럼만 정의 (Projection 최적화)
REQUIRED_COLUMNS = ['timestamp', 'open', 'high', 'low', 'close', 'volume']


class FileStorage:
    """
    파일 기반 OHLC 데이터 저장소
    
    Parquet 형식으로 OHLC 데이터를 저장합니다.
    """
    
    def __init__(self, base_path: str = None):
        """
        Args:
            base_path: 저장소 기본 경로 (None이면 config에서 로드)
        """
        self.base_path = Path(base_path or config.get("storage.path", "data/ohlc"))
        
        # 디렉토리 생성
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileStorage initialized at: {self.base_path}")
    
    def _make_file_path(self, symbol: str, interval: str) -> Path:
        """파일 경로 생성"""
        # 종목별 디렉토리
        symbol_dir = self.base_path / symbol
        symbol_dir.mkdir(exist_ok=True)
        
        # 파일명: {symbol}_{interval}.parquet
        filename = f"{symbol}_{interval}.parquet"
        return symbol_dir / filename
    
    async def save_ohlc(
        self,
        symbol: str,
        interval: str,
        ohlc_data: List[OHLC]
    ) -> bool:
        """
        OHLC 데이터 저장 (최적화: Cache Eviction 포함)
        
        Args:
            symbol: 종목코드
            interval: 시간 간격
            ohlc_data: OHLC 데이터
        
        Returns:
            저장 성공 여부
        """
        if not ohlc_data:
            return False
        
        file_path = self._make_file_path(symbol, interval)
        
        try:
            # OHLC를 DataFrame으로 변환
            df = pd.DataFrame([
                {
                    "timestamp": bar.timestamp,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume
                }
                for bar in ohlc_data
            ])
            
            # 기존 데이터 로드 (있으면)
            if file_path.exists():
                try:
                    # PyArrow로 필요한 컬럼만 읽기
                    existing_df = pd.read_parquet(
                        file_path,
                        engine='pyarrow',
                        columns=REQUIRED_COLUMNS
                    )
                    
                    # 병합 (중복 제거)
                    df = pd.concat([existing_df, df], ignore_index=True)
                    df = df.drop_duplicates(subset=["timestamp"], keep="last")
                    df = df.sort_values("timestamp")
                except Exception as e:
                    logger.warning(f"Failed to load existing data, overwriting: {e}")
            
            # Cache Eviction: 최근 1년치 데이터만 유지 (타임존 고려)
            from datetime import timezone
            kst = timezone(timedelta(hours=9))
            cutoff_date = datetime.now(kst) - timedelta(days=365)
            # 타임존 없는 timestamp는 naive datetime으로 처리
            if df["timestamp"].dtype == 'datetime64[ns]':
                df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
            df = df[df["timestamp"] >= cutoff_date.replace(tzinfo=None)]
            
            if df.empty:
                logger.warning(f"All data older than 1 year for {symbol} ({interval}), skipping save")
                return False
            
            # Parquet 저장 (pyarrow 엔진 사용)
            df.to_parquet(
                file_path, 
                index=False,
                engine='pyarrow',
                compression='snappy'  # 압축 최적화
            )
            
            logger.info(f"Saved {len(df)} OHLC bars to {file_path} (1 year retention)")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save OHLC data: {e}", exc_info=True)
            return False
    
    async def load_ohlc(
        self,
        symbol: str,
        interval: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Optional[List[OHLC]]:
        """
        OHLC 데이터 로드 (최적화)
        
        Args:
            symbol: 종목코드
            interval: 시간 간격
            start_date: 시작일 (None이면 전체)
            end_date: 종료일 (None이면 전체)
        
        Returns:
            OHLC 데이터 (없으면 None)
        """
        file_path = self._make_file_path(symbol, interval)
        
        if not file_path.exists():
            logger.debug(f"File not found: {file_path}")
            return None
        
        try:
            # 최적화된 로드 (컬럼 선택 + 필터링)
            df = self.load(symbol, interval, start_date, end_date)
            
            if df.empty:
                return None
            
            # DataFrame을 OHLC 리스트로 변환 (벡터화 연산 사용)
            # iterrows() 대신 to_dict('records') 사용
            df_reset = df.reset_index()
            ohlc_list = []
            for row in df_reset.to_dict('records'):
                # timestamp 변환 (DatetimeIndex 또는 datetime 객체 처리)
                ts = row["timestamp"]
                if isinstance(ts, pd.Timestamp):
                    ts = ts.to_pydatetime()
                elif not isinstance(ts, datetime):
                    # 문자열인 경우 파싱 시도
                    try:
                        ts = pd.to_datetime(ts).to_pydatetime()
                    except:
                        logger.warning(f"Invalid timestamp format: {ts}")
                        continue
                
                ohlc_list.append(
                    OHLC(
                        symbol=symbol,
                        timestamp=ts,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=int(row["volume"])
                    )
                )
            
            logger.debug(f"Loaded {len(ohlc_list)} OHLC bars from {file_path}")
            return ohlc_list
        
        except Exception as e:
            logger.error(f"Failed to load OHLC data: {e}", exc_info=True)
            return None
    
    async def delete_ohlc(self, symbol: str, interval: str = None) -> bool:
        """
        OHLC 데이터 삭제
        
        Args:
            symbol: 종목코드
            interval: 시간 간격 (None이면 해당 종목 전체 삭제)
        
        Returns:
            삭제 성공 여부
        """
        try:
            if interval:
                # 특정 interval 파일 삭제
                file_path = self._make_file_path(symbol, interval)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted: {file_path}")
                    return True
            else:
                # 종목 디렉토리 전체 삭제
                symbol_dir = self.base_path / symbol
                if symbol_dir.exists():
                    import shutil
                    shutil.rmtree(symbol_dir)
                    logger.info(f"Deleted directory: {symbol_dir}")
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to delete OHLC data: {e}")
            return False
    
    def load(
        self, 
        symbol: str, 
        interval: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        OHLC 데이터를 DataFrame으로 로드 (동기 버전, 최적화)
        
        Args:
            symbol: 종목코드
            interval: 시간 간격
            start_date: 시작일 (None이면 전체)
            end_date: 종료일 (None이면 전체)
        
        Returns:
            OHLC DataFrame (timestamp가 인덱스, 시계열 정렬됨)
        """
        file_path = self._make_file_path(symbol, interval)
        
        if not file_path.exists():
            logger.debug(f"File not found: {file_path}")
            return pd.DataFrame()
        
        try:
            # PyArrow를 사용한 최적화된 로드
            # 1. 필요한 컬럼만 선택 (Projection)
            # 2. 날짜 필터링 (Predicate Pushdown)
            filters = None
            if start_date or end_date:
                filter_list = []
                if start_date:
                    filter_list.append(('timestamp', '>=', start_date))
                if end_date:
                    filter_list.append(('timestamp', '<=', end_date))
                filters = filter_list
            
            # PyArrow로 읽기 (컬럼 선택 + 필터링)
            try:
                # PyArrow filters 형식: 리스트의 리스트 또는 단일 리스트
                # [('timestamp', '>=', start_date)] 또는 [[('timestamp', '>=', start_date)]]
                pyarrow_filters = None
                if filters:
                    # PyArrow는 리스트의 리스트 형식을 선호
                    pyarrow_filters = [filters] if isinstance(filters[0], tuple) else filters
                
                table = pq.read_table(
                    file_path,
                    columns=REQUIRED_COLUMNS,  # 필요한 컬럼만 선택
                    filters=pyarrow_filters,  # Predicate pushdown
                    use_pandas_metadata=True
                )
                df = table.to_pandas()
            except Exception as e:
                # PyArrow 실패 시 pandas fallback
                logger.warning(f"PyArrow read failed, using pandas fallback: {e}")
                df = pd.read_parquet(
                    file_path,
                    engine='pyarrow',  # pyarrow 엔진 사용
                    columns=REQUIRED_COLUMNS  # 필요한 컬럼만 선택
                )
                # 메모리에서 필터링 (fallback)
                # 타임존 처리: naive datetime으로 변환하여 비교
                if 'timestamp' in df.columns:
                    if df["timestamp"].dtype == 'datetime64[ns]':
                        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
                    if start_date:
                        start_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
                        df = df[df["timestamp"] >= start_naive]
                    if end_date:
                        end_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
                        df = df[df["timestamp"] <= end_naive]
            
            if df.empty:
                logger.debug(f"Empty DataFrame after filtering: {file_path}")
                return pd.DataFrame()
            
            # timestamp를 인덱스로 설정
            if 'timestamp' in df.columns:
                df.set_index('timestamp', inplace=True)
            
            # 시계열 정렬 검증 및 정렬
            if not df.index.is_monotonic_increasing:
                logger.warning(f"Timestamp not sorted for {symbol} ({interval}), sorting...")
                df = df.sort_index()
            
            logger.debug(f"Loaded {len(df)} OHLC bars from {file_path} (columns: {list(df.columns)})")
            return df
        
        except Exception as e:
            logger.error(f"Failed to load OHLC data: {e}", exc_info=True)
            return pd.DataFrame()
    
    def list_symbols(self) -> List[str]:
        """저장된 종목 목록 조회"""
        try:
            symbols = [
                d.name for d in self.base_path.iterdir()
                if d.is_dir()
            ]
            return sorted(symbols)
        except Exception as e:
            logger.error(f"Failed to list symbols: {e}")
            return []
    
    def get_storage_size(self) -> int:
        """저장소 크기 조회 (바이트)"""
        try:
            total_size = 0
            for file_path in self.base_path.rglob("*.parquet"):
                total_size += file_path.stat().st_size
            return total_size
        except Exception as e:
            logger.error(f"Failed to get storage size: {e}")
            return 0
    
    def evict_old_data(self, retention_days: int = 365) -> int:
        """
        오래된 데이터 삭제 (Cache Eviction)
        
        Args:
            retention_days: 보관 기간 (일, 기본: 365일)
        
        Returns:
            삭제된 파일 수
        """
        from datetime import timezone
        kst = timezone(timedelta(hours=9))
        cutoff_date = datetime.now(kst) - timedelta(days=retention_days)
        cutoff_naive = cutoff_date.replace(tzinfo=None)  # naive datetime으로 변환
        deleted_count = 0
        
        try:
            for file_path in self.base_path.rglob("*.parquet"):
                try:
                    # 파일의 최신 데이터 확인
                    df = pd.read_parquet(
                        file_path,
                        engine='pyarrow',
                        columns=['timestamp']
                    )
                    
                    if df.empty:
                        continue
                    
                    # 최신 timestamp 확인 (타임존 처리)
                    max_timestamp = df['timestamp'].max()
                    if isinstance(max_timestamp, pd.Timestamp):
                        max_timestamp = max_timestamp.to_pydatetime()
                    # 타임존 제거하여 비교
                    if max_timestamp.tzinfo:
                        max_timestamp = max_timestamp.replace(tzinfo=None)
                    
                    # 오래된 데이터면 파일 삭제
                    if max_timestamp < cutoff_naive:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Evicted old data: {file_path} (latest: {max_timestamp.date()})")
                
                except Exception as e:
                    logger.warning(f"Failed to check {file_path} for eviction: {e}")
                    continue
            
            if deleted_count > 0:
                logger.info(f"Cache eviction completed: {deleted_count} files deleted")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Failed to evict old data: {e}", exc_info=True)
            return deleted_count
