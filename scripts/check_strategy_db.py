"""
전략 DB 상태 확인 스크립트
"""
import sys
sys.path.append('.')

from data.repository import get_db_session
from data.models import StrategyBuilderModel

def main():
    db = get_db_session()
    
    try:
        # 전략 ID 3 조회
        strategy = db.query(StrategyBuilderModel).filter(
            StrategyBuilderModel.id == 3
        ).first()
        
        if not strategy:
            print("❌ 전략 ID 3을 찾을 수 없습니다")
            return
        
        print(f"✅ 전략 발견:")
        print(f"  ID: {strategy.id}")
        print(f"  이름: {strategy.name}")
        print(f"  설명: {strategy.description}")
        print(f"  생성일: {strategy.created_at}")
        print(f"  수정일: {strategy.updated_at}")
        print(f"  활성: {strategy.is_active}")
        print(f"\n📝 Python 코드 (처음 50줄):")
        print("=" * 80)
        lines = strategy.python_code.split('\n')[:50]
        for i, line in enumerate(lines, 1):
            print(f"{i:3d}: {line}")
        print("=" * 80)
        print(f"\n총 {len(strategy.python_code.split(chr(10)))}줄")
        
        # select_universe 메서드 확인
        if 'def select_universe' in strategy.python_code:
            print("\n✅ select_universe() 메서드 있음")
        else:
            print("\n❌ select_universe() 메서드 없음")
        
        # 187번째 줄 확인
        lines_all = strategy.python_code.split('\n')
        if len(lines_all) >= 187:
            print(f"\n📍 187번째 줄:")
            for i in range(max(0, 185), min(len(lines_all), 190)):
                marker = ">>> " if i == 186 else "    "
                print(f"{marker}{i+1:3d}: {lines_all[i]}")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
