"""Order Panel Component - LS Open API 주문 시스템"""

from nicegui import ui
from nicegui.observables import ObservableDict
from datetime import datetime

from ..utils.logger import get_logger


class OrderPanel:
    """LS Open API 기반 주문 패널 컴포넌트 (StockCard 패턴 적용)"""
    
    def __init__(self, symbol: str, data_provider, market_data: ObservableDict, account_data: ObservableDict):
        """
        Args:
            symbol: 주문할 종목 심볼 (예: "AAPL")
            data_provider: 기존 DataProvider 인스턴스
            market_data: 실시간 시세 데이터 (종목명, 현재가 조회용)
            account_data: 계좌 정보 및 주문 상태 데이터  
        """
        self.symbol = symbol.upper()
        self.data_provider = data_provider
        self.market_data = market_data
        self.account_data = account_data
        self.logger = get_logger(f"OrderPanel.{self.symbol}")
        
        # 주문 상태 관리 (ObservableDict)
        self.order_states = ObservableDict()
        self.current_tab = "buy"
        
        # UI 요소 참조
        self.tabs = None
        self.tab_panels = None
        
        # LS API 주문 데이터 구조 초기화 (StockCard 패턴)
        self._initialize_order_data()
        
        # 동적 UI 생성 (StockCard 패턴)
        self._create_ui()
    
    # ========================================
    # 초기 설정 메서드들
    # ========================================
        
    def _initialize_order_data(self):
        """LS Open API 주문 데이터 구조 초기화"""
        
        if self.symbol not in self.market_data:
            self.market_data[self.symbol] = {
                "name": "",       # 종목명
                "price": 0.0,     # 현재가
            }

        if self.symbol not in self.order_states:
            # 각 탭별 주문 입력 상태 관리
            self.order_states.update({
                "buy": {
                    "symbol": "",
                    "quantity": 0,
                    "price": 0.0,
                    "order_type": "지정가",  # 지정가, 시장가, LOO, LOC, MOO, MOC
                    "cash_type": "현금",     # 현금, 대출 (매수만)
                    "current_price": 0.0,   # 현재가 표시용
                    "symbol_name": "",      # 종목명 표시용
                },
                "sell": {
                    "symbol": "",
                    "quantity": 0,
                    "price": 0.0,
                    "order_type": "지정가",
                    "current_price": 0.0,
                    "symbol_name": "",
                },
                "modify": {
                    "original_order_no": "",
                    "symbol": "",
                    "quantity": 0,
                    "price": 0.0,
                    "order_type": "지정가",
                    "current_price": 0.0,
                    "symbol_name": "",
                },
                "cancel": {
                    "original_order_no": "",
                    "symbol": "",
                    "symbol_name": "",
                }
            })
        
        # 계좌 데이터 초기화
        if "orders" not in self.account_data:
            self.account_data["orders"] = {
                "pending": {},      # 미체결 주문들
                "completed": {},    # 체결 완료 주문들
                "results": {},      # 주문 결과들
                "last_order_time": datetime.now().isoformat()
            }
    
    def _create_ui(self):
        """기본 UI 생성"""
        
        with ui.card().classes('w-full h-full cursor-pointer hover:shadow-xl transition-all duration-300 border-l-4 border-gray-300').style(
            'display: flex; flex-direction: column; padding: 1rem; '
            'background: #fff;'
        ):
            with ui.column().classes('w-full h-full gap-3'):
                # 헤더
                with ui.row().classes('w-full justify-between items-center mb-2'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('shopping_cart', size='md').classes('text-blue-600')
                        ui.label('주문 패널').classes('text-xl font-bold text-gray-800')
                    
                    # 연결 상태 표시
                    ui.label().classes('text-sm text-gray-600').bind_text_from(
                        self.account_data, 'connection_status', 
                        backward=lambda status: f"상태: {status or '연결중...'}")
                
                # 탭 시스템
                with ui.tabs().classes('w-full') as self.tabs:
                    # 매수 탭 (연한 빨간색)
                    self.buy_tab = ui.tab('매수', icon='trending_up')
                    
                    # 매도 탭 (연한 파란색) 
                    self.sell_tab = ui.tab('매도', icon='trending_down')
                    
                    # 정정 탭 (연한 초록색)
                    self.modify_tab = ui.tab('정정', icon='edit')
                    
                    # 취소 탭 (연한 갈색)
                    self.cancel_tab = ui.tab('취소', icon='cancel')

                # 탭 변경 이벤트
                self.tabs.on('update:model-value', self._on_tab_changed)
                
                # 탭 컨텐츠
                if hasattr(self, 'tabs') and self.tabs:
                    # 가로형 탭이 있는 경우
                    with ui.tab_panels(self.tabs, value='매수').classes('w-full flex-1'):
                        with ui.tab_panel(self.buy_tab):
                            self._create_buy_panel()
                        with ui.tab_panel(self.sell_tab):
                            self._create_sell_panel()
                        with ui.tab_panel(self.modify_tab):
                            self._create_modify_panel()
                        with ui.tab_panel(self.cancel_tab):
                            self._create_cancel_panel()
                else:
                    # 세로형 버튼 네비게이션인 경우
                    with ui.column().classes('w-full flex-1') as self.content_area:
                        self._create_buy_panel()  # 기본으로 매수 패널 표시

    def _create_buy_panel(self):
        """매수 주문 패널 (PLAN_ORDER_PANEL.md 요구사항)"""
        with ui.column().classes('w-full gap-4 bg-red-25'):
            # 1. 종목 심볼과 종목명
            self._create_symbol_input_section('buy')
            
            # 2. 주문 구분 및 매수금 유형
            with ui.row().classes('w-full gap-4'):
                # 주문 구분
                ui.select(
                    options=['지정가', '시장가', 'LOO', 'LOC', 'MOO', 'MOC'], 
                    value='지정가',
                    label='주문 구분'
                ).classes('flex-1').bind_value(self.order_states, 'buy.order_type')
                
                # 매수금 유형 (매수 전용)
                with ui.column().classes('flex-1 gap-0'):
                    ui.label('매수금 유형').classes('text-sm text-gray-600 mb-1')
                    ui.radio(['현금', '대출'], value='현금').props('inline').bind_value(
                        self.order_states, 'buy.cash_type'
                    )
            
            # 3. 주문 수량
            ui.number('주문 수량', value=0, min=0, step=1, format='%.0f').classes('w-full').bind_value(
                self.order_states, 'buy.quantity'
            )
            
            # 4. 주문 가격 및 현재가
            with ui.row().classes('w-full gap-4 items-center'):
                ui.number('주문 가격', value=0.0, min=0, step=0.01, format='%.2f').classes('flex-1').bind_value(
                    self.order_states, 'buy.price'
                )
                
                # 현재가 표시
                with ui.column().classes('flex-1'):
                    ui.label('현재가').classes('text-sm text-gray-600')
                    ui.label().classes('text-lg font-bold text-red-600').bind_text_from(
                        self.market_data, self.symbol,
                        backward=lambda price: f"${price.get(f'price', 0) if isinstance(price, dict) else 0:.2f}"
                    )
            
            # 5. 주문 버튼
            ui.space()
            ui.button('매수 주문', icon='shopping_cart').classes(
                'w-full bg-red-500 text-white hover:bg-red-600'
            ).on('click', lambda: self._execute_buy_order())

    def _create_sell_panel(self):
        """매도 주문 패널"""
        with ui.column().classes('w-full gap-4 bg-blue-25'):
            # 매수와 동일하되 매수금 유형 제외
            self._create_symbol_input_section('sell')
            
            # 주문 구분
            ui.select(
                options=['지정가', '시장가', 'LOO', 'LOC', 'MOO', 'MOC'],
                value='지정가', 
                label='주문 구분'
            ).classes('w-full').bind_value(self.order_states, 'sell.order_type')
            
            # 주문 수량
            ui.number('주문 수량', value=0, min=0, step=1, format='%.0f').classes('w-full').bind_value(
                self.order_states, 'sell.quantity'
            )
            
            # 주문 가격 및 현재가
            with ui.row().classes('w-full gap-4 items-center'):
                ui.number('주문 가격', value=0.0, min=0, step=0.01, format='%.2f').classes('flex-1').bind_value(
                    self.order_states, 'sell.price'
                )
                
                with ui.column().classes('flex-1'):
                    ui.label('현재가').classes('text-sm text-gray-600')
                    ui.label().classes('text-lg font-bold text-blue-600').bind_text_from(
                        self.order_states, 'sell.current_price',
                        backward=lambda price: f"${price:.2f}" if price else "N/A"
                    )
            
            # 매도 주문 버튼
            ui.space()
            ui.button('매도 주문', icon='sell').classes(
                'w-full bg-blue-500 text-white hover:bg-blue-600'
            ).on('click', lambda: self._execute_sell_order())

    def _create_modify_panel(self):
        """정정 주문 패널"""
        with ui.column().classes('w-full gap-4 bg-green-25'):
            # 1. 종목 심볼과 종목명
            self._create_symbol_input_section('modify')
            
            # 2. 원주문 번호 및 미체결 조회
            with ui.row().classes('w-full gap-2 items-end'):
                ui.input('원주문 번호', placeholder='주문번호 입력').classes('flex-1').bind_value(
                    self.order_states, 'modify.original_order_no'
                )
                ui.button('미체결 조회', icon='search').classes('flex-shrink-0').on(
                    'click', self._show_pending_orders_dialog
                )
            
            # 3. 주문 구분
            ui.select(
                options=['지정가', '시장가', 'LOO', 'LOC', 'MOO', 'MOC'],
                value='지정가',
                label='주문 구분'
            ).classes('w-full').bind_value(self.order_states, 'modify.order_type')
            
            # 4. 정정 수량 및 가격
            ui.number('정정 수량', value=0, min=0, step=1, format='%.0f').classes('w-full').bind_value(
                self.order_states, 'modify.quantity'
            )
            
            ui.number('정정 가격', value=0.0, min=0, step=0.01, format='%.2f').classes('w-full').bind_value(
                self.order_states, 'modify.price'
            )
            
            # 5. 정정 버튼
            ui.space()
            ui.button('정정 주문', icon='edit').classes(
                'w-full bg-green-500 text-white hover:bg-green-600'
            ).on('click', lambda: self._execute_modify_order())

    def _create_cancel_panel(self):
        """취소 주문 패널"""
        with ui.column().classes('w-full gap-4 bg-amber-25'):
            # 1. 원주문 번호 및 미체결 조회
            with ui.row().classes('w-full gap-2 items-end'):
                ui.input('원주문 번호', placeholder='주문번호 입력').classes('flex-1').bind_value(
                    self.order_states, 'cancel.original_order_no'
                )
                ui.button('미체결 조회', icon='search').classes('flex-shrink-0').on(
                    'click', self._show_pending_orders_dialog
                )
            
            # 2. 종목 심볼과 종목명
            self._create_symbol_input_section('cancel')
            
            # 3. 취소 버튼
            ui.space()
            ui.button('취소 주문', icon='cancel').classes(
                'w-full bg-amber-500 text-white hover:bg-amber-600'
            ).on('click', lambda: self._execute_cancel_order())

    def _create_symbol_input_section(self, tab_type: str):
        """종목 입력 섹션 (재사용 가능)"""
        with ui.row().classes('w-full gap-4 items-center'):
            # 종목 심볼 입력
            ui.input('종목 심볼', placeholder='AAPL', value=self.symbol).classes('flex-1')
            
            # 종목명 표시
            with ui.column().classes('flex-1'):
                ui.label('종목명').classes('text-sm text-gray-600')
                ui.label().classes('text-base font-medium text-gray-800').bind_text_from(
                    self.order_states, f'{tab_type}.symbol_name',
                    backward=lambda name: name.get(f'name', '') if isinstance(name, dict) else ''
                )

                # TODO : g3104 조회 후 종목명 수신 받을 수 있게

    # ========================================
    # 이벤트 핸들러들
    # ========================================

    def _on_tab_changed(self, e):
        """탭 변경 이벤트 핸들러"""
        self.current_tab = e.args.lower() if hasattr(e, 'args') else 'buy'
        self.logger.info(f"주문 탭 변경: {self.current_tab}")

    def _switch_tab(self, tab_name: str):
        """탭 전환 (세로형 네비게이션용)"""
        self.current_tab = tab_name
        # 컨텐츠 영역 업데이트
        if hasattr(self, 'content_area'):
            self.content_area.clear()
            with self.content_area:
                if tab_name == 'buy':
                    self._create_buy_panel()
                elif tab_name == 'sell':
                    self._create_sell_panel()
                elif tab_name == 'modify':
                    self._create_modify_panel()
                elif tab_name == 'cancel':
                    self._create_cancel_panel()

    def _update_symbol_info(self, tab_type: str, symbol: str):
        """종목 정보 업데이트 (실시간 현재가 연동)"""
        print(f"Update symbol info called with tab_type={tab_type}, symbol={symbol}")
    #     if not symbol:
    #         return
            
    #     try:
    #         symbol = symbol.upper().strip()
            
    #         # market_data에서 종목 정보 가져오기
    #         symbol_data = self.market_data.get(symbol, {})
            
    #         # 현재가 업데이트
    #         current_price = symbol_data.get('price', 0.0)
    #         self.order_states[tab_type]['current_price'] = current_price
            
    #         # 종목명 업데이트 (임시로 심볼 사용, 실제로는 종목명 API 호출)
    #         self.order_states[tab_type]['symbol_name'] = symbol_data.get('name', symbol)
            
    #         # 주문 가격 기본값 설정 (현재가로)
    #         if current_price > 0:
    #             self.order_states[tab_type]['price'] = current_price
                
    #     except Exception as e:
    #         self.logger.error(f"종목 정보 업데이트 실패: {e}")

    def _show_pending_orders_dialog(self):
        """미체결 주문 조회 Dialog (NiceGUI 네이티브)"""
        with ui.dialog().props('maximized') as dialog:
            with ui.card().classes('w-full'):
                ui.label('미체결 주문 조회').classes('text-xl font-bold mb-4')
                
                # 미체결 주문 목록 (ui.aggrid)
                pending_orders = self.account_data.get('orders', {}).get('pending', {})
                
                if not pending_orders:
                    ui.label('미체결 주문이 없습니다.').classes('text-gray-500 text-center')
                else:
                    # AgGrid로 미체결 주문 표시
                    orders_data = []
                    for order_no, order_info in pending_orders.items():
                        orders_data.append({
                            'order_no': order_no,
                            'symbol': order_info.get('symbol', ''),
                            'order_type': order_info.get('order_type', ''),
                            'quantity': order_info.get('quantity', 0),
                            'price': order_info.get('price', 0.0),
                            'order_time': order_info.get('order_time', '')
                        })
                    
                    aggrid = ui.aggrid({
                        'columnDefs': [
                            {'headerName': '주문번호', 'field': 'order_no'},
                            {'headerName': '종목', 'field': 'symbol'},
                            {'headerName': '구분', 'field': 'order_type'},
                            {'headerName': '수량', 'field': 'quantity'},
                            {'headerName': '가격', 'field': 'price'},
                            {'headerName': '주문시간', 'field': 'order_time'},
                        ],
                        'rowData': orders_data,
                        'rowSelection': 'single'
                    }).classes('w-full h-64')
                
                # 버튼들
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('선택', icon='check').on('click', lambda: self._select_pending_order(aggrid, dialog))
                    ui.button('닫기', icon='close').on('click', dialog.close)
        
        dialog.open()

    def _select_pending_order(self, aggrid, dialog):
        """미체결 주문 선택 처리"""
        # 선택된 주문 정보를 현재 탭의 입력 필드에 설정
        # (실제 구현시 aggrid.get_selected_rows() 사용)
        ui.notify('주문이 선택되었습니다.', type='positive')
        dialog.close()

    # ========================================
    # LS Open API 주문 실행 메서드들
    # ========================================

    async def _execute_buy_order(self):
        """매수 주문 실행 (COSAT00301)"""
        try:
            order_data = self.order_states['buy']
            
            # 입력 검증
            if not order_data['symbol'] or order_data['quantity'] <= 0 or order_data['price'] <= 0:
                ui.notify('주문 정보를 확인해주세요.', type='warning')
                return
            
            # LS API 호출
            # result = await self.data_provider.execute_order()
            
            # 임시 성공 처리
            ui.notify(f"{order_data['symbol']} 매수 주문이 접수되었습니다.", type='positive')
            
            # 주문 상태 초기화
            self._reset_order_inputs('buy')
            
        except Exception as e:
            self.logger.error(f"매수 주문 실행 실패: {e}")
            ui.notify(f'주문 실행 오류: {e}', type='negative')

    async def _execute_sell_order(self):
        """매도 주문 실행 (COSAT00301)"""
        try:
            order_data = self.order_states['sell']
            
            # 입력 검증
            if not order_data['symbol'] or order_data['quantity'] <= 0 or order_data['price'] <= 0:
                ui.notify('주문 정보를 확인해주세요.', type='warning')
                return

            # LS API 호출 (실제 구현시)
            # result = await self.data_provider.execute_order()

            ui.notify(f"{order_data['symbol']} 매도 주문이 접수되었습니다.", type='positive')
            self._reset_order_inputs('sell')
            
        except Exception as e:
            self.logger.error(f"매도 주문 실행 실패: {e}")
            ui.notify(f'주문 실행 오류: {e}', type='negative')

    async def _execute_modify_order(self):
        """정정 주문 실행 (COSAT00311)"""
        try:
            order_data = self.order_states['modify']
            
            # 입력 검증
            if not order_data['original_order_no'] or not order_data['symbol']:
                ui.notify('원주문 번호와 종목을 확인해주세요.', type='warning')
                return
            
            # LS API 호출 (실제 구현시)
            # result = await self.data_provider.correct_order()
            
            ui.notify(f"주문번호 {order_data['original_order_no']} 정정 주문이 접수되었습니다.", type='positive')
            self._reset_order_inputs('modify')
            
        except Exception as e:
            self.logger.error(f"정정 주문 실행 실패: {e}")
            ui.notify(f'주문 실행 오류: {e}', type='negative')

    async def _execute_cancel_order(self):
        """취소 주문 실행 (COSAT00301)"""
        try:
            order_data = self.order_states['cancel']
            
            # 입력 검증
            if not order_data['original_order_no']:
                ui.notify('원주문 번호를 확인해주세요.', type='warning')
                return
            
            # LS API 호출 (실제 구현시)
            # result = await self.data_provider.execute_order()
            
            ui.notify(f"주문번호 {order_data['original_order_no']} 취소 주문이 접수되었습니다.", type='positive')
            self._reset_order_inputs('cancel')
            
        except Exception as e:
            self.logger.error(f"취소 주문 실행 실패: {e}")
            ui.notify(f'주문 실행 오류: {e}', type='negative')

    def _reset_order_inputs(self, tab_type: str):
        """주문 입력 초기화"""
        if tab_type in ['buy', 'sell']:
            self.order_states[tab_type].update({
                'symbol': '',
                'quantity': 0,
                'price': 0.0,
                'current_price': 0.0,
                'symbol_name': ''
            })
        elif tab_type in ['modify', 'cancel']:
            self.order_states[tab_type].update({
                'original_order_no': '',
                'symbol': '',
                'symbol_name': ''
            })
            if tab_type == 'modify':
                self.order_states[tab_type].update({
                    'quantity': 0,
                    'price': 0.0,
                    'current_price': 0.0
                })
                