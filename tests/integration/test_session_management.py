#!/usr/bin/env python3
"""
세션 관리 개선사항 테스트
"""
import requests
import time
import json

def test_session_management():
    """세션 관리 개선사항 테스트"""
    
    print("🔐 세션 관리 개선사항 테스트")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # 1. 로그인 테스트
    print("1️⃣ 로그인 테스트...")
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            
            print(f"✅ 로그인 성공")
            print(f"  - 액세스 토큰: {access_token[:20]}...")
            print(f"  - 리프레시 토큰: {refresh_token[:20] if refresh_token else 'None'}...")
            
            # 2. 토큰 검증 테스트
            print("\n2️⃣ 토큰 검증 테스트...")
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            me_response = requests.get(f"{base_url}/api/auth/me", headers=headers)
            
            if me_response.status_code == 200:
                user_data = me_response.json()
                print(f"✅ 토큰 검증 성공")
                print(f"  - 사용자: {user_data.get('username')}")
                print(f"  - 이메일: {user_data.get('email')}")
                print(f"  - 역할: {user_data.get('role')}")
            else:
                print(f"❌ 토큰 검증 실패: {me_response.status_code}")
            
            # 3. 보호된 리소스 접근 테스트
            print("\n3️⃣ 보호된 리소스 접근 테스트...")
            
            backtest_response = requests.get(f"{base_url}/api/backtest/results", headers=headers)
            
            if backtest_response.status_code == 200:
                backtest_data = backtest_response.json()
                print(f"✅ 보호된 리소스 접근 성공")
                print(f"  - 백테스트 결과: {len(backtest_data)}개")
            else:
                print(f"❌ 보호된 리소스 접근 실패: {backtest_response.status_code}")
            
            # 4. 토큰 갱신 테스트 (refresh_token이 있는 경우)
            if refresh_token:
                print("\n4️⃣ 토큰 갱신 테스트...")
                
                refresh_response = requests.post(f"{base_url}/api/auth/refresh", json={
                    "refresh_token": refresh_token
                })
                
                if refresh_response.status_code == 200:
                    new_token_data = refresh_response.json()
                    new_access_token = new_token_data.get('access_token')
                    
                    print(f"✅ 토큰 갱신 성공")
                    print(f"  - 새 액세스 토큰: {new_access_token[:20]}...")
                    
                    # 새 토큰으로 API 호출 테스트
                    new_headers = {"Authorization": f"Bearer {new_access_token}"}
                    test_response = requests.get(f"{base_url}/api/auth/me", headers=new_headers)
                    
                    if test_response.status_code == 200:
                        print("✅ 새 토큰으로 API 호출 성공")
                    else:
                        print(f"❌ 새 토큰으로 API 호출 실패: {test_response.status_code}")
                else:
                    print(f"❌ 토큰 갱신 실패: {refresh_response.status_code}")
            
            # 5. 로그아웃 테스트
            print("\n5️⃣ 로그아웃 테스트...")
            
            logout_response = requests.post(f"{base_url}/api/auth/logout", headers=headers)
            
            if logout_response.status_code == 200:
                logout_data = logout_response.json()
                print(f"✅ 로그아웃 성공")
                print(f"  - 메시지: {logout_data.get('message')}")
                
                # 로그아웃 후 토큰 검증 (실패해야 함)
                post_logout_response = requests.get(f"{base_url}/api/auth/me", headers=headers)
                
                if post_logout_response.status_code == 401:
                    print("✅ 로그아웃 후 토큰 무효화 확인")
                else:
                    print(f"⚠️ 로그아웃 후에도 토큰이 유효함: {post_logout_response.status_code}")
            else:
                print(f"❌ 로그아웃 실패: {logout_response.status_code}")
        
        else:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            print(f"응답: {login_response.text}")
    
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
    
    # 6. 프론트엔드 세션 관리 가이드
    print(f"\n📋 프론트엔드 세션 관리 개선사항:")
    print("=" * 50)
    
    print("🔒 보안 강화:")
    print("  1. sessionStorage 사용 (브라우저 종료 시 자동 삭제)")
    print("  2. 토큰 만료 시간 검증 (30분)")
    print("  3. 주기적 토큰 유효성 검사 (1분마다)")
    print("  4. 사용자 활동 모니터링 (마우스, 키보드 이벤트)")
    
    print("\n⏰ 자동 로그아웃:")
    print("  1. 30분 비활성 시 자동 로그아웃")
    print("  2. 브라우저 종료 시 세션 정리")
    print("  3. 탭 포커스 변경 시 토큰 재검증")
    
    print("\n🛡️ 보안 개선:")
    print("  1. localStorage → sessionStorage 변경")
    print("  2. XSS 공격 방지")
    print("  3. 토큰 자동 갱신")
    print("  4. 서버 측 토큰 검증")
    
    print(f"\n🧪 테스트 방법:")
    print("  1. 로그인 후 브라우저 종료 → 재접속 시 로그인 페이지")
    print("  2. 30분 방치 → 자동 로그아웃")
    print("  3. 다른 탭에서 로그아웃 → 모든 탭에서 로그아웃")
    print("  4. 개발자 도구에서 sessionStorage 확인")

if __name__ == "__main__":
    test_session_management()