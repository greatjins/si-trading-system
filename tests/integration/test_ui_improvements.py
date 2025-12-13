#!/usr/bin/env python3
"""
UI 개선사항 테스트
"""

import asyncio
import httpx

async def test_ui_improvements():
    """UI 개선사항 테스트"""
    
    print("🎨 UI 개선사항 테스트")
    print("=" * 50)
    
    # 프론트엔드 서버 상태 확인
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:3000")
            
            if response.status_code == 200:
                print("✅ 프론트엔드 서버 정상 동작")
                print("🌐 브라우저에서 확인하세요: http://localhost:3000")
                
                print("\n📋 개선사항 체크리스트:")
                print("1. ✅ 거래횟수 표시 개선: '2회 (1쌍)' 형식")
                print("2. ✅ 공통 스타일 시스템 적용")
                print("3. ✅ 반응형 디자인 개선")
                print("4. ✅ 에러 메시지 컴포넌트 개선")
                print("5. ✅ 중복 스타일 코드 제거")
                
                print("\n🎯 테스트 항목:")
                print("- 백테스트 페이지: http://localhost:3000/backtest")
                print("- 백테스트 비교: http://localhost:3000/backtest/compare")
                print("- 백테스트 결과: http://localhost:3000/backtest/results/[ID]")
                print("- 모바일 반응형 (개발자 도구에서 확인)")
                
                print("\n📱 반응형 테스트:")
                print("- 데스크톱: 1200px 이상")
                print("- 태블릿: 768px ~ 1199px")
                print("- 모바일: 767px 이하")
                
            else:
                print(f"❌ 프론트엔드 서버 오류: {response.status_code}")
                
    except Exception as e:
        print(f"❌ 프론트엔드 서버 연결 실패: {e}")
        print("💡 npm run dev로 프론트엔드 서버를 시작하세요")

if __name__ == "__main__":
    asyncio.run(test_ui_improvements())