# 전략 설정 JSON 스키마 (config_json)

## 개요

`StrategyBuilderModel`의 `config_json` 필드는 UI에서 선택한 지표, 파라미터, 매매 조건을 구조화된 데이터로 저장합니다.

## 전체 구조

```json
{
  "indicators": [...],
  "conditions": {
    "buy": [...],
    "sell": [...]
  },
  "ict_config": {...},
  "parameters": {...},
  "stock_selection": {...},
  "entry_strategy": {...},
  "position_management": {...},
  "risk_management": {...}
}
```

## 1. Indicators (지표)

사용자가 선택한 기술적 지표 및 ICT 지표 목록입니다.

```json
{
  "indicators": [
    {
      "type": "technical",  // "technical" | "ict"
      "name": "rsi",         // 지표 이름
      "parameters": {
        "period": 14,
        "lookback": 20
      }
    },
    {
      "type": "ict",
      "name": "fvg",        // "fvg" | "liquidity" | "order_block" | "mss" | "bos"
      "parameters": {
        "lookback": 20,
        "min_gap_size": 0.002
      }
    }
  ]
}
```

### 기술적 지표 (technical)

- `sma`, `ema`: 이동평균
  - `period`: 기간
- `rsi`: 상대강도지수
  - `period`: 기간 (기본: 14)
- `macd`: MACD
  - `fast`: 빠른 EMA 기간 (기본: 12)
  - `slow`: 느린 EMA 기간 (기본: 26)
  - `signal`: 시그널 라인 기간 (기본: 9)
- `bollinger_bands`: 볼린저 밴드
  - `period`: 기간 (기본: 20)
  - `std_dev`: 표준편차 배수 (기본: 2.0)
- `atr`: Average True Range
  - `period`: 기간 (기본: 14)
- `stochastic`: 스토캐스틱
  - `period`: 기간 (기본: 14)
- `adx`: Average Directional Index
  - `period`: 기간 (기본: 14)
- `volume_ma`: 거래량 이동평균
  - `period`: 기간 (기본: 20)

### ICT 지표 (ict)

- `fvg`: Fair Value Gap
  - `lookback`: 확인 기간 (기본: 3)
  - `min_gap_size`: 최소 갭 크기 (비율, 기본: 0.001)
  - `check_filled`: 필드 여부 확인 (기본: true)
- `liquidity_zones`: 유동성 구간
  - `period`: 기간 (기본: 20)
  - `tolerance`: 허용 오차 (비율, 기본: 0.001)
  - `min_touches`: 최소 테스트 횟수 (기본: 2)
- `order_block`: Order Block
  - `lookback`: 추세 전환 탐지 기간 (기본: 20)
  - `volume_multiplier`: 거래량 배수 (기본: 1.5)
- `mss`: Market Structure Shift
  - `swing_lookback`: Swing High/Low 판단 기간 (기본: 5)
- `bos`: Break of Structure
  - `swing_lookback`: Swing High/Low 판단 기간 (기본: 5)

## 2. Conditions (매매 조건)

매수/매도 조건을 정의합니다.

```json
{
  "conditions": {
    "buy": [
      {
        "id": "buy_1",
        "type": "indicator",  // "indicator" | "price" | "volume" | "ict"
        "indicator": "rsi",
        "operator": "<",      // ">" | "<" | ">=" | "<=" | "==" | "in_range" | "in_gap" | "in_zone" | "cross_above" | "cross_below"
        "value": 35,
        "period": 14
      },
      {
        "id": "buy_2",
        "type": "ict",
        "indicator": "fvg",
        "operator": "in_gap",
        "value": "bullish",   // "bullish" | "bearish"
        "check_filled": false
      },
      {
        "id": "buy_3",
        "type": "ict",
        "indicator": "order_block",
        "operator": "in_block",
        "value": "bullish",
        "lookback": 20
      }
    ],
    "sell": [
      {
        "id": "sell_1",
        "type": "indicator",
        "indicator": "rsi",
        "operator": ">",
        "value": 70,
        "period": 14
      }
    ]
  }
}
```

### Condition 타입별 상세

#### indicator 타입
- `indicator`: 지표 이름 (rsi, ma, macd 등)
- `operator`: 비교 연산자
- `value`: 비교 값 또는 참조 지표
- `period`: 지표 기간

#### ict 타입
- `indicator`: ICT 지표 이름 (fvg, liquidity, order_block, mss, bos)
- `operator`: 
  - `in_gap`: FVG 구간 내에 있는지
  - `in_zone`: Liquidity Zone 내에 있는지
  - `in_block`: Order Block 내에 있는지
  - `break_high`: BOS 상승 돌파
  - `break_low`: BOS 하락 돌파
  - `structure_shift`: MSS 발생
- `value`: 지표별 값
  - FVG: "bullish" | "bearish"
  - Liquidity: "support" | "resistance"
  - Order Block: "bullish" | "bearish"
  - MSS/BOS: "bullish" | "bearish"

## 3. ICT Config (ICT 전용 설정)

ICT 지표의 전역 설정입니다.

```json
{
  "ict_config": {
    "fvg": {
      "enabled": true,
      "min_gap_size": 0.002,
      "check_filled": true,
      "ignore_filled": false
    },
    "liquidity_zones": {
      "enabled": true,
      "period": 20,
      "tolerance": 0.001,
      "min_touches": 2
    },
    "order_block": {
      "enabled": true,
      "lookback": 20,
      "volume_multiplier": 1.5,
      "min_body_ratio": 0.02
    },
    "mss_bos": {
      "enabled": true,
      "swing_lookback": 5,
      "detect_bos": true,
      "detect_mss": true
    }
  }
}
```

## 4. Parameters (전략 파라미터)

전략 실행 파라미터입니다.

```json
{
  "parameters": {
    "timeframe": "1m",        // "1m" | "5m" | "15m" | "30m" | "1h" | "4h" | "1d"
    "lookback_period": 100,
    "symbol": "005930",       // 단일 종목 전략인 경우
    "is_portfolio": false     // 포트폴리오 전략 여부
  }
}
```

## 5. Stock Selection (종목 선정)

종목 필터링 조건입니다.

```json
{
  "stock_selection": {
    "marketCap": {"min": 3000, "max": 100000},
    "volume": {"min": 500000},
    "volumeValue": {"min": 5000},
    "price": {"min": 10000, "max": 200000},
    "market": ["KOSPI", "KOSDAQ"],
    "sector": ["IT", "금융"],
    "per": {"min": 3, "max": 15},
    "pbr": {"min": 0.3, "max": 2.0},
    "roe": {"min": 8},
    "excludeManaged": true,
    "excludeClearing": true,
    "excludeSpac": true,
    "minListingDays": 180
  }
}
```

## 6. Entry Strategy (진입 전략)

진입 방식 설정입니다.

```json
{
  "entry_strategy": {
    "type": "single",         // "single" | "pyramid"
    "pyramid_levels": [
      {
        "level": 1,
        "distance": 0.02,     // 2% 거리
        "size": 0.33          // 33% 비율
      }
    ],
    "max_levels": 3,
    "max_position_size": 0.15, // 15%
    "min_interval": 1         // 최소 진입 간격 (일)
  }
}
```

## 7. Position Management (포지션 관리)

포지션 크기 및 관리 설정입니다.

```json
{
  "position_management": {
    "sizing_method": "equal_weight",  // "equal_weight" | "risk_based" | "fixed"
    "max_position_size": 0.125,       // 12.5%
    "max_positions": 8,
    "rebalance_period": "daily"       // "daily" | "weekly" | "monthly"
  }
}
```

## 8. Risk Management (리스크 관리)

리스크 관리 설정입니다.

```json
{
  "risk_management": {
    "stop_loss": {
      "enabled": true,
      "percentage": 8.0,      // 8%
      "type": "trailing"      // "fixed" | "trailing"
    },
    "take_profit": {
      "enabled": true,
      "percentage": 25.0,     // 25%
      "type": "fixed"         // "fixed" | "trailing"
    },
    "max_daily_loss": 0.05,   // 5%
    "max_mdd": 0.20           // 20%
  }
}
```

## 예시: ICT 기반 전략

```json
{
  "indicators": [
    {
      "type": "ict",
      "name": "fvg",
      "parameters": {
        "min_gap_size": 0.003
      }
    },
    {
      "type": "ict",
      "name": "order_block",
      "parameters": {
        "lookback": 20,
        "volume_multiplier": 2.0
      }
    },
    {
      "type": "ict",
      "name": "liquidity_zones",
      "parameters": {
        "period": 20
      }
    },
    {
      "type": "technical",
      "name": "rsi",
      "parameters": {
        "period": 14
      }
    }
  ],
  "conditions": {
    "buy": [
      {
        "id": "buy_1",
        "type": "ict",
        "indicator": "fvg",
        "operator": "in_gap",
        "value": "bullish",
        "check_filled": false
      },
      {
        "id": "buy_2",
        "type": "ict",
        "indicator": "order_block",
        "operator": "in_block",
        "value": "bullish"
      },
      {
        "id": "buy_3",
        "type": "indicator",
        "indicator": "rsi",
        "operator": "<",
        "value": 40,
        "period": 14
      }
    ],
    "sell": [
      {
        "id": "sell_1",
        "type": "ict",
        "indicator": "fvg",
        "operator": "in_gap",
        "value": "bearish"
      },
      {
        "id": "sell_2",
        "type": "indicator",
        "indicator": "rsi",
        "operator": ">",
        "value": 70,
        "period": 14
      }
    ]
  },
  "ict_config": {
    "fvg": {
      "enabled": true,
      "min_gap_size": 0.003,
      "check_filled": true
    },
    "order_block": {
      "enabled": true,
      "lookback": 20,
      "volume_multiplier": 2.0
    },
    "liquidity_zones": {
      "enabled": true,
      "period": 20,
      "tolerance": 0.001
    }
  },
  "parameters": {
    "timeframe": "1d",
    "lookback_period": 50
  },
  "stock_selection": {
    "marketCap": {"min": 5000, "max": 100000},
    "volume": {"min": 500000}
  },
  "entry_strategy": {
    "type": "single",
    "max_position_size": 0.10
  },
  "position_management": {
    "sizing_method": "equal_weight",
    "max_positions": 10
  },
  "risk_management": {
    "stop_loss": {
      "enabled": true,
      "percentage": 5.0
    },
    "take_profit": {
      "enabled": true,
      "percentage": 15.0
    }
  }
}
```

