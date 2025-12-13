#!/usr/bin/env python3
"""
API를 통한 모든 백테스트 데이터 삭제
"""
import requests
import time

def clear_all_backtest_data():
    """API를 통해 모든 백테스트 데이터 삭제"""
    
    print("🗑️ API를 통한 모든 백테스트 데이터 삭제")
    print("=" * 50)
    
    try:
        # 1. 현재 백테스트 목록 조회
        print("📊 현재 백테스트 목록 조회...")
        
        response = requests.get('http://localhost:8000/api/backtest/results')
        
        if response.status_code != 200:
            print(f"❌ 백테스트 목록 조회 실패: {response.status_code}")
            return
        
        backtest_list = response.json()
        total_count = len(backtest_list)
        
        print(f"📋 총 {total_count}개의 백테스트 발견")
        
        if total_count == 0:
            print("✅ 삭제할 백테스트가 없습니다.")
            return
        
        # 2. 각 백테스트 ID 수집
        backtest_ids = []
        for bt in backtest_list:
            backtest_id = bt.get('backtest_id')
            strategy_name = bt.get('strategy_name', 'N/A')
            total_return = bt.get('total_return', 0)
            
            if backtest_id:
                backtest_ids.append(backtest_id)
                print(f"  ID {backtest_id}: {strategy_name} ({total_return:.2f}%)")
        
        print(f"\n🎯 삭제 대상: {len(backtest_ids)}개")
        
        # 3. 일괄 삭제 시도 (배치 삭제 API가 있다면)
        print("\n🚀 일괄 삭제 시도...")
        
        try:
            batch_response = requests.delete(
                'http://localhost:8000/api/backtest/results/batch',
                json={"backtest_ids": backtest_ids},
                timeout=30
            )
            
            if batch_response.status_code == 200:
                print("✅ 일괄 삭제 성공!")
                
                # 삭제 확인
                check_response = requests.get('http://localhost:8000/api/backtest/results')
                if check_response.status_code == 200:
                    remaining = len(check_response.json())
                    print(f"📊 삭제 후 남은 백테스트: {remaining}개")
                
                return
            else:
                print(f"⚠️ 일괄 삭제 실패: {batch_response.status_code}")
                print("개별 삭제로 진행...")
        
        except Exception as e:
            print(f"⚠️ 일괄 삭제 오류: {e}")
            print("개별 삭제로 진행...")
        
        # 4. 개별 삭제
        print(f"\n🔄 개별 삭제 진행 ({len(backtest_ids)}개)...")
        
        deleted_count = 0
        failed_count = 0
        
        for i, backtest_id in enumerate(backtest_ids, 1):
            try:
                print(f"  [{i}/{len(backtest_ids)}] 삭제 중: ID {backtest_id}...", end="")
                
                delete_response = requests.delete(
                    f'http://localhost:8000/api/backtest/results/{backtest_id}',
                    timeout=10
                )
                
                if delete_response.status_code == 200:
                    print(" ✅")
                    deleted_count += 1
                else:
                    print(f" ❌ ({delete_response.status_code})")
                    failed_count += 1
                
                # 서버 부하 방지
                if i % 10 == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f" ❌ (오류: {e})")
                failed_count += 1
        
        # 5. 결과 요약
        print(f"\n📊 삭제 결과:")
        print(f"  성공: {deleted_count}개")
        print(f"  실패: {failed_count}개")
        print(f"  전체: {len(backtest_ids)}개")
        
        # 6. 최종 확인
        print("\n🔍 최종 확인...")
        
        final_response = requests.get('http://localhost:8000/api/backtest/results')
        if final_response.status_code == 200:
            final_list = final_response.json()
            final_count = len(final_list)
            
            print(f"📋 남은 백테스트: {final_count}개")
            
            if final_count == 0:
                print("🎉 모든 백테스트 데이터 삭제 완료!")
            else:
                print("⚠️ 일부 데이터가 남아있습니다:")
                for bt in final_list[:5]:  # 최대 5개만 표시
                    bt_id = bt.get('backtest_id')
                    strategy = bt.get('strategy_name', 'N/A')
                    print(f"  ID {bt_id}: {strategy}")
        
        print("\n📋 다음 단계:")
        print("1. 백엔드 서버 재시작 권장")
        print("2. 프론트엔드 새로고침")
        print("3. 수정된 엔진으로 새 백테스트 실행")
        
    except Exception as e:
        print(f"❌ 전체 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clear_all_backtest_data()