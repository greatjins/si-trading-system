#!/usr/bin/env python3
"""
전략 목록 구조 확인
"""

import asyncio
import httpx
import json

async def check_strategy_list():
    async with httpx.AsyncClient() as client:
        # 로그인
        login_response = await client.post(
            "http://localhost:8000/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass"
            }
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 전략 목록 조회
        list_response = await client.get(
            "http://localhost:8000/api/strategy-builder/list",
            headers=headers
        )
        
        print(f"Status: {list_response.status_code}")
        print(f"Response: {json.dumps(list_response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(check_strategy_list())