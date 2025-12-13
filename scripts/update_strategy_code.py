"""
기존 전략의 python_code를 재생성하는 스크립트
"""
from data.repository import get_db_session
from data.models import StrategyBuilderModel
from api.routes.strategy_builder import generate_strategy_code, StrategyBuilderRequest

def update_strategy_code(strategy_id: int):
    """전략 코드 재생성"""
    db = get_db_session()
    
    try:
        # 전략 조회
        strategy = db.query(StrategyBuilderModel).filter(
            StrategyBuilderModel.id == strategy_id
        ).first()
        
        if not strategy:
            print(f"❌ 전략 ID {strategy_id}를 찾을 수 없습니다")
            return
        
        print(f"✅ 전략 발견: {strategy.name}")
        print(f"   생성일: {strategy.created_at}")
        
        # config에서 StrategyBuilderRequest 생성
        config = strategy.config
        request = StrategyBuilderRequest(**config)
        
        # 새 코드 생성
        print("🔄 코드 재생성 중...")
        new_code = generate_strategy_code(request)
        
        # 업데이트
        strategy.python_code = new_code
        db.commit()
        
        print(f"✅ 코드 업데이트 완료!")
        print(f"   코드 길이: {len(new_code)} 문자")
        
        # select_universe 메서드 확인
        if 'def select_universe' in new_code:
            print("✅ select_universe 메서드 포함됨 (포트폴리오 전략)")
        else:
            print("ℹ️  select_universe 메서드 없음 (단일 종목 전략)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("사용법: python scripts/update_strategy_code.py <strategy_id>")
        print("예: python scripts/update_strategy_code.py 3")
        sys.exit(1)
    
    strategy_id = int(sys.argv[1])
    update_strategy_code(strategy_id)
