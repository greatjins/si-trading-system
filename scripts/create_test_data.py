"""
테스트 OHLC 데이터 생성
"""
import pandas as pd
from datetime import datetime, timedelta
import random
from pathlib import Path

def generate_ohlc_data(symbol: str, days: int = 100):
    """랜덤 OHLC 데이터 생성"""
    # 시작 가격
    base_price = 70000 if symbol == "005930" else 50000
    
    data = []
    current_price = base_price
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)
        
        # 랜덤 변동
        change = random.uniform(-0.03, 0.03)
        current_price = current_price * (1 + change)
        
        open_price = current_price
        high_price = open_price * (1 + random.uniform(0, 0.02))
        low_price = open_price * (1 - random.uniform(0, 0.02))
        close_price = random.uniform(low_price, high_price)
        volume = random.randint(1000000, 10000000)
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    # 저장
    base_path = Path("data/ohlc")
    symbol_dir = base_path / symbol
    symbol_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = symbol_dir / f"{symbol}_1d.parquet"
    df.to_parquet(file_path)
    
    print(f"✅ {symbol} 데이터 {len(df)}개 생성 완료 -> {file_path}")

if __name__ == "__main__":
    # 삼성전자
    generate_ohlc_data("005930", 100)
    
    # SK하이닉스
    generate_ohlc_data("000660", 100)
    
    print("\n테스트 데이터 생성 완료!")
