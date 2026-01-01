"""
Phase 3, 4 관련 테이블 존재 확인
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, inspect
from utils.config import config

db_type = config.get("database.type", "sqlite")
if db_type == "sqlite":
    db_path = config.get("database.path", "data/hts.db")
    db_url = f"sqlite:///{db_path}"
else:
    host = config.get("database.host", "localhost")
    port = config.get("database.port", 5432)
    database = config.get("database.database", "hts")
    username = config.get("database.user", "hts_user")
    password = config.get("database.password", "")
    db_url = f"postgresql+pg8000://{username}:{password}@{host}:{port}/{database}"

engine = create_engine(db_url, echo=False)
inspector = inspect(engine)
tables = inspector.get_table_names()

target_tables = ['live_trades', 'strategy_performance', 'backtest_live_comparisons']

print(f"\n데이터베이스: {db_type}")
print(f"\nPhase 3, 4 관련 테이블 확인:")
for table in target_tables:
    if table in tables:
        columns = inspector.get_columns(table)
        print(f"  [OK] {table}: {len(columns)}개 컬럼")
    else:
        print(f"  [MISSING] {table}: 없음")

