/**
 * 전략 빌더 페이지 - 노코드 전략 생성
 */
import { useState, useEffect } from 'react';
import { PageLayout } from '../components/Layout/PageLayout';
import { httpClient } from '../services/http';

interface IndicatorParameter {
  name: string;
  type: string;
  default: number;
  min?: number;
  max?: number;
  step?: number;
}

interface IndicatorInfo {
  id: string;
  name: string;
  category: string;
  parameters: IndicatorParameter[];
  operators: string[];
  description: string;
}

interface Condition {
  id: string;
  type: 'indicator' | 'price' | 'volume';
  indicator?: string;
  operator: string;
  value: string | number;
  period?: number;
  // ATR 관련
  atrMultiple?: number;
  // 볼린저 밴드
  stdDev?: number;
  // MACD
  fastPeriod?: number;
  slowPeriod?: number;
  signalPeriod?: number;
}

interface PyramidLevel {
  level: number;
  condition: 'initial' | 'price_increase' | 'indicator';
  priceChange?: number; // % (0, 10, 18, 25)
  units: number; // 유닛 수 (1.0, 1.0, 1.0, 0.5)
  description?: string;
}

interface Strategy {
  name: string;
  description: string;
  // 종목 선정
  stockSelection: {
    // 기본 필터
    marketCap?: { min: number; max: number }; // 시가총액 (억원)
    volume?: { min: number }; // 최소 거래량 (주)
    volumeValue?: { min: number }; // 최소 거래대금 (백만원)
    price?: { min: number; max: number }; // 가격 범위 (원)
    
    // 업종/섹터
    sector?: string[]; // 업종
    market?: string[]; // 시장 (코스피/코스닥/코넥스)
    
    // 재무 지표
    per?: { min: number; max: number }; // PER
    pbr?: { min: number; max: number }; // PBR
    roe?: { min: number }; // ROE (%)
    debtRatio?: { max: number }; // 부채비율 (%)
    
    // 기술적 지표
    pricePosition?: { // 52주 최고가/최저가 대비 위치
      from52WeekHigh?: { min: number; max: number }; // % (0~100)
      from52WeekLow?: { min: number; max: number }; // % (0~100)
    };
    
    // 제외 조건
    excludeManaged?: boolean; // 관리종목 제외
    excludeClearing?: boolean; // 정리매매 제외
    excludePreferred?: boolean; // 우선주 제외
    excludeSpac?: boolean; // SPAC 제외
    minListingDays?: number; // 최소 상장일수
  };
  // 매수 조건
  buyConditions: Condition[];
  // 매도 조건
  sellConditions: Condition[];
  // 진입 전략
  entryStrategy: {
    type: 'single' | 'pyramid';
    pyramidLevels?: PyramidLevel[];
    maxLevels?: number;
    maxPositionSize?: number; // 총 포지션 한도 (계좌 %)
    minInterval?: number; // 최소 진입 간격 (일)
  };
  // 포지션 관리
  positionManagement: {
    // 포지션 사이징 방식
    sizingMethod: 'fixed' | 'atr_risk' | 'kelly' | 'volatility';
    
    // 고정 비율 (기존)
    positionSize?: number; // 비율 (0.1 = 10%)
    
    // ATR 기반 리스크 관리
    accountRisk?: number; // 트레이드당 최대 손실 % (예: 1.0 = 1%)
    atrPeriod?: number; // ATR 계산 기간
    atrMultiple?: number; // 손절 배수 (예: 2.0 = ATR × 2)
    
    // 켈리 공식
    winRate?: number; // 승률 (0-1)
    winLossRatio?: number; // 평균 수익/손실 비율
    kellyFraction?: number; // 켈리 비율 조정 (0-1, 보통 0.25)
    
    // 변동성 기반
    volatilityPeriod?: number; // 변동성 계산 기간
    volatilityTarget?: number; // 목표 변동성 %
    
    maxPositions: number;
    
    // 손절 설정
    stopLoss?: {
      enabled: boolean;
      method: 'fixed' | 'atr' | 'support' | 'time';
      fixedPercent?: number; // 고정 %
      atrMultiple?: number; // ATR 배수
      minPercent?: number; // 최소 손절 %
      maxPercent?: number; // 최대 손절 %
      timeDays?: number; // 시간 기반 (N일 후 자동 청산)
    };
    
    // 익절 설정
    takeProfit?: {
      enabled: boolean;
      method: 'fixed' | 'r_multiple' | 'partial';
      fixedPercent?: number; // 고정 %
      rMultiple?: number; // R배수 (리스크 대비)
      partialLevels?: Array<{ percent: number; ratio: number }>; // 분할 익절
    };
    
    // 트레일링 스탑
    trailingStop?: {
      enabled: boolean;
      method: 'atr' | 'percentage' | 'parabolic_sar';
      atrMultiple?: number; // ATR 배수
      percentage?: number; // 고정 %
      activationProfit?: number; // 활성화 수익률 %
      updateFrequency?: 'every_bar' | 'new_high';
    };
  };
}

export const StrategyBuilderPage = () => {
  const [editingStrategyId, setEditingStrategyId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // URL 파라미터에서 edit ID 가져오기
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const editId = params.get('edit');
    
    if (editId) {
      setEditingStrategyId(Number(editId));
      loadStrategy(Number(editId));
    }
  }, []);
  
  // 전략 로드
  const loadStrategy = async (strategyId: number) => {
    setIsLoading(true);
    try {
      const response = await httpClient.get(`/api/strategy-builder/${strategyId}`);
      const loadedStrategy = response.data;
      
      // config에서 전략 설정 복원
      if (loadedStrategy.config) {
        setStrategy({
          name: loadedStrategy.config.name,
          description: loadedStrategy.config.description,
          stockSelection: loadedStrategy.config.stockSelection,
          buyConditions: loadedStrategy.config.buyConditions,
          sellConditions: loadedStrategy.config.sellConditions,
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
      pyramidLevels: [
        { level: 1, condition: 'initial', priceChange: 0, units: 1.0, description: '첫 진입' },
        { level: 2, condition: 'price_increase', priceChange: 10, units: 1.0, description: '10% 상승 시' },
        { level: 3, condition: 'price_increase', priceChange: 18, units: 1.0, description: '18% 상승 시' },
        { level: 4, condition: 'price_increase', priceChange: 25, units: 0.5, description: '25% 상승 시' },
      ],
      maxLevels: 4,
      maxPositionSize: 40,
      minInterval: 1,
    },
    positionManagement: {
      sizingMethod: 'fixed',
      positionSize: 0.1,
      accountRisk: 1.0,
      atrPeriod: 20,
      atrMultiple: 2.0,
      winRate: 0.5,
      winLossRatio: 2.0,
      kellyFraction: 0.25,
      volatilityPeriod: 20,
      volatilityTarget: 2.0,
      maxPositions: 5,
      stopLoss: {
        enabled: true,
        method: 'fixed',
        fixedPercent: 5,
        atrMultiple: 2.0,
        minPercent: 3,
        maxPercent: 10,
        timeDays: 30,
      },
      takeProfit: {
        enabled: true,
        method: 'fixed',
        fixedPercent: 10,
        rMultiple: 3,
        partialLevels: [
          { percent: 50, ratio: 2 },
          { percent: 50, ratio: 3 },
        ],
      },
      trailingStop: {
        enabled: false,
        method: 'atr',
        atrMultiple: 3.0,
        percentage: 5.0,
        activationProfit: 5.0,
        updateFrequency: 'every_bar',
      },
    },
  });
  
  const [activeTab, setActiveTab] = useState<'stock' | 'buy' | 'sell' | 'position' | 'entry'>('stock');
  const [indicators, setIndicators] = useState<IndicatorInfo[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  
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
  
  // 매수 조건 추가
  const addBuyCondition = () => {
    const defaultIndicator = indicators[0] || { id: 'ma', parameters: [{ name: 'period', default: 20 }], operators: ['>'] };
    const newCondition: Condition = {
      id: Date.now().toString(),
      type: 'indicator',
      indicator: defaultIndicator.id,
      operator: defaultIndicator.operators[0],
      value: 0,
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
      value: 0,
      period: defaultIndicator.parameters[0]?.default || 20,
    };
    setStrategy({
      ...strategy,
      sellConditions: [...strategy.sellConditions, newCondition],
    });
  };
  
  // 조건 삭제
  const removeCondition = (id: string, type: 'buy' | 'sell') => {
    if (type === 'buy') {
      setStrategy({
        ...strategy,
        buyConditions: strategy.buyConditions.filter((c) => c.id !== id),
      });
    } else {
      setStrategy({
        ...strategy,
        sellConditions: strategy.sellConditions.filter((c) => c.id !== id),
      });
    }
  };
  
  // 전략 저장
  const handleSave = async () => {
    if (!strategy.name) {
      alert('전략 이름을 입력하세요');
      return;
    }
    
    console.log('💾 전략 저장:', strategy);
    
    try {
      const response = await httpClient.post('/api/strategy-builder/save', strategy);
      console.log('✅ 저장 성공:', response.data);
      
      const goToBacktest = confirm(
        `전략이 저장되었습니다!\n\n이름: ${response.data.name}\n\n백테스트를 실행하시겠습니까?`
      );
      
      if (goToBacktest) {
        window.location.href = `/backtest?strategy=${response.data.strategy_id}`;
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
      title={editingStrategyId ? "전략 수정" : "전략 빌더"} 
      description={editingStrategyId ? "기존 전략을 수정합니다" : "노코드로 나만의 매매 전략을 만드세요"}
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
              placeholder="예: 골든크로스 + 거래량 급증 전략"
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
            className={`tab-btn ${activeTab === 'stock' ? 'active' : ''}`}
            onClick={() => setActiveTab('stock')}
          >
            1️⃣ 종목 선정
          </button>
          <button
            className={`tab-btn ${activeTab === 'buy' ? 'active' : ''}`}
            onClick={() => setActiveTab('buy')}
          >
            2️⃣ 매수 조건
          </button>
          <button
            className={`tab-btn ${activeTab === 'entry' ? 'active' : ''}`}
            onClick={() => setActiveTab('entry')}
          >
            3️⃣ 진입 전략
          </button>
          <button
            className={`tab-btn ${activeTab === 'sell' ? 'active' : ''}`}
            onClick={() => setActiveTab('sell')}
          >
            4️⃣ 매도 조건
          </button>
          <button
            className={`tab-btn ${activeTab === 'position' ? 'active' : ''}`}
            onClick={() => setActiveTab('position')}
          >
            5️⃣ 포지션 관리
          </button>
        </div>
        
        {/* 탭 컨텐츠 */}
        <div className="tab-content">
          {/* 종목 선정 */}
          {activeTab === 'stock' && (
            <div className="builder-section">
              <h3>종목 선정 조건</h3>
              <p className="section-desc">어떤 종목을 대상으로 할지 필터링 조건을 설정하세요</p>
              
              {/* 기본 필터 */}
              <h4 style={{ fontSize: '16px', marginTop: '24px', marginBottom: '16px' }}>📊 기본 필터</h4>
              
              <div className="condition-group">
                <label>시가총액 (억원)</label>
                <div className="range-inputs">
                  <input
                    type="number"
                    placeholder="최소 (예: 1000)"
                    className="form-input"
                    value={strategy.stockSelection.marketCap?.min || ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        marketCap: {
                          ...strategy.stockSelection.marketCap,
                          min: Number(e.target.value),
                          max: strategy.stockSelection.marketCap?.max || 0,
                        },
                      },
                    })}
                  />
                  <span>~</span>
                  <input
                    type="number"
                    placeholder="최대 (선택)"
                    className="form-input"
                    value={strategy.stockSelection.marketCap?.max || ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        marketCap: {
                          min: strategy.stockSelection.marketCap?.min || 0,
                          max: Number(e.target.value),
                        },
                      },
                    })}
                  />
                </div>
                <small>예: 1,000억 ~ 10,000억 (중형주)</small>
              </div>
              
              <div className="condition-group">
                <label>주가 범위 (원)</label>
                <div className="range-inputs">
                  <input
                    type="number"
                    placeholder="최소 (예: 5000)"
                    className="form-input"
                    value={strategy.stockSelection.price?.min || ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        price: {
                          ...strategy.stockSelection.price,
                          min: Number(e.target.value),
                          max: strategy.stockSelection.price?.max || 0,
                        },
                      },
                    })}
                  />
                  <span>~</span>
                  <input
                    type="number"
                    placeholder="최대 (예: 100000)"
                    className="form-input"
                    value={strategy.stockSelection.price?.max || ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        price: {
                          min: strategy.stockSelection.price?.min || 0,
                          max: Number(e.target.value),
                        },
                      },
                    })}
                  />
                </div>
                <small>저가주/고가주 제외 (예: 5,000원 ~ 100,000원)</small>
              </div>
              
              <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="condition-group">
                  <label>최소 거래량 (주)</label>
                  <input
                    type="number"
                    placeholder="예: 100000"
                    className="form-input"
                    value={strategy.stockSelection.volume?.min || ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        volume: { min: Number(e.target.value) },
                      },
                    })}
                  />
                  <small>유동성 확보</small>
                </div>
                
                <div className="condition-group">
                  <label>최소 거래대금 (백만원)</label>
                  <input
                    type="number"
                    placeholder="예: 1000"
                    className="form-input"
                    value={strategy.stockSelection.volumeValue?.min || ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        volumeValue: { min: Number(e.target.value) },
                      },
                    })}
                  />
                  <small>10억원 이상 권장</small>
                </div>
              </div>
              
              {/* 시장/업종 */}
              <h4 style={{ fontSize: '16px', marginTop: '32px', marginBottom: '16px' }}>🏢 시장 & 업종</h4>
              
              <div className="condition-group">
                <label>시장 선택</label>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  {['KOSPI', 'KOSDAQ', 'KONEX'].map(market => (
                    <label key={market} className="checkbox-label" style={{ padding: '8px 16px', flex: '0 0 auto' }}>
                      <input
                        type="checkbox"
                        checked={strategy.stockSelection.market?.includes(market) || false}
                        onChange={(e) => {
                          const markets = strategy.stockSelection.market || [];
                          setStrategy({
                            ...strategy,
                            stockSelection: {
                              ...strategy.stockSelection,
                              market: e.target.checked
                                ? [...markets, market]
                                : markets.filter(m => m !== market),
                            },
                          });
                        }}
                      />
                      <span>{market}</span>
                    </label>
                  ))}
                </div>
                <small>선택 안하면 전체 시장 대상</small>
              </div>
              
              {/* 재무 지표 */}
              <h4 style={{ fontSize: '16px', marginTop: '32px', marginBottom: '16px' }}>💰 재무 지표 (선택)</h4>
              
              <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="condition-group">
                  <label>PER (배)</label>
                  <div className="range-inputs">
                    <input
                      type="number"
                      placeholder="최소"
                      className="form-input"
                      value={strategy.stockSelection.per?.min || ''}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        stockSelection: {
                          ...strategy.stockSelection,
                          per: {
                            ...strategy.stockSelection.per,
                            min: Number(e.target.value),
                            max: strategy.stockSelection.per?.max || 0,
                          },
                        },
                      })}
                    />
                    <span>~</span>
                    <input
                      type="number"
                      placeholder="최대"
                      className="form-input"
                      value={strategy.stockSelection.per?.max || ''}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        stockSelection: {
                          ...strategy.stockSelection,
                          per: {
                            min: strategy.stockSelection.per?.min || 0,
                            max: Number(e.target.value),
                          },
                        },
                      })}
                    />
                  </div>
                  <small>저평가 종목 (예: 0~15배)</small>
                </div>
                
                <div className="condition-group">
                  <label>PBR (배)</label>
                  <div className="range-inputs">
                    <input
                      type="number"
                      placeholder="최소"
                      className="form-input"
                      value={strategy.stockSelection.pbr?.min || ''}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        stockSelection: {
                          ...strategy.stockSelection,
                          pbr: {
                            ...strategy.stockSelection.pbr,
                            min: Number(e.target.value),
                            max: strategy.stockSelection.pbr?.max || 0,
                          },
                        },
                      })}
                    />
                    <span>~</span>
                    <input
                      type="number"
                      placeholder="최대"
                      className="form-input"
                      value={strategy.stockSelection.pbr?.max || ''}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        stockSelection: {
                          ...strategy.stockSelection,
                          pbr: {
                            min: strategy.stockSelection.pbr?.min || 0,
                            max: Number(e.target.value),
                          },
                        },
                      })}
                    />
                  </div>
                  <small>저평가 종목 (예: 0~2배)</small>
                </div>
              </div>
              
              <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="condition-group">
                  <label>최소 ROE (%)</label>
                  <input
                    type="number"
                    placeholder="예: 10"
                    className="form-input"
                    value={strategy.stockSelection.roe?.min || ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        roe: { min: Number(e.target.value) },
                      },
                    })}
                  />
                  <small>수익성 좋은 기업 (10% 이상 권장)</small>
                </div>
                
                <div className="condition-group">
                  <label>최대 부채비율 (%)</label>
                  <input
                    type="number"
                    placeholder="예: 200"
                    className="form-input"
                    value={strategy.stockSelection.debtRatio?.max || ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        debtRatio: { max: Number(e.target.value) },
                      },
                    })}
                  />
                  <small>재무 안정성 (200% 이하 권장)</small>
                </div>
              </div>
              
              {/* 기술적 위치 */}
              <h4 style={{ fontSize: '16px', marginTop: '32px', marginBottom: '16px' }}>📈 기술적 위치 (선택)</h4>
              
              <div className="condition-group">
                <label>52주 최고가 대비 위치 (%)</label>
                <div className="range-inputs">
                  <input
                    type="number"
                    placeholder="최소 (예: 70)"
                    className="form-input"
                    value={strategy.stockSelection.pricePosition?.from52WeekHigh?.min ?? ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        pricePosition: {
                          ...strategy.stockSelection.pricePosition,
                          from52WeekHigh: {
                            min: e.target.value === '' ? 0 : Number(e.target.value),
                            max: strategy.stockSelection.pricePosition?.from52WeekHigh?.max || 100,
                          },
                        },
                      },
                    })}
                  />
                  <span>~</span>
                  <input
                    type="number"
                    placeholder="최대 (예: 100)"
                    className="form-input"
                    value={strategy.stockSelection.pricePosition?.from52WeekHigh?.max ?? ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        pricePosition: {
                          ...strategy.stockSelection.pricePosition,
                          from52WeekHigh: {
                            min: strategy.stockSelection.pricePosition?.from52WeekHigh?.min || 0,
                            max: e.target.value === '' ? 100 : Number(e.target.value),
                          },
                        },
                      },
                    })}
                  />
                </div>
                <small>고점 근처 종목 (예: 70~100% = 최고가의 70~100%)</small>
              </div>
              
              <div className="condition-group">
                <label>52주 최저가 대비 위치 (%)</label>
                <div className="range-inputs">
                  <input
                    type="number"
                    placeholder="최소 (예: 0)"
                    className="form-input"
                    value={strategy.stockSelection.pricePosition?.from52WeekLow?.min ?? ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        pricePosition: {
                          ...strategy.stockSelection.pricePosition,
                          from52WeekLow: {
                            min: e.target.value === '' ? 0 : Number(e.target.value),
                            max: strategy.stockSelection.pricePosition?.from52WeekLow?.max || 100,
                          },
                        },
                      },
                    })}
                  />
                  <span>~</span>
                  <input
                    type="number"
                    placeholder="최대 (예: 30)"
                    className="form-input"
                    value={strategy.stockSelection.pricePosition?.from52WeekLow?.max ?? ''}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        pricePosition: {
                          ...strategy.stockSelection.pricePosition,
                          from52WeekLow: {
                            min: strategy.stockSelection.pricePosition?.from52WeekLow?.min || 0,
                            max: e.target.value === '' ? 100 : Number(e.target.value),
                          },
                        },
                      },
                    })}
                  />
                </div>
                <small>저점 근처 종목 (예: 0~30% = 최저가 근처)</small>
              </div>
              
              {/* 제외 조건 */}
              <h4 style={{ fontSize: '16px', marginTop: '32px', marginBottom: '16px' }}>🚫 제외 조건</h4>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <label className="checkbox-label" style={{ padding: '12px' }}>
                  <input
                    type="checkbox"
                    checked={strategy.stockSelection.excludeManaged || false}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        excludeManaged: e.target.checked,
                      },
                    })}
                  />
                  <span>관리종목 제외 (권장)</span>
                </label>
                
                <label className="checkbox-label" style={{ padding: '12px' }}>
                  <input
                    type="checkbox"
                    checked={strategy.stockSelection.excludeClearing || false}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        excludeClearing: e.target.checked,
                      },
                    })}
                  />
                  <span>정리매매 종목 제외 (권장)</span>
                </label>
                
                <label className="checkbox-label" style={{ padding: '12px' }}>
                  <input
                    type="checkbox"
                    checked={strategy.stockSelection.excludePreferred || false}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        excludePreferred: e.target.checked,
                      },
                    })}
                  />
                  <span>우선주 제외</span>
                </label>
                
                <label className="checkbox-label" style={{ padding: '12px' }}>
                  <input
                    type="checkbox"
                    checked={strategy.stockSelection.excludeSpac || false}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      stockSelection: {
                        ...strategy.stockSelection,
                        excludeSpac: e.target.checked,
                      },
                    })}
                  />
                  <span>SPAC 제외 (권장)</span>
                </label>
              </div>
              
              <div className="condition-group" style={{ marginTop: '16px' }}>
                <label>최소 상장일수 (일)</label>
                <input
                  type="number"
                  placeholder="예: 90"
                  className="form-input"
                  value={strategy.stockSelection.minListingDays || ''}
                  onChange={(e) => setStrategy({
                    ...strategy,
                    stockSelection: {
                      ...strategy.stockSelection,
                      minListingDays: Number(e.target.value),
                    },
                  })}
                />
                <small>신규 상장 종목 제외 (90일 이상 권장)</small>
              </div>
              
              <div className="info-box" style={{ marginTop: '24px' }}>
                <strong>💡 종목 선정 팁</strong>
                <p>• 너무 많은 조건을 설정하면 대상 종목이 없을 수 있습니다</p>
                <p>• 시가총액, 거래량, 제외 조건은 필수로 설정하는 것을 권장합니다</p>
                <p>• 재무 지표는 가치투자 전략에 유용합니다</p>
                <p>• 기술적 위치는 추세 추종 전략에 유용합니다</p>
              </div>
            </div>
          )}
          
          {/* 매수 조건 */}
          {activeTab === 'buy' && (
            <div className="builder-section">
              <h3>매수 조건</h3>
              <p className="section-desc">어떤 신호가 나타나면 매수할지 조건을 설정하세요 (AND 조건)</p>
              
              {strategy.buyConditions.map((condition) => {
                const indicatorInfo = indicators.find(ind => ind.id === condition.indicator);
                
                return (
                  <div key={condition.id} className="condition-card">
                    <div className="condition-row">
                      <select
                        value={condition.indicator}
                        onChange={(e) => {
                          const newIndicator = indicators.find(ind => ind.id === e.target.value);
                          const updated = strategy.buyConditions.map((c) =>
                            c.id === condition.id ? { 
                              ...c, 
                              indicator: e.target.value,
                              operator: newIndicator?.operators[0] || '>',
                              period: newIndicator?.parameters.find(p => p.name === 'period')?.default
                            } : c
                          );
                          setStrategy({ ...strategy, buyConditions: updated });
                        }}
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
                          value={(condition as any)[param.name] || param.default}
                          onChange={(e) => {
                            const updated = strategy.buyConditions.map((c) =>
                              c.id === condition.id ? { ...c, [param.name]: Number(e.target.value) } : c
                            );
                            setStrategy({ ...strategy, buyConditions: updated });
                          }}
                          placeholder={param.name}
                          min={param.min}
                          max={param.max}
                          step={param.step}
                          className="form-input small"
                          title={param.name}
                        />
                      ))}
                      
                      <select
                        value={condition.operator}
                        onChange={(e) => {
                          const updated = strategy.buyConditions.map((c) =>
                            c.id === condition.id ? { ...c, operator: e.target.value } : c
                          );
                          setStrategy({ ...strategy, buyConditions: updated });
                        }}
                        className="form-select small"
                      >
                        {indicatorInfo?.operators.map(op => (
                          <option key={op} value={op}>
                            {op === 'cross_above' ? '상향 돌파' : 
                             op === 'cross_below' ? '하향 돌파' :
                             op === 'cloud_above' ? '구름 위' :
                             op === 'cloud_below' ? '구름 아래' :
                             op === '>=' ? '≥' :
                             op === '<=' ? '≤' : op}
                          </option>
                        ))}
                      </select>
                      
                      <input
                        type="text"
                        value={condition.value}
                        onChange={(e) => {
                          const updated = strategy.buyConditions.map((c) =>
                            c.id === condition.id ? { ...c, value: e.target.value } : c
                          );
                          setStrategy({ ...strategy, buyConditions: updated });
                        }}
                        placeholder="값 또는 MA(50)"
                        className="form-input"
                      />
                      
                      <button
                        onClick={() => removeCondition(condition.id, 'buy')}
                        className="btn btn-sm btn-danger"
                      >
                        삭제
                      </button>
                    </div>
                    {indicatorInfo && (
                      <div className="condition-hint">
                        💡 {indicatorInfo.description}
                      </div>
                    )}
                  </div>
                );
              })}
              
              <button onClick={addBuyCondition} className="btn btn-secondary">
                + 매수 조건 추가
              </button>
            </div>
          )}
          
          {/* 진입 전략 */}
          {activeTab === 'entry' && (
            <div className="builder-section">
              <h3>진입 전략</h3>
              <p className="section-desc">일괄 진입 또는 단계적 진입(피라미딩) 방식을 선택하세요</p>
              
              <div className="condition-group">
                <label>진입 방식</label>
                <div className="radio-group-inline">
                  <label className="radio-label-inline">
                    <input
                      type="radio"
                      name="entryType"
                      value="single"
                      checked={strategy.entryStrategy.type === 'single'}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        entryStrategy: {
                          ...strategy.entryStrategy,
                          type: e.target.value as any,
                        },
                      })}
                    />
                    <span>일괄 진입 (간단)</span>
                  </label>
                  
                  <label className="radio-label-inline">
                    <input
                      type="radio"
                      name="entryType"
                      value="pyramid"
                      checked={strategy.entryStrategy.type === 'pyramid'}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        entryStrategy: {
                          ...strategy.entryStrategy,
                          type: e.target.value as any,
                        },
                      })}
                    />
                    <span>피라미딩 (단계적 진입)</span>
                  </label>
                </div>
              </div>
              
              {strategy.entryStrategy.type === 'single' && (
                <div className="info-box">
                  <strong>💡 일괄 진입</strong>
                  <p>매수 조건이 만족되면 한 번에 전체 포지션을 진입합니다.</p>
                  <p>장점: 단순하고 관리가 쉬움</p>
                  <p>단점: 진입 타이밍이 잘못되면 큰 손실 가능</p>
                </div>
              )}
              
              {strategy.entryStrategy.type === 'pyramid' && (
                <div className="pyramid-config">
                  <div className="info-box">
                    <strong>💡 피라미딩이란?</strong>
                    <p>추세가 확인되면 단계적으로 포지션을 추가하는 전략입니다.</p>
                    <p>장점: 리스크 분산, 추세 확인 후 진입, 평균 단가 관리</p>
                    <p>단점: 복잡한 관리, 수수료 증가, 늦은 진입 가능성</p>
                  </div>
                  
                  <div className="condition-group">
                    <label>진입 단계 수</label>
                    <input
                      type="number"
                      value={strategy.entryStrategy.maxLevels || 4}
                      onChange={(e) => {
                        const newLevels = Number(e.target.value);
                        const currentLevels = strategy.entryStrategy.pyramidLevels || [];
                        
                        // 레벨 수 조정
                        let updatedLevels = [...currentLevels];
                        if (newLevels > currentLevels.length) {
                          // 레벨 추가
                          for (let i = currentLevels.length; i < newLevels; i++) {
                            updatedLevels.push({
                              level: i + 1,
                              condition: 'price_increase',
                              priceChange: (i + 1) * 10,
                              units: 1.0,
                              description: `${(i + 1) * 10}% 상승 시`,
                            });
                          }
                        } else {
                          // 레벨 제거
                          updatedLevels = updatedLevels.slice(0, newLevels);
                        }
                        
                        setStrategy({
                          ...strategy,
                          entryStrategy: {
                            ...strategy.entryStrategy,
                            maxLevels: newLevels,
                            pyramidLevels: updatedLevels,
                          },
                        });
                      }}
                      min="2"
                      max="10"
                      className="form-input"
                    />
                    <small>권장: 3~5단계</small>
                  </div>
                  
                  {/* 피라미딩 레벨 설정 */}
                  <div className="pyramid-levels">
                    <h4 style={{ fontSize: '15px', marginBottom: '16px', marginTop: '24px' }}>진입 단계 설정</h4>
                    
                    {strategy.entryStrategy.pyramidLevels?.map((level, index) => (
                      <div key={level.level} className="pyramid-level-card">
                        <div className="level-header">
                          <span className="level-badge">{level.level}차 진입</span>
                          {index === 0 && <span className="level-tag">기본</span>}
                        </div>
                        
                        <div className="level-content">
                          {index === 0 ? (
                            <div className="condition-group">
                              <label>조건</label>
                              <input
                                type="text"
                                value="매수 시그널 발생 시 (기본)"
                                disabled
                                className="form-input"
                                style={{ opacity: 0.7 }}
                              />
                            </div>
                          ) : (
                            <div className="condition-group">
                              <label>진입 조건</label>
                              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                                <span style={{ whiteSpace: 'nowrap' }}>첫 진입가 대비</span>
                                <input
                                  type="number"
                                  value={level.priceChange || 0}
                                  onChange={(e) => {
                                    const updated = strategy.entryStrategy.pyramidLevels?.map((l) =>
                                      l.level === level.level ? { ...l, priceChange: Number(e.target.value) } : l
                                    );
                                    setStrategy({
                                      ...strategy,
                                      entryStrategy: {
                                        ...strategy.entryStrategy,
                                        pyramidLevels: updated,
                                      },
                                    });
                                  }}
                                  min="0"
                                  max="100"
                                  step="1"
                                  className="form-input"
                                  style={{ width: '100px' }}
                                />
                                <span>% 상승 시</span>
                              </div>
                            </div>
                          )}
                          
                          <div className="condition-group">
                            <label>투자 비율 (유닛)</label>
                            <input
                              type="number"
                              value={level.units}
                              onChange={(e) => {
                                const updated = strategy.entryStrategy.pyramidLevels?.map((l) =>
                                  l.level === level.level ? { ...l, units: Number(e.target.value) } : l
                                );
                                setStrategy({
                                  ...strategy,
                                  entryStrategy: {
                                    ...strategy.entryStrategy,
                                    pyramidLevels: updated,
                                  },
                                });
                              }}
                              min="0.1"
                              max="5"
                              step="0.1"
                              className="form-input"
                            />
                            <small>1.0 = 기본 단위, 0.5 = 절반, 2.0 = 2배</small>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {/* 피라미딩 제한 설정 */}
                  <div style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid var(--color-border)' }}>
                    <h4 style={{ fontSize: '15px', marginBottom: '16px' }}>피라미딩 제한</h4>
                    
                    <div className="condition-group">
                      <label>총 포지션 한도 (계좌 자산 대비 %)</label>
                      <input
                        type="number"
                        value={strategy.entryStrategy.maxPositionSize || 40}
                        onChange={(e) => setStrategy({
                          ...strategy,
                          entryStrategy: {
                            ...strategy.entryStrategy,
                            maxPositionSize: Number(e.target.value),
                          },
                        })}
                        min="10"
                        max="100"
                        step="5"
                        className="form-input"
                      />
                      <small>예: 40% = 1천만원 중 최대 400만원까지 투자</small>
                    </div>
                    
                    <div className="condition-group">
                      <label>최소 진입 간격 (일)</label>
                      <input
                        type="number"
                        value={strategy.entryStrategy.minInterval || 1}
                        onChange={(e) => setStrategy({
                          ...strategy,
                          entryStrategy: {
                            ...strategy.entryStrategy,
                            minInterval: Number(e.target.value),
                          },
                        })}
                        min="0"
                        max="30"
                        className="form-input"
                      />
                      <small>너무 빠른 연속 진입 방지. 0 = 제한 없음</small>
                    </div>
                  </div>
                  
                  <div className="example-box" style={{ marginTop: '20px' }}>
                    <strong>📊 피라미딩 예시</strong>
                    <p>계좌: 1,000만원 | 기본 단위: 100만원 (10%)</p>
                    <p>1차: 10,000원 진입 → 100만원 (10주)</p>
                    <p>2차: 11,000원 (10% 상승) → 100만원 추가 (9주)</p>
                    <p>3차: 11,800원 (18% 상승) → 100만원 추가 (8주)</p>
                    <p>4차: 12,500원 (25% 상승) → 50만원 추가 (4주)</p>
                    <p>→ 총 투자: 350만원 (31주), 평균 단가: 11,290원</p>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* 매도 조건 */}
          {activeTab === 'sell' && (
            <div className="builder-section">
              <h3>매도 조건</h3>
              <p className="section-desc">어떤 신호가 나타나면 매도할지 조건을 설정하세요 (OR 조건)</p>
              
              {/* 트레일링 스탑 섹션 */}
              <div className="trailing-stop-section">
                <div className="section-header">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={strategy.positionManagement.trailingStop?.enabled || false}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          trailingStop: {
                            ...strategy.positionManagement.trailingStop!,
                            enabled: e.target.checked,
                          },
                        },
                      })}
                    />
                    <span className="checkbox-title">🎯 트레일링 스탑 활성화</span>
                  </label>
                  <small className="checkbox-desc">수익이 나는 포지션의 손절선을 자동으로 올려 수익을 보호합니다</small>
                </div>
                
                {strategy.positionManagement.trailingStop?.enabled && (
                  <div className="trailing-stop-config">
                    <div className="info-box">
                      <strong>💡 트레일링 스탑이란?</strong>
                      <p>가격이 상승하면 손절선도 함께 올라가지만, 가격이 하락해도 손절선은 내려가지 않습니다.</p>
                      <p>예: 10,000원 진입 → 12,000원 상승 → 손절선 11,000원 → 가격 하락 시 11,000원에 매도</p>
                    </div>
                    
                    <div className="condition-group">
                      <label>트레일링 방식</label>
                      <div className="radio-group-inline">
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="trailingMethod"
                            value="atr"
                            checked={strategy.positionManagement.trailingStop?.method === 'atr'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                trailingStop: {
                                  ...strategy.positionManagement.trailingStop!,
                                  method: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>ATR 기반 (추천)</span>
                        </label>
                        
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="trailingMethod"
                            value="percentage"
                            checked={strategy.positionManagement.trailingStop?.method === 'percentage'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                trailingStop: {
                                  ...strategy.positionManagement.trailingStop!,
                                  method: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>고정 %</span>
                        </label>
                        
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="trailingMethod"
                            value="parabolic_sar"
                            checked={strategy.positionManagement.trailingStop?.method === 'parabolic_sar'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                trailingStop: {
                                  ...strategy.positionManagement.trailingStop!,
                                  method: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>Parabolic SAR</span>
                        </label>
                      </div>
                    </div>
                    
                    {/* ATR 기반 설정 */}
                    {strategy.positionManagement.trailingStop?.method === 'atr' && (
                      <div className="condition-group">
                        <label>ATR 배수</label>
                        <input
                          type="number"
                          value={strategy.positionManagement.trailingStop?.atrMultiple || 3.0}
                          onChange={(e) => setStrategy({
                            ...strategy,
                            positionManagement: {
                              ...strategy.positionManagement,
                              trailingStop: {
                                ...strategy.positionManagement.trailingStop!,
                                atrMultiple: Number(e.target.value),
                              },
                            },
                          })}
                          min="0.5"
                          max="10"
                          step="0.5"
                          className="form-input"
                        />
                        <small>손절선 = 최고가 - (ATR × 배수). 권장: 2.5~4.0</small>
                      </div>
                    )}
                    
                    {/* 고정 % 설정 */}
                    {strategy.positionManagement.trailingStop?.method === 'percentage' && (
                      <div className="condition-group">
                        <label>트레일링 거리 (%)</label>
                        <input
                          type="number"
                          value={strategy.positionManagement.trailingStop?.percentage || 5.0}
                          onChange={(e) => setStrategy({
                            ...strategy,
                            positionManagement: {
                              ...strategy.positionManagement,
                              trailingStop: {
                                ...strategy.positionManagement.trailingStop!,
                                percentage: Number(e.target.value),
                              },
                            },
                          })}
                          min="1"
                          max="20"
                          step="0.5"
                          className="form-input"
                        />
                        <small>손절선 = 최고가 × (1 - %). 예: 5% = 최고가에서 5% 하락 시 매도</small>
                      </div>
                    )}
                    
                    {/* Parabolic SAR 설명 */}
                    {strategy.positionManagement.trailingStop?.method === 'parabolic_sar' && (
                      <div className="info-box">
                        <strong>📈 Parabolic SAR</strong>
                        <p>추세 추종 지표로, 가격 아래에 점이 표시되며 자동으로 손절선이 올라갑니다.</p>
                        <p>추세가 강할수록 빠르게 올라가는 특징이 있습니다.</p>
                      </div>
                    )}
                    
                    <div className="condition-group">
                      <label>활성화 조건 (수익률 %)</label>
                      <input
                        type="number"
                        value={strategy.positionManagement.trailingStop?.activationProfit || 5.0}
                        onChange={(e) => setStrategy({
                          ...strategy,
                          positionManagement: {
                            ...strategy.positionManagement,
                            trailingStop: {
                              ...strategy.positionManagement.trailingStop!,
                              activationProfit: Number(e.target.value),
                            },
                          },
                        })}
                        min="0"
                        max="50"
                        step="1"
                        className="form-input"
                      />
                      <small>이 수익률 이상일 때만 트레일링 스탑 작동. 0 = 즉시 활성화</small>
                    </div>
                    
                    <div className="condition-group">
                      <label>업데이트 주기</label>
                      <div className="radio-group-inline">
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="updateFrequency"
                            value="every_bar"
                            checked={strategy.positionManagement.trailingStop?.updateFrequency === 'every_bar'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                trailingStop: {
                                  ...strategy.positionManagement.trailingStop!,
                                  updateFrequency: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>매 봉마다</span>
                        </label>
                        
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="updateFrequency"
                            value="new_high"
                            checked={strategy.positionManagement.trailingStop?.updateFrequency === 'new_high'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                trailingStop: {
                                  ...strategy.positionManagement.trailingStop!,
                                  updateFrequency: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>최고가 갱신 시</span>
                        </label>
                      </div>
                      <small>매 봉마다: 더 민감, 최고가 갱신 시: 더 여유있게</small>
                    </div>
                    
                    <div className="example-box">
                      <strong>📊 트레일링 스탑 예시</strong>
                      <p>진입가: 10,000원 | ATR: 200원 | 배수: 3.0 | 활성화: 5%</p>
                      <p>→ 10,500원 도달 (5% 수익) → 트레일링 스탑 활성화</p>
                      <p>→ 최고가 12,000원 → 손절선 = 12,000 - (200 × 3) = 11,400원</p>
                      <p>→ 가격 하락 시 11,400원에 자동 매도 (14% 수익 확보)</p>
                    </div>
                  </div>
                )}
              </div>
              
              <div style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid var(--color-border)' }}>
                <h4 style={{ fontSize: '16px', marginBottom: '12px' }}>기본 매도 조건</h4>
                <p className="section-desc">지표 기반 매도 신호 (트레일링 스탑과 함께 사용 가능)</p>
              </div>
              
              {strategy.sellConditions.map((condition) => {
                const indicatorInfo = indicators.find(ind => ind.id === condition.indicator);
                
                return (
                  <div key={condition.id} className="condition-card">
                    <div className="condition-row">
                      <select
                        value={condition.indicator}
                        onChange={(e) => {
                          const newIndicator = indicators.find(ind => ind.id === e.target.value);
                          const updated = strategy.sellConditions.map((c) =>
                            c.id === condition.id ? { 
                              ...c, 
                              indicator: e.target.value,
                              operator: newIndicator?.operators[0] || '<',
                              period: newIndicator?.parameters.find(p => p.name === 'period')?.default
                            } : c
                          );
                          setStrategy({ ...strategy, sellConditions: updated });
                        }}
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
                          value={(condition as any)[param.name] || param.default}
                          onChange={(e) => {
                            const updated = strategy.sellConditions.map((c) =>
                              c.id === condition.id ? { ...c, [param.name]: Number(e.target.value) } : c
                            );
                            setStrategy({ ...strategy, sellConditions: updated });
                          }}
                          placeholder={param.name}
                          min={param.min}
                          max={param.max}
                          step={param.step}
                          className="form-input small"
                          title={param.name}
                        />
                      ))}
                      
                      <select
                        value={condition.operator}
                        onChange={(e) => {
                          const updated = strategy.sellConditions.map((c) =>
                            c.id === condition.id ? { ...c, operator: e.target.value } : c
                          );
                          setStrategy({ ...strategy, sellConditions: updated });
                        }}
                        className="form-select small"
                      >
                        {indicatorInfo?.operators.map(op => (
                          <option key={op} value={op}>
                            {op === 'cross_above' ? '상향 돌파' : 
                             op === 'cross_below' ? '하향 돌파' :
                             op === 'cloud_above' ? '구름 위' :
                             op === 'cloud_below' ? '구름 아래' :
                             op === '>=' ? '≥' :
                             op === '<=' ? '≤' : op}
                          </option>
                        ))}
                      </select>
                      
                      <input
                        type="text"
                        value={condition.value}
                        onChange={(e) => {
                          const updated = strategy.sellConditions.map((c) =>
                            c.id === condition.id ? { ...c, value: e.target.value } : c
                          );
                          setStrategy({ ...strategy, sellConditions: updated });
                        }}
                        placeholder="값 또는 MA(50)"
                        className="form-input"
                      />
                      
                      <button
                        onClick={() => removeCondition(condition.id, 'sell')}
                        className="btn btn-sm btn-danger"
                      >
                        삭제
                      </button>
                    </div>
                    {indicatorInfo && (
                      <div className="condition-hint">
                        💡 {indicatorInfo.description}
                      </div>
                    )}
                  </div>
                );
              })}
              
              <button onClick={addSellCondition} className="btn btn-secondary">
                + 매도 조건 추가
              </button>
            </div>
          )}
          
          {/* 포지션 관리 */}
          {activeTab === 'position' && (
            <div className="builder-section">
              <h3>포지션 관리</h3>
              <p className="section-desc">자금 배분과 리스크 관리 설정</p>
              
              {/* 포지션 사이징 방식 선택 */}
              <div className="condition-group">
                <label>포지션 사이징 방식</label>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="sizingMethod"
                      value="fixed"
                      checked={strategy.positionManagement.sizingMethod === 'fixed'}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          sizingMethod: e.target.value as any,
                        },
                      })}
                    />
                    <span>고정 비율 (간단)</span>
                  </label>
                  
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="sizingMethod"
                      value="atr_risk"
                      checked={strategy.positionManagement.sizingMethod === 'atr_risk'}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          sizingMethod: e.target.value as any,
                        },
                      })}
                    />
                    <span>ATR 기반 리스크 관리 (추천)</span>
                  </label>
                  
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="sizingMethod"
                      value="kelly"
                      checked={strategy.positionManagement.sizingMethod === 'kelly'}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          sizingMethod: e.target.value as any,
                        },
                      })}
                    />
                    <span>켈리 공식 (고급)</span>
                  </label>
                  
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="sizingMethod"
                      value="volatility"
                      checked={strategy.positionManagement.sizingMethod === 'volatility'}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          sizingMethod: e.target.value as any,
                        },
                      })}
                    />
                    <span>변동성 기반</span>
                  </label>
                </div>
              </div>
              
              {/* 고정 비율 설정 */}
              {strategy.positionManagement.sizingMethod === 'fixed' && (
                <div className="sizing-config">
                  <div className="condition-group">
                    <label>포지션 크기 (계좌 자산 대비 %)</label>
                    <input
                      type="number"
                      value={(strategy.positionManagement.positionSize || 0.1) * 100}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          positionSize: Number(e.target.value) / 100,
                        },
                      })}
                      min="1"
                      max="100"
                      className="form-input"
                    />
                    <small>예: 10% = 1천만원 중 100만원씩 투자</small>
                  </div>
                </div>
              )}
              
              {/* ATR 기반 리스크 관리 */}
              {strategy.positionManagement.sizingMethod === 'atr_risk' && (
                <div className="sizing-config">
                  <div className="info-box">
                    <strong>💡 ATR 기반 리스크 관리란?</strong>
                    <p>변동성(ATR)에 따라 포지션 크기를 자동 조절하여 각 트레이드의 리스크를 일정하게 유지합니다.</p>
                    <p className="formula">포지션 크기 = (계좌 × 리스크%) / (ATR × 배수)</p>
                  </div>
                  
                  <div className="condition-group">
                    <label>계좌 리스크 (트레이드당 최대 손실 %)</label>
                    <input
                      type="number"
                      value={strategy.positionManagement.accountRisk || 1.0}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          accountRisk: Number(e.target.value),
                        },
                      })}
                      min="0.1"
                      max="10"
                      step="0.1"
                      className="form-input"
                    />
                    <small>권장: 1~2% (보수적), 3~5% (공격적)</small>
                  </div>
                  
                  <div className="condition-group">
                    <label>ATR 기간 (일)</label>
                    <input
                      type="number"
                      value={strategy.positionManagement.atrPeriod || 20}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          atrPeriod: Number(e.target.value),
                        },
                      })}
                      min="5"
                      max="50"
                      className="form-input"
                    />
                    <small>일반적으로 14~20일 사용</small>
                  </div>
                  
                  <div className="condition-group">
                    <label>손절 배수 (ATR × 배수)</label>
                    <input
                      type="number"
                      value={strategy.positionManagement.atrMultiple || 2.0}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          atrMultiple: Number(e.target.value),
                        },
                      })}
                      min="0.5"
                      max="5"
                      step="0.1"
                      className="form-input"
                    />
                    <small>손절선 = 진입가 - (ATR × 배수)</small>
                  </div>
                  
                  <div className="example-box">
                    <strong>📊 예시 계산</strong>
                    <p>계좌: 1,000만원 | 리스크: 1% | ATR: 1,000원 | 배수: 2.0</p>
                    <p>→ 포지션 크기 = (10,000,000 × 0.01) / (1,000 × 2) = 50주</p>
                    <p>→ 최대 손실 = 50주 × 2,000원 = 100,000원 (1%)</p>
                  </div>
                </div>
              )}
              
              {/* 켈리 공식 */}
              {strategy.positionManagement.sizingMethod === 'kelly' && (
                <div className="sizing-config">
                  <div className="info-box">
                    <strong>💡 켈리 공식이란?</strong>
                    <p>승률과 손익비를 기반으로 최적의 포지션 크기를 계산합니다.</p>
                    <p className="formula">켈리 % = (승률 × 손익비 - (1 - 승률)) / 손익비</p>
                  </div>
                  
                  <div className="condition-group">
                    <label>승률 (%)</label>
                    <input
                      type="number"
                      value={(strategy.positionManagement.winRate || 0.5) * 100}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          winRate: Number(e.target.value) / 100,
                        },
                      })}
                      min="1"
                      max="99"
                      className="form-input"
                    />
                    <small>과거 전략의 승률 (예: 50%)</small>
                  </div>
                  
                  <div className="condition-group">
                    <label>평균 손익비 (수익/손실)</label>
                    <input
                      type="number"
                      value={strategy.positionManagement.winLossRatio || 2.0}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          winLossRatio: Number(e.target.value),
                        },
                      })}
                      min="0.1"
                      max="10"
                      step="0.1"
                      className="form-input"
                    />
                    <small>예: 2.0 = 평균 수익이 평균 손실의 2배</small>
                  </div>
                  
                  <div className="condition-group">
                    <label>켈리 비율 조정</label>
                    <input
                      type="number"
                      value={strategy.positionManagement.kellyFraction || 0.25}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          kellyFraction: Number(e.target.value),
                        },
                      })}
                      min="0.1"
                      max="1"
                      step="0.05"
                      className="form-input"
                    />
                    <small>권장: 0.25 (1/4 켈리) - 리스크 감소</small>
                  </div>
                </div>
              )}
              
              {/* 변동성 기반 */}
              {strategy.positionManagement.sizingMethod === 'volatility' && (
                <div className="sizing-config">
                  <div className="info-box">
                    <strong>💡 변동성 기반 사이징이란?</strong>
                    <p>종목의 변동성에 반비례하여 포지션 크기를 조절합니다. 변동성이 높으면 작게, 낮으면 크게 투자합니다.</p>
                  </div>
                  
                  <div className="condition-group">
                    <label>변동성 계산 기간 (일)</label>
                    <input
                      type="number"
                      value={strategy.positionManagement.volatilityPeriod || 20}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          volatilityPeriod: Number(e.target.value),
                        },
                      })}
                      min="5"
                      max="100"
                      className="form-input"
                    />
                  </div>
                  
                  <div className="condition-group">
                    <label>목표 변동성 (%)</label>
                    <input
                      type="number"
                      value={strategy.positionManagement.volatilityTarget || 2.0}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          volatilityTarget: Number(e.target.value),
                        },
                      })}
                      min="0.5"
                      max="10"
                      step="0.1"
                      className="form-input"
                    />
                    <small>포트폴리오 전체의 목표 변동성</small>
                  </div>
                </div>
              )}
              
              {/* 공통 설정 */}
              <div className="condition-group" style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid var(--color-border)' }}>
                <label>최대 보유 종목 수</label>
                <input
                  type="number"
                  value={strategy.positionManagement.maxPositions}
                  onChange={(e) => setStrategy({
                    ...strategy,
                    positionManagement: {
                      ...strategy.positionManagement,
                      maxPositions: Number(e.target.value),
                    },
                  })}
                  min="1"
                  max="20"
                  className="form-input"
                />
              </div>
              
              {/* 손절 설정 */}
              <div style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid var(--color-border)' }}>
                <h4 style={{ fontSize: '16px', marginBottom: '16px' }}>🛡️ 손절 설정</h4>
                
                <div className="condition-group">
                  <label className="checkbox-label" style={{ padding: '12px' }}>
                    <input
                      type="checkbox"
                      checked={strategy.positionManagement.stopLoss?.enabled || false}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          stopLoss: {
                            ...strategy.positionManagement.stopLoss!,
                            enabled: e.target.checked,
                          },
                        },
                      })}
                    />
                    <span className="checkbox-title">손절 활성화</span>
                  </label>
                </div>
                
                {strategy.positionManagement.stopLoss?.enabled && (
                  <div className="risk-config">
                    <div className="condition-group">
                      <label>손절 방식</label>
                      <div className="radio-group-inline">
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="stopLossMethod"
                            value="fixed"
                            checked={strategy.positionManagement.stopLoss?.method === 'fixed'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                stopLoss: {
                                  ...strategy.positionManagement.stopLoss!,
                                  method: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>고정 %</span>
                        </label>
                        
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="stopLossMethod"
                            value="atr"
                            checked={strategy.positionManagement.stopLoss?.method === 'atr'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                stopLoss: {
                                  ...strategy.positionManagement.stopLoss!,
                                  method: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>ATR 기반</span>
                        </label>
                        
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="stopLossMethod"
                            value="time"
                            checked={strategy.positionManagement.stopLoss?.method === 'time'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                stopLoss: {
                                  ...strategy.positionManagement.stopLoss!,
                                  method: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>시간 기반</span>
                        </label>
                      </div>
                    </div>
                    
                    {strategy.positionManagement.stopLoss?.method === 'fixed' && (
                      <div className="condition-group">
                        <label>손절 비율 (%)</label>
                        <input
                          type="number"
                          value={strategy.positionManagement.stopLoss?.fixedPercent || 5}
                          onChange={(e) => setStrategy({
                            ...strategy,
                            positionManagement: {
                              ...strategy.positionManagement,
                              stopLoss: {
                                ...strategy.positionManagement.stopLoss!,
                                fixedPercent: Number(e.target.value),
                              },
                            },
                          })}
                          min="1"
                          max="50"
                          step="0.5"
                          className="form-input"
                        />
                        <small>진입가 대비 이 비율만큼 하락 시 손절</small>
                      </div>
                    )}
                    
                    {strategy.positionManagement.stopLoss?.method === 'atr' && (
                      <>
                        <div className="condition-group">
                          <label>ATR 배수</label>
                          <input
                            type="number"
                            value={strategy.positionManagement.stopLoss?.atrMultiple || 2.0}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                stopLoss: {
                                  ...strategy.positionManagement.stopLoss!,
                                  atrMultiple: Number(e.target.value),
                                },
                              },
                            })}
                            min="0.5"
                            max="10"
                            step="0.5"
                            className="form-input"
                          />
                          <small>손절선 = 진입가 - (ATR × 배수)</small>
                        </div>
                        
                        <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                          <div className="condition-group">
                            <label>최소 손절 (%)</label>
                            <input
                              type="number"
                              value={strategy.positionManagement.stopLoss?.minPercent || 3}
                              onChange={(e) => setStrategy({
                                ...strategy,
                                positionManagement: {
                                  ...strategy.positionManagement,
                                  stopLoss: {
                                    ...strategy.positionManagement.stopLoss!,
                                    minPercent: Number(e.target.value),
                                  },
                                },
                              })}
                              min="1"
                              max="20"
                              className="form-input"
                            />
                          </div>
                          
                          <div className="condition-group">
                            <label>최대 손절 (%)</label>
                            <input
                              type="number"
                              value={strategy.positionManagement.stopLoss?.maxPercent || 10}
                              onChange={(e) => setStrategy({
                                ...strategy,
                                positionManagement: {
                                  ...strategy.positionManagement,
                                  stopLoss: {
                                    ...strategy.positionManagement.stopLoss!,
                                    maxPercent: Number(e.target.value),
                                  },
                                },
                              })}
                              min="5"
                              max="50"
                              className="form-input"
                            />
                          </div>
                        </div>
                        <small>ATR이 너무 작거나 클 때 손절 범위 제한</small>
                      </>
                    )}
                    
                    {strategy.positionManagement.stopLoss?.method === 'time' && (
                      <div className="condition-group">
                        <label>보유 기간 (일)</label>
                        <input
                          type="number"
                          value={strategy.positionManagement.stopLoss?.timeDays || 30}
                          onChange={(e) => setStrategy({
                            ...strategy,
                            positionManagement: {
                              ...strategy.positionManagement,
                              stopLoss: {
                                ...strategy.positionManagement.stopLoss!,
                                timeDays: Number(e.target.value),
                              },
                            },
                          })}
                          min="1"
                          max="365"
                          className="form-input"
                        />
                        <small>이 기간 후 자동 청산 (손익 무관)</small>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              {/* 익절 설정 */}
              <div style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid var(--color-border)' }}>
                <h4 style={{ fontSize: '16px', marginBottom: '16px' }}>💰 익절 설정</h4>
                
                <div className="condition-group">
                  <label className="checkbox-label" style={{ padding: '12px' }}>
                    <input
                      type="checkbox"
                      checked={strategy.positionManagement.takeProfit?.enabled || false}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        positionManagement: {
                          ...strategy.positionManagement,
                          takeProfit: {
                            ...strategy.positionManagement.takeProfit!,
                            enabled: e.target.checked,
                          },
                        },
                      })}
                    />
                    <span className="checkbox-title">익절 활성화</span>
                  </label>
                </div>
                
                {strategy.positionManagement.takeProfit?.enabled && (
                  <div className="risk-config">
                    <div className="condition-group">
                      <label>익절 방식</label>
                      <div className="radio-group-inline">
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="takeProfitMethod"
                            value="fixed"
                            checked={strategy.positionManagement.takeProfit?.method === 'fixed'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                takeProfit: {
                                  ...strategy.positionManagement.takeProfit!,
                                  method: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>고정 %</span>
                        </label>
                        
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="takeProfitMethod"
                            value="r_multiple"
                            checked={strategy.positionManagement.takeProfit?.method === 'r_multiple'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                takeProfit: {
                                  ...strategy.positionManagement.takeProfit!,
                                  method: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>R배수</span>
                        </label>
                        
                        <label className="radio-label-inline">
                          <input
                            type="radio"
                            name="takeProfitMethod"
                            value="partial"
                            checked={strategy.positionManagement.takeProfit?.method === 'partial'}
                            onChange={(e) => setStrategy({
                              ...strategy,
                              positionManagement: {
                                ...strategy.positionManagement,
                                takeProfit: {
                                  ...strategy.positionManagement.takeProfit!,
                                  method: e.target.value as any,
                                },
                              },
                            })}
                          />
                          <span>분할 익절</span>
                        </label>
                      </div>
                    </div>
                    
                    {strategy.positionManagement.takeProfit?.method === 'fixed' && (
                      <div className="condition-group">
                        <label>익절 비율 (%)</label>
                        <input
                          type="number"
                          value={strategy.positionManagement.takeProfit?.fixedPercent || 10}
                          onChange={(e) => setStrategy({
                            ...strategy,
                            positionManagement: {
                              ...strategy.positionManagement,
                              takeProfit: {
                                ...strategy.positionManagement.takeProfit!,
                                fixedPercent: Number(e.target.value),
                              },
                            },
                          })}
                          min="1"
                          max="200"
                          step="1"
                          className="form-input"
                        />
                        <small>진입가 대비 이 비율만큼 상승 시 익절</small>
                      </div>
                    )}
                    
                    {strategy.positionManagement.takeProfit?.method === 'r_multiple' && (
                      <div className="condition-group">
                        <label>목표 R배수</label>
                        <input
                          type="number"
                          value={strategy.positionManagement.takeProfit?.rMultiple || 3}
                          onChange={(e) => setStrategy({
                            ...strategy,
                            positionManagement: {
                              ...strategy.positionManagement,
                              takeProfit: {
                                ...strategy.positionManagement.takeProfit!,
                                rMultiple: Number(e.target.value),
                              },
                            },
                          })}
                          min="1"
                          max="10"
                          step="0.5"
                          className="form-input"
                        />
                        <small>손절 1R 대비 수익 목표. 예: 3R = 손절 5%면 익절 15%</small>
                      </div>
                    )}
                    
                    {strategy.positionManagement.takeProfit?.method === 'partial' && (
                      <div className="info-box">
                        <strong>📊 분할 익절</strong>
                        <p>기본 설정: 50% at 2R, 50% at 3R</p>
                        <p>예: 손절 5% 설정 시</p>
                        <p>→ 10% 상승 시 절반 매도 (2R)</p>
                        <p>→ 15% 상승 시 나머지 매도 (3R)</p>
                        <small>* 고급 설정은 추후 추가 예정</small>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        
        {/* 저장 버튼 */}
        <div className="builder-actions">
          <button onClick={handleSave} className="btn btn-primary btn-large">
            {editingStrategyId ? '✏️ 전략 수정' : '💾 전략 저장'}
          </button>
          <button className="btn btn-secondary btn-large">
            🧪 백테스트 실행
          </button>
        </div>
      </div>
    </PageLayout>
  );
};
