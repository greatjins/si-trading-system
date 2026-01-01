# 전략 설정 가이드 - 단일 종목 vs 포트폴리오

## 개요

전략을 생성할 때 **단일 종목 전략**인지 **포트폴리오 전략**인지를 명시적으로 지정할 수 있습니다.

## 설정 방법

### 방법 1: JSON Config에 직접 지정 (권장)

전략 빌더에서 생성하는 JSON config에 `is_portfolio` 필드를 추가하세요:

```json
{
  "strategy_type": "ict_pyramiding",
  "is_portfolio": false,  // ⭐ 이 필드로 직접 제어
  "parameters": {
    "symbol": "005930",
    "fvg_threshold": 0.002
  }
}
```

**값 설명:**
- `false`: 단일 종목 전략 (하나의 종목만 거래)
- `true`: 포트폴리오 전략 (여러 종목을 자동으로 선택하여 거래)

### 방법 2: 전략 타입별 기본값

전략 타입(`strategy_type`)에 따라 자동으로 판단됩니다:

- `ict_pyramiding`: 단일 종목 전략 (기본값)
- `ma_cross`: 단일 종목 전략
- `value_portfolio`: 포트폴리오 전략
- `simple_portfolio`: 포트폴리오 전략

### 방법 3: stockSelection 설정으로 자동 판단

`stockSelection` 설정이 있고 조건이 있으면 자동으로 포트폴리오 전략으로 판단됩니다:

```json
{
  "strategy_type": "ict_pyramiding",
  "stockSelection": {
    "per": { "max": 15 },
    "pbr": { "max": 1.5 }
  }
}
```

## 우선순위

전략 타입 판단은 다음 우선순위로 진행됩니다:

1. **`is_portfolio` 필드** (최우선) - 명시적으로 지정된 값 사용
2. **전략 인스턴스 생성** - 실제 전략 클래스의 `is_portfolio_strategy()` 메서드 호출
3. **`stockSelection` 설정** - 종목 선택 조건이 있으면 포트폴리오 전략

## 예시

### 단일 종목 전략 예시

```json
{
  "strategy_type": "ict_pyramiding",
  "is_portfolio": false,
  "parameters": {
    "symbol": "005930",
    "fvg_threshold": 0.002,
    "pyramid_levels": 2
  }
}
```

**특징:**
- 하나의 종목만 거래
- 백테스트 시 `symbol` 파라미터 필수
- `/api/backtest/run` 엔드포인트 사용

### 포트폴리오 전략 예시

```json
{
  "strategy_type": "value_portfolio",
  "is_portfolio": true,
  "parameters": {
    "per_max": 15.0,
    "pbr_max": 1.5,
    "max_stocks": 20
  },
  "stockSelection": {
    "per": { "max": 15 },
    "pbr": { "max": 1.5 },
    "roe": { "min": 5 }
  }
}
```

**특징:**
- 여러 종목을 자동으로 선택하여 거래
- 백테스트 시 `symbol` 파라미터 불필요
- `/api/backtest/portfolio` 엔드포인트 사용

## 전략 빌더 UI에서 설정

전략 빌더 UI에 "전략 타입" 선택 옵션을 추가할 수 있습니다:

```typescript
// 전략 타입 선택
<div className="form-group">
  <label>전략 타입</label>
  <select 
    value={strategy.is_portfolio ? 'portfolio' : 'single'}
    onChange={(e) => {
      setStrategy({
        ...strategy,
        is_portfolio: e.target.value === 'portfolio'
      });
    }}
  >
    <option value="single">단일 종목 전략</option>
    <option value="portfolio">포트폴리오 전략</option>
  </select>
</div>
```

## 주의사항

1. **단일 종목 전략**은 `symbol` 파라미터가 필수입니다.
2. **포트폴리오 전략**은 `select_universe()` 메서드를 구현해야 합니다.
3. `is_portfolio` 필드를 명시적으로 지정하면 다른 판단 로직보다 우선합니다.

## 문제 해결

### 문제: 단일 종목 전략인데 포트폴리오로 인식됨

**해결:**
```json
{
  "strategy_type": "ict_pyramiding",
  "is_portfolio": false,  // 명시적으로 false 지정
  "parameters": { ... }
}
```

### 문제: 포트폴리오 전략인데 단일 종목으로 인식됨

**해결:**
```json
{
  "strategy_type": "value_portfolio",
  "is_portfolio": true,  // 명시적으로 true 지정
  "parameters": { ... }
}
```

## 참고

- 전략 타입 판단 로직: `api/routes/strategy_builder.py`의 `list_strategies()` 함수
- 전략 생성 로직: `core/strategy/factory.py`의 `create_from_db_config()` 함수
- 전략 타입 확인: `core/strategy/base.py`의 `is_portfolio_strategy()` 메서드

