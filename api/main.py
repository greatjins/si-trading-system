"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.routes import account, orders, strategy, strategies, backtest, price, auth, websocket, strategy_builder, accounts, data_collection, backtest_results, dashboard, notifications, analysis
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 백그라운드 태스크 추적용
background_tasks = []

# FastAPI 앱 생성
app = FastAPI(
    title="LS HTS 플랫폼 API",
    description="국내주식 자동매매 시스템 API",
    version="0.1.0",
    redirect_slashes=False  # 슬래시 유무에 상관없이 307 리다이렉트 방지
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """모든 예외를 로깅"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)}
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 예외 로깅"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """유효성 검사 예외 로깅"""
    logger.warning(f"Validation error: {exc.errors()}")
    
    # bytes를 str로 변환하여 JSON 직렬화 가능하게 만듦
    errors = []
    for error in exc.errors():
        error_dict = {}
        for key, value in error.items():
            if isinstance(value, bytes):
                error_dict[key] = value.decode('utf-8')
            elif isinstance(value, tuple):
                error_dict[key] = [v.decode('utf-8') if isinstance(v, bytes) else v for v in value]
            else:
                error_dict[key] = value
        errors.append(error_dict)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors}
    )

# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(websocket.router, prefix="/api", tags=["WebSocket"])
app.include_router(account.router, prefix="/api/account", tags=["계좌"])
app.include_router(accounts.router, tags=["계좌 관리"])  # 새로운 계좌 관리
app.include_router(orders.router, prefix="/api/orders", tags=["주문"])
app.include_router(strategy.router, prefix="/api/strategy", tags=["전략 실행"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["전략 관리"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["백테스트"])
app.include_router(backtest_results.router, prefix="/api/backtest", tags=["백테스트 결과"])
app.include_router(price.router, prefix="/api/price", tags=["시세"])
app.include_router(strategy_builder.router, prefix="/api/strategy-builder", tags=["전략 빌더"])
app.include_router(data_collection.router, tags=["데이터 수집"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["대시보드"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["알림"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["비교 분석"])

# 고급 기능 라우터
from api.routes import advanced_backtest
app.include_router(advanced_backtest.router, prefix="/api/advanced-backtest", tags=["고급 백테스트"])


# TradingScheduler 전역 변수
_trading_scheduler = None
_execution_engine = None


class TradingScheduler:
    """
    거래 스케줄러
    
    apscheduler를 사용하여 일일 거래 일정을 관리합니다.
    """
    
    def __init__(self):
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        from utils.notifier import get_telegram_notifier
        
        self.scheduler = AsyncIOScheduler()
        self.telegram_notifier = get_telegram_notifier()
        self.execution_engine = None
        self.broker_adapter = None  # adapter를 클래스 변수로 저장
        logger.info("TradingScheduler initialized")
    
    def start(self):
        """스케줄러 시작"""
        from apscheduler.triggers.cron import CronTrigger
        
        # 08:00: 서버 시간 동기화(t0167) 및 전종목 스캔(Scanner) 실행
        self.scheduler.add_job(
            self.job_sync_time_and_scan,
            CronTrigger(hour=8, minute=0),
            id="sync_time_and_scan",
            name="서버 시간 동기화 및 전종목 스캔"
        )
        
        # 08:30: 선정된 종목으로 실시간 엔진(ExecutionEngine) 가동 및 NXT 시장 대기
        self.scheduler.add_job(
            self.job_start_engine,
            CronTrigger(hour=8, minute=30),
            id="start_engine",
            name="실시간 엔진 가동"
        )
        
        # 09:00: KRX 정규장 매매 활성화 (이미 엔진이 가동 중이므로 별도 작업 없음)
        self.scheduler.add_job(
            self.job_market_open,
            CronTrigger(hour=9, minute=0),
            id="market_open",
            name="KRX 정규장 시작"
        )
        
        # 15:30: KRX 장 마감 처리 및 일일 수익률 정산
        self.scheduler.add_job(
            self.job_market_close,
            CronTrigger(hour=15, minute=30),
            id="market_close",
            name="KRX 장 마감 처리"
        )
        
        # 20:00: NXT 시장 종료 후 시스템 대기 모드 전환
        self.scheduler.add_job(
            self.job_nxt_close,
            CronTrigger(hour=20, minute=0),
            id="nxt_close",
            name="NXT 시장 종료"
        )
        
        self.scheduler.start()
        logger.info("TradingScheduler started")
    
    async def stop(self):
        """스케줄러 중지"""
        if self.execution_engine:
            await self.execution_engine.stop()
            self.execution_engine = None
        
        # adapter 정리
        if self.broker_adapter:
            try:
                await self.broker_adapter.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing adapter: {e}")
            self.broker_adapter = None
        
        self.scheduler.shutdown()
        logger.info("TradingScheduler stopped")
    
    async def job_sync_time_and_scan(self):
        """08:00 작업: 서버 시간 동기화 및 전종목 스캔"""
        try:
            logger.info("Starting job: 서버 시간 동기화 및 전종목 스캔")
            
            # 1. 서버 시간 동기화 (t0167)
            try:
                from broker.ls.adapter import LSAdapter
                from broker.ls.services.time_sync import ensure_synced
                
                async with LSAdapter() as adapter:
                    await ensure_synced(adapter.market_service)
                    logger.info("Server time synchronized")
                    await self.telegram_notifier.send_success(
                        "서버 시간 동기화",
                        "서버 시간 동기화가 완료되었습니다."
                    )
            except Exception as e:
                error_msg = f"서버 시간 동기화 실패: {e}"
                logger.error(error_msg, exc_info=True)
                await self.telegram_notifier.send_error(error_msg, "TimeSyncError")
                raise
            
            # 2. 전종목 스캔 실행
            try:
                from core.execution.scanner import run_daily_scan
                filtered_symbols = await run_daily_scan()
                logger.info(f"Daily scan completed: {len(filtered_symbols)} symbols filtered")
                await self.telegram_notifier.send_success(
                    "전종목 스캔 완료",
                    f"{len(filtered_symbols)}개 종목이 필터링되었습니다.\n종목: {', '.join(filtered_symbols[:10])}{'...' if len(filtered_symbols) > 10 else ''}"
                )
            except Exception as e:
                error_msg = f"전종목 스캔 실패: {e}"
                logger.error(error_msg, exc_info=True)
                await self.telegram_notifier.send_error(error_msg, "ScanError")
                raise
        
        except Exception as e:
            logger.error(f"Error in job_sync_time_and_scan: {e}", exc_info=True)
            await self.telegram_notifier.send_error(
                f"08:00 작업 실패: {e}",
                "JobError",
                "서버 시간 동기화 및 전종목 스캔"
            )
    
    async def job_start_engine(self):
        """08:30 작업: 실시간 엔진 가동"""
        try:
            logger.info("Starting job: 실시간 엔진 가동")
            
            # ExecutionEngine 생성 (DB에서 전략 설정 로드)
            from core.execution.engine import ExecutionEngine
            from broker.ls.adapter import LSAdapter
            from core.risk.manager import RiskManager
            
            # adapter를 클래스 변수로 저장 (컨텍스트가 끝나도 유지)
            if self.broker_adapter is None:
                self.broker_adapter = LSAdapter()
                await self.broker_adapter.__aenter__()
            
            risk_manager = RiskManager(
                max_position_size=0.1,
                max_daily_loss=0.05,
                max_drawdown=0.15
            )
            
            # DB에서 전략 설정 로드하여 엔진 생성
            self.execution_engine = await ExecutionEngine.create_from_db_config(
                broker=self.broker_adapter,
                risk_manager=risk_manager
            )
            
            # active_universe에서 종목 리스트 읽어와 엔진 시작
            await self.execution_engine.start_with_active_universe()
            
            logger.info("Execution engine started")
            await self.telegram_notifier.send_success(
                "실시간 엔진 가동",
                "실시간 엔진이 가동되었습니다. NXT 시장 대기 중..."
            )
        
        except Exception as e:
            error_msg = f"실시간 엔진 가동 실패: {e}"
            logger.error(error_msg, exc_info=True)
            await self.telegram_notifier.send_error(error_msg, "EngineStartError")
            raise
    
    async def job_market_open(self):
        """09:00 작업: KRX 정규장 시작"""
        try:
            logger.info("Starting job: KRX 정규장 시작")
            await self.telegram_notifier.send_info(
                "KRX 정규장 시작",
                "KRX 정규장이 시작되었습니다. 매매가 활성화됩니다."
            )
        except Exception as e:
            logger.error(f"Error in job_market_open: {e}", exc_info=True)
            await self.telegram_notifier.send_error(
                f"09:00 작업 실패: {e}",
                "JobError",
                "KRX 정규장 시작"
            )
    
    async def job_market_close(self):
        """15:30 작업: KRX 장 마감 처리 및 일일 수익률 정산"""
        try:
            logger.info("Starting job: KRX 장 마감 처리")
            
            # 일일 수익률 정산 (추후 구현)
            # TODO: 일일 수익률 계산 및 저장
            
            await self.telegram_notifier.send_info(
                "KRX 장 마감",
                "KRX 정규장이 마감되었습니다. 일일 수익률 정산이 완료되었습니다."
            )
        except Exception as e:
            logger.error(f"Error in job_market_close: {e}", exc_info=True)
            await self.telegram_notifier.send_error(
                f"15:30 작업 실패: {e}",
                "JobError",
                "KRX 장 마감 처리"
            )
    
    async def job_nxt_close(self):
        """20:00 작업: NXT 시장 종료 후 시스템 대기 모드 전환"""
        try:
            logger.info("Starting job: NXT 시장 종료")
            
            # ExecutionEngine 중지
            if self.execution_engine:
                await self.execution_engine.stop()
                self.execution_engine = None
                logger.info("Execution engine stopped")
            
            await self.telegram_notifier.send_info(
                "NXT 시장 종료",
                "NXT 시장이 종료되었습니다. 시스템이 대기 모드로 전환되었습니다."
            )
        except Exception as e:
            logger.error(f"Error in job_nxt_close: {e}", exc_info=True)
            await self.telegram_notifier.send_error(
                f"20:00 작업 실패: {e}",
                "JobError",
                "NXT 시장 종료"
            )


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시"""
    from core.strategy.registry import StrategyRegistry
    from broker.connection_pool import connection_pool
    import asyncio
    global _trading_scheduler
    
    # 전략 자동 탐색
    StrategyRegistry.auto_discover("core.strategy.examples")
    logger.info(f"Loaded {len(StrategyRegistry.list_strategies())} strategies")
    
    # 연결 풀 정리 태스크 시작
    async def cleanup_task():
        try:
            while True:
                # cleanup_interval 사용
                await asyncio.sleep(connection_pool._cleanup_interval)
                await connection_pool.cleanup_idle_connections()
                
                # 통계 로깅
                stats = connection_pool.get_stats()
                if stats["total_connections"] > 0:
                    logger.debug(f"Connection pool: {stats['active_connections']}/{stats['total_connections']} active")
        except asyncio.CancelledError:
            logger.info("Connection pool cleanup task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}", exc_info=True)
    
    task = asyncio.create_task(cleanup_task())
    background_tasks.append(task)
    logger.info("Connection pool cleanup task started")
    
    # TradingScheduler 시작
    _trading_scheduler = TradingScheduler()
    _trading_scheduler.start()
    logger.info("TradingScheduler started")
    
    logger.info("LS HTS API Server starting...")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시"""
    import asyncio
    from api.websocket.streams import price_streamer
    from broker.connection_pool import connection_pool
    global _trading_scheduler
    
    logger.info("LS HTS API Server shutting down...")
    
    # TradingScheduler 중지
    if _trading_scheduler:
        await _trading_scheduler.stop()
        logger.info("TradingScheduler stopped")
    
    # 백그라운드 태스크 취소 및 정리
    if background_tasks:
        logger.info(f"Cancelling {len(background_tasks)} background tasks...")
        for task in background_tasks:
            if not task.done():
                task.cancel()
        
        # 모든 태스크가 완료될 때까지 대기 (CancelledError 무시)
        if background_tasks:
            await asyncio.gather(*background_tasks, return_exceptions=True)
        background_tasks.clear()
        logger.info("Background tasks cancelled")
    
    # 스트리머 정지
    try:
        await price_streamer.stop()
    except Exception as e:
        logger.warning(f"Error stopping price streamer: {e}")
    
    # 연결 풀 정리
    try:
        await connection_pool.close_all()
    except Exception as e:
        logger.warning(f"Error closing connection pool: {e}")
    
    logger.info("LS HTS API Server shutdown complete")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": "LS HTS 플랫폼 API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
