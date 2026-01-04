"""
백테스트 관련 API
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from datetime import datetime
import uuid

from api.schemas import BacktestRequest, BacktestResponse, AutoMLRequest, AutoMLResponse
from data.repository import DataRepository
from core.backtest.engine import BacktestEngine
from core.automl.grid_search import GridSearch
from core.automl.random_search import RandomSearch
from core.automl.genetic import GeneticAlgorithm
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# 포트폴리오 백테스트 백그라운드 작업 저장소
portfolio_backtest_tasks: Dict[str, Dict[str, Any]] = {}


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    백테스트 실행
    
    Args:
        request: 백테스트 요청
        
    Returns:
        백테스트 결과
    """
    try:
        from core.strategy.registry import StrategyRegistry
        from data.repository import BacktestRepository
        
        # 데이터 로드 (단일 종목 전략만)
        ohlc_list = None
        if request.symbol:
            repo = DataRepository()
            data = repo.get_ohlc(
                symbol=request.symbol,
                interval=request.interval,
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            if data.empty:
                raise HTTPException(status_code=404, detail="No data found for the given period")
            
            logger.info(f"Loaded {len(data)} bars for {request.symbol}")
            
            # DataFrame을 OHLC 리스트로 변환
            from utils.types import OHLC
            ohlc_list = [
                OHLC(
                    symbol=request.symbol,
                    timestamp=row.Index,
                    open=row.open,
                    high=row.high,
                    low=row.low,
                    close=row.close,
                    volume=int(row.volume)
                )
                for row in data.itertuples()
            ]
        else:
            logger.info(f"Portfolio backtest: no symbol specified")
        
        # 전략 로드 (코드 기반 또는 전략 빌더)
        strategy = None
        try:
            # 먼저 코드 기반 전략 시도
            strategy_class = StrategyRegistry.get(request.strategy_name)
            strategy = strategy_class(params=request.parameters or {})
            logger.info(f"Loaded strategy from registry: {request.strategy_name}")
        except (ValueError, KeyError, Exception) as e:
            logger.info(f"Strategy not in registry, trying builder: {e}")
        
        # 전략이 레지스트리에 없으면 전략 빌더에서 로드 (JSON 기반)
        if strategy is None:
            from data.models import StrategyBuilderModel
            from data.repository import get_db_session
            from core.strategy.factory import StrategyFactory
            
            # DB 세션 생성
            db = get_db_session()
            
            try:
                # 전략 빌더에서 전략 찾기
                builder_strategy = db.query(StrategyBuilderModel).filter(
                    StrategyBuilderModel.name == request.strategy_name,
                    StrategyBuilderModel.is_active == True
                ).first()
                
                if not builder_strategy:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Strategy '{request.strategy_name}' not found in registry or strategy builder"
                    )
            finally:
                db.close()
            
            # JSON 설정 기반으로 전략 생성 (exec() 대신)
            try:
                db_config = {
                    "id": builder_strategy.id,  # DynamicStrategy용
                    "config": builder_strategy.config,  # 기존 호환성
                    "config_json": builder_strategy.config_json,  # 구조화된 설정 (우선 사용)
                    "python_code": builder_strategy.python_code,  # 참고용 (사용 안 함)
                    "name": builder_strategy.name
                }
                
                # StrategyFactory를 사용하여 전략 생성
                strategy = StrategyFactory.create_from_db_config(db_config)
                
                # 요청 파라미터로 오버라이드 (있는 경우)
                if request.parameters:
                    for key, value in request.parameters.items():
                        strategy.set_param(key, value)
                
                logger.info(f"✓ Loaded strategy from JSON config: {request.strategy_name}")
            except Exception as e:
                logger.error(f"Failed to create strategy from JSON config: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to load strategy from config: {str(e)}"
                )
        
        # 포트폴리오 전략 여부 확인 (is_portfolio_strategy() 사용)
        is_portfolio = strategy.is_portfolio_strategy()
        
        if is_portfolio and not request.symbol:
            logger.info(f"Strategy '{request.strategy_name}' is portfolio strategy - running as portfolio backtest")
            # symbol 없이 포트폴리오 백테스트 실행
            ohlc_list = None
        elif not request.symbol and not is_portfolio:
            # 단일 종목 전략인데 symbol이 없으면 에러
            raise HTTPException(
                status_code=400,
                detail=f"Strategy '{request.strategy_name}' requires a symbol. Please provide 'symbol' in the request."
            )
        
        if request.symbol:
            logger.info(f"Running single-symbol backtest: {request.strategy_name} on {request.symbol}")
        else:
            logger.info(f"Running portfolio backtest: {request.strategy_name}")
        
        # 백테스트 실행
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=request.initial_capital,
            commission=request.commission or 0.0015,
            slippage=request.slippage or 0.001,
            execution_delay=request.execution_delay or 1.5,
            use_dynamic_slippage=request.use_dynamic_slippage if request.use_dynamic_slippage is not None else True,
            use_tiered_commission=request.use_tiered_commission if request.use_tiered_commission is not None else True
        )
        
        # 비동기 실행
        result = await engine.run(
            ohlc_data=ohlc_list,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # 결과 저장
        backtest_repo = BacktestRepository()
        backtest_id = backtest_repo.save_backtest_result(result)
        
        logger.info(f"Backtest completed: ID={backtest_id}, Return={result.total_return:.2%}")
        
        return BacktestResponse(
            backtest_id=backtest_id,
            strategy_name=result.strategy_name,
            start_date=result.start_date,
            end_date=result.end_date,
            initial_capital=result.initial_capital,
            final_equity=result.final_equity,
            total_return=result.total_return,
            mdd=result.mdd,
            sharpe_ratio=result.sharpe_ratio,
            win_rate=result.win_rate,
            profit_factor=result.profit_factor,
            total_trades=result.total_trades,
            parameters=request.parameters,
            created_at=datetime.now()
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run backtest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automl", response_model=AutoMLResponse)
async def run_automl(request: AutoMLRequest):
    """
    AutoML 실행
    
    Args:
        request: AutoML 요청
        
    Returns:
        AutoML 결과
    """
    try:
        # 데이터 로드
        repo = DataRepository()
        data = repo.get_ohlc(
            symbol=request.symbol,
            interval=request.interval,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if data.empty:
            raise HTTPException(status_code=404, detail="No data found for the given period")
        
        # 전략 동적 로드
        # TODO: 전략 레지스트리 구현
        from core.strategy.base import BaseStrategy
        
        # 백테스트 엔진 생성
        engine = BacktestEngine(initial_capital=10_000_000, commission=0.00015)
        
        # Optimizer 선택
        if request.method == "grid":
            optimizer = GridSearch(
                strategy_class=BaseStrategy,  # TODO: 실제 전략 클래스
                param_space=request.parameter_space,
                engine=engine
            )
        elif request.method == "random":
            optimizer = RandomSearch(
                strategy_class=BaseStrategy,
                param_space=request.parameter_space,
                engine=engine,
                n_iterations=request.n_iterations or 100
            )
        elif request.method == "genetic":
            optimizer = GeneticAlgorithm(
                strategy_class=BaseStrategy,
                param_space=request.parameter_space,
                engine=engine,
                population_size=request.population_size or 20,
                generations=request.generations or 10
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid optimization method")
        
        # 최적화 실행
        # TODO: 비동기 실행 및 결과 저장
        # results = optimizer.optimize(data)
        
        # 임시 응답
        raise HTTPException(status_code=501, detail="AutoML execution not fully implemented")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run AutoML: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio")
async def run_portfolio_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks
):
    """
    포트폴리오 백테스트 실행 (종목 선택 전략) - 비동기 작업
    
    Args:
        request: 백테스트 요청 (symbol은 무시됨)
        background_tasks: FastAPI BackgroundTasks
        
    Returns:
        task_id: 백테스트 작업 ID (상태 조회용)
    """
    # 작업 ID 생성
    task_id = str(uuid.uuid4())
    
    logger.info(f"Starting portfolio backtest task: {task_id}, strategy: {request.strategy_name}")
    
    # 백그라운드 작업 등록
    background_tasks.add_task(
        _run_portfolio_backtest_task,
        task_id,
        request
    )
    
    # 작업 상태 초기화
    portfolio_backtest_tasks[task_id] = {
        "status": "running",
        "strategy_name": request.strategy_name,
        "start_date": request.start_date.isoformat() if request.start_date else None,
        "end_date": request.end_date.isoformat() if request.end_date else None,
        "progress": 0,
        "message": "백테스트 시작 중...",
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "task_id": task_id,
        "status": "running",
        "message": "포트폴리오 백테스트가 시작되었습니다. /api/backtest/portfolio/{task_id} 엔드포인트로 상태를 확인하세요."
    }


@router.get("/portfolio/{task_id}")
async def get_portfolio_backtest_status(task_id: str):
    """
    포트폴리오 백테스트 상태 조회
    
    Args:
        task_id: 백테스트 작업 ID
        
    Returns:
        백테스트 상태 및 결과
    """
    if task_id not in portfolio_backtest_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_status = portfolio_backtest_tasks[task_id]
    
    # 완료된 경우 결과 반환
    if task_status["status"] == "completed" and task_status["result"]:
        return {
            "task_id": task_id,
            "status": "completed",
            "result": task_status["result"]
        }
    
    # 실패한 경우 에러 반환
    if task_status["status"] == "failed":
        return {
            "task_id": task_id,
            "status": "failed",
            "error": task_status["error"]
        }
    
    # 진행 중인 경우 상태 반환
    return {
        "task_id": task_id,
        "status": task_status["status"],
        "progress": task_status.get("progress", 0),
        "message": task_status.get("message", "백테스트 진행 중...")
    }


async def _run_portfolio_backtest_task(task_id: str, request: BacktestRequest):
    """
    백그라운드에서 포트폴리오 백테스트 실행
    """
    try:
        from core.strategy.registry import StrategyRegistry
        from data.repository import BacktestRepository
        
        # 상태 업데이트
        portfolio_backtest_tasks[task_id]["message"] = "전략 로드 중..."
        portfolio_backtest_tasks[task_id]["progress"] = 10
        
        # 전략 로드 (코드 기반 또는 전략 빌더)
        strategy = None
        try:
            strategy_class = StrategyRegistry.get(request.strategy_name)
            strategy = strategy_class(params=request.parameters or {})
            logger.info(f"Loaded strategy from registry: {request.strategy_name}")
        except (ValueError, KeyError, Exception) as e:
            logger.info(f"Strategy not in registry, trying builder: {e}")
        
        # 전략이 레지스트리에 없으면 전략 빌더에서 로드 (JSON 기반)
        if strategy is None:
            from data.models import StrategyBuilderModel
            from data.repository import get_db_session
            from core.strategy.factory import StrategyFactory
            
            db = get_db_session()
            
            try:
                builder_strategy = db.query(StrategyBuilderModel).filter(
                    StrategyBuilderModel.name == request.strategy_name,
                    StrategyBuilderModel.is_active == True
                ).first()
                
                if not builder_strategy:
                    portfolio_backtest_tasks[task_id]["status"] = "failed"
                    portfolio_backtest_tasks[task_id]["error"] = f"Strategy '{request.strategy_name}' not found in registry or strategy builder"
                    return
            finally:
                db.close()
            
            # JSON 설정 기반으로 전략 생성
            try:
                db_config = {
                    "id": builder_strategy.id,
                    "config": builder_strategy.config,
                    "config_json": builder_strategy.config_json,
                    "python_code": builder_strategy.python_code,
                    "name": builder_strategy.name
                }
                
                strategy = StrategyFactory.create_from_db_config(db_config)
                
                if request.parameters:
                    for key, value in request.parameters.items():
                        strategy.set_param(key, value)
                
                logger.info(f"✓ Loaded strategy from JSON config: {request.strategy_name}")
            except Exception as e:
                logger.error(f"Failed to create strategy from JSON config: {e}", exc_info=True)
                portfolio_backtest_tasks[task_id]["status"] = "failed"
                portfolio_backtest_tasks[task_id]["error"] = f"Failed to load strategy from config: {str(e)}"
                return
        
        # 포트폴리오 전략인지 확인
        is_portfolio = strategy.is_portfolio_strategy()
        if not is_portfolio:
            portfolio_backtest_tasks[task_id]["status"] = "failed"
            portfolio_backtest_tasks[task_id]["error"] = f"Strategy '{request.strategy_name}' is not a portfolio strategy"
            return
        
        # 상태 업데이트
        portfolio_backtest_tasks[task_id]["message"] = "백테스트 엔진 초기화 중..."
        portfolio_backtest_tasks[task_id]["progress"] = 20
        
        # 백테스트 엔진 생성
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=request.initial_capital,
            commission=request.commission or 0.0015,
            slippage=request.slippage or 0.001,
            execution_delay=request.execution_delay or 1.5,
            use_dynamic_slippage=request.use_dynamic_slippage if request.use_dynamic_slippage is not None else True,
            use_tiered_commission=request.use_tiered_commission if request.use_tiered_commission is not None else True
        )
        
        # 상태 업데이트
        portfolio_backtest_tasks[task_id]["message"] = "백테스트 실행 중... (데이터 로드 및 시뮬레이션)"
        portfolio_backtest_tasks[task_id]["progress"] = 30
        
        # 포트폴리오 백테스트 실행
        result = await engine.run(
            ohlc_data=None,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # 상태 업데이트
        portfolio_backtest_tasks[task_id]["message"] = "결과 저장 중..."
        portfolio_backtest_tasks[task_id]["progress"] = 90
        
        # 결과 저장
        backtest_repo = BacktestRepository()
        backtest_id = backtest_repo.save_backtest_result(result)
        
        logger.info(f"Portfolio backtest completed: ID={backtest_id}, Return={result.total_return:.2%}")
        
        # 결과 저장
        portfolio_backtest_tasks[task_id]["status"] = "completed"
        portfolio_backtest_tasks[task_id]["progress"] = 100
        portfolio_backtest_tasks[task_id]["message"] = "백테스트 완료"
        portfolio_backtest_tasks[task_id]["result"] = {
            "backtest_id": backtest_id,
            "strategy_name": result.strategy_name,
            "start_date": result.start_date.isoformat() if result.start_date else None,
            "end_date": result.end_date.isoformat() if result.end_date else None,
            "initial_capital": result.initial_capital,
            "final_equity": result.final_equity,
            "total_return": result.total_return,
            "mdd": result.mdd,
            "sharpe_ratio": result.sharpe_ratio,
            "win_rate": result.win_rate,
            "profit_factor": result.profit_factor,
            "total_trades": result.total_trades,
            "parameters": request.parameters,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Portfolio backtest task failed: {task_id}, {e}", exc_info=True)
        portfolio_backtest_tasks[task_id]["status"] = "failed"
        portfolio_backtest_tasks[task_id]["error"] = str(e)


@router.get("/results", response_model=List[BacktestResponse])
async def get_backtest_results(limit: int = 100, offset: int = 0):
    """
    백테스트 결과 목록 조회 (페이지네이션 지원)
    
    Args:
        limit: 조회할 최대 개수 (기본값: 100)
        offset: 건너뛸 개수 (기본값: 0)
    
    Returns:
        백테스트 결과 리스트
    """
    try:
        from data.repository import BacktestRepository
        
        repo = BacktestRepository()
        results = repo.get_all_backtest_results(limit=limit)
        
        # 오프셋 적용
        if offset > 0:
            results = results[offset:]
        
        logger.info(f"Returning {len(results)} backtest results (limit={limit}, offset={offset})")
        
        # MDD 일관성을 위한 재계산
        from core.backtest.metrics import calculate_mdd
        
        response_list = []
        for r in results:
            # MDD 재계산 (자산 곡선이 있는 경우)
            calculated_mdd = r.mdd  # 기본값
            if r.equity_curve and len(r.equity_curve) >= 2:
                calculated_mdd = calculate_mdd(r.equity_curve)
            
            response_list.append(BacktestResponse(
                backtest_id=r.id,
                strategy_name=r.strategy_name,
                parameters=r.parameters,
                start_date=r.start_date,
                end_date=r.end_date,
                initial_capital=r.initial_capital,
                final_equity=r.final_equity,
                total_return=r.total_return,
                mdd=calculated_mdd,  # 재계산된 값 사용
                sharpe_ratio=r.sharpe_ratio,
                win_rate=r.win_rate,
                profit_factor=r.profit_factor,
                total_trades=r.total_trades,
                created_at=r.created_at
            ))
        
        return response_list
    
    except Exception as e:
        logger.error(f"Failed to get backtest results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/results/batch")
async def delete_multiple_backtest_results(backtest_ids: List[int]):
    """
    여러 백테스트 결과 일괄 삭제
    
    Args:
        backtest_ids: 삭제할 백테스트 ID 리스트
        
    Returns:
        삭제 결과
    """
    try:
        from data.repository import BacktestRepository
        
        repo = BacktestRepository()
        
        deleted_count = 0
        failed_ids = []
        
        for backtest_id in backtest_ids:
            try:
                # 백테스트 존재 확인
                existing = repo.get_backtest_result(backtest_id)
                if existing:
                    success = repo.delete_backtest_result(backtest_id)
                    if success:
                        deleted_count += 1
                        logger.info(f"Backtest result deleted: ID={backtest_id}")
                    else:
                        failed_ids.append(backtest_id)
                else:
                    failed_ids.append(backtest_id)
            except Exception as e:
                logger.error(f"Failed to delete backtest {backtest_id}: {e}")
                failed_ids.append(backtest_id)
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "total_requested": len(backtest_ids),
            "failed_ids": failed_ids,
            "message": f"{deleted_count}개의 백테스트가 성공적으로 삭제되었습니다."
        }
    
    except Exception as e:
        logger.error(f"Failed to delete multiple backtest results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/results/{backtest_id}")
async def delete_backtest_result(backtest_id: int):
    """
    백테스트 결과 삭제
    
    Args:
        backtest_id: 삭제할 백테스트 ID
        
    Returns:
        삭제 성공 메시지
    """
    try:
        from data.repository import BacktestRepository
        
        repo = BacktestRepository()
        
        # 백테스트 존재 확인
        existing = repo.get_backtest_result(backtest_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Backtest result {backtest_id} not found"
            )
        
        # 삭제 실행
        success = repo.delete_backtest_result(backtest_id)
        
        if success:
            logger.info(f"Backtest result deleted: ID={backtest_id}")
            return {
                "success": True,
                "message": f"백테스트 결과 {backtest_id}가 성공적으로 삭제되었습니다.",
                "backtest_id": backtest_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="백테스트 삭제에 실패했습니다."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete backtest result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 백테스트 결과 상세 조회는 backtest_results.py에서 처리
