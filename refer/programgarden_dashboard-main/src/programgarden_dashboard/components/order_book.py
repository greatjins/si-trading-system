"""Order Book Component - LS Open API 호가창"""

from nicegui import ui
from nicegui.observables import ObservableDict
from datetime import datetime
from typing import Dict, Any

from ..utils.logger import get_logger


class OrderBook:
    """LS Open API 기반 호가창 컴포넌트 (StockCard 패턴 적용)"""
    
    def __init__(self, symbol: str, order_book_data: ObservableDict):
        """
        Args:
            symbol: 주식 심볼 (예: "AAPL", "GOOGL")
            order_book_data: LS API 호가 데이터가 실시간으로 업데이트되는 ObservableDict
        """
        self.symbol = symbol.upper()
        self.order_book_data = order_book_data
        self.logger = get_logger(f"OrderBook.{self.symbol}")
        
        # LS API 호가 데이터 구조 초기화
        self._initialize_order_book_data()
        
        # 동적 UI 생성
        self._create_ui()
    
    # ========================================
    # 초기 설정 메서드
    # ========================================
        
    def _initialize_order_book_data(self):
        """LS Open API 호가 데이터 구조 초기화 (GSH 응답 구조)"""
        
        if self.symbol not in self.order_book_data:
            # GSH (해외주식 호가) 응답 필드에 맞춘 완전한 초기 구조
            self.order_book_data[self.symbol] = {
                # 기본 정보
                "symbol": self.symbol,
                "korea_time": datetime.now().strftime("%H:%M:%S"),  # 한국호가시간
                
                # 매도 호가 (10단계)
                "ask_prices": [0.0] * 10,   # 매도가격 10단계
                "ask_volumes": [0] * 10,    # 매도잔량 10단계  
                "ask_counts": [0] * 10,     # 매도건수 10단계
                
                # 매수 호가 (10단계)
                "bid_prices": [0.0] * 10,   # 매수가격 10단계
                "bid_volumes": [0] * 10,    # 매수잔량 10단계
                "bid_counts": [0] * 10,     # 매수건수 10단계
                
                # 합계 정보
                "total_ask_volume": 0,      # 매도총잔량
                "total_ask_count": 0,       # 매도총건수
                "total_bid_volume": 0,      # 매수총잔량
                "total_bid_count": 0,       # 매수총건수
                
                # 데이터 소스 정보
                "source": "연결중...",
                "last_updated": datetime.now().isoformat()
            }
    
    def _create_ui(self):
        """기본 레이아웃"""

        with ui.card().classes('w-full h-full cursor-pointer hover:shadow-xl transition-all duration-300 border-l-4 border-gray-300').style(
            'display: flex; flex-direction: column; padding: 1rem; '
            'background: #fff;'
        ):
            with ui.column().classes('w-full h-full gap-0.5'):
                with ui.row().classes('w-full justify-between items-center mb-1 p-2 bg-gray-100 rounded'):
                    with ui.row().classes('h-12 items-center gap-2'):
                        ui.icon('assessment', size='md').classes('text-purple-600')
                        ui.label(f'{self.symbol} 호가창').classes('text-lg font-bold text-gray-800')
                    
                    # 한국호가시간 표시
                    with ui.column().classes('items-end'):
                        ui.label().classes('text-sm font-mono text-gray-700').bind_text_from(
                            self.order_book_data, self.symbol,
                            backward=lambda time: time.get(f'last_updated', '--:--') if isinstance(time, dict) else '--:--'
                        )
                
                with ui.column().classes('w-full flex-1 gap-1'):
                    # 테이블 헤더
                    with ui.row().classes('w-full bg-gray-200 p-1 text-xs font-bold text-gray-700'):
                        ui.label('건수').classes('w-12 text-center')
                        ui.label('매도잔량').classes('flex-1 text-center')
                        ui.label('호가').classes('flex-1 text-center')
                        ui.label('매수잔량').classes('flex-1 text-center')
                        ui.label('건수').classes('w-12 text-center')
                    
                    # 매도 호가 (10호가부터 1호가까지)
                    for i in range(10):
                        self._create_ask_row(i)
                    
                    # 매수 호가 (1호가부터 10호가까지)  
                    for i in range(10):
                        self._create_bid_row(i)
                
                with ui.row().classes('w-full bg-gray-100 p-2 border-t-2 border-gray-300 text-sm font-bold'):
                    # 매도총건수
                    with ui.column().classes('flex-1 items-center'):
                        ui.label().classes('text-blue-700').bind_text_from(
                            self.order_book_data, self.symbol,
                            backward=lambda counts: counts.get(f'total_ask_count', 0) if isinstance(counts, dict) else 0
                        )
                    
                    # 매도총잔량
                    with ui.column().classes('flex-1 items-center'):
                        ui.label().classes('text-blue-700').bind_text_from(
                            self.order_book_data, self.symbol,
                            backward=lambda volume: volume.get(f'total_ask_volume', 0) if isinstance(volume, dict) else 0
                        )
                    
                    # 합계 라벨
                    with ui.column().classes('flex-1 items-center'):
                        ui.label('합계').classes('text-sm font-bold text-gray-800')
                    
                    # 매수총잔량
                    with ui.column().classes('flex-1 items-center'):
                        ui.label().classes('text-red-700').bind_text_from(
                            self.order_book_data, self.symbol,
                            backward=lambda volume: volume.get(f'total_bid_volume', 0) if isinstance(volume, dict) else 0
                        )
                    
                    # 매수총건수
                    with ui.column().classes('flex-1 items-center'):
                        ui.label().classes('text-red-700').bind_text_from(
                            self.order_book_data, self.symbol,
                            backward=lambda count: count.get(f'total_bid_count', 0) if isinstance(count, dict) else 0
                        )

    def _create_ask_row(self, index: int):
        """매도 호가 행 생성 (연한 파란색 배경, 진한 파란색 글씨)"""
        
        with ui.row().classes('w-full h-6 bg-blue-50 border-b border-blue-100 p-1 text-xs hover:bg-blue-100'):
            # 매도 건수
            ui.label().classes('w-12 text-center text-blue-800 font-medium').bind_text_from(
                self.order_book_data, self.symbol,
                backward=lambda counts: counts.get('ask_counts', [0] * 10)[9-index] if isinstance(counts, dict) else 0
            )
            
            # 매도 잔량
            ui.label().classes('flex-1 text-center text-blue-800 font-medium').bind_text_from(
                self.order_book_data, self.symbol,
                backward=lambda volumes: volumes.get('ask_volumes', [0] * 10)[9-index] if isinstance(volumes, dict) else 0
            )
            
            # 매도 호가
            ui.label().classes('flex-1 text-center text-blue-900 font-bold').bind_text_from(
                self.order_book_data, self.symbol,
                backward=lambda prices: f"{prices.get('ask_prices', [0.00] * 10)[9-index]:.2f}" if isinstance(prices, dict) else "0.00"
            )
            
            # 빈 공간 (매수 쪽)
            ui.label('').classes('flex-1')
            ui.label('').classes('w-12')

    def _create_bid_row(self, index: int):
        """매수 호가 행 생성 (연한 빨간색 배경, 진한 빨간색 글씨)"""
        with ui.row().classes('w-full h-6 bg-red-50 border-b border-red-100 p-1 text-xs hover:bg-red-100'):
            # 빈 공간 (매도 쪽)
            ui.label('').classes('w-12')
            ui.label('').classes('flex-1')
            
            # 매수 호가
            ui.label().classes('flex-1 text-center text-red-900 font-bold').bind_text_from(
                self.order_book_data, self.symbol,
                backward=lambda prices: f"{prices.get('bid_prices', [0.00] * 10)[index]:.2f}" if isinstance(prices, dict) else 0
            )
            
            # 매수 잔량
            ui.label().classes('flex-1 text-center text-red-800 font-medium').bind_text_from(
                self.order_book_data, self.symbol,
                backward=lambda volumes: volumes.get('bid_volumes', [0] * 10)[index] if isinstance(volumes, dict) else 0
            )
            
            # 매수 건수
            ui.label().classes('w-12 text-center text-red-800 font-medium').bind_text_from(
                self.order_book_data, self.symbol,
                backward=lambda counts: counts.get('bid_counts', [0] * 10)[index] if isinstance(counts, dict) else 0
            )

    # ========================================
    # 유틸리티 메서드들
    # ========================================

    def update_orderbook(self, gsh_data: Dict[str, Any]):
        """LS API GSH 호가 데이터 업데이트"""
        try:
            if self.symbol in self.order_book_data:
                # GSH 응답 데이터를 ObservableDict에 반영
                symbol_data = self.order_book_data[self.symbol]
                
                # 매도/매수 호가 업데이트
                if 'ask_prices' in gsh_data:
                    symbol_data['ask_prices'] = gsh_data['ask_prices'][:10]
                if 'ask_volumes' in gsh_data:
                    symbol_data['ask_volumes'] = gsh_data['ask_volumes'][:10]
                if 'ask_counts' in gsh_data:
                    symbol_data['ask_counts'] = gsh_data['ask_counts'][:10]
                    
                if 'bid_prices' in gsh_data:
                    symbol_data['bid_prices'] = gsh_data['bid_prices'][:10]
                if 'bid_volumes' in gsh_data:
                    symbol_data['bid_volumes'] = gsh_data['bid_volumes'][:10]
                if 'bid_counts' in gsh_data:
                    symbol_data['bid_counts'] = gsh_data['bid_counts'][:10]
                
                # 합계 정보 계산 및 업데이트
                symbol_data['total_ask_volume'] = sum(symbol_data['ask_volumes'])
                symbol_data['total_ask_count'] = sum(symbol_data['ask_counts'])
                symbol_data['total_bid_volume'] = sum(symbol_data['bid_volumes'])
                symbol_data['total_bid_count'] = sum(symbol_data['bid_counts'])
                
                # 시간 업데이트
                symbol_data['korea_time'] = datetime.now().strftime("%H:%M:%S")
                symbol_data['last_updated'] = datetime.now().isoformat()
                symbol_data['source'] = "LS Open API"
                
                self.logger.debug(f"호가창 데이터 업데이트 완료: {self.symbol}")
                
        except Exception as e:
            self.logger.error(f"호가창 데이터 업데이트 실패: {e}")

    def get_best_bid_ask(self) -> Dict[str, float]:
        """최우선 매수/매도 호가 반환"""
        try:
            symbol_data = self.order_book_data.get(self.symbol, {})
            
            # 최우선 매도호가 (ask_prices[0])
            best_ask = symbol_data.get('ask_prices', [0])[0] if symbol_data.get('ask_prices') else 0.0
            
            # 최우선 매수호가 (bid_prices[0])
            best_bid = symbol_data.get('bid_prices', [0])[0] if symbol_data.get('bid_prices') else 0.0
            
            return {
                "best_ask": best_ask,
                "best_bid": best_bid,
                "spread": best_ask - best_bid if best_ask > 0 and best_bid > 0 else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"최우선 호가 조회 실패: {e}")
            return {"best_ask": 0.0, "best_bid": 0.0, "spread": 0.0}