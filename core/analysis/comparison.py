"""
백테스트-실전 비교 분석 엔진
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from data.models import (
    BacktestResultModel, LiveTradeModel, StrategyPerformanceModel,
    BacktestLiveComparisonModel
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ComparisonEngine:
    """
    백테스트-실전 비교 분석 엔진
    
    백테스트 결과와 실전 거래 결과를 비교하여 차이를 분석하고,
    차이 원인(슬리피지, 수수료, 체결 지연, 유동성 등)의 기여도를 계산합니다.
    """
    
    def __init__(self, db_session: Session):
        """
        Args:
            db_session: 데이터베이스 세션
        """
        self.db = db_session
        logger.info("ComparisonEngine initialized")
    
    def compare(
        self,
        backtest_id: int,
        strategy_id: int,
        user_id: int,
        live_start: datetime,
        live_end: datetime
    ) -> BacktestLiveComparisonModel:
        """
        백테스트-실전 비교 실행
        
        Args:
            backtest_id: 백테스트 결과 ID
            strategy_id: 전략 ID
            user_id: 사용자 ID
            live_start: 실전 거래 시작일
            live_end: 실전 거래 종료일
        
        Returns:
            비교 결과 모델
        """
        try:
            # 1. 백테스트 결과 조회
            backtest_result = self.db.query(BacktestResultModel).filter(
                BacktestResultModel.id == backtest_id
            ).first()
            
            if not backtest_result:
                raise ValueError(f"Backtest result not found: {backtest_id}")
            
            # 2. 실전 거래 결과 조회
            live_trades = self.db.query(LiveTradeModel).filter(
                LiveTradeModel.strategy_id == strategy_id,
                LiveTradeModel.user_id == user_id,
                LiveTradeModel.timestamp >= live_start,
                LiveTradeModel.timestamp <= live_end
            ).all()
            
            # 3. 실전 성과 계산
            live_metrics = self._calculate_live_metrics(live_trades, backtest_result.initial_capital)
            
            # 4. 차이 계산
            return_difference = live_metrics['total_return'] - backtest_result.total_return
            trade_difference = live_metrics['total_trades'] - backtest_result.total_trades
            
            # 5. 차이 원인 분석
            cause_analysis = self._analyze_cause_differences(
                backtest_result,
                live_metrics,
                live_trades
            )
            
            # 6. 비교 결과 저장
            comparison = BacktestLiveComparisonModel(
                backtest_id=backtest_id,
                strategy_id=strategy_id,
                user_id=user_id,
                backtest_start=backtest_result.start_date,
                backtest_end=backtest_result.end_date,
                live_start=live_start,
                live_end=live_end,
                backtest_return=backtest_result.total_return,
                backtest_trades=backtest_result.total_trades,
                backtest_win_rate=backtest_result.win_rate,
                live_return=live_metrics['total_return'],
                live_trades=live_metrics['total_trades'],
                live_win_rate=live_metrics['win_rate'],
                return_difference=return_difference,
                trade_difference=trade_difference,
                slippage_contribution=cause_analysis.get('slippage_contribution'),
                commission_contribution=cause_analysis.get('commission_contribution'),
                delay_contribution=cause_analysis.get('delay_contribution'),
                liquidity_contribution=cause_analysis.get('liquidity_contribution'),
                market_change_contribution=cause_analysis.get('market_change_contribution')
            )
            
            self.db.add(comparison)
            self.db.commit()
            self.db.refresh(comparison)
            
            logger.info(
                f"Comparison completed: backtest_id={backtest_id}, "
                f"return_diff={return_difference:.2%}"
            )
            
            return comparison
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Comparison failed: {e}", exc_info=True)
            raise
    
    def _calculate_live_metrics(
        self,
        live_trades: List[LiveTradeModel],
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        실전 거래 메트릭 계산
        
        Args:
            live_trades: 실전 거래 내역
            initial_capital: 초기 자본
        
        Returns:
            실전 메트릭 (total_return, total_trades, win_rate 등)
        """
        if not live_trades:
            return {
                'total_return': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0
            }
        
        # 매수/매도 쌍 매칭
        buy_trades = {}
        completed_trades = []
        
        for trade in sorted(live_trades, key=lambda t: t.timestamp):
            if trade.side == 'buy':
                if trade.symbol not in buy_trades:
                    buy_trades[trade.symbol] = []
                buy_trades[trade.symbol].append(trade)
            elif trade.side == 'sell':
                if trade.symbol in buy_trades and buy_trades[trade.symbol]:
                    buy_trade = buy_trades[trade.symbol].pop(0)
                    # 손익 계산
                    pnl = (trade.price - buy_trade.price) * trade.quantity
                    pnl -= (buy_trade.commission + trade.commission)
                    completed_trades.append({
                        'pnl': pnl,
                        'is_win': pnl > 0
                    })
        
        # 메트릭 계산
        total_pnl = sum(t['pnl'] for t in completed_trades)
        total_return = total_pnl / initial_capital if initial_capital > 0 else 0.0
        total_trades = len(completed_trades)
        win_count = sum(1 for t in completed_trades if t['is_win'])
        win_rate = win_count / total_trades if total_trades > 0 else 0.0
        
        return {
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl
        }
    
    def _analyze_cause_differences(
        self,
        backtest_result: BacktestResultModel,
        live_metrics: Dict[str, Any],
        live_trades: List[LiveTradeModel]
    ) -> Dict[str, Optional[float]]:
        """
        차이 원인 분석
        
        Args:
            backtest_result: 백테스트 결과
            live_metrics: 실전 메트릭
            live_trades: 실전 거래 내역
        
        Returns:
            각 원인별 기여도 (%)
        """
        return_diff = live_metrics['total_return'] - backtest_result.total_return
        
        if abs(return_diff) < 0.0001:  # 차이가 거의 없음
            return {
                'slippage_contribution': 0.0,
                'commission_contribution': 0.0,
                'delay_contribution': 0.0,
                'liquidity_contribution': 0.0,
                'market_change_contribution': 0.0
            }
        
        # 1. 슬리피지 기여도 계산
        slippage_contribution = self._estimate_slippage_impact(live_trades)
        
        # 2. 수수료 기여도 계산
        commission_contribution = self._estimate_commission_impact(
            backtest_result,
            live_trades
        )
        
        # 3. 체결 지연 기여도 계산
        delay_contribution = self._estimate_delay_impact(live_trades)
        
        # 4. 유동성 문제 기여도 계산
        liquidity_contribution = self._estimate_liquidity_impact(live_trades)
        
        # 5. 시장 상황 변화 기여도 (나머지)
        total_estimated = (
            slippage_contribution +
            commission_contribution +
            delay_contribution +
            liquidity_contribution
        )
        market_change_contribution = max(0.0, abs(return_diff) - total_estimated)
        
        # 기여도를 비율로 변환
        total_contribution = (
            slippage_contribution +
            commission_contribution +
            delay_contribution +
            liquidity_contribution +
            market_change_contribution
        )
        
        if total_contribution > 0:
            scale = abs(return_diff) / total_contribution
            slippage_contribution *= scale
            commission_contribution *= scale
            delay_contribution *= scale
            liquidity_contribution *= scale
            market_change_contribution *= scale
        
        return {
            'slippage_contribution': slippage_contribution / abs(return_diff) * 100 if return_diff != 0 else 0.0,
            'commission_contribution': commission_contribution / abs(return_diff) * 100 if return_diff != 0 else 0.0,
            'delay_contribution': delay_contribution / abs(return_diff) * 100 if return_diff != 0 else 0.0,
            'liquidity_contribution': liquidity_contribution / abs(return_diff) * 100 if return_diff != 0 else 0.0,
            'market_change_contribution': market_change_contribution / abs(return_diff) * 100 if return_diff != 0 else 0.0
        }
    
    def _estimate_slippage_impact(self, live_trades: List[LiveTradeModel]) -> float:
        """슬리피지로 인한 차이 추정"""
        if not live_trades:
            return 0.0
        
        total_slippage_cost = 0.0
        for trade in live_trades:
            if trade.slippage:
                slippage_cost = trade.price * trade.quantity * trade.slippage
                total_slippage_cost += slippage_cost
        
        # 백테스트에서는 기본 슬리피지(0.1%) 사용 가정
        backtest_slippage_rate = 0.001
        backtest_slippage_cost = sum(
            trade.price * trade.quantity * backtest_slippage_rate
            for trade in live_trades
        )
        
        return total_slippage_cost - backtest_slippage_cost
    
    def _estimate_commission_impact(
        self,
        backtest_result: BacktestResultModel,
        live_trades: List[LiveTradeModel]
    ) -> float:
        """수수료로 인한 차이 추정"""
        if not live_trades:
            return 0.0
        
        # 실전 수수료
        live_commission = sum(trade.commission for trade in live_trades)
        
        # 백테스트 수수료 (백테스트 결과에서 추정)
        # 백테스트에서는 일반적으로 0.15% 사용
        backtest_commission_rate = 0.0015
        backtest_commission = sum(
            trade.price * trade.quantity * backtest_commission_rate
            for trade in live_trades
        )
        
        return live_commission - backtest_commission
    
    def _estimate_delay_impact(self, live_trades: List[LiveTradeModel]) -> float:
        """체결 지연으로 인한 차이 추정"""
        # 간단한 추정: 체결 지연으로 인한 가격 변동 추정
        # 실제로는 더 정교한 계산 필요
        return 0.0  # TODO: 더 정교한 계산 필요
    
    def _estimate_liquidity_impact(self, live_trades: List[LiveTradeModel]) -> float:
        """유동성 문제로 인한 차이 추정"""
        # 유동성 부족으로 인한 주문 실패나 부분 체결 추정
        # 실제로는 주문 실패 기록이 필요
        return 0.0  # TODO: 더 정교한 계산 필요

