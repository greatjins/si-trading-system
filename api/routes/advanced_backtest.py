"""
고급 백테스트 API 라우트
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from api.dependencies import get_current_user
from core.backtest.parallel_engine import ParallelBacktestEngine, BatchBacktestEngine
from core.risk.advanced_manager import AdvancedRiskManager, RiskMetrics
from core.strategy.registry import StrategyRegistry
from data.repository import BacktestRepository
from utils.types import BacktestResult
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


class ParallelBacktestRequest(BaseModel):
    """병렬 백테스트 요청"""
    strategy_names: List[str] = Field(..., description="전략 이름 리스트")
    symbol: str = Field(..., description="종목 코드")
    start_date: datetime = Field(..., description="시작일")
    end_date: datetime = Field(..., description="종료일")
    initial_capital: float = Field(10_000_000, description="초기 자본")
    commission: float = Field(0.0015, description="수수료율")
    slippage: float = Field(0.0005, description="슬리피지")
    max_workers: Optional[int] = Field(None, description="최대 워커 수")


class ParameterOptimizationRequest(BaseModel):
    """파라미터 최적화 요청"""
    strategy_name: str = Field(..., description="전략 이름")
    parameter_grid: Dict[str, List[Any]] = Field(..., description="파라미터 그리드")
    symbol: str = Field(..., description="종목 코드")
    start_date: datetime = Field(..., description="시작일")
    end_date: datetime = Field(..., description="종료일")
    initial_capital: float = Field(10_000_000, description="초기 자본")
    commission: float = Field(0.0015, description="수수료율")
    slippage: float = Field(0.0005, description="슬리피지")


class RiskAnalysisRequest(BaseModel):
    """리스크 분석 요청"""
    backtest_ids: List[int] = Field(..., description="백테스트 ID 리스트")
    sector_mapping: Optional[Dict[str, str]] = Field(None, description="종목별 섹터 매핑")


class ParallelBacktestResponse(BaseModel):
    """병렬 백테스트 응답"""
    task_id: str = Field(..., description="작업 ID")
    total_strategies: int = Field(..., description="총 전략 수")
    status: str = Field(..., description="상태")


class OptimizationResult(BaseModel):
    """최적화 결과"""
    strategy_name: str
    parameters: Dict[str, Any]
    total_return: float
    mdd: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    rank: int


class OptimizationResponse(BaseModel):
    """최적화 응답"""
    total_combinations: int
    successful_runs: int
    best_result: OptimizationResult
    top_10_results: List[OptimizationResult]


# 백그라운드 작업 저장소
background_tasks_storage: Dict[str, Dict[str, Any]] = {}


@router.post("/parallel", response_model=ParallelBacktestResponse)
async def run_parallel_backtest(
    request: ParallelBacktestRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    여러 전략을 병렬로 백테스트 실행
    """
    logger.info(f"Parallel backtest requested by {current_user['username']}: {len(request.strategy_names)} strategies")
    
    # 전략 존재 확인
    available_strategies = StrategyRegistry.list_strategies()
    for strategy_name in request.strategy_names:
        if strategy_name not in available_strategies:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy not found: {strategy_name}"
            )
    
    # 작업 ID 생성
    import uuid
    task_id = str(uuid.uuid4())
    
    # 백그라운드 작업 등록
    background_tasks.add_task(
        _run_parallel_backtest_task,
        task_id,
        request,
        current_user["user_id"]
    )
    
    # 작업 상태 초기화
    background_tasks_storage[task_id] = {
        "status": "running",
        "total_strategies": len(request.strategy_names),
        "completed": 0,
        "results": [],
        "error": None
    }
    
    return ParallelBacktestResponse(
        task_id=task_id,
        total_strategies=len(request.strategy_names),
        status="running"
    )


@router.get("/parallel/{task_id}")
async def get_parallel_backtest_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """병렬 백테스트 상태 조회"""
    if task_id not in background_tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return background_tasks_storage[task_id]


@router.post("/optimize", response_model=OptimizationResponse)
async def run_parameter_optimization(
    request: ParameterOptimizationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    파라미터 최적화 실행
    """
    logger.info(f"Parameter optimization requested by {current_user['username']}: {request.strategy_name}")
    
    # 전략 클래스 가져오기
    strategy_class = StrategyRegistry.get_strategy_class(request.strategy_name)
    if not strategy_class:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy not found: {request.strategy_name}"
        )
    
    try:
        # OHLC 데이터 로드
        from data.loaders import OHLCLoader
        loader = OHLCLoader()
        ohlc_data = await loader.load_ohlc(
            request.symbol,
            request.start_date,
            request.end_date,
            "1d"
        )
        
        if not ohlc_data:
            raise HTTPException(
                status_code=404,
                detail=f"No OHLC data found for {request.symbol}"
            )
        
        # 병렬 엔진으로 최적화 실행
        engine = ParallelBacktestEngine()
        results = await engine.run_parameter_optimization(
            strategy_class=strategy_class,
            parameter_grid=request.parameter_grid,
            ohlc_data=ohlc_data,
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage
        )
        
        # 결과 정렬 (샤프 비율 기준)
        sorted_results = sorted(
            results,
            key=lambda x: x.sharpe_ratio,
            reverse=True
        )
        
        # 응답 생성
        optimization_results = []
        for i, result in enumerate(sorted_results[:10]):  # 상위 10개
            optimization_results.append(OptimizationResult(
                strategy_name=result.strategy_name,
                parameters=result.parameters,
                total_return=result.total_return,
                mdd=result.mdd,
                sharpe_ratio=result.sharpe_ratio,
                win_rate=result.win_rate,
                total_trades=result.total_trades,
                rank=i + 1
            ))
        
        best_result = optimization_results[0] if optimization_results else None
        
        return OptimizationResponse(
            total_combinations=len(results),
            successful_runs=len([r for r in results if r.total_trades > 0]),
            best_result=best_result,
            top_10_results=optimization_results
        )
        
    except Exception as e:
        logger.error(f"Parameter optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk-analysis")
async def analyze_portfolio_risk(
    request: RiskAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    포트폴리오 리스크 분석
    """
    logger.info(f"Risk analysis requested by {current_user['username']}: {len(request.backtest_ids)} backtests")
    
    try:
        # 백테스트 결과 로드
        repository = BacktestRepository()
        backtest_results = []
        
        for backtest_id in request.backtest_ids:
            result = await repository.get_backtest_result(backtest_id)
            if result:
                backtest_results.append(result)
        
        if not backtest_results:
            raise HTTPException(
                status_code=404,
                detail="No backtest results found"
            )
        
        # 포지션 데이터 준비 (백테스트 결과에서 추출)
        positions = []
        for result in backtest_results:
            # 마지막 거래 기준으로 포지션 생성
            if result.trades:
                last_trade = result.trades[-1]
                from utils.types import Position
                position = Position(
                    symbol=last_trade.symbol,
                    quantity=last_trade.quantity,
                    avg_price=last_trade.price,
                    current_price=last_trade.price,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0
                )
                positions.append(position)
        
        # 계좌 정보 생성
        from utils.types import Account
        total_equity = sum(result.final_equity for result in backtest_results)
        account = Account(
            account_id="portfolio",
            balance=total_equity * 0.1,  # 10% 현금
            equity=total_equity,
            margin_used=total_equity * 0.9,
            margin_available=total_equity * 0.1
        )
        
        # 리스크 분석 실행
        risk_manager = AdvancedRiskManager()
        
        # 가격 히스토리 업데이트 (백테스트 데이터 사용)
        for result in backtest_results:
            for i, timestamp in enumerate(result.equity_timestamps):
                if result.trades:
                    symbol = result.trades[0].symbol  # 첫 번째 거래 종목
                    price = result.equity_curve[i] / 1000  # 임시 가격
                    risk_manager.update_price_history(symbol, timestamp, price)
        
        # 리스크 메트릭 계산
        risk_metrics = risk_manager.calculate_portfolio_risk(
            positions=positions,
            account=account,
            sector_mapping=request.sector_mapping
        )
        
        return risk_metrics.to_dict()
        
    except Exception as e:
        logger.error(f"Risk analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch-status")
async def get_batch_backtest_capabilities():
    """배치 백테스트 기능 정보"""
    return {
        "max_concurrent_strategies": 50,
        "max_batch_size": 10,
        "supported_optimizations": [
            "grid_search",
            "random_search",
            "genetic_algorithm"
        ],
        "risk_metrics": [
            "var_95",
            "cvar_95",
            "max_drawdown",
            "volatility",
            "sharpe_ratio",
            "sortino_ratio",
            "beta",
            "correlation_risk",
            "concentration_risk"
        ]
    }


async def _run_parallel_backtest_task(
    task_id: str,
    request: ParallelBacktestRequest,
    user_id: int
):
    """백그라운드에서 병렬 백테스트 실행"""
    try:
        # OHLC 데이터 로드
        from data.loaders import OHLCLoader
        loader = OHLCLoader()
        ohlc_data = await loader.load_ohlc(
            request.symbol,
            request.start_date,
            request.end_date,
            "1d"
        )
        
        if not ohlc_data:
            background_tasks_storage[task_id]["status"] = "failed"
            background_tasks_storage[task_id]["error"] = f"No OHLC data found for {request.symbol}"
            return
        
        # 전략 인스턴스 생성
        strategies = []
        for strategy_name in request.strategy_names:
            strategy_class = StrategyRegistry.get_strategy_class(strategy_name)
            if strategy_class:
                # 기본 파라미터로 전략 생성
                metadata = StrategyRegistry.get_strategy_metadata(strategy_name)
                default_params = {}
                if metadata and metadata.parameters:
                    for param_name, param_info in metadata.parameters.items():
                        default_params[param_name] = param_info.get("default")
                
                strategy = strategy_class(default_params)
                strategies.append(strategy)
        
        # 병렬 실행
        engine = ParallelBacktestEngine(max_workers=request.max_workers)
        results = await engine.run_multiple_strategies(
            strategies=strategies,
            ohlc_data=ohlc_data,
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage
        )
        
        # 결과 저장
        repository = BacktestRepository()
        saved_results = []
        
        for result in results:
            backtest_id = await repository.save_backtest_result(result, user_id)
            saved_results.append({
                "backtest_id": backtest_id,
                "strategy_name": result.strategy_name,
                "total_return": result.total_return,
                "mdd": result.mdd,
                "sharpe_ratio": result.sharpe_ratio,
                "total_trades": result.total_trades
            })
        
        # 작업 완료
        background_tasks_storage[task_id]["status"] = "completed"
        background_tasks_storage[task_id]["completed"] = len(results)
        background_tasks_storage[task_id]["results"] = saved_results
        
        logger.info(f"Parallel backtest completed: {task_id}, {len(results)} results")
        
    except Exception as e:
        logger.error(f"Parallel backtest task failed: {task_id}, {e}")
        background_tasks_storage[task_id]["status"] = "failed"
        background_tasks_storage[task_id]["error"] = str(e)