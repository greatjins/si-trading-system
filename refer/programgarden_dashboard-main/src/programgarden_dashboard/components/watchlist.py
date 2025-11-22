"""Watchlist Component"""

from nicegui import ui, app
from nicegui.observables import ObservableDict
from typing import List, Optional

from ..utils.data_formatter import DataFormatter
from ..utils.logger import get_logger


class Watchlist:
    """관심종목 관리 컴포넌트"""
    
    def __init__(self, data_provider, market_data: ObservableDict, symbols: Optional[List[str]] = None, watchlist_key: Optional[str] = None):
        """
        Args:
            data_provider: 데이터 제공자
            market_data: LS API 데이터가 실시간으로 업데이트되는 ObservableDict
            symbols: 관심종목 리스트
            watchlist_key: 선택적 KEY - 제공시 영구 저장, 없으면 메모리 전용
        """
        self.data_provider = data_provider
        self.market_data = market_data
        self.watchlist_key = watchlist_key
        self.logger = get_logger(f"Watchlist.{self.watchlist_key or 'temp'}")
        
        # 관심종목 리스트 (브라우저 로컬 저장)
        self.symbols = symbols or []
        self._load_watchlist()
        
        # UI 요소들
        self.table = None
        self.add_input = None
        self.detail_button = None
        self.remove_button = None
        self.selected_symbol = None
        self.count_label = None
        
        # 초기 데이터 설정
        self._initialize_ls_market_data()
        
        # UI 생성
        self._create_ui()
    
    # ========================================
    # 저장 및 불러오기 메서드들
    # ========================================
        
    def _get_storage_key(self) -> str:
        """저장소 키 생성 - KEY별 독립적 저장"""
        if self.watchlist_key:
            return f'watchlist_{self.watchlist_key}'
        else:
            # KEY 없는 경우 메모리 전용이므로 실제로 저장되지 않음
            return 'watchlist_temp'
        
    def _load_watchlist(self):
        """NiceGUI 네이티브 저장소에서 관심종목 로드"""
        # KEY가 없으면 저장소 로드 안함 (메모리 전용)
        if not self.watchlist_key:
            return
            
        try:
            storage_key = self._get_storage_key()
            saved_symbols = app.storage.general.get(storage_key, [])
            if saved_symbols:
                self.symbols = saved_symbols
                self.logger.info(f"로드된 관심종목 [{self.watchlist_key}]: {self.symbols}")
        except Exception as e:
            self.logger.error(f"관심종목 로드 실패 [{self.watchlist_key}]: {e}")
            
    def _save_watchlist(self):
        """NiceGUI 네이티브 저장소에 관심종목 저장"""
        # KEY가 없으면 저장 안함 (메모리 전용)
        if not self.watchlist_key:
            self.logger.debug("watchlist_key 없음 - 메모리 전용 모드")
            return
            
        try:
            storage_key = self._get_storage_key()
            app.storage.general[storage_key] = self.symbols
            self.logger.info(f"저장된 관심종목 [{self.watchlist_key}]: {self.symbols}")
        except Exception as e:
            self.logger.error(f"관심종목 저장 실패 [{self.watchlist_key}]: {e}")
            
    # ========================================
    # 초기 UI 생성 메서드들
    # ========================================

    def _create_ui(self):
        """관심종목 UI 생성 (NiceGUI 네이티브)"""
        with ui.card().classes('w-full h-full cursor-pointer hover:shadow-xl transition-all duration-300 border-l-4 border-gray-300').style(
            'display: flex; flex-direction: column; padding: 1rem; '
            'background: #fff;'
        ):
            # 헤더
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label('관심종목').classes('text-xl font-bold text-gray-800')
                self.count_label = ui.label(f'{len(self.symbols)}개').classes('text-sm text-gray-500')
                
            # 종목 추가 입력
            with ui.row().classes('w-full gap-2 mb-4'):
                self.add_input = ui.input(
                    placeholder='종목 심볼 (예: AAPL)',
                    validation={'Symbol required': lambda value: len(value.upper().strip()) > 0}
                ).classes('flex-1').on('keydown.enter', lambda: self._add_symbol())
                
                ui.button('추가', on_click=self._add_symbol).props('color=primary size=sm')
                
            # 선택된 종목 액션 버튼들
            with ui.row().classes('w-full gap-2 mb-2 justify-end'):
                self.detail_button = ui.button('상세보기', on_click=self._show_selected_detail).props('color=info size=sm disabled')
                self.remove_button = ui.button('제거', on_click=self._remove_selected).props('color=negative size=sm disabled')
                
            # NiceGUI 네이티브 테이블
            self._create_native_table()
            
    def _create_native_table(self):
        """NiceGUI 네이티브 ui.table 생성"""

        # 컬럼 정의 (NiceGUI 네이티브)
        columns = [
            {
                'name': 'symbol',
                'label': '심볼',
                'field': 'symbol',
                'align': 'left',
                'sortable': True,
                'style': 'font-weight: bold; color: #1f2937; width: 80px;'
            },
            {
                'name': 'price',
                'label': '현재가',
                'field': 'price',
                'align': 'right',
                'sortable': True,
                'style': 'text-align: right; font-family: monospace; width: 100px;'
            },
            {
                'name': 'change',
                'label': '변동',
                'field': 'change',
                'align': 'right',
                'sortable': True,
                'style': 'text-align: right; font-family: monospace; width: 140px;'
            },
            {
                'name': 'volume',
                'label': '거래량',
                'field': 'volume',
                'align': 'right',
                'sortable': True,
                'style': 'text-align: right; font-family: monospace; font-size: 0.875rem; width: 80px;'
            },
            {
                'name': 'source',
                'label': '소스',
                'field': 'source',
                'align': 'left',
                'sortable': False,
                'style': 'font-size: 0.75rem; color: #6b7280; width: 80px;'
            }
        ]
        
        # 초기 행 데이터 생성
        rows = []
        for symbol in self.symbols:
            initial_data = self.market_data.get(symbol, {})
            rows.append({
                'symbol': symbol,
                'price': DataFormatter.price(initial_data, 'price'),
                'change': DataFormatter.change(initial_data, 'change', 'change_percent'),
                'volume': DataFormatter.volume(initial_data, 'volume'),
                'source': DataFormatter.source(initial_data, 'source')
            })
        
        # NiceGUI 네이티브 테이블 생성
        self.table = ui.table(
            columns=columns,
            rows=rows,
            row_key='symbol',
            selection='single',
            on_select=self._on_selection_changed
        ).classes('w-full h-full').style('font-size: 0.875rem;')
        
        # 조건부 포맷팅 슬롯 추가 (변동 컬럼 색상)
        self._add_conditional_formatting()
        
        # Client 안전한 실시간 바인딩 설정
        self._setup_safe_real_time_binding()
        
    def _add_conditional_formatting(self):
        """조건부 포맷팅 추가 - 변동률에 따른 색상 표시"""
        # 변동 컬럼에 조건부 색상 적용
        self.table.add_slot('body-cell-change', '''
            <q-td key="change" :props="props">
                <span :class="{
                    'text-green-600': props.value.includes('+'),
                    'text-red-600': props.value.includes('-'),
                    'text-gray-600': !props.value.includes('+') && !props.value.includes('-')
                }">
                    {{ props.value }}
                </span>
            </q-td>
        ''')

    # ========================================
    # 데이터 바인딩 및 업데이트
    # ========================================

    def _create_default_symbol_data(self, symbol: str) -> dict:
        """기본 심볼 데이터 구조 생성"""
        return {
            # 기본 정보
            "symbol": symbol,
            "price": 0.0,           # GSC.price
            "change": 0.0,          # GSC.diff (전일대비)
            "change_percent": 0.0,  # GSC.rate (등락율)
            "volume": 0,            # GSC.totq (누적체결수량)
            "open": 0.0,            # GSC.open (시가)
            "high": 0.0,            # GSC.high (고가)
            "low": 0.0,             # GSC.low (저가)
            # 누적거래대금 정보
            "amount": 0,            # GSC.amount (누적거래대금)
            # 데이터 소스 정보
            "source": "연결중..."
        }
            
    def _initialize_ls_market_data(self):
        """관심종목들의 market_data 초기화"""
        for symbol in self.symbols:
            if symbol not in self.market_data:
                self.market_data[symbol] = self._create_default_symbol_data(symbol)
    
    def _setup_safe_real_time_binding(self):
        """Client 안전한 실시간 바인딩 설정"""
        
        def on_market_data_change():
            """market_data 변경 시 테이블 안전 업데이트"""
            try:
                for row in self.table.rows:
                    symbol = row['symbol']
                    if symbol in self.market_data:
                        data = self.market_data[symbol]
                        row['price'] = DataFormatter.price(data, 'price')
                        row['change'] = DataFormatter.change(data, 'change', 'change_percent')
                        row['volume'] = DataFormatter.volume(data, 'volume')
                        row['source'] = DataFormatter.source(data, 'source')
                
                self.table.update()
                
            except Exception as e:
                # Client 에러가 발생할 수 없는 구조이지만 방어적 처리
                self.logger.debug(f"테이블 업데이트 중 오류 (무시 가능): {e}")
        
        # ObservableDict 변경 감지
        self.market_data.on_change(on_market_data_change)

    # ========================================
    # UI 이벤트 핸들러들
    # ========================================

    async def _add_symbol(self):
        """종목 추가"""
        if not self.add_input.value:
            return
            
        symbol = self.add_input.value.upper().strip()
        
        if symbol in self.symbols:
            ui.notify(f'{symbol}은 이미 추가된 종목입니다', type='warning')
            return
            
        # 관심종목 추가
        self.symbols.append(symbol)

        # 실시간 종목 추가
        await self.data_provider.subscribe_symbols([symbol])
        
        # market_data 초기화
        if symbol not in self.market_data:
            self.market_data[symbol] = self._create_default_symbol_data(symbol)
            
        # 로컬 저장
        self._save_watchlist()
        
        try:
            initial_data = self.market_data.get(symbol, {})
            new_row = {
                'symbol': symbol,
                'price': DataFormatter.price(initial_data, 'price'),
                'change': DataFormatter.change(initial_data, 'change', 'change_percent'),
                'volume': DataFormatter.volume(initial_data, 'volume'),
                'source': DataFormatter.source(initial_data, 'source')
            }
            
            self.table.add_row(new_row)
            
            # 카운트 레이블 업데이트
            self.count_label.set_text(f'{len(self.symbols)}개')
            
        except Exception as e:
            self.logger.error(f"테이블 행 추가 실패: {e}")
        
        # 입력 초기화
        self.add_input.value = ''
        
        ui.notify(f'{symbol} 추가완료', type='positive')
        self.logger.info(f"종목 추가: {symbol}")
    
    async def _remove_symbol(self, symbol: str):
        """종목 제거"""
        if symbol in self.symbols:
            # 관심종목 제거
            self.symbols.remove(symbol)

            # 실시간 종목 제거
            await self.data_provider.unsubscribe_symbols([symbol])

            # 로컬 저장
            self._save_watchlist()
            
            try:
                # 해당 행 찾아서 제거
                for row in self.table.rows[:]:  # 복사본으로 순회
                    if row['symbol'] == symbol:
                        self.table.remove_row(row)
                        break
                
                # 카운트 레이블 업데이트
                self.count_label.set_text(f'{len(self.symbols)}개')
                        
            except Exception as e:
                self.logger.error(f"테이블 행 제거 실패: {e}")
                
            ui.notify(f'{symbol} 제거완료', type='success')
            self.logger.info(f"종목 제거: {symbol}")
            
    def _show_symbol_detail(self, symbol: str):
        """종목 상세보기 - 공통 로직"""
        ui.navigate.to(f'https://finance.yahoo.com/quote/{symbol}/', new_tab=True)
            
    def _set_action_buttons_enabled(self, enabled: bool):
        """액션 버튼들 활성화/비활성화 상태 설정"""
        try:
            if enabled:
                self.detail_button.props(remove='disabled')
                self.remove_button.props(remove='disabled')
            else:
                self.detail_button.props(add='disabled')
                self.remove_button.props(add='disabled')
        except Exception as e:
            self.logger.debug(f"버튼 상태 변경 중 오류: {e}")
            
    def _on_selection_changed(self, event):
        """선택 변경 이벤트"""
        try:
            # 선택 처리
            selected_rows = event.selection
            
            if selected_rows:
                symbol = selected_rows[0]['symbol']
                self.selected_symbol = symbol
                
                # 액션 버튼들 활성화
                self._set_action_buttons_enabled(True)
                self.logger.debug(f"선택된 종목: {symbol}")
            else:
                self.selected_symbol = None
                # 액션 버튼들 비활성화
                self._set_action_buttons_enabled(False)
                self.logger.debug("선택 해제됨")
                
        except Exception as e:
            self.logger.error(f"선택 변경 처리 실패: {e}")
            
    def _show_selected_detail(self):
        """선택된 종목 상세보기"""
        if self.selected_symbol:
            self._show_symbol_detail(self.selected_symbol)
        else:
            ui.notify('종목을 먼저 선택해주세요', type='warning')
            
    async def _remove_selected(self):
        """선택된 종목 제거"""
        if self.selected_symbol:
            await self._remove_symbol(self.selected_symbol)
            self.selected_symbol = None
            # 버튼 비활성화
            self._set_action_buttons_enabled(False)
        else:
            ui.notify('제거할 종목을 먼저 선택해주세요', type='warning')

    # ========================================
    # 필터링 기능
    # ========================================
    
    def set_filter(self, filter_text: str):
        """테이블 필터 설정"""
        try:
            self.table.set_filter(filter_text)
        except Exception as e:
            self.logger.error(f"필터 설정 실패: {e}")
    
    def bind_filter_to_input(self, input_element):
        """입력 요소에 필터 바인딩"""
        try:
            self.table.bind_filter_from(input_element, 'value')
        except Exception as e:
            self.logger.error(f"필터 바인딩 실패: {e}")

    # ========================================
    # 컴포넌트 정리
    # ========================================

    async def cleanup(self):
        """컴포넌트 정리"""
        try:
            # 구독 해제
            if self.symbols:
                await self.data_provider.unsubscribe_symbols(self.symbols)
                
            # market_data에서 종목 데이터 제거
            for symbol in self.symbols:
                if symbol in self.market_data:
                    del self.market_data[symbol]
                    
            # UI 참조 해제
            self.table = None
            self.add_input = None
            self.detail_button = None
            self.remove_button = None
            self.count_label = None
                    
            self.logger.info(f"🗑️ Watchlist 컴포넌트 정리 완료 [{self.watchlist_key}]")
            
        except Exception as e:
            self.logger.error(f"Watchlist 컴포넌트 정리 실패 [{self.watchlist_key}]: {e}")