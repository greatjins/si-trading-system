#!/usr/bin/env python3
"""DB 상태 확인 스크립트"""

import sqlite3
import os

def check_database():
    db_path = "data/hts.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 테이블 목록 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Available tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 전략 빌더 테이블 확인
    strategy_tables = [t[0] for t in tables if 'strategy' in t[0].lower()]
    
    if strategy_tables:
        print(f"\nStrategy related tables: {strategy_tables}")
        
        for table_name in strategy_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} records")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"    Columns: {columns}")
                print(f"    Sample data: {rows[:1]}")
    
    conn.close()

if __name__ == "__main__":
    check_database()