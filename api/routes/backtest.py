"""
백테스트 관련 API
"""
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from api.schemas import BacktestRequest, BacktestResponse, AutoMLRequest, AutoMLResponse
from data.repository import DataRepository
from core.backtest.engine import BacktestEngine
from core.automl.grid_search import GridSearch
from core.automl.random_search import RandomSearch
from core.automl.genetic import GeneticAlgorithm
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


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
        
        # 전략이 레지스트리에 없으면 전략 빌더에서 로드
        if strategy is None:
            from data.models import StrategyBuilderModel
            from data.repository import get_db_session
            
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
            
            # Python 코드 실행하여 전략 클래스 생성
            python_code = builder_strategy.python_code
            
            # 디버깅: 생성된 코드 저장
            import os
            debug_file = f"data/debug_strategy_{builder_strategy.id}.py"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(python_code)
            logger.info(f"Generated code saved to: {debug_file}")
            
            # 전략 클래스 동적 로드
            import sys
            from types import ModuleType
            import pandas as pd
            
            # 임시 모듈 생성
            temp_module = ModuleType("temp_strategy")
            temp_module.__dict__.update({
                "BaseStrategy": __import__("core.strategy.base", fromlist=["BaseStrategy"]).BaseStrategy,
                "strategy": __import__("core.strategy.registry", fromlist=["strategy"]).strategy,
                "OHLC": __import__("utils.types", fromlist=["OHLC"]).OHLC,
                "Position": __import__("utils.types", fromlist=["Position"]).Position,
                "Account": __import__("utils.types", fromlist=["Account"]).Account,
                "OrderSignal": __import__("utils.types", fromlist=["OrderSignal"]).OrderSignal,
                "OrderSide": __import__("utils.types", fromlist=["OrderSide"]).OrderSide,
                "OrderType": __import__("utils.types", fromlist=["OrderType"]).OrderType,
                "Order": __import__("utils.types", fromlist=["Order"]).Order,
                "List": List,
                "pd": pd,
                "datetime": datetime,
            })
            
            # 코드 실행
            try:
                exec(python_code, temp_module.__dict__)
            except SyntaxError as e:
                logger.error(f"Syntax error in generated code: {e}")
                logger.error(f"Full code:\n{python_code}")
                raise
            
            # 전략 클래스 찾기
            strategy_class = None
            for name, obj in temp_module.__dict__.items():
                if isinstance(obj, type) and hasattr(obj, "on_bar") and name != "BaseStrategy":
                    strategy_class = obj
                    break
            
            if not strategy_class:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to load strategy class from generated code"
                )
            
            strategy = strategy_class(params=request.parameters or {})
            logger.info(f"Loaded strategy from builder: {request.strategy_name}")
        
        # select_universe 메서드가 있고 symbol이 없으면 포트폴리오 전략
        if hasattr(strategy, 'select_universe') and not request.symbol:
            logger.info(f"Strategy '{request.strategy_name}' has select_universe - running as portfolio strategy")
            # symbol 없이 포트폴리오 백테스트 실행
            ohlc_list = None
        
        if request.symbol:
            logger.info(f"Running single-symbol backtest: {request.strategy_name} on {request.symbol}")
        else:
            logger.info(f"Running portfolio backtest: {request.strategy_name}")
        
        # 백테스트 실행
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=request.initial_capital,
            commission=0.00015
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


@router.post("/portfolio", response_model=BacktestResponse)
async def run_portfolio_backtest(request: BacktestRequest):
    """
    포트폴리오 백테스트 실행 (종목 선택 전략)
    
    Args:
        request: 백테스트 요청 (symbol은 무시됨)
        
    Returns:
        백테스트 결과
    """
    try:
        from core.strategy.registry import StrategyRegistry
        from data.repository import BacktestRepository
        
        logger.info(f"Running portfolio backtest: {request.strategy_name}")
        
        # 전략 로드 (코드 기반 또는 전략 빌더)
        strategy = None
        try:
            strategy_class = StrategyRegistry.get(request.strategy_name)
            strategy = strategy_class(params=request.parameters or {})
            logger.info(f"Loaded strategy from registry: {request.strategy_name}")
        except (ValueError, KeyError, Exception) as e:
            logger.info(f"Strategy not in registry, trying builder: {e}")
        
        # 전략이 레지스트리에 없으면 전략 빌더에서 로드
        if strategy is None:
            from data.models import StrategyBuilderModel
            from data.repository import get_db_session
            
            db = get_db_session()
            
            try:
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
            
            # Python 코드 실행하여 전략 클래스 생성
            python_code = builder_strategy.python_code
            
            import sys
            from types import ModuleType
            import pandas as pd
            
            temp_module = ModuleType("temp_strategy")
            temp_module.__dict__.update({
                "BaseStrategy": __import__("core.strategy.base", fromlist=["BaseStrategy"]).BaseStrategy,
                "strategy": __import__("core.strategy.registry", fromlist=["strategy"]).strategy,
                "OHLC": __import__("utils.types", fromlist=["OHLC"]).OHLC,
                "Position": __import__("utils.types", fromlist=["Position"]).Position,
                "Account": __import__("utils.types", fromlist=["Account"]).Account,
                "OrderSignal": __import__("utils.types", fromlist=["OrderSignal"]).OrderSignal,
                "OrderSide": __import__("utils.types", fromlist=["OrderSide"]).OrderSide,
                "OrderType": __import__("utils.types", fromlist=["OrderType"]).OrderType,
                "Order": __import__("utils.types", fromlist=["Order"]).Order,
                "List": List,
                "pd": pd,
                "datetime": datetime,
            })
            
            try:
                exec(python_code, temp_module.__dict__)
            except SyntaxError as e:
                logger.error(f"Syntax error in generated code: {e}")
                raise HTTPException(status_code=500, detail=f"Syntax error in strategy code: {e}")
            
            strategy_class = None
            for name, obj in temp_module.__dict__.items():
                if isinstance(obj, type) and hasattr(obj, "on_bar") and name != "BaseStrategy":
                    strategy_class = obj
                    break
            
            if not strategy_class:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to load strategy class from generated code"
                )
            
            strategy = strategy_class(params=request.parameters or {})
            logger.info(f"Loaded strategy from builder: {request.strategy_name}")
        
        # 포트폴리오 전략인지 확인
        if not hasattr(strategy, 'select_universe'):
            raise HTTPException(
                status_code=400,
                detail=f"Strategy '{request.strategy_name}' is not a portfolio strategy. Use /api/backtest/run instead."
            )
        
        # 백테스트 엔진 생성
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=request.initial_capital,
            commission=0.00015
        )
        
        # 포트폴리오 백테스트 실행 (symbol 없이)
        result = await engine.run(
            ohlc_data=None,  # 포트폴리오 전략은 내부에서 데이터 로드
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # 결과 저장
        backtest_repo = BacktestRepository()
        backtest_id = backtest_repo.save_backtest_result(result)
        
        logger.info(f"Portfolio backtest completed: ID={backtest_id}, Return={result.total_return:.2%}")
        
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
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run portfolio backtest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
