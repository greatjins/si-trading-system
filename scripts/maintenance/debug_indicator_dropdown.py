#!/usr/bin/env python3
"""
지표 드롭다운 문제 디버깅
"""
import requests
import json

def debug_indicator_api():
    """지표 API 응답 확인"""
    
    base_url = "http://localhost:8000"
    
    try:
        print("🔍 지표 API 응답 확인 중...")
        response = requests.get(f"{base_url}/api/strategy-builder/indicators")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API 응답 성공")
            print(f"📊 지표 개수: {len(data.get('indicators', []))}")
            print(f"📂 카테고리 개수: {len(data.get('categories', []))}")
            
            # 카테고리별 지표 확인
            for category in data.get('categories', []):
                cat_indicators = [ind for ind in data.get('indicators', []) if ind.get('category') == category['id']]
                print(f"\n📁 {category['name']} ({category['id']}): {len(cat_indicators)}개")
                for ind in cat_indicators[:3]:  # 처음 3개만 표시
                    print(f"   - {ind['name']} ({ind['id']})")
                    
            # ICT 지표 확인
            ict_indicators = [ind for ind in data.get('indicators', []) if ind.get('category') == 'ict']
            if ict_indicators:
                print(f"\n🎯 ICT 지표 상세:")
                for ind in ict_indicators:
                    print(f"   - {ind['name']} (id: {ind['id']})")
                    print(f"     operators: {ind.get('operators', [])}")
                    print(f"     parameters: {[p['name'] for p in ind.get('parameters', [])]}")
            
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 서버 연결 실패. 백엔드 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def check_frontend_console():
    """프론트엔드 콘솔 확인 방법 안내"""
    
    print("\n🌐 프론트엔드 디버깅 방법:")
    print("1. 브라우저에서 F12 키를 눌러 개발자 도구 열기")
    print("2. Console 탭에서 다음 로그 확인:")
    print("   - '✅ 지표 목록 로드:' 메시지가 있는지 확인")
    print("   - 오류 메시지가 있는지 확인")
    print("3. Network 탭에서 '/api/strategy-builder/indicators' 요청 확인")
    print("4. 지표 드롭다운을 클릭했을 때 반응이 있는지 확인")
    print("\n💡 문제 해결 방법:")
    print("- 페이지 새로고침 (Ctrl+F5)")
    print("- 브라우저 캐시 삭제")
    print("- 서버 재시작")

if __name__ == "__main__":
    debug_indicator_api()
    check_frontend_console()