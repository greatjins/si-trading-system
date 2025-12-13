/**
 * 고급 조건 입력 컴포넌트 - 모든 지표 지원
 */
import React from 'react';

interface IndicatorInfo {
  id: string;
  name: string;
  category: string;
  parameters: Array<{
    name: string;
    type: string;
    default: number;
    min?: number;
    max?: number;
    step?: number;
  }>;
  operators: string[];
  description: string;
}

interface AdvancedConditionInputProps {
  value: string | number;
  indicator: string;
  indicators: IndicatorInfo[];
  onChange: (value: string | number) => void;
}

export const AdvancedConditionInput: React.FC<AdvancedConditionInputProps> = ({
  value,
  indicator,
  indicators,
  onChange
}) => {
  // 현재 지표 정보 가져오기
  const currentIndicator = indicators.find(ind => ind.id === indicator);
  
  // 값 타입 감지
  const getValueType = () => {
    if (typeof value === 'string') {
      if (['close', 'open', 'high', 'low'].includes(value)) return value;
      if (value.match(/^(MA|EMA|RSI|MACD|ATR|STOCH|ADX|CCI|MFI|Williams|OBV|VWAP)\(/)) return 'indicator';
      if (['MACD', 'OBV', 'VWAP'].includes(value)) return 'indicator';
    }
    return 'number';
  };

  // 지표별 기본값 설정
  const getDefaultIndicatorValue = (indicatorId: string) => {
    switch (indicatorId) {
      case 'ma': return 'MA(20)';
      case 'ema': return 'EMA(20)';
      case 'rsi': return 'RSI(14)';
      case 'macd': return 'MACD';
      case 'atr': return 'ATR(14)';
      case 'stochastic': return 'STOCH(14)';
      case 'adx': return 'ADX(14)';
      case 'cci': return 'CCI(20)';
      case 'williams_r': return 'Williams(14)';
      case 'mfi': return 'MFI(14)';
      case 'obv': return 'OBV';
      case 'vwap': return 'VWAP';
      case 'volume_ma': return 'VMA(20)';
      default: return 'MA(20)';
    }
  };

  // 지표에서 파라미터 추출
  const extractParameters = (indicatorValue: string) => {
    const match = indicatorValue.match(/\(([^)]+)\)/);
    if (match) {
      return match[1].split(',').map(p => p.trim());
    }
    return [];
  };

  // 지표 타입 추출
  const extractIndicatorType = (indicatorValue: string) => {
    return indicatorValue.split('(')[0];
  };

  const valueType = getValueType();

  return (
    <div className="advanced-condition-input">
      {/* 값 타입 선택 */}
      <select
        value={valueType}
        onChange={(e) => {
          let newValue: string | number;
          switch(e.target.value) {
            case 'close': newValue = 'close'; break;
            case 'open': newValue = 'open'; break;
            case 'high': newValue = 'high'; break;
            case 'low': newValue = 'low'; break;
            case 'indicator': newValue = getDefaultIndicatorValue(indicator); break;
            default: newValue = 0; break;
          }
          onChange(newValue);
        }}
        className="value-type-select"
      >
        <option value="number">숫자</option>
        <option value="close">종가</option>
        <option value="open">시가</option>
        <option value="high">고가</option>
        <option value="low">저가</option>
        <option value="indicator">지표</option>
      </select>

      {/* 숫자 입력 */}
      {valueType === 'number' && (
        <input
          type="number"
          value={typeof value === 'number' ? value : ''}
          onChange={(e) => onChange(Number(e.target.value))}
          placeholder="값 입력"
          className="number-input"
        />
      )}

      {/* 지표 입력 */}
      {valueType === 'indicator' && typeof value === 'string' && (
        <div className="indicator-input-group">
          {/* 지표 타입 선택 */}
          <select
            value={extractIndicatorType(value)}
            onChange={(e) => {
              const newType = e.target.value;
              const params = extractParameters(value.toString());
              let newValue = '';
              
              switch(newType) {
                case 'MA': newValue = `MA(${params[0] || '20'})`; break;
                case 'EMA': newValue = `EMA(${params[0] || '20'})`; break;
                case 'RSI': newValue = `RSI(${params[0] || '14'})`; break;
                case 'MACD': newValue = 'MACD'; break;
                case 'ATR': newValue = `ATR(${params[0] || '14'})`; break;
                case 'STOCH': newValue = `STOCH(${params[0] || '14'})`; break;
                case 'ADX': newValue = `ADX(${params[0] || '14'})`; break;
                case 'CCI': newValue = `CCI(${params[0] || '20'})`; break;
                case 'Williams': newValue = `Williams(${params[0] || '14'})`; break;
                case 'MFI': newValue = `MFI(${params[0] || '14'})`; break;
                case 'OBV': newValue = 'OBV'; break;
                case 'VWAP': newValue = 'VWAP'; break;
                case 'VMA': newValue = `VMA(${params[0] || '20'})`; break;
                default: newValue = `MA(${params[0] || '20'})`;
              }
              onChange(newValue);
            }}
            className="indicator-type-select"
          >
            <option value="MA">이동평균 (MA)</option>
            <option value="EMA">지수평균 (EMA)</option>
            <option value="RSI">RSI</option>
            <option value="MACD">MACD</option>
            <option value="ATR">ATR</option>
            <option value="STOCH">스토캐스틱</option>
            <option value="ADX">ADX</option>
            <option value="CCI">CCI</option>
            <option value="Williams">Williams %R</option>
            <option value="MFI">MFI</option>
            <option value="OBV">OBV</option>
            <option value="VWAP">VWAP</option>
            <option value="VMA">거래량 MA</option>
          </select>

          {/* 파라미터 입력 (기간이 있는 지표만) */}
          {!['MACD', 'OBV', 'VWAP'].includes(extractIndicatorType(value)) && (
            <>
              <span>(</span>
              <input
                type="number"
                value={extractParameters(value)[0] || '20'}
                onChange={(e) => {
                  const indicatorType = extractIndicatorType(value);
                  const newPeriod = e.target.value;
                  onChange(`${indicatorType}(${newPeriod})`);
                }}
                className="period-input"
                min="1"
                max="200"
              />
              <span>)</span>
            </>
          )}
        </div>
      )}

      {/* 지표별 특수 조건 (RSI 범위 등) */}
      {indicator === 'rsi' && valueType === 'number' && (
        <div className="rsi-range-helper">
          <small>💡 RSI 범위: 과매도(30 이하), 중립(30-70), 과매수(70 이상)</small>
        </div>
      )}

      {indicator === 'stochastic' && valueType === 'number' && (
        <div className="stoch-range-helper">
          <small>💡 스토캐스틱: 과매도(20 이하), 과매수(80 이상)</small>
        </div>
      )}

      <style>{`
        .advanced-condition-input {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
        }

        .value-type-select,
        .indicator-type-select {
          min-width: 100px;
          padding: 4px 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .number-input,
        .period-input {
          width: 80px;
          padding: 4px 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .indicator-input-group {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .rsi-range-helper,
        .stoch-range-helper {
          width: 100%;
          margin-top: 4px;
        }

        .rsi-range-helper small,
        .stoch-range-helper small {
          color: #666;
          font-size: 11px;
        }
      `}</style>
    </div>
  );
};