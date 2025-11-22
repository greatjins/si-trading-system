"""TradingView Chart Component"""

from nicegui import ui, html

from ..utils.logger import get_logger


class TradingViewChart:
    """TradingView Chart Component"""
    
    def __init__(self, symbol: str):
        """
        Args:
            symbol: 주식 심볼 (예: "AAPL", "GOOGL")
        """
        self.symbol = symbol.upper()
        self.logger = get_logger(f"TradingViewChart.{self.symbol}")
        
        # 동적 UI 생성
        self._create_ui()
    
    def _create_ui(self):
        """동적 크기 대응 UI 생성"""
        
        with ui.card().classes('w-full h-full cursor-pointer hover:shadow-xl transition-all duration-300 border-l-4 border-gray-300').style(
            'display: flex; flex-direction: column; padding: 1rem; '
            'background: #fff;'
        ):
            with ui.column().classes('flex-1 w-full'):
                self._create_tradingview_container()        

    def _create_tradingview_container(self):
        """NiceGUI 네이티브 TradingView 차트 컨테이너"""
        try:
            tradingview_symbol = f'NASDAQ:{self.symbol}'
            width = 1080
            height = 960

            # TradingView iframe URL 생성
            iframe_url = f"https://www.tradingview.com/embed-widget/advanced-chart/?symbol={tradingview_symbol}&theme=light&style=1&locale=en&width={width}&height={height}&range=1D&hide_side_toolbar=false&allow_symbol_change=true&save_image=false&calendar=false&hide_volume=false&support_host=https://www.tradingview.com"
            
            # NiceGUI html.iframe 사용
            html.iframe().props(f'src="{iframe_url}" width="{width}" height="{height}" frameborder="0"').classes('w-full h-full')
            
        except Exception as e:
            self.logger.error(f"TradingView 차트 생성 실패: {e}")