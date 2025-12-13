#!/usr/bin/env python3
"""
전략 등록 및 백테스트 테스트
"""
import sys
import os
sys.path.append(os.getcwd())

def test_strategy_registration():
    """전략 등록 및 백테스트 테스트"""
    
    print("🔧 전략 등록 및 백테스트 테스트")
    print("=" * 50)
    
    try:
        # 1. 전략 레지스트리 임포트
        from core.strategy.registry import StrategyRegistry
        
        print("1️⃣ 전략 자동 탐색...")
        
        # 전략 자동 탐색
        StrategyRegistry.auto_discover("core.strategy.examples")
        
        # 등록된 전략 확인
        strategies = StrategyRegistry.list_strategies()
        print(f"📋 등록된 전략: {len(strategies)}개")
        
        for strategy_name in strategies:
            metadata = StrategyRegistry.get_metadata(strategy_name)
            print(f"  - {strategy_name}: {metadata.description}")
        
        if not strategies:
            print("⚠️ 등록된 전략이 없습니다. 수동 등록을 시도합니다.")
            
            # 수동 등록
            from core.strategy.examples.ma_cross import MACrossStrategy
            
            StrategyRegistry.register(
                name="MACrossStrategy",
                strategy_class=MACrossStrategy,
                description="이동평균 교차 전략",
                author="LS HTS Team",
                version="1.0.0"
            )
            
            strategies = StrategyRegistry.list_strategies()
            print(f"📋 수동 등록 후: {len(strategies)}개")
        
        # 2. 백테스트 실행 테스트
        print("\n2️⃣ 백테스트 실행 테스트...")
        
        import requests
        
        # 간단한 백테스트 요청
        backtest_request = {
            "strategy_name": "MACrossStrategy",
            "symbol": "005930",  # 삼성전자
            "start_date": "2025-11-01",
            "end_date": "2025-11-30", 
            "initial_capital": 10000000,
            "interval": "1d",
            "parameters": {
                "short_period": 5,
                "long_period": 20,
                "position_size": 0.1
            }
        }
        
        print(f"📊 백테스트 요청: {backtest_request['strategy_name']}")
        print(f"   종목: {backtest_request['symbol']}")
        print(f"   기간: {backtest_request['start_date']} ~ {backtest_request['end_date']}")
        
        response = requests.post(
            'http://localhost:8000/api/backtest/run',
            json=backtest_request,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            backtest_id = result.get('backtest_id')
            
            print(f"✅ 백테스트 실행 성공: ID {backtest_id}")
            
            # 결과 조회
            import time
            time.sleep(2)
            
            detail_response = requests.get(f'http://localhost:8000/api/backtest/results/{backtest_id}')
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                
                total_return = detail_data.get('total_return', 0)
                mdd = detail_data.get('mdd', 0)
                sharpe_ratio = detail_data.get('sharpe_ratio', 0)
                win_rate = detail_data.get('win_rate', 0)
                total_trades = detail_data.get('total_trades', 0)
                
                equity_curve = detail_data.get('equity_curve', [])
                initial_capital = detail_data.get('initial_capital', 10000000)
                
                print(f"\n📈 백테스트 결과:")
                print(f"  총 수익률: {total_return:.2f}%")
                print(f"  MDD: {mdd:.2f}%")
                print(f"  샤프 비율: {sharpe_ratio:.2f}")
                print(f"  승률: {win_rate:.1f}%")
                print(f"  총 거래: {total_trades}회")
                
                if equity_curve:
                    final_equity = equity_curve[-1]
                    min_equity = min(equity_curve)
                    max_equity = max(equity_curve)
                    
                    print(f"  초기 자산: {initial_capital:,.0f}원")
                    print(f"  최종 자산: {final_equity:,.0f}원")
                    print(f"  최고 자산: {max_equity:,.0f}원")
                    print(f"  최저 자산: {min_equity:,.0f}원")
                    
                    # 🔍 안전성 검증
                    print(f"\n🔍 안전성 검증:")
                    
                    if min_equity < 0:
                        print("  🚨 마이너스 자산 발생! - 수정된 엔진 적용 필요")
                    else:
                        print("  ✅ 마이너스 자산 방지 성공")
                    
                    # MDD 검증
                    calculated_mdd = 0
                    peak = equity_curve[0]
                    for equity in equity_curve:
                        if equity > peak:
                            peak = equity
                        drawdown = (peak - equity) / peak * 100 if peak > 0 else 0
                        calculated_mdd = max(calculated_mdd, drawdown)
                    
                    print(f"  MDD 검증: 계산값 {calculated_mdd:.2f}% vs 보고값 {mdd:.2f}%")
                    
                    if abs(calculated_mdd - mdd) < 0.1:
                        print("  ✅ MDD 계산 정확")
                    else:
                        print("  ⚠️ MDD 계산 불일치")
                    
                    # 수익률 검증
                    calculated_return = (final_equity - initial_capital) / initial_capital * 100
                    print(f"  수익률 검증: 계산값 {calculated_return:.2f}% vs 보고값 {total_return:.2f}%")
                    
                    if abs(calculated_return - total_return) < 0.01:
                        print("  ✅ 수익률 계산 정확")
                    else:
                        print("  ⚠️ 수익률 계산 불일치")
                
                print(f"\n🎯 종합 평가:")
                if min_equity >= 0 and abs(calculated_mdd - mdd) < 0.1:
                    print("  ✅ 수정된 백테스트 엔진이 정상 작동합니다!")
                else:
                    print("  ❌ 백테스트 엔진에 여전히 문제가 있습니다.")
            
            else:
                print(f"❌ 결과 조회 실패: {detail_response.status_code}")
        
        else:
            print(f"❌ 백테스트 실행 실패: {response.status_code}")
            print(f"응답: {response.text}")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_strategy_registration()