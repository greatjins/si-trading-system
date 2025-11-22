from nicegui import ui

# ========================================
# 사용자 가이드 페이지
# ========================================

@ui.page('/guide')
def user_guide_page():
    """사용자 가이드 페이지 생성"""
    ui.page_title("ProgramGarden Dashboard - 사용자 가이드")
    
    # 헤더
    with ui.header(elevated=True).classes('items-center justify-between px-6'):
        ui.label("사용자 가이드").classes('text-h5 font-bold')
        
        with ui.row().classes('gap-3 items-center'):
            ui.button(
                '대시보드로 돌아가기',
                icon='home',
                on_click=lambda: ui.navigate.to('/')
            ).classes('text-white hover:text-gray-300').props('outline')
    
    # 메인 콘텐츠
    with ui.column().classes('w-full max-w-4xl mx-auto p-6 gap-6'):
        
        # 소개 섹션
        with ui.card().classes('w-full p-6'):
            ui.label("📊 ProgramGarden Dashboard란?").classes('text-h5 font-bold mb-4')
            ui.markdown("""
            **ProgramGarden Dashboard**는 파이썬 초보자를 위한 **3줄로 완성**할 수 있는 간단한 해외 주식 대시보드 라이브러리입니다.
            
            - **LS Open API** 기반 실시간 해외 주식 데이터
            - **NiceGUI** 프레임워크로 구축된 직관적인 웹 UI
            - **3줄 코드**로 전문가급 대시보드 완성
            """)
        
        # 빠른 시작 가이드
        with ui.card().classes('w-full p-6'):
            ui.label("🚀 빠른 시작 (3줄 코드)").classes('text-h5 font-bold mb-4')
            
            ui.markdown("**1단계: 기본 대시보드 생성**")
            with ui.card().classes('bg-gray-100 p-4 mb-4'):
                ui.code("""
from programgarden_dashboard import ProgramGardenDashboard

dashboard = ProgramGardenDashboard(
app_key="your_ls_api_key", 
app_secret="your_ls_api_secret"
)
dashboard.add_stock_card("AAPL")
dashboard.run()
                """).classes('text-sm')
            
            ui.markdown("**2단계: 컴포넌트 추가 (선택사항)**")
            with ui.card().classes('bg-gray-100 p-4 mb-4'):
                ui.code("""
# 관심종목 + 호가창 + 주문패널 + 트레이딩뷰 차트 추가
dashboard.add_watchlist(["AAPL", "GOOGL", "TSLA"])
dashboard.add_order_book("AAPL")
dashboard.add_order_panel("AAPL")
dashboard.add_trading_view_chart("AAPL")
                """).classes('text-sm')
        
        # 컴포넌트 가이드
        with ui.card().classes('w-full p-6'):
            ui.label("🧩 주요 컴포넌트").classes('text-h5 font-bold mb-4')
            
            components_data = [
                ['컴포넌트', '메서드', '설명', '예시'],
                ['주식카드', 'add_stock_card("AAPL")', '실시간 가격 정보', 'AAPL $150.25 (+2.1%)'],
                ['관심종목', 'add_watchlist(["AAPL", "GOOGL"])', '여러 종목 모니터링', '테이블 형태 목록'],
                ['호가창', 'add_order_book("AAPL")', '실시간 매수/매도 호가', '10단계 호가 정보'],
                ['주문패널', 'add_order_panel("AAPL")', '매수/매도 주문 실행', '지정가/시장가 주문'],
                ['차트', 'add_trading_view_chart("AAPL")', 'TradingView 차트', '캔들스틱 차트'],
                ['계좌정보', 'add_account()', '계좌 잔고 및 보유종목', '잔고/수익률 정보']
            ]
            
            ui.table(columns=[
                {'name': 'component', 'label': '컴포넌트', 'field': 'component', 'align': 'center'},
                {'name': 'method', 'label': '메서드', 'field': 'method', 'align': 'left'},
                {'name': 'description', 'label': '설명', 'field': 'description', 'align': 'left'},
                {'name': 'example', 'label': '예시', 'field': 'example', 'align': 'left'}
            ], rows=[
                {'component': row[0], 'method': row[1], 'description': row[2], 'example': row[3]} 
                for row in components_data[1:]
            ]).classes('w-full')
        
        # LS Open API 설정 가이드
        with ui.card().classes('w-full p-6'):
            ui.label("🔑 LS Open API 설정").classes('text-h5 font-bold mb-4')
            
            with ui.expansion('1. LS Open API 신청 방법', icon='key').classes('w-full'):
                ui.markdown("""
                **단계별 신청 가이드:**
                
                1. **LS증권 홈페이지 방문**: https://openapi.ls-sec.co.kr/
                2. **회원가입 및 로그인** (LS증권 계좌 필요)
                3. **Xing API 사용 신청**
                4. **Open API 사용 신청**
                5. **APP KEY / APP SECRET 발급**
                """)
            
            with ui.expansion('2. API 키 사용 방법', icon='code').classes('w-full'):
                ui.markdown("**환경변수 설정 (권장)**")
                with ui.card().classes('bg-gray-100 p-3'):
                    ui.code("""
# .env 파일에 저장
APPKEY="your_actual_app_key_here"
APPSECRET="your_actual_app_secret_here"

# Python 코드에서 사용
import os
from dotenv import load_dotenv
load_dotenv()

dashboard = ProgramGardenDashboard(
app_key=os.getenv("APPKEY"),
app_secret=os.getenv("APPSECRET")
)
                    """).classes('text-sm')
                
                ui.markdown("**직접 입력 (테스트용)**")
                with ui.card().classes('bg-gray-100 p-3'):
                    ui.code("""
dashboard = ProgramGardenDashboard(
app_key="실제_발급받은_APP_KEY",
app_secret="실제_발급받은_APP_SECRET"  
)
                    """).classes('text-sm')
        
        # 고급 기능 가이드
        with ui.card().classes('w-full p-6'):
            ui.label("⚙️ 고급 기능").classes('text-h5 font-bold mb-4')
            
            with ui.expansion('레이아웃 커스터마이징', icon='dashboard').classes('w-full'):
                ui.markdown("**컴포넌트 위치 지정**")
                with ui.card().classes('bg-gray-100 p-3'):
                    ui.code("""
# position = (row, col, width, height)
dashboard.add_stock_card("AAPL", position=(0, 0, 2, 2))
dashboard.add_watchlist(["GOOGL", "TSLA"], position=(0, 2, 4, 4))
dashboard.add_order_book("AAPL", position=(2, 0, 4, 2))
                    """).classes('text-sm')
            
#             with ui.expansion('실시간 데이터 접근', icon='timeline').classes('w-full'):
#                 ui.markdown("**데이터 콜백 설정**")
#                 with ui.card().classes('bg-gray-100 p-3'):
#                     ui.code("""
# def on_price_update(symbol, data):
# print(f"{symbol}: ${data['price']} ({data['change_percent']:+.2f}%)")

# dashboard.data_provider.setup_dashboard_integration(
# on_price_update=on_price_update
# )
#                     """).classes('text-sm')
        
        # FAQ 섹션
        with ui.card().classes('w-full p-6'):
            ui.label("❓ 자주 묻는 질문").classes('text-h5 font-bold mb-4')
            
            faqs = [
                ("무료로 사용할 수 있나요?", "네, ProgramGarden Dashboard는 무료 오픈소스입니다. 다만 LS Open API 사용을 위해서는 LS증권 계좌가 필요합니다."),
                ("실시간 데이터가 안 나와요", "1) LS API 키 확인 2) 인터넷 연결 확인 3) LS증권 서버 상태 확인을 해보세요."),
                ("더 많은 종목을 추가할 수 있나요?", "네, add_stock_card()나 add_watchlist()로 원하는 만큼 추가할 수 있습니다."),
                ("모바일에서도 볼 수 있나요?", "네, 웹 기반이므로 모바일 브라우저에서도 접근 가능합니다."),
                ("커스터마이징은 어떻게 하나요?", "position 매개변수로 레이아웃 조정이 가능하며, 자세한 내용은 GitHub 문서를 참고하세요.")
            ]
            
            for question, answer in faqs:
                with ui.expansion(question, icon='help').classes('w-full'):
                    ui.markdown(f"**답변**: {answer}")
        
        # 연락처/지원
        with ui.card().classes('w-full p-6'):
            ui.label("📞 지원 및 문의").classes('text-h5 font-bold mb-4')
            
            with ui.row().classes('gap-4 flex-wrap justify-center'):
                ui.button(
                    'GitHub Repository', 
                    icon='code',
                    on_click=lambda: ui.navigate.to('https://github.com/programgarden/programgarden_dashboard', new_tab=True)
                ).props('outline color=primary')
                
                ui.button(
                    'Issues 및 버그 신고',
                    icon='bug_report', 
                    on_click=lambda: ui.navigate.to('https://github.com/programgarden/programgarden_dashboard/issues', new_tab=True)
                ).props('outline color=orange')
                
                ui.button(
                    'LS Open API 문서',
                    icon='description',
                    on_click=lambda: ui.navigate.to('https://openapi.ls-sec.co.kr/', new_tab=True)
                ).props('outline color=green')
