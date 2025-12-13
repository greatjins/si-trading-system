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
    strategy: Optional[str] = "mixed"  # mixed, volume_only, change_only
    volume_ratio: float = 0.5  # 거래대금 비율 (0.0~1.0)


class CollectionStatus(BaseModel):
    """데이터 수집 상태"""
    is_running: bool
    current_symbol: Optional[str]
    progress: int
    total: int
    logs: List[str]
    start_time: Optional[datetime]
    error: Optional[str]


async def collect_data_background(count: int, days: int, strategy: str = "mixed", volume_ratio: float = 0.5):
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
        
        add_log(f"데이터 수집 시작: {count}종목, {days}일 (전략: {strategy})")
        
        # LS증권 어댑터 초기화
        async with LSAdapter() as adapter:
            # 1. 전체 종목 조회 (시장 구분 매핑용)
            add_log("전체 종목 정보 조회 중...")
            all_symbols = await adapter.market_service.get_all_symbols(market="0")
            symbol_market_map = {s["symbol"]: s["market"] for s in all_symbols}
            add_log(f"✓ {len(all_symbols)}개 종목 정보 로드")
            
            # 2. 종목 선별 (전략에 따라)
            top_stocks = []
            
            if strategy == "volume_only":
                # 거래대금 상위만
                add_log("거래대금 상위 종목 조회 중...")
                top_stocks = await adapter.market_service.get_top_volume_stocks(
                    market="0",
                    count=count
                )
                add_log(f"✓ 거래대금 상위 {len(top_stocks)}개 종목 선별")
            
            elif strategy == "change_only":
                # 등락율 상위만 (상승률 + 하락률)
                add_log("등락율 상위 종목 조회 중...")
                
                # 상승률 상위
                up_count = count // 2
                up_stocks = await adapter.market_service.get_top_change_rate_stocks(
                    gubun1="0",  # 전체
                    gubun2="0",  # 상승률
                    gubun3="0",  # 당일
                    count=up_count
                )
                add_log(f"✓ 상승률 상위 {len(up_stocks)}개")
                
                # Rate Limit
                await asyncio.sleep(1.1)
                
                # 하락률 상위
                down_count = count - up_count
                down_stocks = await adapter.market_service.get_top_change_rate_stocks(
                    gubun1="0",  # 전체
                    gubun2="1",  # 하락률
                    gubun3="0",  # 당일
                    count=down_count
                )
                add_log(f"✓ 하락률 상위 {len(down_stocks)}개")
                
                # 합치기 (중복 제거)
                seen = set()
                for stock in up_stocks + down_stocks:
                    if stock["symbol"] not in seen:
                        top_stocks.append(stock)
                        seen.add(stock["symbol"])
                
                add_log(f"✓ 등락율 상위 {len(top_stocks)}개 종목 선별 (중복 제거)")
            
            else:  # mixed (기본)
                # 거래대금 + 등락율 조합
                volume_count = int(count * volume_ratio)
                change_count = count - volume_count
                
                add_log(f"거래대금 상위 {volume_count}개 + 등락율 상위 {change_count}개 조회 중...")
                
                # 거래대금 상위
                volume_stocks = await adapter.market_service.get_top_volume_stocks(
                    market="0",
                    count=volume_count
                )
                add_log(f"✓ 거래대금 상위 {len(volume_stocks)}개")
                
                # Rate Limit
                await asyncio.sleep(1.1)
                
                # 등락율 상위 (상승률 + 하락률)
                up_count = change_count // 2
                down_count = change_count - up_count
                
                up_stocks = await adapter.market_service.get_top_change_rate_stocks(
                    gubun1="0",
                    gubun2="0",
                    gubun3="0",
                    count=up_count
                )
                add_log(f"✓ 상승률 상위 {len(up_stocks)}개")
                
                await asyncio.sleep(1.1)
                
                down_stocks = await adapter.market_service.get_top_change_rate_stocks(
                    gubun1="0",
                    gubun2="1",
                    gubun3="0",
                    count=down_count
                )
                add_log(f"✓ 하락률 상위 {len(down_stocks)}개")
                
                # 합치기 (중복 제거)
                seen = set()
                for stock in volume_stocks + up_stocks + down_stocks:
                    if stock["symbol"] not in seen:
                        top_stocks.append(stock)
                        seen.add(stock["symbol"])
                
                add_log(f"✓ 총 {len(top_stocks)}개 종목 선별 (중복 제거)")
            
            collection_status["total"] = len(top_stocks)
            add_log(f"✓ 최종 {len(top_stocks)}개 종목 선별 완료")
            
            # 2. 각 종목 데이터 수집
            repo = OHLCRepository()
            
            for idx, stock_info in enumerate(top_stocks, 1):
                stock_session = get_db_session()  # 각 종목마다 새 세션
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
                        
                        # 시장 구분 (symbol_market_map에서 조회)
                        market_code = symbol_market_map.get(symbol, "1")
                        market = "KOSPI" if market_code == "1" else "KOSDAQ"
                        
                        # 재무 정보 조회 (t3320)
                        financial_info = None
                        try:
                            financial_info = await adapter.market_service.get_financial_info(symbol)
                            if financial_info and financial_info.per:
                                add_log(f"  ✓ 재무정보: PER={financial_info.per}, PBR={financial_info.pbr}, ROE={financial_info.roe}")
                        except Exception as e:
                            # 재무정보 조회 실패해도 계속 진행
                            logger.debug(f"재무정보 조회 실패 (계속 진행): {str(e)}")
                        
                        # stock_master 저장
                        stock = StockMasterModel(
                            symbol=symbol,
                            name=name,
                            market=market,
                            current_price=current_price,
                            volume_amount=stock_info.get("volume_amount", 0),
                            high_52w=high_52w,
                            low_52w=low_52w,
                            price_position=price_position,
                            
                            # 재무 정보 (있으면 저장)
                            market_cap=financial_info.market_cap if financial_info else None,
                            shares=financial_info.shares if financial_info else None,
                            per=financial_info.per if financial_info else None,
                            pbr=financial_info.pbr if financial_info else None,
                            eps=financial_info.eps if financial_info else None,
                            bps=financial_info.bps if financial_info else None,
                            roe=financial_info.roe if financial_info else None,
                            roa=financial_info.roa if financial_info else None,
                            dividend_yield=financial_info.dividend_yield if financial_info else None,
                            foreign_ratio=financial_info.foreign_ratio if financial_info else None,
                            
                            is_active=True,
                            updated_at=datetime.now()
                        )
                        stock_session.merge(stock)
                        stock_session.commit()
                        
                        # OHLC 데이터 저장
                        saved = await repo.save_ohlc_batch(ohlc_list, "1d")
                        add_log(f"  ✓ OHLC {len(ohlc_list)}개 수집, {saved}개 저장")
                    else:
                        add_log(f"  ⚠️ 데이터 없음")
                    
                    # Rate Limit (재무정보 조회 추가로 더 긴 대기)
                    await asyncio.sleep(1.5)
                
                except Exception as e:
                    add_log(f"  ✗ 오류: {str(e)}")
                finally:
                    stock_session.close()  # 각 종목 처리 후 세션 닫기
            
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
        request.days,
        request.strategy,
        request.volume_ratio
    )
    
    return {
        "message": "데이터 수집이 시작되었습니다",
        "strategy": request.strategy,
        "count": request.count,
        "volume_ratio": request.volume_ratio if request.strategy == "mixed" else None
    }


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
        
        # 재무 정보가 있는 종목 수
        financial_count = session.query(StockMasterModel).filter(
            StockMasterModel.is_active == True,
            StockMasterModel.per.isnot(None)
        ).count()
        
        # 최근 업데이트 시간
        latest_stock = session.query(StockMasterModel).order_by(
            StockMasterModel.updated_at.desc()
        ).first()
        
        return {
            "stock_count": stock_count,
            "ohlc_count": ohlc_count,
            "financial_count": financial_count,
            "last_updated": latest_stock.updated_at if latest_stock else None
        }
    
    finally:
        session.close()


@router.get("/filter/value")
async def get_value_stocks_api(
    per_max: float = 10,
    pbr_max: float = 1.0,
    roe_min: float = 10,
    limit: int = 50
):
    """가치주 필터링"""
    from data.stock_filter import FinancialFilter
    
    session = get_db_session()
    try:
        stocks = FinancialFilter.get_value_stocks(session, per_max, pbr_max, roe_min, limit)
        
        return {
            "total": len(stocks),
            "criteria": {
                "per_max": per_max,
                "pbr_max": pbr_max,
                "roe_min": roe_min
            },
            "stocks": [
                {
                    "symbol": s.symbol,
                    "name": s.name,
                    "market": s.market,
                    "price": s.current_price,
                    "per": s.per,
                    "pbr": s.pbr,
                    "roe": s.roe,
                    "market_cap": s.market_cap
                }
                for s in stocks
            ]
        }
    finally:
        session.close()


@router.get("/filter/dividend")
async def get_dividend_stocks_api(
    dividend_yield_min: float = 3.0,
    limit: int = 50
):
    """배당주 필터링"""
    from data.stock_filter import FinancialFilter
    
    session = get_db_session()
    try:
        stocks = FinancialFilter.get_dividend_stocks(session, dividend_yield_min, limit)
        
        return {
            "total": len(stocks),
            "criteria": {
                "dividend_yield_min": dividend_yield_min
            },
            "stocks": [
                {
                    "symbol": s.symbol,
                    "name": s.name,
                    "market": s.market,
                    "price": s.current_price,
                    "dividend_yield": s.dividend_yield,
                    "per": s.per,
                    "pbr": s.pbr
                }
                for s in stocks
            ]
        }
    finally:
        session.close()


@router.get("/filter/quality")
async def get_quality_stocks_api(
    roe_min: float = 15,
    roa_min: float = 10,
    market_cap_min: float = 1_000_000_000_000,
    limit: int = 50
):
    """우량주 필터링"""
    from data.stock_filter import FinancialFilter
    
    session = get_db_session()
    try:
        stocks = FinancialFilter.get_quality_stocks(session, roe_min, roa_min, market_cap_min, limit)
        
        return {
            "total": len(stocks),
            "criteria": {
                "roe_min": roe_min,
                "roa_min": roa_min,
                "market_cap_min": market_cap_min
            },
            "stocks": [
                {
                    "symbol": s.symbol,
                    "name": s.name,
                    "market": s.market,
                    "price": s.current_price,
                    "roe": s.roe,
                    "roa": s.roa,
                    "market_cap": s.market_cap,
                    "per": s.per,
                    "pbr": s.pbr
                }
                for s in stocks
            ]
        }
    finally:
        session.close()
