"""
백테스트 성과 메트릭 계산
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from utils.types import Trade, OrderSide
from utils.logger import setup_logger

logger = setup_logger(__name__)


# --- 디자인 문서 기반 데이터 모델 ---

@dataclass
class CompletedTrade:
    """완결된 거래 (매수 → 매도)"""
    symbol: str
    entry_date: datetime
    entry_price: float
    entry_quantity: float
    exit_date: datetime
    exit_price: float
    exit_quantity: float
    pnl: float  # 손익 (원)
    return_pct: float  # 수익률 (%)
    holding_period: int  # 보유 기간 (일)
    commission: float  # 수수료

@dataclass
class SymbolPerformance:
    """종목별 성과"""
    symbol: str
    total_return: float  # 총 수익률 (%)
    trade_count: int  # 거래 횟수
    win_rate: float  # 승률 (%)
    profit_factor: float  # 손익비
    avg_holding_period: float  # 평균 보유 기간 (일)
    total_pnl: float  # 총 손익 (원)


# --- 디자인 문서 기반 분석기 ---

class TradeAnalyzer:
    """거래 분석 및 메트릭 계산"""
    
    @staticmethod
    def group_trades_by_symbol(trades: List[Trade]) -> Dict[str, List[Trade]]:
        """종목별로 거래 그룹화"""
        grouped = {}
        for trade in trades:
            if trade.symbol not in grouped:
                grouped[trade.symbol] = []
            grouped[trade.symbol].append(trade)
        return grouped
    
    @staticmethod
    def match_entry_exit(trades: List[Trade]) -> List[CompletedTrade]:
        """매수/매도 거래를 매칭하여 완결된 거래 생성"""
        if not trades:
            return []
            
        # 시간순 정렬
        sorted_trades = sorted(trades, key=lambda x: x.timestamp)
        completed_trades = []
        
        # FIFO 매칭을 위한 큐
        buy_queue = []  # (quantity, price, timestamp, commission_per_unit)
        
        for trade in sorted_trades:
            if trade.side == OrderSide.BUY:
                buy_queue.append({
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'date': trade.timestamp,
                    'commission': trade.commission / trade.quantity if trade.quantity > 0 else 0
                })
            
            elif trade.side == OrderSide.SELL:
                remaining_sell_qty = trade.quantity
                
                while remaining_sell_qty > 0 and buy_queue:
                    buy_item = buy_queue[0]
                    match_qty = min(remaining_sell_qty, buy_item['quantity'])
                    
                    # 매수/매도 수수료 계산 (비례 배분)
                    entry_commission = buy_item['commission'] * match_qty
                    exit_commission = (trade.commission / trade.quantity) * match_qty if trade.quantity > 0 else 0
                    total_commission = entry_commission + exit_commission
                    
                    # 손익 계산
                    buy_val = match_qty * buy_item['price']
                    sell_val = match_qty * trade.price
                    pnl = sell_val - buy_val - total_commission
                    return_pct = (pnl / buy_val) if buy_val > 0 else 0.0
                    
                    # 보유 기간
                    holding_days = (trade.timestamp - buy_item['date']).days
                    
                    completed_trades.append(CompletedTrade(
                        symbol=trade.symbol,
                        entry_date=buy_item['date'],
                        entry_price=buy_item['price'],
                        entry_quantity=match_qty,
                        exit_date=trade.timestamp,
                        exit_price=trade.price,
                        exit_quantity=match_qty,
                        pnl=pnl,
                        return_pct=return_pct,
                        holding_period=holding_days,
                        commission=total_commission
                    ))
                    
                    # 큐 업데이트
                    remaining_sell_qty -= match_qty
                    buy_item['quantity'] -= match_qty
                    
                    if buy_item['quantity'] <= 0.000001: # 부동소수점 오차 고려
                        buy_queue.pop(0)
                        
        return completed_trades

    @staticmethod
    def calculate_symbol_metrics(trades: List[Trade]) -> SymbolPerformance:
        """종목별 성과 메트릭 계산"""
        if not trades:
            return None
            
        symbol = trades[0].symbol
        completed_trades = TradeAnalyzer.match_entry_exit(trades)
        
        if not completed_trades:
            return SymbolPerformance(symbol, 0, 0, 0, 0, 0, 0)
            
        total_pnl = sum(t.pnl for t in completed_trades)
        wins = [t for t in completed_trades if t.pnl > 0]
        losses = [t for t in completed_trades if t.pnl <= 0]
        
        win_rate = len(wins) / len(completed_trades) if completed_trades else 0.0
        
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        avg_holding = np.mean([t.holding_period for t in completed_trades])
        
        # 총 수익률 (단순 합산 방식, 자본금 대비 아님에 유의)
        total_return_sum = sum(t.return_pct for t in completed_trades)
        
        return SymbolPerformance(
            symbol=symbol,
            total_return=total_return_sum,
            trade_count=len(completed_trades),
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_holding_period=avg_holding,
            total_pnl=total_pnl
        )


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
    MDD (Maximum Drawdown) 계산 (개선된 버전)
    
    Args:
        equity_curve: 자산 곡선
    
    Returns:
        MDD (소수, 양수) - 0.0 ~ 1.0 범위
    """
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    
    # 유효한 양수 값만 사용 (0 이하 값 제외)
    valid_equity = [e for e in equity_curve if e > 0]
    
    if len(valid_equity) < 2:
        logger.warning(f"유효한 자산 값이 부족합니다. 전체: {len(equity_curve)}, 유효: {len(valid_equity)}")
        return 0.0
    
    peak = valid_equity[0]
    max_drawdown = 0.0
    
    for equity in valid_equity:
        # 새로운 고점 갱신
        if equity > peak:
            peak = equity
        
        # 현재 드로우다운 계산
        if peak > 0:
            current_drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, current_drawdown)
    
    # MDD는 0~1 사이 값이어야 함
    mdd_result = min(max_drawdown, 1.0)
    
    # 디버깅 로그
    if mdd_result > 0.5:  # 50% 이상 MDD인 경우 로그
        logger.warning(f"높은 MDD 감지: {mdd_result:.2%}, 최고점: {peak:,.0f}, 최저점: {min(valid_equity):,.0f}")
    
    return mdd_result


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
