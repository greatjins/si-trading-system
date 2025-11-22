"""
DataCollector 테스트
"""
import pytest
from datetime import datetime, timedelta
import tempfile
import shutil

from broker.mock.adapter import MockBroker
from data.cache import RedisCache
from data.storage import FileStorage
from data.collector import DataCollector


@pytest.mark.asyncio
async def test_data_collector_with_storage():
    """파일 저장소를 사용한 데이터 수집 테스트"""
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp()
    
    try:
        broker = MockBroker()
        storage = FileStorage(base_path=temp_dir)
        collector = DataCollector(broker=broker, storage=storage)
        
        # 데이터 수집
        symbol = "005930"
        interval = "1d"
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        
        # 첫 번째 호출 - 브로커에서 가져오기
        data1 = await collector.get_ohlc(symbol, interval, start_date, end_date)
        assert len(data1) > 0
        
        # 두 번째 호출 - 저장소에서 가져오기
        data2 = await collector.get_ohlc(symbol, interval, start_date, end_date)
        assert len(data2) == len(data1)
        
        # 저장소 정보 확인
        info = collector.get_storage_info()
        assert info["symbols_count"] > 0
        assert symbol in info["symbols"]
    
    finally:
        # 임시 디렉토리 삭제
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_data_collector_without_cache():
    """캐시 없이 데이터 수집 테스트"""
    broker = MockBroker()
    collector = DataCollector(broker=broker)
    
    symbol = "005930"
    interval = "1d"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 5)
    
    # 데이터 수집 (항상 브로커에서 가져옴)
    data = await collector.get_ohlc(symbol, interval, start_date, end_date)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_get_current_price():
    """현재가 조회 테스트"""
    broker = MockBroker()
    collector = DataCollector(broker=broker)
    
    price = await collector.get_current_price("005930")
    assert price > 0


@pytest.mark.asyncio
async def test_refresh_cache():
    """캐시 새로고침 테스트"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        broker = MockBroker()
        storage = FileStorage(base_path=temp_dir)
        collector = DataCollector(broker=broker, storage=storage)
        
        symbol = "005930"
        interval = "1d"
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        
        # 캐시 새로고침
        success = await collector.refresh_cache(symbol, interval, start_date, end_date)
        assert success
    
    finally:
        shutil.rmtree(temp_dir)
