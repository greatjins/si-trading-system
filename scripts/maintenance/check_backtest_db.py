#!/usr/bin/env python3
"""
백테스트 결과 DB 직접 확인
"""

import sys
sys.path.append('.')

from data.repository import get_db_session
from data.models import BacktestResultModel, TradeModel
import json

def check_backtest_result(backtest_id: int = 103):
    """백테스트 결과 DB 직접 확인"""
    
    print(f"🔍 백테스트 결과 DB 직접 확인 (ID: {backtest_id})")
    print("=" * 50)
    
    db = get_db_session()
    
    try:
        # 백테스트 결과 조회
        backtest = db.query(BacktestResultModel).filter(
            BacktestResultModel.id == backtest_id
        ).first()
        
        if not backtest:
            print(f"❌ 백테스트 결과 없음 (ID: {backtest_id})")
            return
        
        print(f"✅ 백테스트 결과 발견")
        print(f"   Strategy: {backtest.strategy_name}")
        print(f"   Total Return: {backtest.total_return:.2%}")
        print(f"   Total Trades: {backtest.total_trades}")
        
        # 자산 곡선 확인
        if backtest.equity_curve:
            print(f"   Equity Curve: {len(backtest.equity_curve)}개 포인트")
            print(f"     First: {backtest.equity_curve[0]:,.0f}")
            print(f"     Last: {backtest.equity_curve[-1]:,.0f}")
        else:
            print(f"   ❌ Equity Curve: None 또는 빈 리스트")
        
        # 타임스탬프 확인
        if backtest.equity_timestamps:
            print(f"   Equity Timestamps: {len(backtest.equity_timestamps)}개")
            print(f"     First: {backtest.equity_timestamps[0]}")
            print(f"     Last: {backtest.equity_timestamps[-1]}")
        else:
            print(f"   ❌ Equity Timestamps: None 또는 빈 리스트")
        
        # 거래 내역 확인
        trades = db.query(TradeModel).filter(
            TradeModel.backtest_id == backtest_id
        ).all()
        
        print(f"   Trades: {len(trades)}개")
        for i, trade in enumerate(trades):
            print(f"     {i+1}. {trade.side} {trade.quantity} {trade.symbol} @ {trade.price:,.0f}")
        
        # Raw 데이터 타입 확인
        print(f"\n🔍 Raw 데이터 타입 확인")
        print(f"   equity_curve type: {type(backtest.equity_curve)}")
        print(f"   equity_timestamps type: {type(backtest.equity_timestamps)}")
        
        if backtest.equity_curve:
            print(f"   equity_curve content: {backtest.equity_curve[:3]}...")
        
        if backtest.equity_timestamps:
            print(f"   equity_timestamps content: {backtest.equity_timestamps[:3]}...")
    
    finally:
        db.close()

if __name__ == "__main__":
    check_backtest_result()