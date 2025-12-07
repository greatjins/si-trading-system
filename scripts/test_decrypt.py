"""
계좌 정보 복호화 테스트
"""
import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from api.repositories.account_repository import AccountRepository

# config.yaml 로드
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

db_config = config['database']

# 데이터베이스 연결
db_url = f"postgresql+pg8000://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

print("🔍 계좌 정보 복호화 테스트...\n")

db = SessionLocal()
try:
    repo = AccountRepository(db)
    
    # 계좌 ID 1번 조회
    account = repo.get_account(1, 2)  # account_id=1, user_id=2
    
    if account:
        print(f"✅ 계좌 발견:")
        print(f"  - ID: {account.id}")
        print(f"  - Name: {account.name}")
        print(f"  - Broker: {account.broker}")
        print(f"  - Account Type: {account.account_type}")
        print(f"  - Encrypted Account Number: {account.account_number[:50]}...")
        
        # 복호화
        credentials = repo.get_account_credentials(1, 2)
        
        if credentials:
            print(f"\n🔓 복호화된 정보:")
            print(f"  - Account Number: {credentials['account_number']}")
            print(f"  - API Key: {credentials['api_key'][:20]}...")
            print(f"  - API Secret: ****")
            
            # 검증
            if credentials['account_number'] == 'qwer1234':
                print(f"\n❌ 문제 발견: 계좌번호가 'qwer1234' (비밀번호)")
            elif credentials['account_number'] and '-' in credentials['account_number']:
                print(f"\n✅ 올바른 계좌번호 형식")
            else:
                print(f"\n⚠️ 계좌번호 형식 확인 필요")
        else:
            print("\n❌ 복호화 실패")
    else:
        print("❌ 계좌를 찾을 수 없습니다")
        
finally:
    db.close()

print("\n완료!")
