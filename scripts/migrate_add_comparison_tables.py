"""
Phase 3, 4 관련 테이블 추가 마이그레이션
- live_trades: 실전 거래 내역
- strategy_performance: 전략별 실시간 성과 추적
- backtest_live_comparisons: 백테스트-실전 비교 결과
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, inspect
from utils.config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


def migrate():
    """Phase 3, 4 관련 테이블 추가"""
    
    # 데이터베이스 연결
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
    
    logger.info(f"데이터베이스 연결: {db_type}")
    engine = create_engine(db_url, echo=False)
    
    is_postgres = "postgresql" in db_url
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # 1. live_trades 테이블 생성
        if 'live_trades' not in existing_tables:
            logger.info("live_trades 테이블 생성 중...")
            try:
                if is_postgres:
                    sql = """
                    CREATE TABLE live_trades (
                        id SERIAL PRIMARY KEY,
                        strategy_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        trade_id VARCHAR(100) UNIQUE NOT NULL,
                        order_id VARCHAR(100),
                        symbol VARCHAR(20) NOT NULL,
                        side VARCHAR(10) NOT NULL,
                        quantity INTEGER NOT NULL,
                        price FLOAT NOT NULL,
                        commission FLOAT NOT NULL,
                        slippage FLOAT,
                        timestamp TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_live_trades_strategy_id ON live_trades(strategy_id);
                    CREATE INDEX idx_live_trades_user_id ON live_trades(user_id);
                    CREATE INDEX idx_live_trades_symbol ON live_trades(symbol);
                    CREATE INDEX idx_live_trades_timestamp ON live_trades(timestamp);
                    """
                else:
                    sql = """
                    CREATE TABLE live_trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        trade_id VARCHAR(100) UNIQUE NOT NULL,
                        order_id VARCHAR(100),
                        symbol VARCHAR(20) NOT NULL,
                        side VARCHAR(10) NOT NULL,
                        quantity INTEGER NOT NULL,
                        price REAL NOT NULL,
                        commission REAL NOT NULL,
                        slippage REAL,
                        timestamp TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_live_trades_strategy_id ON live_trades(strategy_id);
                    CREATE INDEX idx_live_trades_user_id ON live_trades(user_id);
                    CREATE INDEX idx_live_trades_symbol ON live_trades(symbol);
                    CREATE INDEX idx_live_trades_timestamp ON live_trades(timestamp);
                    """
                
                conn.execute(text(sql))
                conn.commit()
                logger.info("✓ live_trades 테이블 생성 완료")
            except Exception as e:
                logger.error(f"✗ live_trades 테이블 생성 실패: {e}")
                conn.rollback()
                raise
        else:
            logger.info("⊙ live_trades 테이블 이미 존재")
        
        # 2. strategy_performance 테이블 생성
        if 'strategy_performance' not in existing_tables:
            logger.info("strategy_performance 테이블 생성 중...")
            try:
                if is_postgres:
                    sql = """
                    CREATE TABLE strategy_performance (
                        id SERIAL PRIMARY KEY,
                        strategy_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        total_return FLOAT NOT NULL DEFAULT 0.0,
                        daily_return FLOAT,
                        total_trades INTEGER NOT NULL DEFAULT 0,
                        win_rate FLOAT,
                        profit_factor FLOAT,
                        initial_capital FLOAT NOT NULL,
                        current_equity FLOAT NOT NULL,
                        realized_pnl FLOAT NOT NULL DEFAULT 0.0,
                        unrealized_pnl FLOAT NOT NULL DEFAULT 0.0,
                        max_drawdown FLOAT,
                        peak_equity FLOAT,
                        start_date TIMESTAMP NOT NULL,
                        last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    );
                    
                    CREATE INDEX idx_strategy_performance_strategy_id ON strategy_performance(strategy_id);
                    CREATE INDEX idx_strategy_performance_user_id ON strategy_performance(user_id);
                    """
                else:
                    sql = """
                    CREATE TABLE strategy_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        total_return REAL NOT NULL DEFAULT 0.0,
                        daily_return REAL,
                        total_trades INTEGER NOT NULL DEFAULT 0,
                        win_rate REAL,
                        profit_factor REAL,
                        initial_capital REAL NOT NULL,
                        current_equity REAL NOT NULL,
                        realized_pnl REAL NOT NULL DEFAULT 0.0,
                        unrealized_pnl REAL NOT NULL DEFAULT 0.0,
                        max_drawdown REAL,
                        peak_equity REAL,
                        start_date TIMESTAMP NOT NULL,
                        last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    );
                    
                    CREATE INDEX idx_strategy_performance_strategy_id ON strategy_performance(strategy_id);
                    CREATE INDEX idx_strategy_performance_user_id ON strategy_performance(user_id);
                    """
                
                conn.execute(text(sql))
                conn.commit()
                logger.info("✓ strategy_performance 테이블 생성 완료")
            except Exception as e:
                logger.error(f"✗ strategy_performance 테이블 생성 실패: {e}")
                conn.rollback()
                raise
        else:
            logger.info("⊙ strategy_performance 테이블 이미 존재")
        
        # 3. backtest_live_comparisons 테이블 생성
        if 'backtest_live_comparisons' not in existing_tables:
            logger.info("backtest_live_comparisons 테이블 생성 중...")
            try:
                if is_postgres:
                    sql = """
                    CREATE TABLE backtest_live_comparisons (
                        id SERIAL PRIMARY KEY,
                        backtest_id INTEGER NOT NULL,
                        strategy_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        backtest_start TIMESTAMP NOT NULL,
                        backtest_end TIMESTAMP NOT NULL,
                        live_start TIMESTAMP NOT NULL,
                        live_end TIMESTAMP NOT NULL,
                        backtest_return FLOAT NOT NULL,
                        backtest_trades INTEGER NOT NULL,
                        backtest_win_rate FLOAT,
                        live_return FLOAT NOT NULL,
                        live_trades INTEGER NOT NULL,
                        live_win_rate FLOAT,
                        return_difference FLOAT NOT NULL,
                        trade_difference INTEGER NOT NULL,
                        slippage_contribution FLOAT,
                        commission_contribution FLOAT,
                        delay_contribution FLOAT,
                        liquidity_contribution FLOAT,
                        market_change_contribution FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_backtest_live_comparisons_backtest_id ON backtest_live_comparisons(backtest_id);
                    CREATE INDEX idx_backtest_live_comparisons_strategy_id ON backtest_live_comparisons(strategy_id);
                    CREATE INDEX idx_backtest_live_comparisons_user_id ON backtest_live_comparisons(user_id);
                    """
                else:
                    sql = """
                    CREATE TABLE backtest_live_comparisons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        backtest_id INTEGER NOT NULL,
                        strategy_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        backtest_start TIMESTAMP NOT NULL,
                        backtest_end TIMESTAMP NOT NULL,
                        live_start TIMESTAMP NOT NULL,
                        live_end TIMESTAMP NOT NULL,
                        backtest_return REAL NOT NULL,
                        backtest_trades INTEGER NOT NULL,
                        backtest_win_rate REAL,
                        live_return REAL NOT NULL,
                        live_trades INTEGER NOT NULL,
                        live_win_rate REAL,
                        return_difference REAL NOT NULL,
                        trade_difference INTEGER NOT NULL,
                        slippage_contribution REAL,
                        commission_contribution REAL,
                        delay_contribution REAL,
                        liquidity_contribution REAL,
                        market_change_contribution REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_backtest_live_comparisons_backtest_id ON backtest_live_comparisons(backtest_id);
                    CREATE INDEX idx_backtest_live_comparisons_strategy_id ON backtest_live_comparisons(strategy_id);
                    CREATE INDEX idx_backtest_live_comparisons_user_id ON backtest_live_comparisons(user_id);
                    """
                
                conn.execute(text(sql))
                conn.commit()
                logger.info("✓ backtest_live_comparisons 테이블 생성 완료")
            except Exception as e:
                logger.error(f"✗ backtest_live_comparisons 테이블 생성 실패: {e}")
                conn.rollback()
                raise
        else:
            logger.info("⊙ backtest_live_comparisons 테이블 이미 존재")
    
    logger.info("✅ 마이그레이션 완료!")


if __name__ == "__main__":
    migrate()

