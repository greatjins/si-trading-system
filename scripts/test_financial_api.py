"""
재무정보 API 테스트
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from broker.ls.adapter import LSAdapter
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    """재무정보 API 테스트"""
    
    test_symbols = ["005930", "000660", "035720"]  # 삼성전자, SK하이닉스, 카카오
    
    async with LSAdapter() as adapter:
        for symbol in test_symbols:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Testing {symbol}")
                logger.info(f"{'='*60}")
                
                # 원본 API 응답 확인
                gicode = f"A{symbol}" if len(symbol) == 6 else symbol
                response = await adapter.market_service.client.request(
                    method="POST",
                    endpoint="/stock/investinfo",
                    data={
                        "t3320InBlock": {
                            "gicode": gicode
                        }
                    },
                    headers={
                        "content-type": "application/json; charset=utf-8",
                        "tr_cd": "t3320",
                        "tr_cont": "N",
                        "tr_cont_key": "",
                        "custtype": "P",
                        "mac_address": ""
                    }
                )
                
                print(f"\n{'='*60}")
                print(f"종목: {symbol}")
                print(f"{'='*60}")
                print(f"\nAPI 응답:")
                import json
                print(json.dumps(response, indent=2, ensure_ascii=False))
                
                financial_info = await adapter.market_service.get_financial_info(symbol)
                
                print(f"\n파싱된 재무정보:")
                print(f"  PER: {financial_info.per}")
                print(f"  PBR: {financial_info.pbr}")
                print(f"  ROE: {financial_info.roe}%")
                
                await asyncio.sleep(1.5)
                
            except Exception as e:
                logger.error(f"Failed to get financial info for {symbol}: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
