"""
ProgramGarden Dashboard
NiceGUI 기반 해외 주식 대시보드
"""

from typing import Optional, Tuple, Dict, List, Set, Union
from collections import defaultdict
from dataclasses import dataclass
from nicegui import app, ui
from nicegui.observables import ObservableDict

from .utils.proxies import StockCardProxy, WatchlistProxy, PriceChartProxy, AccountProxy, OrderPanelProxy, OrderBookProxy
from .data.provider import DataProvider
from .ui.grid_layout import AdaptiveGridManager, GridConfig
from .components.stock_card import StockCard
from .components.watchlist import Watchlist
from .components.trading_view_chart import TradingViewChart
from .components.account import Account
from .components.order_panel import OrderPanel
from .components.order_book import OrderBook
from .pages.user_guide import user_guide_page
from .pages.error import error_page
from .utils.logger import get_logger


@dataclass
class ComponentDefaults:
    """컴포넌트 기본 설정"""
    STOCK_CARD = (2, 2)
    WATCHLIST = (4, 3) 
    TRADING_VIEW_CHART = (6, 4)
    ACCOUNT = (4, 3)
    ORDER_PANEL = (2, 3)
    ORDER_BOOK = (2, 4)


class ProgramGardenDashboard:
    """NiceGUI 기반 해외 주식 대시보드"""
    
    def __init__(
        self, 
        title: str = "ProgramGarden Dashboard",
        app_key: Optional[str] = None, 
        app_secret: Optional[str] = None,
        user_guide: bool = True
    ):
        """대시보드 초기화"""

        self.title: str = title             # 대시보드 제목
        self.app_key: str = app_key         # LS Open API APP KEY
        self.app_secret: str = app_secret   # LS Open API APP SECRET KEY
        self.user_guide: bool = user_guide  # 사용자 가이드 페이지 이동 버튼 표시 여부
        
        # 시스템 초기화
        self.market_data: ObservableDict = ObservableDict()                   # 실시간 데이터 저장소
        self.order_book_data: ObservableDict = ObservableDict()               # 실시간 호가 데이터 저장소
        self.order_data: ObservableDict = ObservableDict()                    # 실시간 주문/체결/접수 데이터 저장소
        self.data_provider: DataProvider = DataProvider(app_key, app_secret)  # 데이터 Provider
        self.components: Dict[str, str] = {}                                  # 컴포넌트 저장소
        self.components_position: Dict[str, Tuple[int, int, int, int]] = {}   # 컴포넌트 위치 저장소
        self.component_counters: defaultdict = defaultdict(int)               # 컴포넌트 타입별 카운터
        self.pending_subscribes: Set[str] = set()                             # 구독 대기 심볼
        self.pending_components: List[str] = []                               # 지연 렌더링을 위한 큐
        self.connection_status: ui.chip = None                                # 연결 상태 표시용 UI 요소 (LS Open API, Yahoo 등)
        self.grid_manager: AdaptiveGridManager = AdaptiveGridManager(GridConfig())  # 적응형 그리드 레이아웃 매니저

        # 로깅
        self.logger = get_logger('ProgramGardenDashboard')

        print("🚀 ProgramGarden Dashboard 초기화 완료")
    
    # ========================================
    # 초기 설정 메서드
    # ========================================
    
    def _setup_data_handlers(self) -> None:
        """데이터 핸들러 설정 - Provider 통합 인터페이스 사용"""
        def on_price_update(symbol: str, data: dict):
            """실시간 가격 업데이트"""
            self.market_data.update({symbol: data})
        
        def on_order_book_update(symbol: str, data: dict):
            """실시간 호가 업데이트"""
            self.order_book_data.update({symbol: data})
        
        def on_order_update(symbol: str, data: dict):
            """실시간 주문/체결/접수 업데이트"""
            self.order_data.update({symbol: data})
            
        def on_connection_status(source: str, connected: bool):
            """연결 상태 업데이트"""
            if self.connection_status is not None:
                if connected:
                    self.connection_status.set_text(f"Connected {source}")
                    self.connection_status.classes('text-white')
                else:
                    self.connection_status.set_text("Disconnected")
                    self.connection_status.classes('text-white bg-red')
                
        # Provider에 콜백 등록
        self.data_provider.setup_dashboard_integration(
            on_price_update=on_price_update,
            on_order_book_update=on_order_book_update,
            on_order_update=on_order_update,
            on_connection_status=on_connection_status
        )

    def create_ui(self) -> None:
        """대시보드 UI 생성"""
        ui.page_title(self.title)
        
        # 적응형 그리드 CSS 및 JavaScript 적용
        ui.add_head_html(f'<style>{self.grid_manager.get_css_styles()}</style>')
        ui.add_head_html(f'<script>{self.grid_manager.get_javascript_utilities()}</script>')

        # 적응형 그리드 컬럼 표시기 JavaScript 추가
        ui.add_head_html(f"""
        <script>
        function updateAdaptiveColumns() {{
            const width = window.innerWidth;
            if (window.adaptiveGrid) {{
                const columns = window.adaptiveGrid.calculateColumns(width);
                const indicator = document.getElementById('adaptive-columns-indicator');
                if (indicator) {{
                    const statusColor = columns === 0 ? 'bg-red-100 border-red-300 text-red-700' : 'bg-blue-100 border-blue-300 text-blue-700';
                    const statusIcon = columns === 0 ? '❌' : '🔲';
                    const statusText = columns === 0 ? '숨김' : `${{columns}}컬럼`;
                    
                    indicator.innerHTML = `
                        <div class="flex items-center gap-1 px-2 py-1 rounded-md ${{statusColor}}">
                            <span class="text-sm">${{statusIcon}}</span>
                            <span class="text-sm font-medium">${{statusText}}</span>
                            <span class="text-xs opacity-75">(${{width}}px)</span>
                        </div>
                    `;
                }}
            }}
        }}
        
        // 적응형 그리드 이벤트 리스너
        window.addEventListener('gridColumnsChanged', updateAdaptiveColumns);
        window.addEventListener('load', updateAdaptiveColumns);
        window.addEventListener('resize', updateAdaptiveColumns);
        </script>
        """)
        
        # 헤더
        with ui.header(elevated=True).classes('items-center justify-between px-6'):
            ui.label(self.title).classes('text-h6 font-bold')
            
            with ui.row().classes('gap-3 items-center'):
                # 🚀 적응형 컬럼 표시기
                ui.html('''
                    <div id="adaptive-columns-indicator" class="flex items-center">
                        <div class="flex items-center gap-1 px-2 py-1 rounded-md bg-blue-100 border border-blue-300">
                            <span class="text-sm">🔲</span>
                            <span class="text-sm font-medium text-blue-700">12컬럼</span>
                            <span class="text-xs text-blue-500">(0px)</span>
                        </div>
                    </div>
                ''')
                
                # 연결 상태 표시
                self.connection_status = ui.chip(
                    'Connecting...', 
                    icon='wifi',
                    color='orange'
                ).props('outline dense')

                # 사용자 가이드 페이지 이동 버튼
                if self.user_guide:
                    with ui.button(
                        icon='help',
                        on_click=lambda: ui.navigate.to('/user_guide')
                        ).classes('text-white hover:text-gray-300').props('flat round'):
                        ui.tooltip('사용자 가이드').classes('bg-green')
        
        # 🚀 적응형 그리드 메인 컨테이너
        with ui.column().classes('w-full min-h-screen bg-gray-50 p-0'):
            self.main_container = ui.element('div').classes('adaptive-grid-container')
            
        # 실제 화면 크기 감지를 위한 JavaScript
        ui.add_head_html("""
        <script>
        // 실제 화면 크기를 서버로 전송하는 함수
        function updateServerScreenWidth() {
            const screenWidth = window.innerWidth;
            // 서버 측 계산과 동기화를 위해 이벤트 발생
            window.dispatchEvent(new CustomEvent('serverScreenWidthUpdate', {
                detail: { screenWidth: screenWidth }
            }));
        }
        
        // 초기 로딩 시 화면 크기 업데이트
        window.addEventListener('load', updateServerScreenWidth);
        window.addEventListener('resize', updateServerScreenWidth);
        </script>
        """)
    
    def _generate_component_id(self, component_type: str, identifier: str = None) -> str:
        """컴포넌트 유니크 ID 생성"""
        self.component_counters[component_type] += 1
        counter = self.component_counters[component_type]
        
        if identifier:
            return f"{component_type}_{identifier}_{counter}"
        else:
            return f"{component_type}_{counter}"
    
    # ========================================
    # 컴포넌트 추가 메서드
    # ========================================

    def _add_component(
        self,
        component_type: str,
        proxy_class: type,
        default_size: Tuple[int, int],
        identifier: Optional[str] = None,
        position: Optional[Tuple[int, int, int, int]] = None,
        **kwargs
    ) -> Union[StockCardProxy, WatchlistProxy, PriceChartProxy, AccountProxy, OrderPanelProxy, OrderBookProxy]:
        """
        공통 컴포넌트 추가 로직 (DRY 원칙)
        
        Args:
            component_type: 컴포넌트 타입
            proxy_class: 프록시 클래스
            default_size: 기본 크기 (width, height)
            identifier: 컴포넌트 식별자
            position: 위치 튜플
            **kwargs: 추가 설정
        """
        # 위치 처리 공통화
        if position:
            row, col, width, height = position
        else:
            row, col, width, height = None, None, *default_size
        
        # ID 생성 공통화
        component_id = self._generate_component_id(component_type, identifier)
        
        # 설정 생성 공통화
        component_config = {
            'type': component_type,
            'position': position,
            'width': width,
            'height': height,
            'row': row,
            'col': col,
            'component_id': component_id,
            **kwargs  # 추가 설정 병합
        }
        
        # 큐 관리 공통화
        self.pending_components.append(component_config)
        
        # 구독 관리
        if 'symbol' in kwargs:
            self.pending_subscribes.add(kwargs['symbol'])

        elif 'symbols' in kwargs and kwargs['symbols'] and not kwargs.get('watchlist_key'):
            # watchlist_key가 있으면 영구 저장 Watchlist이므로 pending_subscribes에 추가하지 않음
            self.pending_subscribes.update(kwargs['symbols'])
        
        # 프록시 반환
        return proxy_class(component_config)

    def add_stock_card(
        self, 
        symbol: str, 
        position: Optional[Tuple[int, int, int, int]] = None
    ) -> StockCardProxy:
        """StockCard 추가

        Args:
            symbol: 종목 심볼
            position: (row, col, width, height) 위치 튜플
        Returns:
            StockCardProxy: 추가된 StockCard의 프록시 객체
        
        """
        return self._add_component(
            component_type="stock_card",
            proxy_class=StockCardProxy,
            default_size=ComponentDefaults.STOCK_CARD,
            identifier=symbol,
            position=position,
            symbol=symbol
        )
        
    def add_watchlist(
        self,
        symbols: Optional[List[str]] = None,
        position: Optional[Tuple[int, int, int, int]] = None,
        key: Optional[str] = None
    ) -> WatchlistProxy:
        """Watchlist 추가
        
        Args:
            symbols: 초기 심볼 리스트
            position: (row, col, width, height) 위치 튜플
            key: Watchlist 식별자 (영구 저장용)
        Returns:
            WatchlistProxy: 추가된 Watchlist의 프록시 객체
        
        """
        return self._add_component(
            component_type="watchlist",
            proxy_class=WatchlistProxy,
            default_size=ComponentDefaults.WATCHLIST,
            position=position,
            symbols=symbols,
            watchlist_key=key
        )

    def add_trading_view_chart(
        self, 
        symbol: str, 
        position: Optional[Tuple[int, int, int, int]] = None
    ) -> PriceChartProxy:
        """TradingView 차트 추가
        
        Args:
            symbol: 종목 심볼
            position: (row, col, width, height) 위치 튜플
        Returns:
            PriceChartProxy: 추가된 TradingView 차트의 프록시 객체
        
        """
        return self._add_component(
            component_type="trading_view_chart",
            proxy_class=PriceChartProxy,
            default_size=ComponentDefaults.TRADING_VIEW_CHART,
            identifier=symbol,
            position=position,
            symbol=symbol
        )

    def add_account(
        self, 
        refresh_interval: int = 10,
        position: Optional[Tuple[int, int, int, int]] = None
    ) -> AccountProxy:
        """계좌 정보 컴포넌트 추가
        
        Args:
            refresh_interval: 계좌 정보 새로고침 주기 (초)
            position: (row, col, width, height) 위치 튜플
        Returns:
            AccountProxy: 추가된 Account 컴포넌트의 프록시 객체
        
        """
        return self._add_component(
            component_type="account",
            proxy_class=AccountProxy,
            default_size=ComponentDefaults.ACCOUNT,
            identifier="account",
            position=position,
            refresh_interval=refresh_interval
        )

    def add_order_panel(
        self, 
        symbol: str, 
        position: Optional[Tuple[int, int, int, int]] = None
    ) -> OrderPanelProxy:
        """주문 패널 컴포넌트 추가
        
        Args:
            symbol: 종목 심볼
            position: (row, col, width, height) 위치 튜플
        Returns:
            OrderPanelProxy: 추가된 OrderPanel 컴포넌트의 프록시 객체
        
        """
        return self._add_component(
            component_type="order_panel",
            proxy_class=OrderPanelProxy,
            default_size=ComponentDefaults.ORDER_PANEL,
            identifier="order_panel",
            position=position,
            symbol=symbol
        )

    def add_order_book(
        self, 
        symbol: str,
        position: Optional[Tuple[int, int, int, int]] = None
    ) -> OrderBookProxy:
        """호가창 컴포넌트 추가

        Args:
            symbol: 종목 심볼
            position: (row, col, width, height) 위치 튜플
        Returns:
            OrderBookProxy: 추가된 OrderBook 컴포넌트의 프록시 객체

        """
        return self._add_component(
            component_type="order_book",
            proxy_class=OrderBookProxy,
            default_size=ComponentDefaults.ORDER_BOOK,
            identifier="order_book",
            position=position,
            symbol=symbol
        )
        
    # ========================================
    # 컴포넌트 렌더링 메서드
    # ========================================
    
    def render_pending_components(self):
        """위치 결정 및 컴포넌트 생성"""

        for config in self.pending_components:
            # 그리드 매니저에 컴포넌트 등록 및 위치 결정
            if config['component_id'] not in self.components:
                final_row, final_col, final_width, final_height = self.grid_manager.add_component(
                    config['component_id'], config['width'], config['height'], 
                    config['row'], config['col']
                )

                self.components_position[config['component_id']] = (final_row, final_col, final_width, final_height)
            
            # 이미 위치가 결정된 경우 기존 위치 사용
            else:
                final_row, final_col, final_width, final_height = self.components_position[config['component_id']]
                
            # 적응형 그리드 클래스 생성 (기본 화면 크기 가정)
            component_classes = self.grid_manager.get_component_classes(config['component_id'], screen_width=1920)
            
            # 고정 위치 컴포넌트 속성 생성 (현재 컬럼 수 전달)
            current_columns = self.grid_manager._calculate_current_columns(1920)
            component_attributes = self.grid_manager.get_component_attributes(config['component_id'], current_columns)
            
            # props 문자열 생성
            props_parts = [f'id="{config["component_id"]}"', f'data-component-id="{config["component_id"]}"']
            for attr_name, attr_value in component_attributes.items():
                props_parts.append(f'{attr_name}="{attr_value}"')
            props_string = " ".join(props_parts)
            
            # 실제 UI 생성
            with self.main_container:
                with ui.element('div').classes(component_classes).props(props_string):
                    if config['type'] == 'stock_card':
                        component = StockCard(config['symbol'], self.market_data, final_width/final_height)
                    elif config['type'] == 'watchlist':
                        component = Watchlist(
                            self.data_provider,
                            self.market_data,
                            config['symbols'],
                            config['watchlist_key'],)
                    elif config['type'] == 'trading_view_chart':
                        component = TradingViewChart(symbol=config['symbol'])
                    elif config['type'] == 'account':
                        component = Account(
                            data_provider=self.data_provider,
                            market_data=self.market_data,
                            refresh_interval=config.get('refresh_interval'),
                        )
                    elif config['type'] == 'order_panel':
                        component = OrderPanel(
                            symbol=config['symbol'],
                            data_provider=self.data_provider,
                            market_data=self.market_data,
                            account_data={}  # 추후 계좌 데이터 ObservableDict로 교체 예정
                        )
                    elif config['type'] == 'order_book':
                        component = OrderBook(
                            symbol=config['symbol'],
                            order_book_data=self.order_book_data
                        )

            # 생성된 컴포넌트 저장
            self.components[config['component_id']] = component

    # ========================================
    # 리소스 정리 메서드
    # ========================================
            
    def _cleanup(self):
        """리소스 정리"""
        if hasattr(self.data_provider, 'cleanup'):
            self.data_provider.cleanup()
        self.components.clear()
    
    # ========================================
    # 실행 메서드
    # ========================================

    async def initialize_data_connection(self):
        """데이터 연결 초기화 (3단계)"""
        
        # 1단계: LS API 연결
        if not await self.data_provider.connect():
            self.logger.error("❌ LS API 연결 실패")
            return False
        
        # 2단계: WebSocket 연결  
        if not await self.data_provider.connect_websocket():
            self.logger.error("❌ WebSocket 연결 실패")
            return False
        
        # 3단계: 필요한 심볼들 수집
        watchlist_symbols = self._collect_all_watchlist_symbols()
        all_symbols = watchlist_symbols.union(self.pending_subscribes)

        # 4단계: 심볼 구독 시작
        if all_symbols:
            await self.data_provider.subscribe_symbols(
                list(all_symbols)
            )
        
        # 5단계: 호가 심볼 구독
        order_book_symbol = self._collect_order_book_symbol()
        if order_book_symbol:
            await self.data_provider.subscribe_order_book_symbol(order_book_symbol)
        
        return True
    
    def _collect_all_watchlist_symbols(self) -> Set[str]:
        """모든 Watchlist 컴포넌트의 심볼 수집"""
        all_symbols = set()
        
        for component in self.components.values():
            if isinstance(component, Watchlist):
                # Watchlist의 저장된 심볼들 수집
                storage_key = component._get_storage_key()
                saved_symbols = app.storage.general.get(storage_key, [])
                all_symbols.update(saved_symbols)
                
        return all_symbols

    def _collect_order_book_symbol(self) -> Set[str]:
        """OrderBook 컴포넌트의 심볼 수집"""        
        for component in self.components.values():
            if isinstance(component, OrderBook):
                symbol = component.symbol

                return symbol

    def run(
            self,
            favicon: str = '⭐',
            host: str = '127.0.0.1',
            port: int = 8080,
            show: bool = True,
            reload: bool = False,
        ) -> None:
        """대시보드 실행
        
        Args:
            favicon: 파비콘 경로
            host: 호스트 주소
            port: 포트 번호
            show: 브라우저 자동 열기 여부
            reload: 코드 변경시 자동 재시작 여부
        
        """
        default_settings = {
            'title': self.title,
            'favicon': favicon,
            'host': host,
            'port': port,
            'show': show,
            'reload': reload
        }
        
        @ui.page('/')
        async def dashboard_page():
            """대시보드 메인 페이지"""
            # 1. 기본 UI 구조 생성
            self.create_ui()
            
            # 2. 저장된 컴포넌트들 순차 생성
            self.render_pending_components()
            
            # 3. 데이터 핸들러 설정
            self._setup_data_handlers()

            # 4. 데이터 연결 초기화
            success = await self.initialize_data_connection()
            if not success:
                ui.navigate.to('/error')
                return

            # 5. 큐 초기화
            self.pending_subscribes.clear()
        
        @ui.page('/error')
        def error():
            """에러 페이지"""
            error_page()
        
        @ui.page('/user_guide')
        def user_guide():
            """사용자 가이드 페이지"""
            user_guide_page()
        
        try:
            ui.run(**default_settings)
        except KeyboardInterrupt:
            print("\n🛑 대시보드를 종료합니다...")
        finally:
            self._cleanup()


