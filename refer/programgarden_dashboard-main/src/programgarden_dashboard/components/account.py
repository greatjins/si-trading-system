"""
계좌 정보 컴포넌트 (Account Component)
===================================

해외 주식 계좌의 잔고, 보유 종목, 수익률을 표시하는 컴포넌트
- LS Open API COSOQ00201 TR 연동
- NiceGUI ui.aggrid + ObservableDict 실시간 바인딩
- 주기 계좌 데이터 갱신 (LS API 제한 고려)
"""

from typing import Dict
from nicegui import ui
from nicegui.observables import ObservableDict

from ..utils.logger import get_logger


class Account:
    """
    Account 컴포넌트 - 계좌 정보 표시
    
    Features:
    - 계좌 요약 (총 자산, 가용 현금, 수익률)
    - 보유 종목 그리드 (심볼, 수량, 평가금액, 수익률)
    - 주기 계좌 데이터 갱신 (LS API 제한 고려)
    - NiceGUI 네이티브 패턴 활용
    """
    
    def __init__(
        self, 
        data_provider, 
        market_data: ObservableDict,
        refresh_interval: int = 10,
    ):
        """
        Account 컴포넌트 초기화
        
        Args:
            data_provider: DataProvider 인스턴스 (LS TR 등 모든 데이터 소스 담당)
            market_data: 실시간 데이터 바인딩용 ObservableDict
        """
        self.data_provider = data_provider
        self.market_data = market_data
        self.refresh_interval = refresh_interval
        self.logger = get_logger(f"Account")
        
        # UI 컴포넌트 참조
        self.container = None
        self.summary_cards = {}
        self.holdings_grid = None
        
        # 데이터 초기화
        self.market_data['account'] = {
            "available_amount": 0.0,
            "cash_eval_profit": 0.0,
            "total_profit_loss": 0.0,
            "total_profit_rate": 0.0,
            "holdings": []
        }
        
        # UI 생성
        self._create_ui()
        
        # 자동 갱신 설정 (10초 주기 - LS API 제한 고려)
        self._setup_auto_refresh()
        
        self.logger.info("✅ Account 컴포넌트 초기화 완료")
    
    def _create_ui(self):
        """Account UI 생성"""
        
        # 컨테이너 생성
        with ui.card().classes('w-full h-full cursor-pointer hover:shadow-xl transition-all duration-300 border-l-4 border-gray-300').style(
            'display: flex; flex-direction: column; padding: 1rem; '
            'background: #fff;'
        ):
            # 제목
            ui.label('💼 계좌 정보').classes('text-h6 text-weight-bold q-mb-md')
            
            # 계좌 요약 카드들
            self._create_summary_cards()
            
            # 보유 종목 그리드
            self._create_holdings_grid()
    
    def _create_summary_cards(self):
        """계좌 요약 정보 카드들 생성"""
        
        with ui.row().classes('w-full q-gutter-md'):
            # 추정 예수금
            with ui.card().classes('flex-1 cursor-pointer hover:shadow-lg transition-all duration-300 border-l-4 border-blue-300').style(
                'padding: 1rem; background: #fff; display: flex; flex-direction: column; gap: 0.5rem;'
            ):
                ui.label('💰 추정 예수금').classes('text-sm text-gray-500 font-medium')
                self.summary_cards['available_amount'] = ui.label('$0.00').classes('text-2xl font-bold text-gray-900')
            
            # 손익 금액
            with ui.card().classes('flex-1 cursor-pointer hover:shadow-lg transition-all duration-300 border-l-4 border-green-300').style(
                'padding: 1rem; background: #fff; display: flex; flex-direction: column; gap: 0.5rem;'
            ):
                ui.label('📈 손익 금액').classes('text-sm text-gray-500 font-medium')
                self.summary_cards['cash_eval_profit'] = ui.label('$0.00').classes('text-2xl font-bold text-gray-900')
            
            # 수익률
            with ui.card().classes('flex-1 cursor-pointer hover:shadow-lg transition-all duration-300 border-l-4 border-purple-300').style(
                'padding: 1rem; background: #fff; display: flex; flex-direction: column; gap: 0.5rem;'
            ):
                ui.label('📊 수익률').classes('text-sm text-gray-500 font-medium')
                self.summary_cards['profit_rate'] = ui.label('0.00%').classes('text-2xl font-bold text-gray-900')
    
    def _create_holdings_grid(self):
        """보유 종목 그리드 생성"""
        
        # 그리드 컬럼 정의
        column_defs = [
            {
                'headerName': '종목',
                'field': 'symbol',
                'width': 80,
                'pinned': 'left'
            },
            {
                'headerName': '종목명',
                'field': 'name', 
                'width': 120,
                'cellRenderer': 'function(params) { return params.value || params.data.symbol; }'
            },
            {
                'headerName': '수량',
                'field': 'quantity',
                'width': 80,
                'type': 'numericColumn',
                'cellRenderer': 'function(params) { return params.value.toLocaleString(); }'
            },
            {
                'headerName': '평균단가',
                'field': 'avg_price',
                'width': 90,
                'type': 'numericColumn',
                'cellRenderer': 'function(params) { return "$" + params.value.toFixed(2); }'
            },
            {
                'headerName': '현재가',
                'field': 'current_price',
                'width': 80,
                'type': 'numericColumn',
                'cellRenderer': 'function(params) { return "$" + params.value.toFixed(2); }'
            },
            {
                'headerName': '평가금액',
                'field': 'market_value',
                'width': 100,
                'type': 'numericColumn',
                'cellRenderer': 'function(params) { return "$" + params.value.toLocaleString(); }'
            },
            {
                'headerName': '수익금',
                'field': 'profit_loss',
                'width': 90,
                'type': 'numericColumn',
                'cellClassRules': {
                    'text-green-600': 'x >= 0',
                    'text-red-600': 'x < 0'
                },
                'cellRenderer': '''function(params) { 
                    const value = params.value;
                    const sign = value >= 0 ? "+" : "";
                    return sign + "$" + value.toLocaleString(); 
                }'''
            },
            {
                'headerName': '수익률',
                'field': 'profit_rate',
                'width': 80,
                'type': 'numericColumn',
                'cellClassRules': {
                    'text-green-600': 'x >= 0',
                    'text-red-600': 'x < 0'
                },
                'cellRenderer': '''function(params) { 
                    const value = params.value;
                    const sign = value >= 0 ? "+" : "";
                    return sign + value.toFixed(2) + "%"; 
                }'''
            }
        ]
        
        # 그리드 생성
        ui.label('📊 보유 종목').classes('text-subtitle2 text-weight-medium q-mt-md q-mb-sm')
        
        self.holdings_grid = ui.aggrid({
            'columnDefs': column_defs,
            'rowData': [],
            'defaultColDef': {
                'sortable': True,
                'filter': True,
                'resizable': True
            },
            'rowSelection': 'single',
            'animateRows': True,
            'enableCellTextSelection': True,
            'suppressRowClickSelection': False
        }).classes('w-full h-full')
        
        # 그리드 이벤트 처리
        self.holdings_grid.on('cellClicked', self._on_holding_clicked)
    
    def _setup_auto_refresh(self):
        """자동 갱신 설정 (10초 주기)"""
        
        # 초기 데이터 로딩
        ui.timer(1.0, self._fetch_account_data, once=True)

        # interval마다 계좌 데이터 갱신 (LS API 제한 고려)
        ui.timer(self.refresh_interval, self._fetch_account_data)
        
        # 100ms마다 UI 업데이트 (부드러운 사용자 경험)
        ui.timer(0.1, self._update_ui_components)
    
    async def _fetch_account_data(self):
        """LS API로부터 계좌 데이터 조회"""
        
        try:
            self.logger.debug("🔄 계좌 데이터 조회 시작...")
            
            # DataProvider를 통한 계좌 잔고 조회
            account_data = await self.data_provider.fetch_account_data()
            
            # ObservableDict 업데이트
            self.market_data['account'] = account_data
            
            if 'error' not in account_data:
                self.logger.info(f"✅ 계좌 데이터 갱신 완료")
            else:
                self.logger.warning(f"⚠️ 계좌 데이터 조회 오류: {account_data['error']}")
                
        except Exception as e:
            self.logger.error(f"❌ 계좌 데이터 조회 실패: {e}")
    
    def _update_ui_components(self):
        """ObservableDict 변경사항을 UI에 반영"""
        
        try:
            account_data = self.market_data.get('account', {})
            
            # 계좌 요약 카드 업데이트
            if 'available_amount' in account_data:
                available_amount = account_data['available_amount']
                self.summary_cards['available_amount'].set_text(f"${available_amount:,.2f}")
            
            if 'cash_eval_profit' in account_data:
                cash_eval_profit = account_data['cash_eval_profit']
                profit_text = f"${cash_eval_profit:+,.2f}"
                
                # 손익 금액 색상 적용
                if cash_eval_profit >= 0:
                    self.summary_cards['cash_eval_profit'].classes(
                        remove='text-red-600', add='text-green-600'
                    )
                else:
                    self.summary_cards['cash_eval_profit'].classes(
                        remove='text-green-600', add='text-red-600'
                    )
                
                self.summary_cards['cash_eval_profit'].set_text(profit_text)
            
            if 'total_profit_rate' in account_data:
                profit_rate = account_data['total_profit_rate']
                rate_text = f"{profit_rate:+.2f}%"
                
                # 수익률 색상 적용
                if profit_rate >= 0:
                    self.summary_cards['profit_rate'].classes(
                        remove='text-red-600', add='text-green-600'
                    )
                else:
                    self.summary_cards['profit_rate'].classes(
                        remove='text-green-600', add='text-red-600'
                    )
                
                self.summary_cards['profit_rate'].set_text(rate_text)
            
            # 보유 종목 그리드 업데이트
            holdings = account_data.get('holdings', [])
            if holdings != getattr(self, '_last_holdings', []):
                self.holdings_grid.options['rowData'] = holdings
                self.holdings_grid.update()
                self._last_holdings = holdings.copy()
                
        except Exception as e:
            self.logger.error(f"❌ UI 업데이트 실패: {str(e)}")
    
    def _on_holding_clicked(self, event):
        """보유 종목 클릭 이벤트 처리"""
        
        try:
            row_data = event.args.get('data', {})
            symbol = row_data.get('symbol', '')
            
            if symbol:
                self.logger.info(f"📊 보유 종목 선택: {symbol}")
                
                # 다른 컴포넌트들에게 심볼 선택 이벤트 전파
                self.market_data['selected_symbol'] = symbol
                
                # 알림 표시
                ui.notify(f"📊 {symbol} 종목 선택됨", type='info', position='top-right')
                
        except Exception as e:
            self.logger.error(f"❌ 보유 종목 클릭 처리 실패: {str(e)}")
    
    def refresh_now(self):
        """즉시 계좌 데이터 갱신"""
        ui.timer(0.1, self._fetch_account_data, once=True)
        ui.notify("🔄 계좌 데이터 갱신 중...", type='info')
    
    def get_account_summary(self) -> Dict:
        """현재 계좌 요약 정보 반환"""
        return self.market_data.get('account', {})
    
    def cleanup(self):
        """컴포넌트 정리"""
        self.logger.info("Account 컴포넌트 정리 중...")
        
        # UI 컴포넌트 정리
        if self.container:
            self.container.delete()
        
        self.logger.info("✅ Account 컴포넌트 정리 완료")