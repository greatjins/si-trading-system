#!/usr/bin/env python3
"""
사용 가능한 데이터 확인
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from data.repository import DataRepository, get_db_session
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def check_data():
    """사용 가능한 데이터 확인"""
    
    print("=== 사용 가능한 데이터 확인 ===")
    
    db = get_db_session()
    repo = DataRepository(db)
    
    try:
        # 1. 전체 데이터 조회 (날짜 범위 없이)
        print("1. 삼성전자(005930) 전체 데이터 조회...")
        ohlc_df = repo.get_ohlc("005930", "1d")
        
        if not ohlc_df.empty:
            print(f"   데이터 개수: {len(ohlc_df)}개")
            print(f"   시작일: {ohlc_df.index[0]}")
            print(f"   종료일: {ohlc_df.index[-1]}")
            print(f"   컬럼: {list(ohlc_df.columns)}")
            
            # 최근 5개 데이터 출력
            print("\n   최근 5개 데이터:")
            print(ohlc_df.tail().to_string())
            
            # 리스트 형태로도 조회
            print("\n2. 리스트 형태로 조회...")
            ohlc_list = repo.get_ohlc_as_list("005930", "1d")
            print(f"   리스트 개수: {len(ohlc_list)}개")
            
            if ohlc_list:
                print(f"   첫 번째: {ohlc_list[0]}")
                print(f"   마지막: {ohlc_list[-1]}")
                
                # 특정 기간 조회 테스트
                print("\n3. 특정 기간 조회 테스트...")
                start_date = datetime(2024, 1, 1)
                end_date = datetime(2024, 12, 31)
                
                period_data = repo.get_ohlc_as_list("005930", "1d", start_date, end_date)
                print(f"   2024년 데이터: {len(period_data)}개")
                
                if period_data:
                    print(f"   첫 번째: {period_data[0]}")
                    print(f"   마지막: {period_data[-1]}")
                    return period_data
                else:
                    # 2023년 시도
                    start_date = datetime(2023, 1, 1)
                    end_date = datetime(2023, 12, 31)
                    
                    period_data = repo.get_ohlc_as_list("005930", "1d", start_date, end_date)
                    print(f"   2023년 데이터: {len(period_data)}개")
                    
                    if period_data:
                        return period_data
        else:
            print("   ❌ 데이터가 없습니다.")
            
        return None
        
    except Exception as e:
        logger.error(f"데이터 확인 중 오류: {e}", exc_info=True)
        return None
    
    finally:
        db.close()


async def main():
    """메인 함수"""
    data = await check_data()
    
    if data:
        print(f"\n✅ 사용 가능한 데이터 발견: {len(data)}개")
    else:
        print(f"\n❌ 사용 가능한 데이터 없음")


if __name__ == "__main__":
    asyncio.run(main())