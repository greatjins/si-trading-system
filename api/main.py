"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.routes import account, orders, strategy, strategies, backtest, price, auth, websocket, strategy_builder, accounts
from utils.logger import setup_logger

logger = setup_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="LS HTS 플랫폼 API",
    description="국내주식 자동매매 시스템 API",
    version="0.1.0"
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
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
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
app.include_router(price.router, prefix="/api/price", tags=["시세"])
app.include_router(strategy_builder.router, prefix="/api/strategy-builder", tags=["전략 빌더"])


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시"""
    from core.strategy.registry import StrategyRegistry
    from broker.connection_pool import connection_pool
    import asyncio
    
    # 전략 자동 탐색
    StrategyRegistry.auto_discover("core.strategy.examples")
    logger.info(f"Loaded {len(StrategyRegistry.list_strategies())} strategies")
    
    # 연결 풀 정리 태스크 시작
    async def cleanup_task():
        while True:
            # cleanup_interval 사용
            await asyncio.sleep(connection_pool._cleanup_interval)
            await connection_pool.cleanup_idle_connections()
            
            # 통계 로깅
            stats = connection_pool.get_stats()
            if stats["total_connections"] > 0:
                logger.debug(f"Connection pool: {stats['active_connections']}/{stats['total_connections']} active")
    
    asyncio.create_task(cleanup_task())
    logger.info("Connection pool cleanup task started")
    
    logger.info("LS HTS API Server starting...")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시"""
    from api.websocket.streams import price_streamer
    from broker.connection_pool import connection_pool
    
    await price_streamer.stop()
    await connection_pool.close_all()
    logger.info("LS HTS API Server shutting down...")


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
