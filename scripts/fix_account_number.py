"""
계좌번호 수정 스크립트
"""
import yaml
from sqlalchemy import create_engine
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

print("🔧 계좌번호 수정 중...\n")

# config에서 올바른 계좌번호 가져오기
correct_account_number = config.get('ls', {}).get('account_id', '555044505-01')
print(f"올바른 계좌번호: {correct_account_number}")

db = SessionLocal()
try:
    repo = AccountRepository(db)
    
    # 계좌 ID 1번 조회
    account = repo.get_account(1, 2)  # account_id=1, user_id=2
    
    if account:
        print(f"\n현재 계좌 정보:")
        print(f"  - ID: {account.id}")
        print(f"  - Name: {account.name}")
        
        # 현재 복호화된 값
        credentials = repo.get_account_credentials(1, 2)
        print(f"  - 현재 계좌번호: {credentials['account_number']}")
        
        # 수정
        print(f"\n수정 중...")
        account.account_number = repo._encrypt(correct_account_number)
        db.commit()
        
        # 검증
        credentials = repo.get_account_credentials(1, 2)
        print(f"\n✅ 수정 완료!")
        print(f"  - 새 계좌번호: {credentials['account_number']}")
        
        if credentials['account_number'] == correct_account_number:
            print(f"\n✅ 검증 성공: 계좌번호가 올바르게 저장되었습니다!")
        else:
            print(f"\n❌ 검증 실패: 계좌번호가 일치하지 않습니다")
    else:
        print("❌ 계좌를 찾을 수 없습니다")
        
finally:
    db.close()

print("\n완료!")
