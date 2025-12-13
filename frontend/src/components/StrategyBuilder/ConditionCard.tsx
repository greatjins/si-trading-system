/**
 * 조건 카드 컴포넌트 - 매수/매도 조건 입력
 */
import React from 'react';
import { ConditionValueInput, ConditionValue } from './ConditionValueInput';

export interface IndicatorInfo {
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

export interface Condition {
  id: string;
  type: 'indicator' | 'price' | 'volume';
  indicator?: string;
  operator: string;
  value: ConditionValue;
  period?: number;
  [key: string]: any; // 동적 파라미터들
}

interface Props {
  condition: Condition;
  indicators: IndicatorInfo[];
  categories: Array<{ id: string; name: string }>;
  onChange: (condition: Condition) => void;
  onRemove: () => void;
}

export const ConditionCard: React.FC<Props> = ({
  condition,
  indicators,
  categories,
  onChange,
  onRemove
}) => {
  
  const indicatorInfo = indicators.find(ind => ind.id === condition.indicator);
  
  const handleIndicatorChange = (indicatorId: string) => {
    const newIndicator = indicators.find(ind => ind.id === indicatorId);
    if (!newIndicator) return;
    
    const updatedCondition: Condition = {
      ...condition,
      indicator: indicatorId,
      operator: newIndicator.operators[0] || '>',
      period: newIndicator.parameters.find(p => p.name === 'period')?.default
    };
    
    onChange(updatedCondition);
  };
  
  const handleOperatorChange = (operator: string) => {
    onChange({ ...condition, operator });
  };
  
  const handleValueChange = (value: ConditionValue) => {
    onChange({ ...condition, value });
  };
  
  const handleParameterChange = (paramName: string, paramValue: number) => {
    onChange({ ...condition, [paramName]: paramValue });
  };
  
  const getOperatorLabel = (op: string): string => {
    const labels: Record<string, string> = {
      'cross_above': '상향 돌파',
      'cross_below': '하향 돌파',
      'cloud_above': '구름 위',
      'cloud_below': '구름 아래',
      'break_high': '고점 돌파',
      'break_low': '저점 돌파',
      'in_gap': '갭 내부',
      'above_gap': '갭 위',
      'below_gap': '갭 아래',
      'in_block': '블록 내부',
      'above_block': '블록 위',
      'below_block': '블록 아래',
      'near_pool': '풀 근처',
      'sweep_pool': '풀 스윕',
      'bullish': '상승',
      'bearish': '하락',
      '>=': '≥',
      '<=': '≤'
    };
    return labels[op] || op;
  };

  return (
    <div className="condition-card">
      <div className="condition-row">
        {/* 지표 선택 */}
        <select
          value={condition.indicator || ''}
          onChange={(e) => handleIndicatorChange(e.target.value)}
          className="form-select"
        >
          {categories.map(cat => (
            <optgroup key={cat.id} label={cat.name}>
              {indicators.filter(ind => ind.category === cat.id).map(ind => (
                <option key={ind.id} value={ind.id}>{ind.name}</option>
              ))}
            </optgroup>
          ))}
        </select>
        
        {/* 동적 파라미터 입력 */}
        {indicatorInfo?.parameters.map(param => (
          <input
            key={param.name}
            type="number"
            value={condition[param.name] || param.default}
            onChange={(e) => handleParameterChange(param.name, Number(e.target.value))}
            placeholder={param.name}
            min={param.min}
            max={param.max}
            step={param.step}
            className="form-input small"
            title={param.name}
          />
        ))}
        
        {/* 연산자 선택 */}
        <select
          value={condition.operator}
          onChange={(e) => handleOperatorChange(e.target.value)}
          className="form-select small"
        >
          {indicatorInfo?.operators.map(op => (
            <option key={op} value={op}>
              {getOperatorLabel(op)}
            </option>
          ))}
        </select>
        
        {/* 값 입력 */}
        <ConditionValueInput
          value={condition.value}
          onChange={handleValueChange}
          className="small"
        />
        
        {/* 삭제 버튼 */}
        <button
          onClick={onRemove}
          className="btn btn-sm btn-danger"
        >
          삭제
        </button>
      </div>
      
      {/* 지표 설명 */}
      {indicatorInfo && (
        <div className="condition-hint">
          💡 {indicatorInfo.description}
        </div>
      )}
    </div>
  );
};