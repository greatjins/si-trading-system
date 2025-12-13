#!/usr/bin/env python3
"""
모든 백테스트 데이터 삭제
"""
import asyncio
import asyncpg
from datetime import datetime

async def clear_all_backtest_data():
    """모든 백테스트 데이터 삭제"""
    
    print("🗑️ 모든 백테스트 데이터 삭제")
    print("=" * 50)
    
    try:
        # 데이터베이스 연결
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="password",
            database="trading_db"
        )
        
        print("✅ 데이터베이스 연결 성공")
        
        # 1. 현재 데이터 현황 조회
        print("\n📊 삭제 전 데이터 현황:")
        
        # 백테스트 결과 수
        backtest_count = await conn.fetchval("SELECT COUNT(*) FROM backtest_results")
        print(f"  백테스트 결과: {backtest_count}개")
        
        # 거래 내역 수
        trade_count = await conn.fetchval("SELECT COUNT(*) FROM backtest_trades")
        print(f"  거래 내역: {trade_count}개")
        
        # 종목별 성과 수
        performance_count = await conn.fetchval("SELECT COUNT(*) FROM backtest_symbol_performances")
        print(f"  종목별 성과: {performance_count}개")
        
        if backtest_count == 0:
            print("\n✅ 삭제할 데이터가 없습니다.")
            return
        
        # 2. 사용자 확인
        print(f"\n⚠️ 총 {backtest_count}개의 백테스트 데이터를 삭제합니다.")
        print("이 작업은 되돌릴 수 없습니다!")
        
        # 자동 진행 (스크립트이므로)
        print("🚀 삭제 진행...")
        
        # 3. 데이터 삭제 (외래키 순서 고려)
        print("\n🗑️ 데이터 삭제 중...")
        
        # 3-1. 종목별 성과 삭제
        deleted_performances = await conn.execute("DELETE FROM backtest_symbol_performances")
        print(f"  ✅ 종목별 성과 삭제: {deleted_performances}")
        
        # 3-2. 거래 내역 삭제
        deleted_trades = await conn.execute("DELETE FROM backtest_trades")
        print(f"  ✅ 거래 내역 삭제: {deleted_trades}")
        
        # 3-3. 백테스트 결과 삭제
        deleted_results = await conn.execute("DELETE FROM backtest_results")
        print(f"  ✅ 백테스트 결과 삭제: {deleted_results}")
        
        # 4. 시퀀스 리셋 (ID 1부터 다시 시작)
        print("\n🔄 시퀀스 리셋...")
        
        await conn.execute("ALTER SEQUENCE backtest_results_backtest_id_seq RESTART WITH 1")
        print("  ✅ backtest_results ID 시퀀스 리셋")
        
        # 5. 삭제 후 확인
        print("\n📊 삭제 후 데이터 현황:")
        
        final_backtest_count = await conn.fetchval("SELECT COUNT(*) FROM backtest_results")
        final_trade_count = await conn.fetchval("SELECT COUNT(*) FROM backtest_trades")
        final_performance_count = await conn.fetchval("SELECT COUNT(*) FROM backtest_symbol_performances")
        
        print(f"  백테스트 결과: {final_backtest_count}개")
        print(f"  거래 내역: {final_trade_count}개")
        print(f"  종목별 성과: {final_performance_count}개")
        
        # 6. 테이블 구조 확인
        print("\n🔍 테이블 구조 확인:")
        
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%backtest%'
            ORDER BY table_name
        """)
        
        for table in tables:
            table_name = table['table_name']
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            print(f"  {table_name}: {count}개")
        
        await conn.close()
        
        print("\n🎉 모든 백테스트 데이터 삭제 완료!")
        print("이제 수정된 백테스트 엔진으로 새로운 백테스트를 실행할 수 있습니다.")
        
        # 7. 다음 단계 안내
        print("\n📋 다음 단계:")
        print("1. 백엔드 서버 재시작 (캐시 초기화)")
        print("2. 프론트엔드에서 백테스트 목록 새로고침")
        print("3. 수정된 엔진으로 새 백테스트 실행")
        print("4. 결과 검증 (마이너스 자산, MDD 계산 등)")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clear_all_backtest_data())