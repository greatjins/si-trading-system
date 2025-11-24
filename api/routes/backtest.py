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
        
        logger.info(f"Loaded {len(data)} bars for {request.symbol}")
        
        # 전략 로드 (코드 기반 또는 전략 빌더)
        try:
            # 먼저 코드 기반 전략 시도
            strategy_class = StrategyRegistry.get(request.strategy_name)
            strategy = strategy_class(params=request.parameters or {})
        except ValueError:
            # 전략 빌더 전략 시도
            from data.models import StrategyBuilderModel
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            # DB 세션 생성
            engine = create_engine("sqlite:///data/hts.db")
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            
            try:
                # 전략 빌더에서 전략 찾기
                builder_strategy = db.query(StrategyBuilderModel).filter(
                    StrategyBuilderModel.name == request.strategy_name,
                    StrategyBuilderModel.is_active == 1
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
        
        logger.info(f"Running backtest: {request.strategy_name} on {request.symbol}")
        
        # 백테스트 실행
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=request.initial_capital,
            commission=0.00015
        )
        
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
        
        # 비동기 실행
        result = await engine.run(ohlc_list)
        
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


@router.get("/results", response_model=List[BacktestResponse])
async def get_backtest_results():
    """
    백테스트 결과 목록 조회
    
    Returns:
        백테스트 결과 리스트
    """
    try:
        # TODO: DB에서 백테스트 결과 조회
        return []
    
    except Exception as e:
        logger.error(f"Failed to get backtest results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_result(backtest_id: int):
    """
    백테스트 결과 조회
    
    Args:
        backtest_id: 백테스트 ID
        
    Returns:
        백테스트 결과
    """
    try:
        # TODO: DB에서 백테스트 결과 조회
        raise HTTPException(status_code=404, detail="Backtest result not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backtest result: {e}")
        raise HTTPException(status_code=500, detail=str(e))
