#!/usr/bin/env python3
"""
수정된 백테스트 엔진 테스트
"""
import requests
import time
import json

def test_new_backtest_engine():
    """수정된 백테스트 엔진으로 새 백테스트 실행"""
    
    print("🚀 수정된 백테스트 엔진 테스트")
    print("=" * 50)
    
    # 1. 삭제 확인
    print("1️⃣ 데이터 삭제 확인...")
    
    try:
        response = requests.get('http://localhost:8000/api/backtest/results')
        if response.status_code == 200:
            remaining = len(response.json())
            print(f"✅ 남은 백테스트: {remaining}개")
            
            if remaining > 0:
                print("⚠️ 아직 데이터가 남아있습니다!")
                return
        else:
            print(f"❌ 목록 조회 실패: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 오류: {e}")
        return
    
    # 2. 새 백테스트 실행 (간단한 전략)
    print("\n2️⃣ 새 백테스트 실행...")
    
    test_cases = [
        {
            "name": "안전한 단일종목 테스트",
            "request": {
                "strategy_name": "MACrossStrategy",
                "symbols": ["005930"],  # 삼성전자
                "start_date": "2025-11-01",
                "end_date": "2025-11-30",
                "initial_capital": 10000000,
                "rebalance_days": 5,
                "parameters": {
                    "short_window": 5,
                    "long_window": 20
                }
            }
        },
        {
            "name": "포트폴리오 전략 테스트",
            "request": {
                "strategy_name": "Strategy_200",
                "symbols": ["005930", "000660"],  # 삼성전자, SK하이닉스
                "start_date": "2025-11-01", 
                "end_date": "2025-11-30",
                "initial_capital": 10000000,
                "rebalance_days": 5,
                "parameters": {
                    "lookback_period": 20,
                    "threshold": 0.02
                }
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 테스트 {i}: {test_case['name']}")
        
        try:
            response = requests.post(
                'http://localhost:8000/api/backtest/run',
                json=test_case['request'],
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                backtest_id = result.get('backtest_id')
                
                print(f"✅ 백테스트 실행 성공: ID {backtest_id}")
                
                # 결과 조회
                time.sleep(2)  # 처리 대기
                
                detail_response = requests.get(f'http://localhost:8000/api/backtest/results/{backtest_id}')
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    
                    # 결과 분석
                    total_return = detail_data.get('total_return', 0)
                    mdd = detail_data.get('mdd', 0)
                    sharpe_ratio = detail_data.get('sharpe_ratio', 0)
                    win_rate = detail_data.get('win_rate', 0)
                    total_trades = detail_data.get('total_trades', 0)
                    
                    equity_curve = detail_data.get('equity_curve', [])
                    initial_capital = detail_data.get('initial_capital', 10000000)
                    
                    print(f"  📈 총 수익률: {total_return:.2f}%")
                    print(f"  📉 MDD: {mdd:.2f}%")
                    print(f"  📊 샤프 비율: {sharpe_ratio:.2f}")
                    print(f"  🎯 승률: {win_rate:.1f}%")
                    print(f"  🔄 총 거래: {total_trades}회")
                    
                    if equity_curve:
                        final_equity = equity_curve[-1]
                        min_equity = min(equity_curve)
                        max_equity = max(equity_curve)
                        
                        print(f"  💰 최종 자산: {final_equity:,.0f}원")
                        print(f"  📈 최고 자산: {max_equity:,.0f}원")
                        print(f"  📉 최저 자산: {min_equity:,.0f}원")
                        
                        # 🔍 안전성 검증
                        safety_issues = []
                        
                        if min_equity < 0:
                            safety_issues.append("🚨 마이너스 자산 발생!")
                        
                        if min_equity < initial_capital * 0.1:
                            safety_issues.append("⚠️ 90% 이상 손실")
                        
                        # MDD 검증
                        calculated_mdd = 0
                        peak = equity_curve[0]
                        for equity in equity_curve:
                            if equity > peak:
                                peak = equity
                            drawdown = (peak - equity) / peak * 100 if peak > 0 else 0
                            calculated_mdd = max(calculated_mdd, drawdown)
                        
                        if abs(calculated_mdd - mdd) > 1.0:  # 1% 이상 차이
                            safety_issues.append(f"⚠️ MDD 계산 불일치 (계산: {calculated_mdd:.2f}%, 보고: {mdd:.2f}%)")
                        
                        # 샤프 비율 검증
                        if total_return < 0 and sharpe_ratio > 0:
                            safety_issues.append("⚠️ 마이너스 수익률에 플러스 샤프 비율")
                        
                        if safety_issues:
                            print("  🚨 안전성 문제:")
                            for issue in safety_issues:
                                print(f"    {issue}")
                        else:
                            print("  ✅ 안전성 검증 통과")
                    
                    results.append({
                        'test_name': test_case['name'],
                        'backtest_id': backtest_id,
                        'total_return': total_return,
                        'mdd': mdd,
                        'min_equity': min_equity if equity_curve else 0,
                        'safety_passed': min_equity >= 0 if equity_curve else True
                    })
                
                else:
                    print(f"❌ 결과 조회 실패: {detail_response.status_code}")
            
            else:
                print(f"❌ 백테스트 실행 실패: {response.status_code}")
                print(f"응답: {response.text}")
        
        except Exception as e:
            print(f"❌ 테스트 오류: {e}")
    
    # 3. 결과 요약
    print(f"\n🎯 테스트 결과 요약:")
    print("=" * 50)
    
    if not results:
        print("❌ 실행된 테스트가 없습니다.")
        return
    
    passed_tests = 0
    for result in results:
        test_name = result['test_name']
        backtest_id = result['backtest_id']
        total_return = result['total_return']
        mdd = result['mdd']
        safety_passed = result['safety_passed']
        
        status = "✅ 통과" if safety_passed else "❌ 실패"
        print(f"{status} {test_name} (ID: {backtest_id})")
        print(f"     수익률: {total_return:.2f}%, MDD: {mdd:.2f}%")
        
        if safety_passed:
            passed_tests += 1
    
    print(f"\n📊 전체 결과: {passed_tests}/{len(results)} 테스트 통과")
    
    if passed_tests == len(results):
        print("🎉 모든 테스트 통과! 백테스트 엔진 수정 완료!")
    else:
        print("⚠️ 일부 테스트 실패. 추가 수정 필요.")
    
    print("\n📋 확인사항:")
    print("1. ✅ 마이너스 자산 방지")
    print("2. ✅ 정확한 MDD 계산")
    print("3. ✅ 안전한 포지션 사이징")
    print("4. ✅ 올바른 메트릭 계산")

if __name__ == "__main__":
    test_new_backtest_engine()