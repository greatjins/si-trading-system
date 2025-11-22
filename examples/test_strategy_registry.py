"""
전략 레지스트리 테스트
"""
import asyncio
import httpx


async def test_strategy_registry():
    """전략 레지스트리 API 테스트"""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. 전략 목록 조회
        print("=== Strategy List ===")
        response = await client.get(f"{base_url}/api/strategies/list")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            strategies = response.json()
            print(f"Total Strategies: {len(strategies)}\n")
            
            for strategy in strategies:
                print(f"- {strategy['name']} (v{strategy['version']})")
                print(f"  Author: {strategy['author']}")
                print(f"  Description: {strategy['description']}\n")
        else:
            print(f"Error: {response.json()}\n")
            return
        
        # 2. 전략 상세 정보 조회
        if strategies:
            strategy_name = strategies[0]["name"]
            
            print(f"=== Strategy Detail: {strategy_name} ===")
            response = await client.get(f"{base_url}/api/strategies/{strategy_name}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                detail = response.json()
                print(f"Name: {detail['name']}")
                print(f"Version: {detail['version']}")
                print(f"Author: {detail['author']}")
                print(f"Class: {detail['class_name']}")
                print(f"Module: {detail['module']}")
                print(f"\nParameters:")
                
                for param_name, param_info in detail['parameters'].items():
                    print(f"  - {param_name}:")
                    print(f"      Type: {param_info.get('type')}")
                    print(f"      Default: {param_info.get('default')}")
                    print(f"      Description: {param_info.get('description')}")
                    
                    if 'min' in param_info:
                        print(f"      Range: [{param_info['min']}, {param_info.get('max', 'inf')}]")
                
                print()
            else:
                print(f"Error: {response.json()}\n")
        
        # 3. 전략 재탐색
        print("=== Discover Strategies ===")
        response = await client.post(f"{base_url}/api/strategies/discover")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Message: {result['message']}\n")
        else:
            print(f"Error: {response.json()}\n")
        
        # 4. 전략 재로드
        print("=== Reload Strategies ===")
        response = await client.post(f"{base_url}/api/strategies/reload")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Message: {result['message']}\n")
        else:
            print(f"Error: {response.json()}\n")


async def test_strategy_usage():
    """전략 사용 예제"""
    
    from core.strategy.registry import StrategyRegistry
    
    print("=== Strategy Registry Usage ===\n")
    
    # 전략 자동 탐색
    StrategyRegistry.auto_discover("core.strategy.examples")
    
    # 등록된 전략 목록
    strategies = StrategyRegistry.list_strategies()
    print(f"Registered Strategies: {strategies}\n")
    
    # 전략 메타데이터 조회
    for strategy_name in strategies:
        metadata = StrategyRegistry.get_metadata(strategy_name)
        print(f"Strategy: {metadata.name}")
        print(f"  Version: {metadata.version}")
        print(f"  Author: {metadata.author}")
        print(f"  Parameters: {list(metadata.parameters.keys())}\n")
    
    # 전략 인스턴스 생성
    if strategies:
        strategy_name = strategies[0]
        print(f"Creating instance of {strategy_name}...")
        
        strategy = StrategyRegistry.create_instance(
            strategy_name,
            symbol="005930",
            short_period=5,
            long_period=20,
            position_size=0.1
        )
        
        print(f"Strategy instance created: {strategy.name}")
        print(f"Parameters: {strategy.params}\n")


if __name__ == "__main__":
    print("FastAPI 서버가 http://localhost:8000 에서 실행 중이어야 합니다.")
    print("서버 시작: python -m uvicorn api.main:app --reload\n")
    
    # API 테스트
    asyncio.run(test_strategy_registry())
    
    # 직접 사용 예제
    asyncio.run(test_strategy_usage())
