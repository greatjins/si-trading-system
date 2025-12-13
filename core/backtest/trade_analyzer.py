"""
거래 분석 및 메트릭 계산
"""
from typing import List, Dict
from collections import defaultdict
from datetime import datetime

from utils.types import Trade, CompletedTrade, SymbolPerformance, OrderSide
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TradeAnalyzer:
    """거래 분석 및 메트릭 계산"""
    
    @staticmethod
    def group_trades_by_symbol(trades: List[Trade]) -> Dict[str, List[Trade]]:
        """
        종목별로 거래 그룹화
        
        Args:
            trades: 전체 거래 리스트
            
        Returns:
            {symbol: [trades]} 딕셔너리
        """
        grouped = defaultdict(list)
        for trade in trades:
            grouped[trade.symbol].append(trade)
        
        # 각 종목의 거래를 시간순 정렬
        for symbol in grouped:
            grouped[symbol].sort(key=lambda t: t.timestamp)
        
        return dict(grouped)
    
    @staticmethod
    def match_entry_exit(trades: List[Trade]) -> List[CompletedTrade]:
        """
        매수/매도 거래를 매칭하여 완결된 거래 생성 (FIFO)
        
        Args:
            trades: 특정 종목의 거래 리스트 (시간순 정렬)
            
        Returns:
            완결된 거래 리스트
        """
        if not trades:
            return []
        
        completed_trades = []
        
        # 매수 포지션 큐 (FIFO)
        buy_queue: List[Trade] = []
        
        for trade in trades:
            if trade.side == OrderSide.BUY:
                # 매수 거래는 큐에 추가
                buy_queue.append(trade)
            
            elif trade.side == OrderSide.SELL:
                # 매도 거래는 큐에서 매수 거래와 매칭
                remaining_quantity = trade.quantity
                
                while remaining_quantity > 0 and buy_queue:
                    buy_trade = buy_queue[0]
                    
                    # 매칭할 수량 결정
                    matched_quantity = min(remaining_quantity, buy_trade.quantity)
                    
                    # 완결된 거래 생성
                    holding_period = (trade.timestamp - buy_trade.timestamp).days
                    entry_cost = matched_quantity * buy_trade.price
                    exit_value = matched_quantity * trade.price
                    commission = buy_trade.commission + trade.commission
                    pnl = exit_value - entry_cost - commission
                    return_pct = (pnl / entry_cost) * 100 if entry_cost > 0 else 0
                    
                    completed_trade = CompletedTrade(
                        symbol=trade.symbol,
                        entry_date=buy_trade.timestamp,
                        entry_price=buy_trade.price,
                        entry_quantity=matched_quantity,
                        exit_date=trade.timestamp,
                        exit_price=trade.price,
                        exit_quantity=matched_quantity,
                        pnl=pnl,
                        return_pct=return_pct,
                        holding_period=holding_period,
                        commission=commission
                    )
                    
                    completed_trades.append(completed_trade)
                    
                    # 큐 업데이트
                    buy_trade.quantity -= matched_quantity
                    remaining_quantity -= matched_quantity
                    
                    if buy_trade.quantity == 0:
                        buy_queue.pop(0)
                
                if remaining_quantity > 0:
                    logger.warning(
                        f"Sell trade has remaining quantity: {trade.symbol} "
                        f"{remaining_quantity} shares at {trade.timestamp}"
                    )
        
        return completed_trades
    
    @staticmethod
    def calculate_symbol_metrics(
        completed_trades: List[CompletedTrade]
    ) -> SymbolPerformance:
        """
        종목별 성과 메트릭 계산
        
        Args:
            completed_trades: 완결된 거래 리스트
            
        Returns:
            종목별 성과 메트릭
        """
        if not completed_trades:
            return SymbolPerformance(
                symbol="",
                name="",
                total_return=0.0,
                trade_count=0,
                win_rate=0.0,
                profit_factor=0.0,
                avg_holding_period=0,
                total_pnl=0.0
            )
        
        symbol = completed_trades[0].symbol
        trade_count = len(completed_trades)
        
        # 총 손익
        total_pnl = sum(t.pnl for t in completed_trades)
        
        # 승률 계산
        winning_trades = [t for t in completed_trades if t.is_profitable()]
        win_rate = (len(winning_trades) / trade_count) * 100 if trade_count > 0 else 0
        
        # 손익비 계산 (총 이익 / 총 손실)
        total_profit = sum(t.pnl for t in completed_trades if t.pnl > 0)
        total_loss = abs(sum(t.pnl for t in completed_trades if t.pnl < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 평균 보유 기간
        avg_holding_period = int(sum(t.holding_period for t in completed_trades) / trade_count)
        
        # 총 수익률 계산 (누적)
        # 각 거래의 수익률을 곱하여 누적 수익률 계산
        cumulative_return = 1.0
        for trade in completed_trades:
            cumulative_return *= (1 + trade.return_pct / 100)
        total_return = (cumulative_return - 1) * 100
        
        return SymbolPerformance(
            symbol=symbol,
            name="",  # 나중에 채워짐
            total_return=total_return,
            trade_count=trade_count,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_holding_period=avg_holding_period,
            total_pnl=total_pnl
        )
    
    @staticmethod
    def analyze_all_symbols(
        trades: List[Trade]
    ) -> Dict[str, SymbolPerformance]:
        """
        모든 종목 분석
        
        Args:
            trades: 전체 거래 리스트
            
        Returns:
            {symbol: SymbolPerformance} 딕셔너리
        """
        # 종목별 그룹화
        grouped_trades = TradeAnalyzer.group_trades_by_symbol(trades)
        
        # 각 종목 분석
        symbol_performances = {}
        for symbol, symbol_trades in grouped_trades.items():
            completed_trades = TradeAnalyzer.match_entry_exit(symbol_trades)
            metrics = TradeAnalyzer.calculate_symbol_metrics(completed_trades)
            symbol_performances[symbol] = metrics
        
        return symbol_performances
