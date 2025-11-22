"""
인증 시스템 테스트 예제
"""
import asyncio
import httpx


async def test_auth():
    """인증 API 테스트"""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. 사용자 등록
        print("=== User Registration ===")
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        response = await client.post(f"{base_url}/api/auth/register", json=register_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user = response.json()
            print(f"User created: {user['username']} (ID: {user['id']})\n")
        else:
            print(f"Error: {response.json()}\n")
        
        # 2. 로그인
        print("=== Login ===")
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        response = await client.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Login failed: {response.json()}")
            return
        
        tokens = response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token")
        print(f"Access Token: {access_token[:50]}...")
        print(f"Refresh Token: {refresh_token[:50] if refresh_token else 'None'}...\n")
        
        # 3. 현재 사용자 정보 조회 (인증 필요)
        print("=== Get Current User ===")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(f"{base_url}/api/auth/me", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user = response.json()
            print(f"Current User: {user['username']}")
            print(f"Email: {user['email']}")
            print(f"Role: {user['role']}\n")
        else:
            print(f"Error: {response.json()}\n")
        
        # 4. 보호된 엔드포인트 접근 (계좌 정보)
        print("=== Access Protected Endpoint (Account) ===")
        response = await client.get(f"{base_url}/api/account/summary", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            account = response.json()
            print(f"Account Balance: {account['balance']:,.0f}원\n")
        else:
            print(f"Error: {response.json()}\n")
        
        # 5. 토큰 없이 접근 시도 (실패 예상)
        print("=== Access Without Token (Should Fail) ===")
        response = await client.get(f"{base_url}/api/account/summary")
        print(f"Status: {response.status_code}")
        print(f"Error: {response.json()}\n")
        
        # 6. 토큰 갱신
        if refresh_token:
            print("=== Refresh Token ===")
            response = await client.post(
                f"{base_url}/api/auth/refresh",
                params={"refresh_token": refresh_token}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                new_tokens = response.json()
                new_access_token = new_tokens["access_token"]
                print(f"New Access Token: {new_access_token[:50]}...\n")
            else:
                print(f"Error: {response.json()}\n")
        
        # 7. 로그아웃
        print("=== Logout ===")
        response = await client.post(f"{base_url}/api/auth/logout", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Message: {result['message']}\n")


if __name__ == "__main__":
    print("FastAPI 서버가 http://localhost:8000 에서 실행 중이어야 합니다.")
    print("서버 시작: python -m uvicorn api.main:app --reload\n")
    
    asyncio.run(test_auth())
