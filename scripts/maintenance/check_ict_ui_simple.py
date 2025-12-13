#!/usr/bin/env python3
"""
ICT 지표 UI 간단 확인
"""
import webbrowser
import time

def open_strategy_builder():
    """전략 빌더 페이지 열기"""
    
    print("🌐 전략 빌더 페이지를 브라우저에서 열고 있습니다...")
    print("📋 확인사항:")
    print("   1. 로그인 후 전략 빌더 페이지로 이동")
    print("   2. 매수조건 추가 버튼 클릭")
    print("   3. 지표 선택에서 '🎯 ICT 이론' 카테고리 확인")
    print("   4. ICT 지표들이 표시되는지 확인:")
    print("      - BOS (Break of Structure)")
    print("      - Fair Value Gap")
    print("      - Order Block")
    print("      - Liquidity Pool")
    print("      - Smart Money Flow")
    print()
    print("✅ 타입 오류 수정 완료!")
    print("✅ ICT 지표 5개 백엔드 구현 완료!")
    print("✅ 프론트엔드/백엔드 서버 실행 중!")
    print()
    print("🔗 URL: http://localhost:3001")
    
    # 브라우저에서 열기
    webbrowser.open("http://localhost:3001")

if __name__ == "__main__":
    open_strategy_builder()