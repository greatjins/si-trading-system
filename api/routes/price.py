"""
시세 관련 API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import pandas as pd

from data.repository import DataRepository
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/{symbol}/ohlc")
async def get_ohlc(
    symbol: str,
    interval: str = Query("1d", regex="^(1m|5m|15m|30m|1h|1d)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    OHLC 데이터 조회
    
    Args:
        symbol: 종목 코드
        interval: 시간 간격
        start_date: 시작일
        end_date: 종료일
        limit: 최대 개수
        
    Returns:
        OHLC 데이터
    """
    try:
        repo = DataRepository()
        
        data = repo.get_ohlc(
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )
        
        if data.empty:
            return {"symbol": symbol, "data": []}
        
        # 최근 limit개만 반환
        data = data.tail(limit)
        
        # DataFrame을 dict로 변환
        records = data.reset_index().to_dict(orient="records")
        
        return {
            "symbol": symbol,
            "interval": interval,
            "count": len(records),
            "data": records
        }
    
    except Exception as e:
        logger.error(f"Failed to get OHLC data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/current")
async def get_current_price(symbol: str):
    """
    현재가 조회
    
    Args:
        symbol: 종목 코드
        
    Returns:
        현재가 정보
    """
    try:
        repo = DataRepository()
        
        # 최근 데이터 조회
        data = repo.get_ohlc(symbol=symbol, interval="1d")
        
        if data.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        latest = data.iloc[-1]
        
        return {
            "symbol": symbol,
            "price": float(latest["close"]),
            "open": float(latest["open"]),
            "high": float(latest["high"]),
            "low": float(latest["low"]),
            "volume": int(latest["volume"]),
            "timestamp": latest.name.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols")
async def get_symbols():
    """
    종목 목록 조회
    
    Returns:
        종목 리스트
    """
    try:
        repo = DataRepository()
        symbols = repo.get_available_symbols()
        
        return {
            "count": len(symbols),
            "symbols": symbols
        }
    
    except Exception as e:
        logger.error(f"Failed to get symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))
