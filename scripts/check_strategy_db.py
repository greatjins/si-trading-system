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
        # 모든 전략 조회
        all_strategies = db.query(StrategyBuilderModel).all()
        
        if not all_strategies:
            print("[INFO] No strategies found in database")
            return
        
        print(f"[INFO] Found {len(all_strategies)} strategies:")
        for s in all_strategies:
            print(f"  ID: {s.id}, Name: {s.name}, Active: {s.is_active}")
        
        # 전략 ID 3 조회 (없으면 첫 번째 전략 사용)
        strategy = db.query(StrategyBuilderModel).filter(
            StrategyBuilderModel.id == 3
        ).first()
        
        if not strategy:
            print("\n[INFO] Strategy ID 3 not found, checking first available strategy")
            if all_strategies:
                strategy = all_strategies[0]
                print(f"[INFO] Using strategy ID {strategy.id} instead")
            else:
                return
        
        print(f"[OK] Strategy found:")
        print(f"  ID: {strategy.id}")
        print(f"  Name: {strategy.name}")
        print(f"  Description: {strategy.description}")
        print(f"  Created: {strategy.created_at}")
        print(f"  Updated: {strategy.updated_at}")
        print(f"  Active: {strategy.is_active}")
        print(f"\n[CODE] Python code (first 50 lines):")
        print("=" * 80)
        lines = strategy.python_code.split('\n')[:50]
        for i, line in enumerate(lines, 1):
            print(f"{i:3d}: {line}")
        print("=" * 80)
        print(f"\nTotal {len(strategy.python_code.split(chr(10)))} lines")
        
        # select_universe 메서드 확인
        if 'def select_universe' in strategy.python_code:
            print("\n[OK] select_universe() method found")
        else:
            print("\n[ERROR] select_universe() method not found")
        
        # 187번째 줄 확인
        lines_all = strategy.python_code.split('\n')
        if len(lines_all) >= 187:
            print(f"\n[LINE 187] Checking around line 187:")
            for i in range(max(0, 185), min(len(lines_all), 190)):
                marker = ">>> " if i == 186 else "    "
                print(f"{marker}{i+1:3d}: {lines_all[i]}")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
