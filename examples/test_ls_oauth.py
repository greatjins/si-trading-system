"""
LS증권 OAuth 인증 테스트
"""
import asyncio
from broker.ls.oauth import LSOAuth, LSTokenManager
from broker.ls.client import LSClient


async def test_oauth_basic():
    """기본 OAuth 테스트"""
    print("=" * 80)
    print("LS증권 OAuth 기본 테스트")
    print("=" * 80)
    print()
    
    # config.yaml에 설정 필요 (LS증권 용어 사용):
    # ls:
    #   appkey: "YOUR_APPKEY"
    #   appsecretkey: "YOUR_APPSECRETKEY"
    #   account_id: "YOUR_ACCOUNT_ID"
    
    try:
        # 1. OAuth 인스턴스 생성
        print("1. OAuth 인스턴스 생성...")
        oauth = LSOAuth()
        print("   ✅ OAuth 인스턴스 생성 완료")
        print()
        
        # 2. 접근 토큰 발급
        print("2. 접근 토큰 발급...")
        token_info = await oauth.get_access_token()
        print(f"   ✅ 접근 토큰: {token_info['access_token'][:30]}...")
        print(f"   ✅ 토큰 타입: {token_info['token_type']}")
        print(f"   ✅ 만료 시간: {token_info['expires_in']}초")
        print(f"   ✅ 만료 일시: {token_info['expires_at']}")
        print()
        
        # 3. 토큰 유효성 확인
        print("3. 토큰 유효성 확인...")
        is_valid = oauth.is_token_valid()
        print(f"   ✅ 토큰 유효: {is_valid}")
        print()
        
        # 4. 인증 헤더 생성
        print("4. 인증 헤더 생성...")
        headers = oauth.get_auth_headers()
        print(f"   ✅ Authorization: {headers['Authorization'][:50]}...")
        print()
        
        # 5. 토큰 갱신 (선택)
        if token_info.get('refresh_token'):
            print("5. 토큰 갱신 테스트...")
            try:
                new_token_info = await oauth.refresh_access_token()
                print(f"   ✅ 새 접근 토큰: {new_token_info['access_token'][:30]}...")
                print()
            except Exception as e:
                print(f"   ⚠️  토큰 갱신 실패 (예상됨): {e}")
                print()
        
        # 6. 토큰 폐기
        print("6. 토큰 폐기...")
        revoked = await oauth.revoke_token()
        print(f"   ✅ 토큰 폐기: {revoked}")
        print()
        
        # 7. 클라이언트 종료
        await oauth.close()
        print("✅ OAuth 테스트 완료")
        print()
    
    except Exception as e:
        print(f"❌ OAuth 테스트 실패: {e}")
        print()


async def test_token_manager():
    """토큰 매니저 테스트 (파일 기반 영속성)"""
    print("=" * 80)
    print("LS증권 토큰 매니저 테스트")
    print("=" * 80)
    print()
    
    try:
        # 1. 토큰 매니저 초기화
        print("1. 토큰 매니저 초기화...")
        manager = LSTokenManager(token_file="data/ls_token_test.json")
        oauth = await manager.initialize()
        print("   ✅ 토큰 매니저 초기화 완료")
        print(f"   ✅ 접근 토큰: {oauth.access_token[:30]}...")
        print()
        
        # 2. 토큰 저장
        print("2. 토큰 파일 저장...")
        saved = await manager.save_token()
        print(f"   ✅ 토큰 저장: {saved}")
        print()
        
        # 3. 유효한 토큰 획득 (자동 갱신)
        print("3. 유효한 토큰 획득...")
        valid_token = await manager.get_valid_token()
        print(f"   ✅ 유효한 토큰: {valid_token[:30]}...")
        print()
        
        # 4. 클라이언트 종료
        await oauth.close()
        print("✅ 토큰 매니저 테스트 완료")
        print()
    
    except Exception as e:
        print(f"❌ 토큰 매니저 테스트 실패: {e}")
        print()


async def test_ls_client():
    """LSClient 테스트"""
    print("=" * 80)
    print("LS증권 클라이언트 테스트")
    print("=" * 80)
    print()
    
    try:
        # 1. 클라이언트 생성 및 연결
        print("1. LSClient 생성 및 연결...")
        async with LSClient() as client:
            print("   ✅ 클라이언트 연결 완료")
            print(f"   ✅ 계좌번호: {client.account_id}")
            print()
            
            # 2. API 요청 예제 (실제 엔드포인트는 LS증권 문서 참고)
            print("2. API 요청 테스트...")
            try:
                # 예: 계좌 잔고 조회
                # response = await client.get("/v1/account/balance")
                # print(f"   ✅ 잔고: {response}")
                print("   ℹ️  실제 API 엔드포인트 구현 필요")
                print()
            except Exception as e:
                print(f"   ⚠️  API 요청 실패 (예상됨): {e}")
                print()
        
        print("✅ LSClient 테스트 완료")
        print()
    
    except Exception as e:
        print(f"❌ LSClient 테스트 실패: {e}")
        print()


async def test_context_manager():
    """컨텍스트 매니저 테스트"""
    print("=" * 80)
    print("OAuth 컨텍스트 매니저 테스트")
    print("=" * 80)
    print()
    
    try:
        # async with 사용
        print("1. async with LSOAuth() 사용...")
        async with LSOAuth() as oauth:
            print(f"   ✅ 자동 토큰 발급: {oauth.access_token[:30]}...")
            print(f"   ✅ 토큰 유효: {oauth.is_token_valid()}")
        
        print("   ✅ 자동 종료 완료")
        print()
        print("✅ 컨텍스트 매니저 테스트 완료")
        print()
    
    except Exception as e:
        print(f"❌ 컨텍스트 매니저 테스트 실패: {e}")
        print()


async def main():
    """메인 함수"""
    print("\n")
    print("🔐 LS증권 OAuth 인증 테스트")
    print()
    print("⚠️  주의: config.yaml에 LS증권 API 키 설정이 필요합니다:")
    print()
    print("ls:")
    print("  appkey: \"YOUR_APPKEY\"")
    print("  appsecretkey: \"YOUR_APPSECRETKEY\"")
    print("  account_id: \"YOUR_ACCOUNT_ID\"")
    print("  base_url: \"https://openapi.ls-sec.co.kr:8080\"")
    print()
    print("-" * 80)
    print()
    
    # 테스트 실행
    await test_oauth_basic()
    await test_token_manager()
    await test_ls_client()
    await test_context_manager()
    
    print("=" * 80)
    print("✅ 모든 OAuth 테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
