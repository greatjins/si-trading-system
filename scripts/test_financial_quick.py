"""재무정보 빠른 테스트"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from broker.ls.adapter import LSAdapter

async def test():
    async with LSAdapter() as adapter:
        info = await adapter.market_service.get_financial_info('005930')
        print(f'삼성전자: PER={info.per}, PBR={info.pbr}, ROE={info.roe}')
        
        info2 = await adapter.market_service.get_financial_info('000660')
        print(f'SK하이닉스: PER={info2.per}, PBR={info2.pbr}, ROE={info2.roe}')

asyncio.run(test())
