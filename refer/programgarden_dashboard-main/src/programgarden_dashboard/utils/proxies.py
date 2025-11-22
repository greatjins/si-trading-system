"""
Proxy 객체들 - 컴포넌트 지연 렌더링을 위한 임시 객체

이 Proxy 클래스들은 다음 목적으로 사용됩니다:
1. Dashboard.add_*() 메서드 호출 시 즉시 반환하여 사용자 경험 개선
2. 실제 UI 컴포넌트 생성은 Dashboard.run() → render_pending_components() 시점까지 지연
3. 컴포넌트 생성에 필요한 설정 정보를 config에 보관
"""


class BaseProxy:
    """모든 Proxy 클래스의 기본 클래스"""
    def __init__(self, config: dict):
        self.config = config


class StockCardProxy(BaseProxy):
    """StockCard 컴포넌트용 프록시"""
    pass


class WatchlistProxy(BaseProxy):
    """Watchlist 컴포넌트용 프록시"""
    pass


class PriceChartProxy(BaseProxy):
    """TradingViewChart 컴포넌트용 프록시"""
    pass


class AccountProxy(BaseProxy):
    """Account 컴포넌트용 프록시"""
    pass


class OrderPanelProxy(BaseProxy):
    """OrderPanel 컴포넌트용 프록시"""
    pass


class OrderBookProxy(BaseProxy):
    """OrderBook 컴포넌트용 프록시"""
    pass