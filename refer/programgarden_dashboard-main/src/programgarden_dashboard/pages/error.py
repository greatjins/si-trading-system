from nicegui import ui

# ========================================
# 오류 페이지
# ========================================

def error_page():
    ui.page_title("ProgramGarden Dashboard - 오류")

    # 헤더
    with ui.header(elevated=True).classes('items-center justify-between px-6'):
        ui.label("사용자 가이드").classes('text-h5 font-bold')
    
    ui.space()

    # 메인 콘텐츠
    with ui.column().classes('w-full h-full max-w-4xl mx-auto p-3 gap-6 items-center justify-center'):
        ui.label("❌ 오류가 발생했습니다.").classes('text-h5 text-red-600')
        ui.label("데이터 연결에 실패했거나, 내부 오류가 발생했을 수 있습니다.").classes('text-subtitle2 text-gray-600')
        ui.label("잠시 후 다시 시도하거나, 문제가 지속되면 관리자에게 문의하세요.").classes('text-subtitle2 text-gray-600')

        # 연락처/지원
        with ui.card().classes('w-full p-6'):
            ui.label("📞 지원 및 문의").classes('text-h5 font-bold mb-4')
            
            with ui.row().classes('gap-4 flex-wrap justify-center'):
                ui.button(
                    'GitHub Repository', 
                    icon='code',
                    on_click=lambda: ui.navigate.to('https://github.com/RakunaryGarden/programgarden_dashboard_lite', new_tab=True)
                ).props('outline color=primary')
                
                ui.button(
                    'Issues 및 버그 신고',
                    icon='bug_report', 
                    on_click=lambda: ui.navigate.to('https://github.com/RakunaryGarden/programgarden_dashboard_lite/issues', new_tab=True)
                ).props('outline color=orange')
                
                ui.button(
                    'LS Open API 문서',
                    icon='description',
                    on_click=lambda: ui.navigate.to('https://openapi.ls-sec.co.kr/', new_tab=True)
                ).props('outline color=green')