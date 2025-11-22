"""
테스트 사용자 생성 스크립트
"""
from api.auth.models import UserRepository
from api.auth.security import get_password_hash

def create_test_user():
    """테스트 사용자 생성"""
    repo = UserRepository()
    
    # 기존 사용자 확인
    existing_user = repo.get_user_by_username("testuser")
    if existing_user:
        print("테스트 사용자가 이미 존재합니다.")
        return
    
    # 사용자 생성
    hashed_password = get_password_hash("testpass")
    user = repo.create_user(
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password,
        full_name="Test User",
        role="trader"
    )
    
    print(f"테스트 사용자 생성 완료: {user.username}")
    print(f"- 사용자명: testuser")
    print(f"- 비밀번호: testpass")
    print(f"- 이메일: test@example.com")

if __name__ == "__main__":
    create_test_user()
