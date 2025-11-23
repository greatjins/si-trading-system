"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    
    # 전략 자동 탐색
    StrategyRegistry.auto_discover("core.strategy.examples")
    logger.info(f"Loaded {len(StrategyRegistry.list_strategies())} strategies")
    
    logger.info("LS HTS API Server starting...")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시"""
    from api.websocket.streams import price_streamer
    await price_streamer.stop()
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
