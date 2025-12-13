from data.repository import get_db_session
from data.models import StrategyBuilderModel

db = get_db_session()
s = db.query(StrategyBuilderModel).filter(StrategyBuilderModel.id == 3).first()
print(f'전략 이름: {s.name}')
print(f'생성일: {s.created_at}')
print(f'업데이트: {s.updated_at}')
print(f'코드 길이: {len(s.python_code)}')
print(f'select_universe 포함: {"def select_universe" in s.python_code}')

# 187번째 줄 확인
lines = s.python_code.split('\n')
if len(lines) >= 187:
    print(f'\n187번째 줄: {lines[186]}')
    print(f'186번째 줄: {lines[185]}')
    print(f'188번째 줄: {lines[187]}')

db.close()
