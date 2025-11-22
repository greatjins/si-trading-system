"""Stock Card Component"""

from nicegui import ui
from nicegui.observables import ObservableDict

from datetime import datetime

from ..utils.data_formatter import DataFormatter
from ..utils.logger import get_logger


class StockCard:
    """Stock Card Component"""
    
    def __init__(self, symbol: str, market_data: ObservableDict, size_ratio: float = 1.0):
        """
        Args:
            symbol: 주식 심볼 (예: "AAPL", "GOOGL")
            market_data: LS API 데이터가 실시간으로 업데이트되는 ObservableDict
            size_ratio: 가로세로 비율 (width/height) - 레이아웃 결정
        """
        self.symbol = symbol.upper()
        self.market_data = market_data
        self.size_ratio = size_ratio
        self.logger = get_logger(f'StockCard.{self.symbol}')
        
        # LS API 데이터 구조에 맞춘 초기화
        self._initialize_ls_market_data()
        
        # UI 컴포넌트 참조
        self.card_container = None
        self.price_labels = {}
        self.change_labels = {}
        
        # 동적 UI 생성
        self._create_ui()
        
        # 실시간 업데이트 설정
        self._setup_realtime_updates()
    
    # ========================================
    # 초기 설정 메서드
    # ========================================
        
    def _initialize_ls_market_data(self):
        """LS Open API GSC 완전 데이터 구조 초기화"""
        if self.symbol not in self.market_data:
            # GSC 응답 필드에 맞춘 완전한 초기 구조
            self.market_data[self.symbol] = {
                # 기본 정보
                "symbol": self.symbol,
                "price": 0.0,           # GSC.price
                "change": 0.0,          # GSC.diff (전일대비)  
                "change_percent": 0.0,  # GSC.rate (등락율)
                "volume": 0,            # GSC.totq (누적체결수량)
                "open": 0.0,            # GSC.open (시가)
                "high": 0.0,            # GSC.high (고가)
                "low": 0.0,             # GSC.low (저가)
                # 52주 데이터
                "high52": 0.0,          # GSC.high52p (52주고가)
                "low52": 0.0,           # GSC.low52p (52주저가)
                # 거래대금 및 체결정보
                "amount": 0,            # GSC.amount (누적거래대금)
                "cgubun": "",           # GSC.cgubun (체결구분)
                "trdq": 0,              # GSC.trdq (건별체결수량)
                "timestamp": datetime.now().isoformat(),
                # 데이터 소스 정보
                "source": "연결중..."
            }
    
    def _create_ui(self):
        """동적 크기 대응 UI 생성"""
        # 크기에 따른 레이아웃 결정
        is_wide = self.size_ratio > 1.5  # 가로가 세로의 1.5배 초과
        is_tall = self.size_ratio < 0.7  # 세로가 가로의 1.4배 초과
        
        self.card_container = ui.card().classes('w-full h-full cursor-pointer hover:shadow-xl transition-all duration-300 border-l-4 border-gray-300').style(
            'display: flex; flex-direction: column; padding: 1rem; '
            'background: #fff;'
        )
        
        with self.card_container:
            if is_wide:
                self._create_wide_layout()
            elif is_tall:
                self._create_tall_layout() 
            else:
                self._create_default_layout()

    def _create_wide_layout(self):
        """가로형 레이아웃 - 좌우 분할"""
        with ui.row().classes('w-full h-full items-center gap-4'):
            # 왼쪽: 심볼과 메인 가격
            with ui.column().classes('items-start gap-1 flex-1'):
                with ui.row().classes('items-center gap-2'):
                    ui.label(self.symbol).classes('text-xl font-bold text-gray-800')
                    ui.icon('circle', size='sm').classes('text-gray-400')
                    ui.icon('trending_flat', size='sm').classes('text-gray-400').bind_name_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.cgubun_icon_name(data)
                    )
                    
                self.price_labels['wide'] = ui.label().classes('text-3xl font-bold text-gray-900').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'price')
                )
                self.change_labels['wide'] = ui.label().classes('text-lg font-medium text-gray-600').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.change(data, 'change', 'change_percent')
                )
                
                # 52주 범위 표시
                with ui.row().classes('w-full items-center gap-1'):
                    ui.label('52주:').classes('text-xs text-gray-500')
                    ui.label().classes('text-xs text-gray-600').bind_text_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.range_52week(data)
                    )

            # 오른쪽: OHLV + 확장 정보
            with ui.column().classes('items-end gap-2'):
                # OHLV 정보
                with ui.grid(columns=2).classes('gap-1 text-xs'):
                    ui.label('시가').classes('text-gray-500')
                    ui.label().classes('text-gray-700').bind_text_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'open')
                    )
                    ui.label('고가').classes('text-gray-500') 
                    ui.label().classes('text-gray-700').bind_text_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'high')
                    )
                    ui.label('저가').classes('text-gray-500')
                    ui.label().classes('text-gray-700').bind_text_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'low')
                    )
                    ui.label('거래량').classes('text-gray-500')
                    ui.label().classes('text-gray-700').bind_text_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.volume(data, 'volume')
                    )
                    
                # 거래대금 및 체결정보
                with ui.grid(columns=2).classes('gap-1 text-xs mt-1'):
                    ui.label('거래대금').classes('text-gray-500')
                    ui.label().classes('text-gray-700').bind_text_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.amount(data)
                    )
                    ui.label('건별량').classes('text-gray-500') 
                    ui.label().classes('text-gray-700').bind_text_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.trdq(data, 'trdq')
                    )
                    
                # 소스 정보
                with ui.column().classes('items-end mt-1'):
                    ui.label('Source').classes('text-xs text-gray-500 uppercase')
                    ui.label().classes('text-xs text-gray-600').bind_text_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.source(data, 'source')
                    )
                    
    def _create_tall_layout(self):
        """세로형 레이아웃 - 상하 분할"""
        with ui.column().classes('w-full h-full justify-between gap-2'):
            # 심볼과 체결구분
            with ui.row().classes('w-full justify-between items-center'):
                ui.label(self.symbol).classes('text-lg font-bold text-gray-800')
                with ui.row().classes('items-center gap-1'):
                    ui.icon('circle', size='sm').classes('text-gray-400')
                    ui.icon('trending_flat', size='sm').classes('text-gray-400').bind_name_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.cgubun_icon_name(data)
                    )

            # 가격 섹션
            with ui.column().classes('w-full items-center gap-2 flex-1 justify-center'):
                self.price_labels['tall'] = ui.label().classes('text-4xl font-bold text-gray-900').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'price')
                )
                self.change_labels['tall'] = ui.label().classes('text-xl font-medium text-gray-600').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.change(data, 'change', 'change_percent')
                )
                
                # 52주 범위 표시
                with ui.column().classes('w-full items-center gap-1 mt-2'):
                    ui.label('52주 범위').classes('text-sm text-gray-500')
                    ui.label().classes('text-sm text-gray-700 font-medium').bind_text_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.range_52week(data)
                    )
                    ui.label().classes('text-xs text-gray-500').bind_text_from(
                        self.market_data, self.symbol, backward=lambda data: f"({DataFormatter.range_52week_percent(data)})"
                    )
            
            # OHLV 정보
            with ui.grid(columns=2).classes('w-full gap-2 text-sm'):
                ui.label('시가').classes('text-gray-500')
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'open')
                )
                ui.label('고가').classes('text-gray-500')
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'high')
                )
                ui.label('저가').classes('text-gray-500')
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'low')
                )
                ui.label('거래량').classes('text-gray-500')
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.volume(data, 'volume')
                )
                
            # 거래대금 및 체결정보
            with ui.grid(columns=2).classes('w-full gap-2 text-xs'):
                ui.label('거래대금').classes('text-gray-500')
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.amount(data)
                )
                ui.label('건별량').classes('text-gray-500')
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.trdq(data, 'trdq')
                )
                
            # 소스 정보
            with ui.row().classes('w-full justify-between'):
                ui.label('Source').classes('text-xs text-gray-500 uppercase')
                ui.label().classes('text-xs text-gray-600').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.source(data, 'source')
                )
                
    def _create_default_layout(self):
        """기본 레이아웃 - 정사각형/기본"""            
        with ui.column().classes('w-full h-full justify-between'):
            # 헤더 + 체결구분
            with ui.row().classes('w-full justify-between items-center mb-2'):
                ui.label(self.symbol).classes('text-lg font-bold text-gray-800')
                with ui.row().classes('items-center gap-1'):
                    # 상태 아이콘 (동적 색상 업데이트 대상)
                    if 'status_icon' not in self.price_labels:
                        self.price_labels['status_icon'] = ui.icon('circle', size='sm').classes('text-gray-400')
                    # 체결구분 아이콘
                    ui.icon('trending_flat', size='sm').classes('text-gray-400').bind_name_from(
                        self.market_data, self.symbol, backward=lambda data: DataFormatter.cgubun_icon_name(data)
                    )

            # 가격 섹션
            with ui.column().classes('w-full items-center gap-1 flex-1 justify-center'):
                self.price_labels['default'] = ui.label().classes('text-2xl font-bold text-gray-900').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'price')
                )
                self.change_labels['default'] = ui.label().classes('text-base font-medium text-gray-600').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.change(data, 'change', 'change_percent')
                )                
            
            # OHLV 정보
            with ui.grid(columns=4).classes('w-full gap-1 text-xs mb-2'):
                ui.label('시가').classes('text-gray-500')
                ui.label('고가').classes('text-gray-500')
                ui.label('저가').classes('text-gray-500') 
                ui.label('거래량').classes('text-gray-500')
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'open')
                )
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'high')
                )
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.price(data, 'low')
                )
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.volume(data, 'volume')
                )
                
            # 거래대금 및 52주 정보
            with ui.grid(columns=2).classes('w-full gap-1 text-xs mb-2'):
                ui.label('거래대금').classes('text-gray-500')
                ui.label().classes('text-gray-700').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.amount(data)
                )
                ui.label('52주 신저가-신고가').classes('text-gray-500')
                ui.label().classes('text-xs text-gray-600').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.range_52week(data)
                )
                ui.label('52주 변동률').classes('text-gray-500')
                ui.label().classes('text-xs text-gray-600').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.range_52week_percent(data)
                )
            
            # 소스 정보
            with ui.row().classes('w-full justify-between items-center pt-2 border-t border-gray-200'):
                ui.label('Source').classes('text-xs text-gray-500 uppercase')
                ui.label().classes('text-xs text-gray-600').bind_text_from(
                    self.market_data, self.symbol, backward=lambda data: DataFormatter.source(data, 'source')
                )
    
    def _setup_realtime_updates(self):
        """실시간 색상 업데이트 설정"""
        # 100ms마다 색상 업데이트 (부드러운 사용자 경험)
        ui.timer(0.1, self._update_dynamic_colors)
    
    def _update_dynamic_colors(self):
        """데이터 변경에 따른 동적 색상 업데이트"""
        try:
            data = self.market_data.get(self.symbol, {})
            change = data.get('change', 0)
            
            # 색상 결정
            is_positive = change >= 0
            text_color = 'text-green-600' if is_positive else 'text-red-600'
            border_color = 'border-green-300' if is_positive else 'border-red-300'
            
            # 카드 테두리 색상 업데이트
            if self.card_container:
                if is_positive:
                    self.card_container.classes(
                        remove='border-red-300 border-gray-300', add=border_color
                    )
                else:
                    self.card_container.classes(
                        remove='border-green-300 border-gray-300', add=border_color
                    )
            
            # 가격/변동 레이블 색상 업데이트
            for layout_type in ['wide', 'tall', 'default']:
                if layout_type in self.price_labels:
                    if is_positive:
                        self.price_labels[layout_type].classes(
                            remove='text-red-600 text-gray-900', add=text_color
                        )
                        self.change_labels[layout_type].classes(
                            remove='text-red-600 text-gray-600', add=text_color
                        )
                    else:
                        self.price_labels[layout_type].classes(
                            remove='text-green-600 text-gray-900', add=text_color
                        )
                        self.change_labels[layout_type].classes(
                            remove='text-green-600 text-gray-600', add=text_color
                        )
            
            # 상태 아이콘 색상 업데이트 (default layout 전용)
            if 'status_icon' in self.price_labels:
                status_icon_color = 'text-green-500' if is_positive else 'text-red-500'
                if is_positive:
                    self.price_labels['status_icon'].classes(
                        remove='text-red-500 text-gray-400', add=status_icon_color
                    )
                else:
                    self.price_labels['status_icon'].classes(
                        remove='text-green-500 text-gray-400', add=status_icon_color
                    )
                        
        except Exception as e:
            self.logger.error(f"❌ 동적 색상 업데이트 실패: {e}")
                
    def cleanup(self):
        """컴포넌트 정리"""
        if self.symbol in self.market_data:
            del self.market_data[self.symbol]
        self.logger.info(f"🗑️ {self.symbol} StockCard 컴포넌트 정리 완료")