"""
OHLC 데이터 구조 확인
"""
from data.repository import DataRepository
from datetime import datetime

repo = DataRepository()

# 삼성전자 데이터 조회
symbol = '005930'
start_date = datetime(2025, 8, 14)
end_date = datetime(2025, 8, 14)

print(f"📊 {symbol} OHLC 데이터 조회")
print(f"기간: {start_date.date()} ~ {end_date.date()}")

ohlc_data = repo.get_ohlc(
    symbol=symbol,
    interval='1d',
    start_date=start_date,
    end_date=end_date
)

print(f"\n타입: {type(ohlc_data)}")

if hasattr(ohlc_data, 'empty'):
    print(f"비어있음: {ohlc_data.empty}")
    if not ohlc_data.empty:
        print(f"\n컬럼: {list(ohlc_data.columns)}")
        print(f"인덱스 타입: {type(ohlc_data.index)}")
        print(f"인덱스 이름: {ohlc_data.index.name}")
        print(f"\n첫 5개 행:")
        print(ohlc_data.head())
elif isinstance(ohlc_data, list):
    print(f"길이: {len(ohlc_data)}")
    if len(ohlc_data) > 0:
        print(f"\n첫 번째 항목:")
        print(ohlc_data[0])
