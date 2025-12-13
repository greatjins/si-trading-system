#!/usr/bin/env python3
"""
ICT 지표가 UI에서 정상 표시되는지 테스트
"""
import requests
import json

def test_ict_indicators():
    """ICT 지표 API 테스트"""
    
    base_url = "http://localhost:8000"
    
    try:
        # 1. 지표 목록 조회
        print("🔍 지표 목록 조회 중...")
        response = requests.get(f"{base_url}/api/strategy-builder/indicators")
        
        if response.status_code == 200:
            data = response.json()
            
            # ICT 카테고리 확인
            ict_category = None
            for category in data.get('categories', []):
                if category['id'] == 'ict':
                    ict_category = category
                    break
            
            if ict_category:
                print(f"✅ ICT 카테고리 발견: {ict_category['name']}")
                
                # ICT 지표들 확인
                ict_indicators = [ind for ind in data.get('indicators', []) if ind.get('category') == 'ict']
                
                print(f"📊 ICT 지표 개수: {len(ict_indicators)}")
                for indicator in ict_indicators:
                    print(f"  - {indicator['name']} ({indicator['id']})")
                    
                if len(ict_indicators) >= 5:
                    print("✅ ICT 지표들이 정상적으로 구현되어 있습니다!")
                else:
                    print("⚠️ ICT 지표가 부족합니다.")
            else:
                print("❌ ICT 카테고리를 찾을 수 없습니다.")
                
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 서버가 실행되지 않았습니다. 먼저 서버를 시작하세요.")
        print("   python -m uvicorn api.main:app --reload")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_ict_indicators()