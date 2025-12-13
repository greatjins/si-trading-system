#!/usr/bin/env python3
"""
백테스트 목록 확인
"""

import sys
sys.path.append('.')

from data.repository import get_db_session
from data.models import BacktestResultModel
from datetime import datetime

def check_backtest_list():
    """백테스트 목록 확인"""
    
    print("🔍 백테스트 목록 확인")
    print("=" * 50)
    
    db = get_db_session()
    
    try:
        # 전체 백테스트 개수 확인
        total_count = db.query(BacktestResultModel).count()
        print(f"📊 전체 백테스트 개수: {total_count}개")
        
        # 최근 백테스트 목록 조회 (최대 20개)
        recent_backtests = db.query(BacktestResultModel).order_by(
            BacktestResultModel.created_at.desc()
        ).limit(20).all()
        
        print(f"\n📋 최근 백테스트 목록 (최대 20개):")
        print("-" * 80)
        print(f"{'ID':<5} {'전략명':<20} {'수익률':<10} {'거래수':<8} {'생성일시':<20}")
        print("-" * 80)
        
        for bt in recent_backtests:
            created_at = bt.created_at.strftime("%Y-%m-%d %H:%M") if bt.created_at else "N/A"
            return_pct = f"{bt.total_return*100:.2f}%" if bt.total_return else "N/A"
            
            print(f"{bt.id:<5} {bt.strategy_name[:18]:<20} {return_pct:<10} {bt.total_trades:<8} {created_at:<20}")
        
        # 전략별 개수 확인
        print(f"\n📈 전략별 백테스트 개수:")
        from sqlalchemy import func
        
        strategy_counts = db.query(
            BacktestResultModel.strategy_name,
            func.count(BacktestResultModel.id).label('count')
        ).group_by(BacktestResultModel.strategy_name).all()
        
        for strategy_name, count in strategy_counts:
            print(f"  - {strategy_name}: {count}개")
        
        # 날짜별 개수 확인
        print(f"\n📅 최근 7일간 백테스트 생성 현황:")
        from datetime import datetime, timedelta
        
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            daily_count = db.query(BacktestResultModel).filter(
                func.date(BacktestResultModel.created_at) == date.date()
            ).count()
            
            if daily_count > 0:
                print(f"  - {date_str}: {daily_count}개")
    
    finally:
        db.close()

if __name__ == "__main__":
    check_backtest_list()