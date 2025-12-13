/**
 * 조건 값 입력 컴포넌트 - 타입 안전성 보장
 */
import React from 'react';

// 명확한 타입 정의
export type ValueType = 'number' | 'price' | 'indicator';
export type PriceType = 'close' | 'open' | 'high' | 'low';
export type IndicatorType = 'MA' | 'EMA' | 'RSI' | 'MACD';

export interface ConditionValue {
  type: ValueType;
  numericValue?: number;
  priceType?: PriceType;
  indicatorType?: IndicatorType;
  indicatorPeriod?: number;
}

interface Props {
  value: ConditionValue;
  onChange: (value: ConditionValue) => void;
  className?: string;
}

export const ConditionValueInput: React.FC<Props> = ({ value, onChange, className = '' }) => {
  
  const handleTypeChange = (newType: ValueType) => {
    let newValue: ConditionValue;
    
    switch (newType) {
      case 'number':
        newValue = { type: 'number', numericValue: 0 };
        break;
      case 'price':
        newValue = { type: 'price', priceType: 'close' };
        break;
      case 'indicator':
        newValue = { type: 'indicator', indicatorType: 'MA', indicatorPeriod: 20 };
        break;
      default:
        newValue = { type: 'number', numericValue: 0 };
    }
    
    onChange(newValue);
  };

  const handleNumericChange = (numericValue: number) => {
    onChange({ ...value, numericValue });
  };

  const handlePriceTypeChange = (priceType: PriceType) => {
    onChange({ ...value, priceType });
  };

  const handleIndicatorTypeChange = (indicatorType: IndicatorType) => {
    onChange({ ...value, indicatorType });
  };

  const handleIndicatorPeriodChange = (indicatorPeriod: number) => {
    onChange({ ...value, indicatorPeriod });
  };

  return (
    <div className={`condition-value-input ${className}`}>
      {/* 값 타입 선택 */}
      <select
        value={value.type}
        onChange={(e) => handleTypeChange(e.target.value as ValueType)}
        className="form-select small"
        style={{ minWidth: '120px' }}
      >
        <option value="number">숫자 입력</option>
        <option value="price">가격</option>
        <option value="indicator">지표</option>
      </select>

      {/* 숫자 입력 */}
      {value.type === 'number' && (
        <input
          type="number"
          value={value.numericValue || 0}
          onChange={(e) => handleNumericChange(Number(e.target.value))}
          placeholder="숫자 값"
          className="form-input small"
          style={{ minWidth: '100px' }}
        />
      )}

      {/* 가격 타입 선택 */}
      {value.type === 'price' && (
        <select
          value={value.priceType || 'close'}
          onChange={(e) => handlePriceTypeChange(e.target.value as PriceType)}
          className="form-select small"
          style={{ minWidth: '100px' }}
        >
          <option value="close">현재가</option>
          <option value="open">시가</option>
          <option value="high">고가</option>
          <option value="low">저가</option>
        </select>
      )}

      {/* 지표 입력 */}
      {value.type === 'indicator' && (
        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          <select
            value={value.indicatorType || 'MA'}
            onChange={(e) => handleIndicatorTypeChange(e.target.value as IndicatorType)}
            className="form-select small"
            style={{ minWidth: '80px' }}
          >
            <option value="MA">이동평균</option>
            <option value="EMA">지수평균</option>
            <option value="RSI">RSI</option>
            <option value="MACD">MACD</option>
          </select>
          
          {value.indicatorType !== 'MACD' && (
            <>
              <span>(</span>
              <input
                type="number"
                value={value.indicatorPeriod || 20}
                onChange={(e) => handleIndicatorPeriodChange(Number(e.target.value))}
                className="form-input small"
                style={{ width: '60px' }}
                min="1"
                max="200"
              />
              <span>)</span>
            </>
          )}
        </div>
      )}
    </div>
  );
};

// 백엔드 호환성을 위한 변환 함수들
export const conditionValueToString = (value: ConditionValue): string => {
  switch (value.type) {
    case 'number':
      return String(value.numericValue || 0);
    case 'price':
      return value.priceType || 'close';
    case 'indicator':
      const type = value.indicatorType || 'MA';
      if (type === 'MACD') return 'MACD';
      return `${type}(${value.indicatorPeriod || 20})`;
    default:
      return '0';
  }
};

export const stringToConditionValue = (str: string | number): ConditionValue => {
  if (typeof str === 'number') {
    return { type: 'number', numericValue: str };
  }
  
  const strValue = String(str);
  
  // 가격 타입 체크
  if (['close', 'open', 'high', 'low'].includes(strValue)) {
    return { type: 'price', priceType: strValue as PriceType };
  }
  
  // 지표 타입 체크
  if (strValue === 'MACD') {
    return { type: 'indicator', indicatorType: 'MACD' };
  }
  
  const indicatorMatch = strValue.match(/^(MA|EMA|RSI)\((\d+)\)$/);
  if (indicatorMatch) {
    return {
      type: 'indicator',
      indicatorType: indicatorMatch[1] as IndicatorType,
      indicatorPeriod: parseInt(indicatorMatch[2])
    };
  }
  
  // 숫자 문자열
  const numValue = parseFloat(strValue);
  if (!isNaN(numValue)) {
    return { type: 'number', numericValue: numValue };
  }
  
  // 기본값
  return { type: 'number', numericValue: 0 };
};