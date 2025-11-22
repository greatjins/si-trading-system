"""
파일 기반 저장소 구현
"""
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import pandas as pd

from utils.types import OHLC
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


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
        OHLC 데이터 저장
        
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
                existing_df = pd.read_parquet(file_path)
                
                # 병합 (중복 제거)
                df = pd.concat([existing_df, df], ignore_index=True)
                df = df.drop_duplicates(subset=["timestamp"], keep="last")
                df = df.sort_values("timestamp")
            
            # Parquet 저장
            df.to_parquet(file_path, index=False)
            
            logger.info(f"Saved {len(ohlc_data)} OHLC bars to {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save OHLC data: {e}")
            return False
    
    async def load_ohlc(
        self,
        symbol: str,
        interval: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Optional[List[OHLC]]:
        """
        OHLC 데이터 로드
        
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
            # Parquet 로드
            df = pd.read_parquet(file_path)
            
            # 날짜 필터링
            if start_date:
                df = df[df["timestamp"] >= start_date]
            if end_date:
                df = df[df["timestamp"] <= end_date]
            
            # DataFrame을 OHLC 리스트로 변환
            ohlc_list = [
                OHLC(
                    symbol=symbol,
                    timestamp=row["timestamp"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"]
                )
                for _, row in df.iterrows()
            ]
            
            logger.info(f"Loaded {len(ohlc_list)} OHLC bars from {file_path}")
            return ohlc_list
        
        except Exception as e:
            logger.error(f"Failed to load OHLC data: {e}")
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
    
    def load(self, symbol: str, interval: str) -> pd.DataFrame:
        """
        OHLC 데이터를 DataFrame으로 로드 (동기 버전)
        
        Args:
            symbol: 종목코드
            interval: 시간 간격
        
        Returns:
            OHLC DataFrame (timestamp가 인덱스)
        """
        file_path = self._make_file_path(symbol, interval)
        
        if not file_path.exists():
            logger.debug(f"File not found: {file_path}")
            return pd.DataFrame()
        
        try:
            # Parquet 로드
            df = pd.read_parquet(file_path)
            
            # timestamp를 인덱스로 설정
            if 'timestamp' in df.columns:
                df.set_index('timestamp', inplace=True)
            
            logger.info(f"Loaded {len(df)} OHLC bars from {file_path}")
            return df
        
        except Exception as e:
            logger.error(f"Failed to load OHLC data: {e}")
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
