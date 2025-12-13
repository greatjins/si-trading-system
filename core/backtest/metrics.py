"""
백테스트 성과 메트릭 계산
"""
from typing import List, Dict
import numpy as np

from utils.types import Trade, OrderSide
from utils.logger import setup_logger

logger = setup_logger(__name__)


def calculate_metrics(
    equity_curve: List[float],
    trades: List[Trade],
    initial_capital: float,
    risk_free_rate: float = 0.02
) -> Dict[str, float]:
    """
    백테스트 성과 지표 계산
    
    Args:
        equity_curve: 자산 곡선
        trades: 거래 내역
        initial_capital: 초기 자본
        risk_free_rate: 무위험 수익률 (연율, 기본: 2%)
    
    Returns:
        메트릭 딕셔너리
    """
    if not equity_curve or len(equity_curve) < 2:
        return _empty_metrics()
    
    metrics = {}
    
    # 총 수익률
    metrics["total_return"] = calculate_total_return(equity_curve, initial_capital)
    
    # MDD (Maximum Drawdown)
    metrics["mdd"] = calculate_mdd(equity_curve)
    
    # 샤프 비율
    metrics["sharpe_ratio"] = calculate_sharpe_ratio(equity_curve, risk_free_rate)
    
    # 거래 기반 메트릭
    if trades:
        metrics["win_rate"] = calculate_win_rate(trades)
        metrics["profit_factor"] = calculate_profit_factor(trades)
        metrics["avg_win"] = calculate_avg_win(trades)
        metrics["avg_loss"] = calculate_avg_loss(trades)
        metrics["max_consecutive_wins"] = calculate_max_consecutive_wins(trades)
        metrics["max_consecutive_losses"] = calculate_max_consecutive_losses(trades)
    else:
        metrics["win_rate"] = 0.0
        metrics["profit_factor"] = 0.0
        metrics["avg_win"] = 0.0
        metrics["avg_loss"] = 0.0
        metrics["max_consecutive_wins"] = 0
        metrics["max_consecutive_losses"] = 0
    
    return metrics


def _empty_metrics() -> Dict[str, float]:
    """빈 메트릭 반환"""
    return {
        "total_return": 0.0,
        "mdd": 0.0,
        "sharpe_ratio": 0.0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "max_consecutive_wins": 0,
        "max_consecutive_losses": 0
    }


def calculate_total_return(equity_curve: List[float], initial_capital: float) -> float:
    """
    총 수익률 계산
    
    Args:
        equity_curve: 자산 곡선
        initial_capital: 초기 자본
    
    Returns:
        총 수익률 (소수)
    """
    if not equity_curve or initial_capital == 0:
        return 0.0
    
    final_equity = equity_curve[-1]
    return (final_equity - initial_capital) / initial_capital


def calculate_mdd(equity_curve: List[float]) -> float:
    """
    MDD (Maximum Drawdown) 계산
    
    Args:
        equity_curve: 자산 곡선
    
    Returns:
        MDD (소수, 양수)
    """
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    
    peak = equity_curve[0]
    max_drawdown = 0.0
    
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        
        drawdown = (peak - equity) / peak if peak > 0 else 0.0
        max_drawdown = max(max_drawdown, drawdown)
    
    return max_drawdown


def calculate_sharpe_ratio(
    equity_curve: List[float],
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """
    샤프 비율 계산
    
    Args:
        equity_curve: 자산 곡선
        risk_free_rate: 무위험 수익률 (연율)
        periods_per_year: 연간 기간 수 (일봉: 252)
    
    Returns:
        샤프 비율
    """
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    
    # 수익률 계산
    returns = []
    for i in range(1, len(equity_curve)):
        if equity_curve[i-1] > 0:
            ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
            returns.append(ret)
    
    if not returns:
        return 0.0
    
    # 평균 수익률 및 표준편차
    avg_return = np.mean(returns)
    std_return = np.std(returns)
    
    if std_return == 0:
        return 0.0
    
    # 일일 무위험 수익률
    daily_rf = risk_free_rate / periods_per_year
    
    # 샤프 비율 (연율화)
    sharpe = (avg_return - daily_rf) / std_return * np.sqrt(periods_per_year)
    
    return sharpe


def calculate_win_rate(trades: List[Trade]) -> float:
    """
    승률 계산 (매수-매도 쌍 매칭)
    
    Args:
        trades: 거래 내역
    
    Returns:
        승률 (0~1)
    """
    if not trades:
        return 0.0
    
    # 종목별로 거래 그룹화
    symbol_trades = {}
    for trade in trades:
        if trade.symbol not in symbol_trades:
            symbol_trades[trade.symbol] = []
        symbol_trades[trade.symbol].append(trade)
    
    total_completed_trades = 0
    winning_trades = 0
    
    # 각 종목별로 매수-매도 쌍 분석
    for symbol, symbol_trade_list in symbol_trades.items():
        # 시간순 정렬
        symbol_trade_list.sort(key=lambda x: x.timestamp)
        
        position_quantity = 0
        position_cost = 0.0
        
        for trade in symbol_trade_list:
            if trade.side == OrderSide.BUY:
                # 매수: 포지션 증가
                position_cost += trade.quantity * trade.price + trade.commission
                position_quantity += trade.quantity
            
            elif trade.side == OrderSide.SELL and position_quantity > 0:
                # 매도: 포지션 감소
                sell_quantity = min(trade.quantity, position_quantity)
                
                # 평균 단가 계산
                avg_cost_per_share = position_cost / position_quantity if position_quantity > 0 else 0
                
                # 손익 계산
                sell_proceeds = sell_quantity * trade.price - trade.commission
                sell_cost = sell_quantity * avg_cost_per_share
                pnl = sell_proceeds - sell_cost
                
                # 완결된 거래로 카운트
                total_completed_trades += 1
                if pnl > 0:
                    winning_trades += 1
                
                # 포지션 업데이트
                position_quantity -= sell_quantity
                position_cost -= sell_cost
    
    return winning_trades / total_completed_trades if total_completed_trades > 0 else 0.0


def calculate_profit_factor(trades: List[Trade]) -> float:
    """
    손익비 (Profit Factor) 계산
    
    Args:
        trades: 거래 내역
    
    Returns:
        손익비 (총 이익 / 총 손실)
    """
    if not trades:
        return 0.0
    
    # 종목별로 거래 그룹화
    symbol_trades = {}
    for trade in trades:
        if trade.symbol not in symbol_trades:
            symbol_trades[trade.symbol] = []
        symbol_trades[trade.symbol].append(trade)
    
    total_profit = 0.0
    total_loss = 0.0
    
    # 각 종목별로 매수-매도 쌍 분석
    for symbol, symbol_trade_list in symbol_trades.items():
        # 시간순 정렬
        symbol_trade_list.sort(key=lambda x: x.timestamp)
        
        position_quantity = 0
        position_cost = 0.0
        
        for trade in symbol_trade_list:
            if trade.side == OrderSide.BUY:
                # 매수: 포지션 증가
                position_cost += trade.quantity * trade.price + trade.commission
                position_quantity += trade.quantity
            
            elif trade.side == OrderSide.SELL and position_quantity > 0:
                # 매도: 포지션 감소
                sell_quantity = min(trade.quantity, position_quantity)
                
                # 평균 단가 계산
                avg_cost_per_share = position_cost / position_quantity if position_quantity > 0 else 0
                
                # 손익 계산
                sell_proceeds = sell_quantity * trade.price - trade.commission
                sell_cost = sell_quantity * avg_cost_per_share
                pnl = sell_proceeds - sell_cost
                
                # 이익/손실 누적
                if pnl > 0:
                    total_profit += pnl
                else:
                    total_loss += abs(pnl)
                
                # 포지션 업데이트
                position_quantity -= sell_quantity
                position_cost -= sell_cost
    
    return total_profit / total_loss if total_loss > 0 else (float('inf') if total_profit > 0 else 0.0)


def calculate_avg_win(trades: List[Trade]) -> float:
    """평균 수익 거래"""
    if not trades:
        return 0.0
    
    profits = _get_trade_pnls(trades)
    winning_trades = [pnl for pnl in profits if pnl > 0]
    
    return np.mean(winning_trades) if winning_trades else 0.0


def calculate_avg_loss(trades: List[Trade]) -> float:
    """평균 손실 거래"""
    if not trades:
        return 0.0
    
    profits = _get_trade_pnls(trades)
    losing_trades = [pnl for pnl in profits if pnl < 0]
    
    return np.mean(losing_trades) if losing_trades else 0.0


def calculate_max_consecutive_wins(trades: List[Trade]) -> int:
    """최대 연속 수익 거래"""
    if not trades:
        return 0
    
    profits = _get_trade_pnls(trades)
    
    max_consecutive = 0
    current_consecutive = 0
    
    for pnl in profits:
        if pnl > 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return max_consecutive


def calculate_max_consecutive_losses(trades: List[Trade]) -> int:
    """최대 연속 손실 거래"""
    if not trades:
        return 0
    
    profits = _get_trade_pnls(trades)
    
    max_consecutive = 0
    current_consecutive = 0
    
    for pnl in profits:
        if pnl < 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return max_consecutive


def _get_trade_pnls(trades: List[Trade]) -> List[float]:
    """거래별 손익 계산"""
    # 종목별로 거래 그룹화
    symbol_trades = {}
    for trade in trades:
        if trade.symbol not in symbol_trades:
            symbol_trades[trade.symbol] = []
        symbol_trades[trade.symbol].append(trade)
    
    pnls = []
    
    # 각 종목별로 매수-매도 쌍 분석
    for symbol, symbol_trade_list in symbol_trades.items():
        # 시간순 정렬
        symbol_trade_list.sort(key=lambda x: x.timestamp)
        
        position_quantity = 0
        position_cost = 0.0
        
        for trade in symbol_trade_list:
            if trade.side == OrderSide.BUY:
                # 매수: 포지션 증가
                position_cost += trade.quantity * trade.price + trade.commission
                position_quantity += trade.quantity
            
            elif trade.side == OrderSide.SELL and position_quantity > 0:
                # 매도: 포지션 감소
                sell_quantity = min(trade.quantity, position_quantity)
                
                # 평균 단가 계산
                avg_cost_per_share = position_cost / position_quantity if position_quantity > 0 else 0
                
                # 손익 계산
                sell_proceeds = sell_quantity * trade.price - trade.commission
                sell_cost = sell_quantity * avg_cost_per_share
                pnl = sell_proceeds - sell_cost
                
                pnls.append(pnl)
                
                # 포지션 업데이트
                position_quantity -= sell_quantity
                position_cost -= sell_cost
    
    return pnls
