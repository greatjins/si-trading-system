"""
백테스트 결과 조회 및 시각화 API (차트 렌더링 최적화)
"""
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
import pandas as pd

from data.repository import BacktestRepository, DataRepository, get_db_session
from data.models import BacktestResultModel, TradeModel, StockMasterModel
from core.backtest.trade_analyzer import TradeAnalyzer
from utils.types import (
    BacktestResultDetail, SymbolPerformance, SymbolDetail,
    CompletedTrade, Trade, OrderSide, OHLC
)
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """테스트 엔드포인트"""
    logger.info("Test endpoint called")
    return {"message": "Backtest results router is working"}


@router.get("/results/{backtest_id}")
async def get_backtest_result(backtest_id: int) -> dict:
    """
    백테스트 전체 결과 조회 (차트 렌더링 최적화)
    """
    logger.info(f"=== Getting backtest result for ID: {backtest_id} ===")
    
    db = get_db_session()
    
    try:
        # 1. 백테스트 결과 조회
        backtest = db.query(BacktestResultModel).filter(
            BacktestResultModel.id == backtest_id
        ).first()
        
        if not backtest:
            logger.warning(f"Backtest result {backtest_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Backtest result {backtest_id} not found"
            )
        
        logger.info(f"Found backtest: {backtest.strategy_name}")
        
        # 2. 기본 응답 생성
        response = {
            "backtest_id": backtest.id,
            "strategy_name": backtest.strategy_name,
            "parameters": backtest.parameters or {},
            "start_date": backtest.start_date.isoformat(),
            "end_date": backtest.end_date.isoformat(),
            "initial_capital": backtest.initial_capital,
            "final_equity": backtest.final_equity,
            "total_return": backtest.total_return,
            "mdd": backtest.mdd,
            "sharpe_ratio": backtest.sharpe_ratio,
            "win_rate": backtest.win_rate,
            "profit_factor": backtest.profit_factor,
            "total_trades": backtest.total_trades,
            "created_at": backtest.created_at.isoformat() if backtest.created_at else None
        }
        
        # 3. 자산 곡선 데이터 (차트 렌더링 최적화)
        equity_curve = backtest.equity_curve or []
        equity_timestamps = backtest.equity_timestamps or []
        
        # 차트용 데이터 형식으로 변환 (Chart.js/D3.js 호환)
        chart_data = []
        performance_data = []  # 수익률 차트용
        
        if len(equity_curve) > 0 and len(equity_timestamps) > 0:
            min_length = min(len(equity_curve), len(equity_timestamps))
            initial_capital = equity_curve[0] if len(equity_curve) > 0 else backtest.initial_capital
            
            for i in range(min_length):
                timestamp = equity_timestamps[i]
                equity_value = round(equity_curve[i], 2)
                return_pct = round(((equity_value / initial_capital) - 1) * 100, 2)
                
                chart_data.append({
                    "x": timestamp,
                    "y": equity_value,
                    "date": timestamp[:10],  # YYYY-MM-DD 형식
                    "value": equity_value,
                    "return": return_pct
                })
                
                performance_data.append({
                    "date": timestamp[:10],
                    "return": return_pct
                })
        
        # 기존 형식 유지 (하위 호환성)
        response["equity_curve"] = equity_curve
        response["equity_timestamps"] = equity_timestamps
        
        # 차트 렌더링용 최적화된 형식
        response["chart_data"] = chart_data
        response["performance_data"] = performance_data
        
        logger.info(f"Added equity_curve: {len(equity_curve)} points")
        logger.info(f"Added equity_timestamps: {len(equity_timestamps)} points")
        logger.info(f"Added chart_data: {len(chart_data)} points")
        
        # 4. 종목별 성과 분석 및 추가
        try:
            logger.info("Starting symbol performance analysis...")
            
            # 거래 내역 조회
            trade_models = db.query(TradeModel).filter(
                TradeModel.backtest_id == backtest_id
            ).order_by(TradeModel.timestamp).all()
            
            logger.info(f"Found {len(trade_models)} trades for analysis")
            
            if trade_models:
                # Trade 객체로 변환
                trades = []
                for t in trade_models:
                    try:
                        trade = Trade(
                            trade_id=t.trade_id,
                            order_id=t.order_id,
                            symbol=t.symbol,
                            side=OrderSide(t.side),
                            quantity=t.quantity,
                            price=t.price,
                            commission=t.commission,
                            timestamp=t.timestamp
                        )
                        trades.append(trade)
                    except Exception as trade_error:
                        logger.error(f"Error converting trade {t.trade_id}: {trade_error}")
                        continue
                
                logger.info(f"Converted {len(trades)} trades successfully")
                
                # 종목별 성과 분석
                symbol_performances_dict = TradeAnalyzer.analyze_all_symbols(trades)
                logger.info(f"Analyzed {len(symbol_performances_dict)} symbols")
                
                # 종목명 조회 및 결과 생성
                symbol_performances = []
                for symbol, perf in symbol_performances_dict.items():
                    try:
                        # 종목명 조회
                        stock = db.query(StockMasterModel).filter(
                            StockMasterModel.symbol == symbol
                        ).first()
                        
                        perf.name = stock.name if stock else symbol
                        
                        symbol_performances.append({
                            "symbol": perf.symbol,
                            "name": perf.name,
                            "total_return": round(perf.total_return, 2),
                            "trade_count": perf.trade_count,
                            "win_rate": round(perf.win_rate, 1),
                            "profit_factor": round(perf.profit_factor, 2),
                            "avg_holding_period": perf.avg_holding_period,
                            "total_pnl": round(perf.total_pnl, 2)
                        })
                    except Exception as symbol_error:
                        logger.error(f"Error processing symbol {symbol}: {symbol_error}")
                        continue
                
                # 수익률 기준 내림차순 정렬
                symbol_performances.sort(key=lambda x: x["total_return"], reverse=True)
                response["symbol_performances"] = symbol_performances
                
                logger.info(f"Added {len(symbol_performances)} symbol performances")
            else:
                response["symbol_performances"] = []
                logger.info("No trades found, empty symbol performances")
        
        except Exception as e:
            logger.error(f"Error in symbol performance analysis: {e}", exc_info=True)
            response["symbol_performances"] = []
        
        logger.info(f"Final response keys: {list(response.keys())}")
        logger.info(f"=== Backtest result API completed ===")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backtest result: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/results/{backtest_id}/symbols")
async def get_symbol_performance(backtest_id: int) -> List[dict]:
    """
    종목별 성과 리스트
    """
    db = get_db_session()
    
    try:
        # 백테스트 존재 확인
        backtest = db.query(BacktestResultModel).filter(
            BacktestResultModel.id == backtest_id
        ).first()
        
        if not backtest:
            raise HTTPException(
                status_code=404,
                detail=f"Backtest result {backtest_id} not found"
            )
        
        # 거래 내역 조회
        trade_models = db.query(TradeModel).filter(
            TradeModel.backtest_id == backtest_id
        ).order_by(TradeModel.timestamp).all()
        
        # Trade 객체로 변환
        trades = [
            Trade(
                trade_id=t.trade_id,
                order_id=t.order_id,
                symbol=t.symbol,
                side=OrderSide(t.side),
                quantity=t.quantity,
                price=t.price,
                commission=t.commission,
                timestamp=t.timestamp
            )
            for t in trade_models
        ]
        
        # 종목별 성과 분석
        symbol_performances_dict = TradeAnalyzer.analyze_all_symbols(trades)
        
        # 종목명 조회 및 추가
        result = []
        for symbol, perf in symbol_performances_dict.items():
            stock = db.query(StockMasterModel).filter(
                StockMasterModel.symbol == symbol
            ).first()
            
            perf.name = stock.name if stock else symbol
            
            result.append({
                "symbol": perf.symbol,
                "name": perf.name,
                "total_return": round(perf.total_return, 2),
                "trade_count": perf.trade_count,
                "win_rate": round(perf.win_rate, 1),
                "profit_factor": round(perf.profit_factor, 2),
                "avg_holding_period": perf.avg_holding_period,
                "total_pnl": round(perf.total_pnl, 2)
            })
        
        # 수익률 기준 내림차순 정렬
        result.sort(key=lambda x: x["total_return"], reverse=True)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get symbol performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/results/{backtest_id}/symbols/{symbol}")
async def get_symbol_detail(backtest_id: int, symbol: str) -> dict:
    """
    특정 종목 상세 정보 (거래 내역 포함)
    """
    db = get_db_session()
    
    try:
        # 백테스트 존재 확인
        backtest = db.query(BacktestResultModel).filter(
            BacktestResultModel.id == backtest_id
        ).first()
        
        if not backtest:
            raise HTTPException(
                status_code=404,
                detail=f"Backtest result {backtest_id} not found"
            )
        
        # 해당 종목의 거래 내역 조회
        trade_models = db.query(TradeModel).filter(
            TradeModel.backtest_id == backtest_id,
            TradeModel.symbol == symbol
        ).order_by(TradeModel.timestamp).all()
        
        if not trade_models:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} not found in backtest {backtest_id}"
            )
        
        # Trade 객체로 변환
        trades = [
            Trade(
                trade_id=t.trade_id,
                order_id=t.order_id,
                symbol=t.symbol,
                side=OrderSide(t.side),
                quantity=t.quantity,
                price=t.price,
                commission=t.commission,
                timestamp=t.timestamp
            )
            for t in trade_models
        ]
        
        # 완결된 거래 생성
        completed_trades = TradeAnalyzer.match_entry_exit(trades)
        
        # 메트릭 계산
        metrics = TradeAnalyzer.calculate_symbol_metrics(completed_trades)
        
        # 종목명 조회
        stock = db.query(StockMasterModel).filter(
            StockMasterModel.symbol == symbol
        ).first()
        
        metrics.name = stock.name if stock else symbol
        
        # 추가 메트릭 계산
        avg_buy_price = sum(t.entry_price * t.entry_quantity for t in completed_trades) / sum(t.entry_quantity for t in completed_trades) if completed_trades else 0
        avg_sell_price = sum(t.exit_price * t.exit_quantity for t in completed_trades) / sum(t.exit_quantity for t in completed_trades) if completed_trades else 0
        avg_holding_days = sum(t.holding_period for t in completed_trades) / len(completed_trades) if completed_trades else 0

        # 응답 생성
        return {
            "symbol": symbol,
            "name": metrics.name,
            "total_return": round(metrics.total_return, 2),
            "trade_count": metrics.trade_count,
            "win_rate": round(metrics.win_rate, 1),
            "profit_factor": round(metrics.profit_factor, 2),
            "avg_holding_period": metrics.avg_holding_period,
            "total_pnl": round(metrics.total_pnl, 2),
            "avg_buy_price": round(avg_buy_price, 2),
            "avg_sell_price": round(avg_sell_price, 2),
            "avg_holding_days": round(avg_holding_days, 1),
            "completed_trades": [
                {
                    "symbol": ct.symbol,
                    "entry_date": ct.entry_date.isoformat(),
                    "entry_price": round(ct.entry_price, 2),
                    "entry_quantity": ct.entry_quantity,
                    "exit_date": ct.exit_date.isoformat(),
                    "exit_price": round(ct.exit_price, 2),
                    "exit_quantity": ct.exit_quantity,
                    "pnl": round(ct.pnl, 2),
                    "return_pct": round(ct.return_pct, 2),
                    "holding_period": ct.holding_period,
                    "commission": round(ct.commission, 2)
                }
                for ct in completed_trades
            ],
            "all_trades": [
                {
                    "trade_id": t.trade_id,
                    "order_id": t.order_id,
                    "symbol": t.symbol,
                    "side": t.side.value,
                    "quantity": t.quantity,
                    "price": round(t.price, 2),
                    "commission": round(t.commission, 2),
                    "timestamp": t.timestamp.isoformat()
                }
                for t in trades
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get symbol detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/results/{backtest_id}/ohlc/{symbol}")
async def get_symbol_ohlc(backtest_id: int, symbol: str) -> List[dict]:
    """
    특정 종목의 OHLC 데이터 (백테스트 기간)
    """
    db = get_db_session()
    
    try:
        # 백테스트 기간 조회
        backtest = db.query(BacktestResultModel).filter(
            BacktestResultModel.id == backtest_id
        ).first()
        
        if not backtest:
            raise HTTPException(
                status_code=404,
                detail=f"Backtest result {backtest_id} not found"
            )
        
        # OHLC 데이터 조회
        repo = DataRepository()
        ohlc_df = repo.get_ohlc(
            symbol=symbol,
            interval='1d',
            start_date=backtest.start_date,
            end_date=backtest.end_date
        )
        
        if ohlc_df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No OHLC data for {symbol} in the backtest period"
            )
        
        # DataFrame을 딕셔너리 리스트로 변환
        result = []
        for idx, row in ohlc_df.iterrows():
            result.append({
                "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                "date": str(idx)[:10],  # YYYY-MM-DD 형식
                "open": round(float(row['open']), 2),
                "high": round(float(row['high']), 2),
                "low": round(float(row['low']), 2),
                "close": round(float(row['close']), 2),
                "volume": int(row['volume'])
            })
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get OHLC data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/results/compare")
async def compare_backtests(backtest_ids: List[int]) -> dict:
    """
    여러 백테스트 결과 비교
    """
    db = get_db_session()
    
    try:
        if not backtest_ids or len(backtest_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 backtest IDs are required for comparison"
            )
        
        # 백테스트 결과 조회
        backtests = db.query(BacktestResultModel).filter(
            BacktestResultModel.id.in_(backtest_ids)
        ).all()
        
        if len(backtests) != len(backtest_ids):
            raise HTTPException(
                status_code=404,
                detail="Some backtest results not found"
            )
        
        # 비교 데이터 생성
        comparison = []
        for bt in backtests:
            comparison.append({
                "backtest_id": bt.id,
                "strategy_name": bt.strategy_name,
                "start_date": bt.start_date.isoformat(),
                "end_date": bt.end_date.isoformat(),
                "total_return": round(bt.total_return, 4),
                "mdd": round(bt.mdd, 4),
                "sharpe_ratio": round(bt.sharpe_ratio, 4),
                "win_rate": round(bt.win_rate, 2),
                "profit_factor": round(bt.profit_factor, 2),
                "total_trades": bt.total_trades,
                "equity_curve": bt.equity_curve
            })
        
        # 최고 성과 찾기
        best_return_idx = max(range(len(comparison)), key=lambda i: comparison[i]["total_return"])
        comparison[best_return_idx]["is_best"] = True
        
        return {
            "comparison": comparison,
            "best_backtest_id": comparison[best_return_idx]["backtest_id"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare backtests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()