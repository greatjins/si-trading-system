-- PostgreSQL 테이블 초기화 스크립트
-- SQLite 스키마와 완전히 일치하도록 작성

-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Keys
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Trading Accounts
CREATE TABLE IF NOT EXISTS trading_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    broker VARCHAR(20) NOT NULL,
    account_type VARCHAR(20) NOT NULL,
    account_number VARCHAR(255) NOT NULL,
    api_key VARCHAR(255),
    api_secret VARCHAR(255),
    app_key VARCHAR(255),
    app_secret VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_connected_at TIMESTAMP
);

-- Backtest Results (SQLite 호환)
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    parameters JSON NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    initial_capital FLOAT NOT NULL,
    final_equity FLOAT NOT NULL,
    total_return FLOAT NOT NULL,
    mdd FLOAT NOT NULL,
    sharpe_ratio FLOAT NOT NULL,
    win_rate FLOAT NOT NULL,
    profit_factor FLOAT NOT NULL,
    total_trades INTEGER NOT NULL,
    equity_curve JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trades (SQLite 호환)
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    backtest_id INTEGER,
    trade_id VARCHAR(100) NOT NULL,
    order_id VARCHAR(100),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price FLOAT NOT NULL,
    commission FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strategy Configs
CREATE TABLE IF NOT EXISTS strategy_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    strategy_class VARCHAR(100) NOT NULL,
    parameters JSON NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strategy Builder (SQLite 호환)
CREATE TABLE IF NOT EXISTS strategy_builder (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    config JSON NOT NULL,
    python_code TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 데이터 수집 관련 테이블
-- ==========================================

-- 종목 마스터 (전체 종목 메타데이터)
CREATE TABLE IF NOT EXISTS stock_master (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(20),  -- KOSPI, KOSDAQ
    sector VARCHAR(50),
    current_price DECIMAL(15, 2),
    volume_amount BIGINT,  -- 거래대금 (원) - BIGINT로 변경
    high_52w DECIMAL(15, 2),  -- 52주 최고가
    low_52w DECIMAL(15, 2),   -- 52주 최저가
    price_position FLOAT,  -- 현재가 / 52주 최고가
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 전략별 종목 유니버스
CREATE TABLE IF NOT EXISTS stock_universe (
    id SERIAL PRIMARY KEY,
    strategy_type VARCHAR(50) NOT NULL,  -- mean_reversion, momentum
    symbol VARCHAR(20) NOT NULL,
    rank INTEGER,  -- 우선순위
    score FLOAT,   -- 점수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(strategy_type, symbol)
);

-- OHLC 데이터
CREATE TABLE IF NOT EXISTS ohlc_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    interval VARCHAR(10) NOT NULL,  -- 1d, 1m, 5m, 10m, 30m, 60m
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(15, 2) NOT NULL,
    high DECIMAL(15, 2) NOT NULL,
    low DECIMAL(15, 2) NOT NULL,
    close DECIMAL(15, 2) NOT NULL,
    volume BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, interval, timestamp)
);

-- Indexes (SQLite 호환)
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS ix_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS ix_trading_accounts_id ON trading_accounts(id);
CREATE INDEX IF NOT EXISTS ix_trading_accounts_user_id ON trading_accounts(user_id);
CREATE INDEX IF NOT EXISTS ix_strategy_builder_user_id ON strategy_builder(user_id);

-- 데이터 수집 관련 인덱스
CREATE INDEX IF NOT EXISTS ix_stock_master_volume ON stock_master(volume_amount DESC);
CREATE INDEX IF NOT EXISTS ix_stock_master_position ON stock_master(price_position);
CREATE INDEX IF NOT EXISTS ix_stock_universe_strategy ON stock_universe(strategy_type, rank);
CREATE INDEX IF NOT EXISTS ix_ohlc_symbol_interval ON ohlc_data(symbol, interval);
CREATE INDEX IF NOT EXISTS ix_ohlc_timestamp ON ohlc_data(timestamp);
CREATE INDEX IF NOT EXISTS ix_ohlc_symbol_interval_timestamp ON ohlc_data(symbol, interval, timestamp);

-- Success message
SELECT 'Tables created successfully!' AS status;
