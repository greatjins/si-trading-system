"""
고급 리스크 관리 시스템
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
import pandas as pd
from enum import Enum

from utils.types import Position, Account, OHLC
from utils.logger import setup_logger
from utils.exceptions import RiskLimitError

logger = setup_logger(__name__)


class RiskLevel(Enum):
    """리스크 레벨"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """리스크 메트릭"""
    portfolio_var: float  # Value at Risk (95%)
    portfolio_cvar: float  # Conditional VaR (Expected Shortfall)
    max_drawdown: float  # 최대 낙폭
    volatility: float  # 변동성 (연율화)
    sharpe_ratio: float  # 샤프 비율
    sortino_ratio: float  # 소르티노 비율
    beta: float  # 베타 (시장 대비)
    correlation_risk: float  # 상관관계 리스크
    concentration_risk: float  # 집중도 리스크
    sector_exposure: Dict[str, float]  # 섹터별 노출도
    risk_level: RiskLevel  # 전체 리스크 레벨
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "portfolio_var": self.portfolio_var,
            "portfolio_cvar": self.portfolio_cvar,
            "max_drawdown": self.max_drawdown,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "beta": self.beta,
            "correlation_risk": self.correlation_risk,
            "concentration_risk": self.concentration_risk,
            "sector_exposure": self.sector_exposure,
            "risk_level": self.risk_level.value
        }


@dataclass
class RiskLimits:
    """리스크 한도"""
    max_portfolio_var: float = 0.05  # 최대 VaR 5%
    max_single_position: float = 0.10  # 단일 종목 최대 10%
    max_sector_exposure: float = 0.30  # 섹터별 최대 30%
    max_correlation: float = 0.80  # 최대 상관관계 80%
    max_drawdown: float = 0.20  # 최대 낙폭 20%
    min_diversification: int = 5  # 최소 분산 종목 수
    max_leverage: float = 1.0  # 최대 레버리지 1배


class AdvancedRiskManager:
    """
    고급 리스크 관리자
    
    포트폴리오 레벨의 리스크 분석 및 관리
    """
    
    def __init__(
        self,
        risk_limits: Optional[RiskLimits] = None,
        lookback_days: int = 252,  # 1년
        confidence_level: float = 0.95
    ):
        """
        Args:
            risk_limits: 리스크 한도
            lookback_days: 리스크 계산 기간 (일)
            confidence_level: 신뢰구간 (VaR 계산용)
        """
        self.risk_limits = risk_limits or RiskLimits()
        self.lookback_days = lookback_days
        self.confidence_level = confidence_level
        
        # 가격 히스토리 저장
        self.price_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self.market_index_history: List[Tuple[datetime, float]] = []
        
        logger.info(f"AdvancedRiskManager initialized: lookback={lookback_days}days, confidence={confidence_level}")
    
    def update_price_history(
        self,
        symbol: str,
        timestamp: datetime,
        price: float
    ) -> None:
        """가격 히스토리 업데이트"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append((timestamp, price))
        
        # 오래된 데이터 제거
        cutoff_date = timestamp - timedelta(days=self.lookback_days + 30)
        self.price_history[symbol] = [
            (ts, p) for ts, p in self.price_history[symbol] 
            if ts >= cutoff_date
        ]
    
    def update_market_index(
        self,
        timestamp: datetime,
        index_value: float
    ) -> None:
        """시장 지수 히스토리 업데이트"""
        self.market_index_history.append((timestamp, index_value))
        
        # 오래된 데이터 제거
        cutoff_date = timestamp - timedelta(days=self.lookback_days + 30)
        self.market_index_history = [
            (ts, val) for ts, val in self.market_index_history 
            if ts >= cutoff_date
        ]
    
    def calculate_portfolio_risk(
        self,
        positions: List[Position],
        account: Account,
        sector_mapping: Optional[Dict[str, str]] = None
    ) -> RiskMetrics:
        """
        포트폴리오 리스크 계산
        
        Args:
            positions: 포지션 리스트
            account: 계좌 정보
            sector_mapping: 종목별 섹터 매핑
            
        Returns:
            리스크 메트릭
        """
        if not positions:
            return self._empty_risk_metrics()
        
        # 포트폴리오 가치 및 비중 계산
        total_value = sum(pos.total_value() for pos in positions)
        weights = {pos.symbol: pos.total_value() / total_value for pos in positions}
        
        # 수익률 데이터 준비
        returns_data = self._prepare_returns_data(positions)
        
        if returns_data.empty:
            return self._empty_risk_metrics()
        
        # 리스크 메트릭 계산
        portfolio_var = self._calculate_var(returns_data, weights)
        portfolio_cvar = self._calculate_cvar(returns_data, weights)
        max_drawdown = self._calculate_max_drawdown(returns_data, weights)
        volatility = self._calculate_volatility(returns_data, weights)
        sharpe_ratio = self._calculate_sharpe_ratio(returns_data, weights)
        sortino_ratio = self._calculate_sortino_ratio(returns_data, weights)
        beta = self._calculate_beta(returns_data, weights)
        correlation_risk = self._calculate_correlation_risk(returns_data)
        concentration_risk = self._calculate_concentration_risk(weights)
        sector_exposure = self._calculate_sector_exposure(positions, sector_mapping)
        
        # 전체 리스크 레벨 결정
        risk_level = self._determine_risk_level(
            portfolio_var, max_drawdown, concentration_risk, correlation_risk
        )
        
        return RiskMetrics(
            portfolio_var=portfolio_var,
            portfolio_cvar=portfolio_cvar,
            max_drawdown=max_drawdown,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            beta=beta,
            correlation_risk=correlation_risk,
            concentration_risk=concentration_risk,
            sector_exposure=sector_exposure,
            risk_level=risk_level
        )
    
    def check_position_limits(
        self,
        new_position: Position,
        existing_positions: List[Position],
        account: Account
    ) -> Tuple[bool, str]:
        """
        포지션 한도 체크
        
        Args:
            new_position: 새로운 포지션
            existing_positions: 기존 포지션들
            account: 계좌 정보
            
        Returns:
            (허용 여부, 메시지)
        """
        total_equity = account.equity
        
        # 단일 종목 한도 체크
        position_ratio = new_position.total_value() / total_equity
        if position_ratio > self.risk_limits.max_single_position:
            return False, f"Single position limit exceeded: {position_ratio:.2%} > {self.risk_limits.max_single_position:.2%}"
        
        # 총 포지션 수 체크
        if len(existing_positions) >= 20:  # 최대 20개 종목
            return False, f"Maximum number of positions exceeded: {len(existing_positions)}"
        
        # 레버리지 체크
        total_position_value = sum(pos.total_value() for pos in existing_positions) + new_position.total_value()
        leverage = total_position_value / total_equity
        if leverage > self.risk_limits.max_leverage:
            return False, f"Leverage limit exceeded: {leverage:.2f}x > {self.risk_limits.max_leverage:.2f}x"
        
        return True, "Position approved"
    
    def suggest_position_size(
        self,
        symbol: str,
        target_weight: float,
        existing_positions: List[Position],
        account: Account,
        risk_budget: float = 0.02  # 2% 리스크 예산
    ) -> int:
        """
        리스크 기반 포지션 사이즈 제안
        
        Args:
            symbol: 종목 코드
            target_weight: 목표 비중
            existing_positions: 기존 포지션들
            account: 계좌 정보
            risk_budget: 리스크 예산 (포트폴리오 대비)
            
        Returns:
            제안 수량
        """
        # 종목별 변동성 계산
        volatility = self._get_symbol_volatility(symbol)
        
        if volatility == 0:
            # 변동성 데이터가 없으면 보수적으로 계산
            volatility = 0.30  # 30% 가정
        
        # 리스크 예산 기반 포지션 크기 계산
        # Position Size = Risk Budget / (Volatility * Price)
        current_price = self._get_current_price(symbol)
        if current_price == 0:
            return 0
        
        # 리스크 조정 포지션 크기
        risk_adjusted_value = (account.equity * risk_budget) / volatility
        
        # 목표 비중과 리스크 조정 중 작은 값 선택
        target_value = account.equity * target_weight
        final_value = min(risk_adjusted_value, target_value)
        
        # 한도 체크
        max_value = account.equity * self.risk_limits.max_single_position
        final_value = min(final_value, max_value)
        
        quantity = int(final_value / current_price)
        return max(0, quantity)
    
    def _prepare_returns_data(self, positions: List[Position]) -> pd.DataFrame:
        """수익률 데이터 준비"""
        returns_dict = {}
        
        for position in positions:
            symbol = position.symbol
            if symbol not in self.price_history:
                continue
            
            # 가격 데이터를 DataFrame으로 변환
            price_data = pd.DataFrame(
                self.price_history[symbol],
                columns=['timestamp', 'price']
            ).set_index('timestamp').sort_index()
            
            # 일일 수익률 계산
            returns = price_data['price'].pct_change().dropna()
            returns_dict[symbol] = returns
        
        if not returns_dict:
            return pd.DataFrame()
        
        # 공통 날짜로 정렬
        returns_df = pd.DataFrame(returns_dict).dropna()
        return returns_df
    
    def _calculate_var(self, returns_data: pd.DataFrame, weights: Dict[str, float]) -> float:
        """Value at Risk 계산"""
        if returns_data.empty:
            return 0.0
        
        # 포트폴리오 수익률 계산
        portfolio_returns = (returns_data * pd.Series(weights)).sum(axis=1)
        
        # VaR 계산 (Historical Simulation)
        var = np.percentile(portfolio_returns, (1 - self.confidence_level) * 100)
        return abs(var)
    
    def _calculate_cvar(self, returns_data: pd.DataFrame, weights: Dict[str, float]) -> float:
        """Conditional VaR (Expected Shortfall) 계산"""
        if returns_data.empty:
            return 0.0
        
        portfolio_returns = (returns_data * pd.Series(weights)).sum(axis=1)
        var = np.percentile(portfolio_returns, (1 - self.confidence_level) * 100)
        
        # CVaR = VaR보다 나쁜 수익률들의 평균
        tail_returns = portfolio_returns[portfolio_returns <= var]
        cvar = tail_returns.mean() if len(tail_returns) > 0 else var
        return abs(cvar)
    
    def _calculate_max_drawdown(self, returns_data: pd.DataFrame, weights: Dict[str, float]) -> float:
        """최대 낙폭 계산"""
        if returns_data.empty:
            return 0.0
        
        portfolio_returns = (returns_data * pd.Series(weights)).sum(axis=1)
        cumulative = (1 + portfolio_returns).cumprod()
        
        # Running maximum
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        return abs(drawdown.min())
    
    def _calculate_volatility(self, returns_data: pd.DataFrame, weights: Dict[str, float]) -> float:
        """변동성 계산 (연율화)"""
        if returns_data.empty:
            return 0.0
        
        portfolio_returns = (returns_data * pd.Series(weights)).sum(axis=1)
        return portfolio_returns.std() * np.sqrt(252)  # 연율화
    
    def _calculate_sharpe_ratio(self, returns_data: pd.DataFrame, weights: Dict[str, float]) -> float:
        """샤프 비율 계산"""
        if returns_data.empty:
            return 0.0
        
        portfolio_returns = (returns_data * pd.Series(weights)).sum(axis=1)
        excess_returns = portfolio_returns - 0.02/252  # 무위험 수익률 2% 가정
        
        if excess_returns.std() == 0:
            return 0.0
        
        return (excess_returns.mean() * 252) / (excess_returns.std() * np.sqrt(252))
    
    def _calculate_sortino_ratio(self, returns_data: pd.DataFrame, weights: Dict[str, float]) -> float:
        """소르티노 비율 계산"""
        if returns_data.empty:
            return 0.0
        
        portfolio_returns = (returns_data * pd.Series(weights)).sum(axis=1)
        excess_returns = portfolio_returns - 0.02/252
        
        # 하방 편차 계산
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_deviation = downside_returns.std() * np.sqrt(252)
        
        if downside_deviation == 0:
            return 0.0
        
        return (excess_returns.mean() * 252) / downside_deviation
    
    def _calculate_beta(self, returns_data: pd.DataFrame, weights: Dict[str, float]) -> float:
        """베타 계산"""
        if returns_data.empty or not self.market_index_history:
            return 1.0
        
        # 시장 수익률 데이터 준비
        market_df = pd.DataFrame(
            self.market_index_history,
            columns=['timestamp', 'index']
        ).set_index('timestamp').sort_index()
        
        market_returns = market_df['index'].pct_change().dropna()
        portfolio_returns = (returns_data * pd.Series(weights)).sum(axis=1)
        
        # 공통 기간 데이터
        common_dates = portfolio_returns.index.intersection(market_returns.index)
        if len(common_dates) < 30:  # 최소 30일 데이터 필요
            return 1.0
        
        port_ret = portfolio_returns.loc[common_dates]
        market_ret = market_returns.loc[common_dates]
        
        # 베타 계산
        covariance = np.cov(port_ret, market_ret)[0, 1]
        market_variance = np.var(market_ret)
        
        if market_variance == 0:
            return 1.0
        
        return covariance / market_variance
    
    def _calculate_correlation_risk(self, returns_data: pd.DataFrame) -> float:
        """상관관계 리스크 계산"""
        if returns_data.empty or len(returns_data.columns) < 2:
            return 0.0
        
        # 상관관계 매트릭스
        correlation_matrix = returns_data.corr()
        
        # 대각선 제외한 상관관계들의 평균
        mask = np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)
        correlations = correlation_matrix.where(mask).stack().dropna()
        
        return correlations.mean() if len(correlations) > 0 else 0.0
    
    def _calculate_concentration_risk(self, weights: Dict[str, float]) -> float:
        """집중도 리스크 계산 (Herfindahl Index)"""
        if not weights:
            return 0.0
        
        # Herfindahl-Hirschman Index
        hhi = sum(w**2 for w in weights.values())
        
        # 정규화 (0~1 범위)
        n = len(weights)
        normalized_hhi = (hhi - 1/n) / (1 - 1/n) if n > 1 else 0
        
        return normalized_hhi
    
    def _calculate_sector_exposure(
        self,
        positions: List[Position],
        sector_mapping: Optional[Dict[str, str]]
    ) -> Dict[str, float]:
        """섹터별 노출도 계산"""
        if not sector_mapping:
            return {}
        
        total_value = sum(pos.total_value() for pos in positions)
        if total_value == 0:
            return {}
        
        sector_values = {}
        for position in positions:
            sector = sector_mapping.get(position.symbol, "Unknown")
            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += position.total_value()
        
        # 비중으로 변환
        return {sector: value / total_value for sector, value in sector_values.items()}
    
    def _determine_risk_level(
        self,
        var: float,
        max_drawdown: float,
        concentration_risk: float,
        correlation_risk: float
    ) -> RiskLevel:
        """전체 리스크 레벨 결정"""
        risk_score = 0
        
        # VaR 점수
        if var > 0.10:
            risk_score += 3
        elif var > 0.05:
            risk_score += 2
        elif var > 0.03:
            risk_score += 1
        
        # MDD 점수
        if max_drawdown > 0.20:
            risk_score += 3
        elif max_drawdown > 0.15:
            risk_score += 2
        elif max_drawdown > 0.10:
            risk_score += 1
        
        # 집중도 점수
        if concentration_risk > 0.80:
            risk_score += 3
        elif concentration_risk > 0.60:
            risk_score += 2
        elif concentration_risk > 0.40:
            risk_score += 1
        
        # 상관관계 점수
        if correlation_risk > 0.80:
            risk_score += 2
        elif correlation_risk > 0.60:
            risk_score += 1
        
        # 레벨 결정
        if risk_score >= 8:
            return RiskLevel.CRITICAL
        elif risk_score >= 5:
            return RiskLevel.HIGH
        elif risk_score >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _empty_risk_metrics(self) -> RiskMetrics:
        """빈 리스크 메트릭 반환"""
        return RiskMetrics(
            portfolio_var=0.0,
            portfolio_cvar=0.0,
            max_drawdown=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            beta=1.0,
            correlation_risk=0.0,
            concentration_risk=0.0,
            sector_exposure={},
            risk_level=RiskLevel.LOW
        )
    
    def _get_symbol_volatility(self, symbol: str) -> float:
        """종목별 변동성 조회"""
        if symbol not in self.price_history:
            return 0.30  # 기본값 30%
        
        prices = [price for _, price in self.price_history[symbol]]
        if len(prices) < 30:
            return 0.30
        
        returns = [prices[i]/prices[i-1] - 1 for i in range(1, len(prices))]
        return np.std(returns) * np.sqrt(252)  # 연율화
    
    def _get_current_price(self, symbol: str) -> float:
        """현재가 조회"""
        if symbol not in self.price_history or not self.price_history[symbol]:
            return 0.0
        
        return self.price_history[symbol][-1][1]