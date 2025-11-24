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

-- Indexes (SQLite 호환)
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS ix_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS ix_trading_accounts_id ON trading_accounts(id);
CREATE INDEX IF NOT EXISTS ix_trading_accounts_user_id ON trading_accounts(user_id);
CREATE INDEX IF NOT EXISTS ix_strategy_builder_user_id ON strategy_builder(user_id);

-- Success message
SELECT 'Tables created successfully!' AS status;
