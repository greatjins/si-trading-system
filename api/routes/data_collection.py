"""
데이터 수집 API 라우터
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio

from broker.ls.adapter import LSAdapter
from data.repository import OHLCRepository, get_db_session
from data.models import StockMasterModel
from data.stock_filter import StockFilter
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/data", tags=["data"])

# 전역 상태 관리
collection_status = {
    "is_running": False,
    "current_symbol": None,
    "progress": 0,
    "total": 0,
    "logs": [],
    "start_time": None,
    "error": None
}


class CollectionRequest(BaseModel):
    """데이터 수집 요청"""
    count: int = 200  # 수집할 종목 수
    days: int = 180   # 수집 기간 (일)
    strategy: Optional[str] = None  # mean_reversion, momentum


class CollectionStatus(BaseModel):
    """데이터 수집 상태"""
    is_running: bool
    current_symbol: Optional[str]
    progress: int
    total: int
    logs: List[str]
    start_time: Optional[datetime]
    error: Optional[str]


async def collect_data_background(count: int, days: int):
    """백그라운드 데이터 수집"""
    global collection_status
    
    try:
        collection_status["is_running"] = True
        collection_status["start_time"] = datetime.now()
        collection_status["logs"] = []
        collection_status["error"] = None
        
        # 로그 추가 함수
        def add_log(message: str):
            collection_status["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            if len(collection_status["logs"]) > 100:
                collection_status["logs"].pop(0)
        
        add_log(f"데이터 수집 시작: 상위 {count}종목, {days}일")
        
        # LS증권 어댑터 초기화
        async with LSAdapter() as adapter:
            # 1. 전체 종목 조회 (시장 구분 매핑용)
            add_log("전체 종목 정보 조회 중...")
            all_symbols = await adapter.market_service.get_all_symbols(market="0")
            symbol_market_map = {s["symbol"]: s["market"] for s in all_symbols}
            add_log(f"✓ {len(all_symbols)}개 종목 정보 로드")
            
            # 2. 거래대금 상위 종목 조회
            add_log("거래대금 상위 종목 조회 중...")
            top_stocks = await adapter.market_service.get_top_volume_stocks(
                market="0",
                count=count
            )
            
            collection_status["total"] = len(top_stocks)
            add_log(f"✓ {len(top_stocks)}개 종목 선별 완료")
            
            # 2. 각 종목 데이터 수집
            repo = OHLCRepository()
            
            for idx, stock_info in enumerate(top_stocks, 1):
                session = get_db_session()  # 각 종목마다 새 세션
                if not collection_status["is_running"]:
                    add_log("⚠️ 사용자에 의해 중지됨")
                    break
                
                symbol = stock_info["symbol"]
                name = stock_info["name"]
                
                collection_status["current_symbol"] = f"{name} ({symbol})"
                collection_status["progress"] = idx
                
                add_log(f"[{idx}/{len(top_stocks)}] {name} ({symbol}) 처리 중...")
                
                try:
                    # OHLC 데이터 수집 (영업일 기준으로 충분히 수집)
                    end_date = datetime.now()
                    from datetime import timedelta
                    
                    # 영업일 N개를 확보하기 위해 충분한 기간 조회
                    # 영업일 비율: 약 70% (주말 제외) → 1.5배 여유
                    calendar_days = int(days * 1.5)
                    start_date = end_date - timedelta(days=calendar_days)
                    
                    ohlc_list = await adapter.get_ohlc(
                        symbol=symbol,
                        interval="1d",
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    # 요청한 개수만큼만 사용 (최신 N개)
                    if len(ohlc_list) > days:
                        ohlc_list = ohlc_list[-days:]
                    
                    if ohlc_list:
                        high_52w = max([o.high for o in ohlc_list])
                        low_52w = min([o.low for o in ohlc_list])
                        current_price = ohlc_list[-1].close
                        price_position = current_price / high_52w if high_52w > 0 else 0
                        
                        # stock_master 저장
                        # 시장 구분 (symbol_market_map에서 조회)
                        market_code = symbol_market_map.get(symbol, "1")
                        market = "KOSPI" if market_code == "1" else "KOSDAQ"
                        
                        stock = StockMasterModel(
                            symbol=symbol,
                            name=name,
                            market=market,
                            current_price=current_price,
                            volume_amount=stock_info["volume_amount"],
                            high_52w=high_52w,
                            low_52w=low_52w,
                            price_position=price_position,
                            is_active=True,
                            updated_at=datetime.now()
                        )
                        session.merge(stock)
                        session.commit()
                        
                        # OHLC 데이터 저장
                        saved = await repo.save_ohlc_batch(ohlc_list, "1d")
                        add_log(f"  ✓ {len(ohlc_list)}개 데이터 수집, {saved}개 저장")
                    else:
                        add_log(f"  ⚠️ 데이터 없음")
                    
                    # Rate Limit
                    await asyncio.sleep(1.1)
                
                except Exception as e:
                    add_log(f"  ✗ 오류: {str(e)}")
                finally:
                    session.close()  # 각 종목 처리 후 세션 닫기
            
            add_log(f"✅ 데이터 수집 완료!")
    
    except Exception as e:
        collection_status["error"] = str(e)
        add_log(f"❌ 오류 발생: {str(e)}")
        logger.error(f"Data collection error: {e}")
    
    finally:
        collection_status["is_running"] = False
        collection_status["current_symbol"] = None


@router.post("/collect/start")
async def start_collection(
    request: CollectionRequest,
    background_tasks: BackgroundTasks
):
    """데이터 수집 시작"""
    global collection_status
    
    if collection_status["is_running"]:
        raise HTTPException(status_code=400, detail="이미 수집이 진행 중입니다")
    
    # 백그라운드 태스크로 실행
    background_tasks.add_task(
        collect_data_background,
        request.count,
        request.days
    )
    
    return {"message": "데이터 수집이 시작되었습니다"}


@router.post("/collect/stop")
async def stop_collection():
    """데이터 수집 중지"""
    global collection_status
    
    if not collection_status["is_running"]:
        raise HTTPException(status_code=400, detail="진행 중인 수집이 없습니다")
    
    collection_status["is_running"] = False
    return {"message": "데이터 수집을 중지합니다"}


@router.get("/collect/status", response_model=CollectionStatus)
async def get_collection_status():
    """데이터 수집 상태 조회"""
    return CollectionStatus(**collection_status)


@router.get("/stocks")
async def get_stocks(
    limit: int = 100,
    offset: int = 0
):
    """수집된 종목 목록 조회"""
    session = get_db_session()
    
    try:
        stocks = session.query(StockMasterModel).filter_by(
            is_active=True
        ).order_by(
            StockMasterModel.volume_amount.desc()
        ).limit(limit).offset(offset).all()
        
        total = session.query(StockMasterModel).filter_by(is_active=True).count()
        
        return {
            "total": total,
            "stocks": [
                {
                    "symbol": s.symbol,
                    "name": s.name,
                    "market": s.market,
                    "current_price": s.current_price,
                    "volume_amount": s.volume_amount,
                    "price_position": s.price_position,
                    "updated_at": s.updated_at
                }
                for s in stocks
            ]
        }
    
    finally:
        session.close()


@router.get("/stats")
async def get_data_stats():
    """데이터 통계"""
    session = get_db_session()
    
    try:
        from data.models import OHLCModel
        
        stock_count = session.query(StockMasterModel).filter_by(is_active=True).count()
        ohlc_count = session.query(OHLCModel).count()
        
        # 최근 업데이트 시간
        latest_stock = session.query(StockMasterModel).order_by(
            StockMasterModel.updated_at.desc()
        ).first()
        
        return {
            "stock_count": stock_count,
            "ohlc_count": ohlc_count,
            "last_updated": latest_stock.updated_at if latest_stock else None
        }
    
    finally:
        session.close()
