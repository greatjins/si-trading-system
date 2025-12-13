/**
 * 전략 빌더 페이지 V2 - 타입 안전성 보장
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { PageLayout } from '../components/Layout/PageLayout';
import { httpClient } from '../services/http';
import { ConditionCard, Condition, IndicatorInfo } from '../components/StrategyBuilder/ConditionCard';
import { conditionValueToString, stringToConditionValue } from '../components/StrategyBuilder/ConditionValueInput';
import '../components/StrategyBuilder/StrategyBuilder.css';

// 전략 인터페이스 (기존과 동일하지만 Condition 타입만 변경)
interface Strategy {
  name: string;
  description: string;
  stockSelection: any; // 기존과 동일
  buyConditions: Condition[];
  sellConditions: Condition[];
  entryStrategy: any; // 기존과 동일
  positionManagement: any; // 기존과 동일
}

export const StrategyBuilderPageV2: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [editingStrategyId, setEditingStrategyId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'stock' | 'buy' | 'sell' | 'position' | 'entry'>('stock');
  const [indicators, setIndicators] = useState<IndicatorInfo[]>([]);
  const [categories, setCategories] = useState<Array<{ id: string; name: string }>>([]);
  
  const [strategy, setStrategy] = useState<Strategy>({
    name: '',
    description: '',
    stockSelection: {
      excludeManaged: true,
      excludeClearing: true,
      excludePreferred: false,
      excludeSpac: true,
      minListingDays: 90,
    },
    buyConditions: [],
    sellConditions: [],
    entryStrategy: {
      type: 'single',
      pyramidLevels: [],
      maxLevels: 4,
      maxPositionSize: 40,
      minInterval: 1,
    },
    positionManagement: {
      sizingMethod: 'fixed',
      positionSize: 0.1,
      maxPositions: 5,
      stopLoss: { enabled: false },
      takeProfit: { enabled: false },
      trailingStop: { enabled: false }
    }
  });

  // URL 파라미터에서 edit ID 가져오기
  useEffect(() => {
    const editId = searchParams.get('edit');
    
    if (editId) {
      setEditingStrategyId(Number(editId));
      loadStrategy(Number(editId));
    }
  }, []);

  // 지표 목록 로드
  useEffect(() => {
    const loadIndicators = async () => {
      try {
        const response = await httpClient.get('/api/strategy-builder/indicators');
        setIndicators(response.data.indicators);
        setCategories(response.data.categories);
        console.log('✅ 지표 목록 로드:', response.data);
      } catch (err) {
        console.error('❌ 지표 목록 로드 실패:', err);
      }
    };
    loadIndicators();
  }, []);

  // 전략 로드
  const loadStrategy = async (strategyId: number) => {
    setIsLoading(true);
    try {
      const response = await httpClient.get(`/api/strategy-builder/${strategyId}`);
      const loadedStrategy = response.data;
      
      if (loadedStrategy.config) {
        setStrategy({
          name: loadedStrategy.config.name,
          description: loadedStrategy.config.description,
          stockSelection: loadedStrategy.config.stockSelection,
          buyConditions: loadedStrategy.config.buyConditions.map((condition: any) => ({
            ...condition,
            value: stringToConditionValue(condition.value)
          })),
          sellConditions: loadedStrategy.config.sellConditions.map((condition: any) => ({
            ...condition,
            value: stringToConditionValue(condition.value)
          })),
          entryStrategy: loadedStrategy.config.entryStrategy,
          positionManagement: loadedStrategy.config.positionManagement,
        });
      }
    } catch (error) {
      console.error('전략 로드 실패:', error);
      alert('전략을 불러올 수 없습니다');
    } finally {
      setIsLoading(false);
    }
  };

  // 매수 조건 추가
  const addBuyCondition = () => {
    const defaultIndicator = indicators[0] || { id: 'ma', parameters: [{ name: 'period', default: 20 }], operators: ['>'] };
    const newCondition: Condition = {
      id: Date.now().toString(),
      type: 'indicator',
      indicator: defaultIndicator.id,
      operator: defaultIndicator.operators[0],
      value: { type: 'number', numericValue: 0 },
      period: defaultIndicator.parameters[0]?.default || 20,
    };
    setStrategy({
      ...strategy,
      buyConditions: [...strategy.buyConditions, newCondition],
    });
  };

  // 매도 조건 추가
  const addSellCondition = () => {
    const defaultIndicator = indicators[0] || { id: 'ma', parameters: [{ name: 'period', default: 20 }], operators: ['<'] };
    const newCondition: Condition = {
      id: Date.now().toString(),
      type: 'indicator',
      indicator: defaultIndicator.id,
      operator: defaultIndicator.operators[0],
      value: { type: 'number', numericValue: 0 },
      period: defaultIndicator.parameters[0]?.default || 20,
    };
    setStrategy({
      ...strategy,
      sellConditions: [...strategy.sellConditions, newCondition],
    });
  };

  // 조건 업데이트
  const updateBuyCondition = (conditionId: string, updatedCondition: Condition) => {
    setStrategy({
      ...strategy,
      buyConditions: strategy.buyConditions.map(c => 
        c.id === conditionId ? updatedCondition : c
      )
    });
  };

  const updateSellCondition = (conditionId: string, updatedCondition: Condition) => {
    setStrategy({
      ...strategy,
      sellConditions: strategy.sellConditions.map(c => 
        c.id === conditionId ? updatedCondition : c
      )
    });
  };

  // 조건 삭제
  const removeBuyCondition = (conditionId: string) => {
    setStrategy({
      ...strategy,
      buyConditions: strategy.buyConditions.filter(c => c.id !== conditionId)
    });
  };

  const removeSellCondition = (conditionId: string) => {
    setStrategy({
      ...strategy,
      sellConditions: strategy.sellConditions.filter(c => c.id !== conditionId)
    });
  };

  // 전략 저장
  const handleSave = async () => {
    if (!strategy.name) {
      alert('전략 이름을 입력하세요');
      return;
    }
    
    console.log('💾 전략 저장:', strategy);
    
    try {
      // 백엔드 호환성을 위해 조건 값들을 문자열로 변환
      const convertedStrategy = {
        ...strategy,
        buyConditions: strategy.buyConditions.map(condition => ({
          ...condition,
          value: conditionValueToString(condition.value)
        })),
        sellConditions: strategy.sellConditions.map(condition => ({
          ...condition,
          value: conditionValueToString(condition.value)
        }))
      };
      
      const payload = editingStrategyId 
        ? { ...convertedStrategy, strategy_id: editingStrategyId }
        : convertedStrategy;
      
      const response = await httpClient.post('/api/strategy-builder/save', payload);
      console.log('✅ 저장 성공:', response.data);
      
      const goToBacktest = confirm(
        `전략이 저장되었습니다!\n\n이름: ${response.data.name}\n\n백테스트를 실행하시겠습니까?`
      );
      
      if (goToBacktest) {
        navigate(`/backtest?strategy=${response.data.strategy_id}`);
      }
    } catch (err: any) {
      console.error('❌ 저장 실패:', err);
      alert(`저장 실패: ${err.response?.data?.detail || err.message}`);
    }
  };

  if (isLoading) {
    return (
      <PageLayout title="전략 빌더">
        <div style={{ padding: '40px', textAlign: 'center' }}>
          <div>전략 로딩 중...</div>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout 
      title={editingStrategyId ? "전략 수정" : "전략 빌더 V2"} 
      description="타입 안전한 노코드 전략 생성"
    >
      <div className="builder-content">
        {/* 전략 기본 정보 */}
        <div className="builder-section">
          <h2>전략 정보</h2>
          <div className="form-group">
            <label>전략 이름</label>
            <input
              type="text"
              value={strategy.name}
              onChange={(e) => setStrategy({ ...strategy, name: e.target.value })}
              placeholder="예: ICT 기반 스마트머니 전략"
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label>설명</label>
            <textarea
              value={strategy.description}
              onChange={(e) => setStrategy({ ...strategy, description: e.target.value })}
              placeholder="전략에 대한 설명을 입력하세요"
              className="form-textarea"
              rows={3}
            />
          </div>
        </div>

        {/* 탭 네비게이션 */}
        <div className="builder-tabs">
          <button
            className={`tab-btn ${activeTab === 'buy' ? 'active' : ''}`}
            onClick={() => setActiveTab('buy')}
          >
            🎯 매수 조건
          </button>
          <button
            className={`tab-btn ${activeTab === 'sell' ? 'active' : ''}`}
            onClick={() => setActiveTab('sell')}
          >
            💰 매도 조건
          </button>
        </div>

        {/* 탭 컨텐츠 */}
        <div className="tab-content">
          {/* 매수 조건 */}
          {activeTab === 'buy' && (
            <div className="builder-section">
              <h3>매수 조건</h3>
              <p className="section-desc">어떤 신호가 나타나면 매수할지 조건을 설정하세요 (AND 조건)</p>
              
              {strategy.buyConditions.map((condition) => (
                <ConditionCard
                  key={condition.id}
                  condition={condition}
                  indicators={indicators}
                  categories={categories}
                  onChange={(updatedCondition) => updateBuyCondition(condition.id, updatedCondition)}
                  onRemove={() => removeBuyCondition(condition.id)}
                />
              ))}
              
              <button onClick={addBuyCondition} className="btn btn-secondary">
                + 매수 조건 추가
              </button>
              
              <div className="info-box" style={{ marginTop: '24px' }}>
                <strong>💡 ICT 이론 기반 매수 조건 예시</strong>
                <p><strong>🎯 BOS (Break of Structure) 패턴:</strong></p>
                <p>• BOS &gt; 고점 돌파 (구조적 상승 확인)</p>
                <p>• Smart Money &gt; 상승 (기관 자금 유입)</p>
                <p>• Fair Value Gap &gt; 갭 내부 (공정가치 리테스트)</p>
                <br />
                <p><strong>📈 이평선 밀집 → 상승전환:</strong></p>
                <p>• MA(5) &gt; MA(20) (단기 &gt; 중기)</p>
                <p>• MA(20) &gt; MA(60) (중기 &gt; 장기)</p>
                <p>• 거래량 &gt; MA(20) (거래량 급증)</p>
              </div>
            </div>
          )}

          {/* 매도 조건 */}
          {activeTab === 'sell' && (
            <div className="builder-section">
              <h3>매도 조건</h3>
              <p className="section-desc">어떤 신호가 나타나면 매도할지 조건을 설정하세요 (OR 조건)</p>
              
              {strategy.sellConditions.map((condition) => (
                <ConditionCard
                  key={condition.id}
                  condition={condition}
                  indicators={indicators}
                  categories={categories}
                  onChange={(updatedCondition) => updateSellCondition(condition.id, updatedCondition)}
                  onRemove={() => removeSellCondition(condition.id)}
                />
              ))}
              
              <button onClick={addSellCondition} className="btn btn-secondary">
                + 매도 조건 추가
              </button>
              
              <div className="info-box" style={{ marginTop: '24px' }}>
                <strong>💡 ICT 이론 기반 매도 조건 예시</strong>
                <p><strong>🔴 Liquidity Pool 도달:</strong></p>
                <p>• Liquidity Pool &gt; 풀 근처 (저항선 도달)</p>
                <p>• Smart Money &gt; 하락 (기관 자금 이탈)</p>
                <br />
                <p><strong>📉 추세 전환 감지:</strong></p>
                <p>• MA(5) &lt; MA(20) (단기 하향 돌파)</p>
                <p>• RSI(14) &gt; 70 (과매수 구간)</p>
              </div>
            </div>
          )}
        </div>

        {/* 저장 버튼 */}
        <div className="builder-actions">
          <button onClick={handleSave} className="btn btn-primary btn-large">
            {editingStrategyId ? '✏️ 전략 수정' : '💾 전략 저장'}
          </button>
          <button 
            className="btn btn-secondary btn-large"
            onClick={() => navigate('/backtest')}
          >
            🧪 백테스트 실행
          </button>
        </div>
      </div>
    </PageLayout>
  );
};