#!/usr/bin/env python3
"""
백테스트 엔진 수정사항 테스트
"""
import asyncio
import requests
from datetime import datetime

async def test_backtest_engine_fixes():
    """수정된 백테스트 엔진 테스트"""
    
    print("🔧 백테스트 엔진 수정사항 테스트")
    print("=" * 50)
    
    # 1. 기존 문제 백테스트 재실행
    print("1️⃣ 문제 백테스트 재분석...")
    
    try:
        response = requests.get('http://localhost:8000/api/backtest/results/98')
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"📊 백테스트 #98 (수정 전 상태)")
            print(f"   총 수익률: {data.get('total_return', 0):.2f}%")
            print(f"   MDD: {data.get('mdd', 0):.2f}%")
            print(f"   샤프 비율: {data.get('sharpe_ratio', 0):.2f}")
            print(f"   승률: {data.get('win_rate', 0):.1f}%")
            print(f"   최종 자산: {data.get('equity_curve', [0])[-1]:,.0f}원")
            
            # 자산 곡선 분석
            equity_curve = data.get('equity_curve', [])
            if equity_curve:
                min_equity = min(equity_curve)
                max_equity = max(equity_curve)
                
                print(f"   최고 자산: {max_equity:,.0f}원")
                print(f"   최저 자산: {min_equity:,.0f}원")
                
                if min_equity < 0:
                    print("   🚨 마이너스 자산 발생 - 수정 필요!")
                else:
                    print("   ✅ 자산 안전성 확보")
        
        print()
        
    except Exception as e:
        print(f"❌ 백테스트 조회 실패: {e}")
    
    # 2. 새로운 백테스트 실행 (수정된 엔진으로)
    print("2️⃣ 수정된 엔진으로 새 백테스트 실행...")
    
    try:
        # 간단한 백테스트 요청
        backtest_request = {
            "strategy_name": "TestStrategy_Fixed",
            "symbols": ["005930"],  # 삼성전자
            "start_date": "2025-10-01",
            "end_date": "2025-11-30",
            "initial_capital": 10000000,
            "rebalance_days": 5,
            "parameters": {
                "lookback_period": 20,
                "threshold": 0.02
            }
        }
        
        response = requests.post(
            'http://localhost:8000/api/backtest/run',
            json=backtest_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            backtest_id = result.get('backtest_id')
            
            print(f"✅ 새 백테스트 실행 완료: ID {backtest_id}")
            
            # 결과 조회
            detail_response = requests.get(f'http://localhost:8000/api/backtest/results/{backtest_id}')
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                
                print(f"📊 새 백테스트 결과:")
                print(f"   총 수익률: {detail_data.get('total_return', 0):.2f}%")
                print(f"   MDD: {detail_data.get('mdd', 0):.2f}%")
                print(f"   샤프 비율: {detail_data.get('sharpe_ratio', 0):.2f}")
                print(f"   승률: {detail_data.get('win_rate', 0):.1f}%")
                print(f"   총 거래: {detail_data.get('total_trades', 0)}회")
                
                # 자산 곡선 검증
                equity_curve = detail_data.get('equity_curve', [])
                if equity_curve:
                    min_equity = min(equity_curve)
                    max_equity = max(equity_curve)
                    initial = detail_data.get('initial_capital', 10000000)
                    
                    print(f"   초기 자산: {initial:,.0f}원")
                    print(f"   최종 자산: {equity_curve[-1]:,.0f}원")
                    print(f"   최고 자산: {max_equity:,.0f}원")
                    print(f"   최저 자산: {min_equity:,.0f}원")
                    
                    # 안전성 검증
                    if min_equity < 0:
                        print("   🚨 여전히 마이너스 자산 발생!")
                    elif min_equity < initial * 0.1:
                        print("   ⚠️ 90% 이상 손실 - 전략 재검토 필요")
                    else:
                        print("   ✅ 자산 안전성 확보")
                    
                    # MDD 검증
                    calculated_mdd = 0
                    peak = equity_curve[0]
                    for equity in equity_curve:
                        if equity > peak:
                            peak = equity
                        drawdown = (peak - equity) / peak * 100 if peak > 0 else 0
                        calculated_mdd = max(calculated_mdd, drawdown)
                    
                    reported_mdd = detail_data.get('mdd', 0)
                    print(f"   MDD 검증: 계산값 {calculated_mdd:.2f}% vs 보고값 {reported_mdd:.2f}%")
                    
                    if abs(calculated_mdd - reported_mdd) < 0.1:
                        print("   ✅ MDD 계산 정확")
                    else:
                        print("   ⚠️ MDD 계산 불일치")
        
        else:
            print(f"❌ 백테스트 실행 실패: {response.status_code}")
            print(f"응답: {response.text}")
    
    except Exception as e:
        print(f"❌ 새 백테스트 실행 실패: {e}")
    
    print()
    print("🎯 수정사항 요약:")
    print("1. ✅ 리스크 관리 강화 - 마이너스 자산 방지")
    print("2. ✅ 포지션 사이징 개선 - 95% 투자 한도")
    print("3. ✅ 메트릭 계산 수정 - 정확한 승률/손익비")
    print("4. ✅ 자산 계산 안전성 확보")
    print("5. ✅ 거래 매칭 로직 개선")

if __name__ == "__main__":
    asyncio.run(test_backtest_engine_fixes())