"""
qrycnt만 사용한 일봉 조회 테스트
"""
import asyncio
from datetime import datetime
from broker.ls.adapter import LSAdapter
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_qrycnt_only():
    """qrycnt만 사용한 조회 테스트"""
    
    symbol = "005930"  # 삼성전자
    qrycnt = 300  # 300개 요청
    
    logger.info(f"Testing qrycnt-only OHLC for {symbol}")
    logger.info(f"Requesting {qrycnt} records")
    
    async with LSAdapter() as adapter:
        response = await adapter.client.request(
            method="POST",
            endpoint="/stock/chart",
            data={
                "t8451InBlock": {
                    "shcode": symbol,
                    "gubun": "2",  # 2:일
                    "qrycnt": qrycnt,
                    "sdate": "",  # 빈 문자열
                    "edate": "",  # 빈 문자열
                    "cts_date": "",
                    "comp_yn": "N",
                    "sujung": "Y",
                    "exchgubun": "U"
                }
            },
            headers={
                "tr_id": "t8451",
                "tr_cont": "N",
                "custtype": "P"
            }
        )
        
        items = response.get("t8451OutBlock1", [])
        logger.info(f"Received {len(items)} records")
        
        if items:
            first_date = items[0].get("date", "")
            last_date = items[-1].get("date", "")
            logger.info(f"First record: {first_date}")
            logger.info(f"Last record: {last_date}")
            
            # 연속조회 키 확인
            out_block = response.get("t8451OutBlock", {})
            cts_date = out_block.get("cts_date", "")
            logger.info(f"cts_date: '{cts_date}'")


if __name__ == "__main__":
    asyncio.run(test_qrycnt_only())
