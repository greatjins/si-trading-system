/**
 * 지표 헬프 모달 - 모든 지표의 설명과 사용 방법
 */
import React, { useState } from 'react';
import { IndicatorInfo } from './ConditionCard';

interface IndicatorHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
  indicators: IndicatorInfo[];
  categories: Array<{ id: string; name: string; description?: string }>;
}

// 연산자 한글 라벨
const getOperatorLabel = (op: string): string => {
  const labels: Record<string, string> = {
    '>': '초과',
    '<': '미만',
    '>=': '이상',
    '<=': '이하',
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
    '==': '같음',
  };
  return labels[op] || op;
};

// 지표별 상세 설명
const getIndicatorDetail = (indicatorId: string): string => {
  const details: Record<string, string> = {
    ma: `단순 이동평균선(SMA)은 특정 기간 동안의 평균 가격을 계산합니다.
• 매수: 현재가가 이동평균선 위에 있을 때 (상승 추세)
• 매도: 현재가가 이동평균선 아래로 떨어질 때 (하락 추세)
• 일반적으로 20일선, 60일선을 많이 사용합니다.`,

    ema: `지수 이동평균선(EMA)은 최근 가격에 더 많은 가중치를 부여합니다.
• SMA보다 빠르게 반응하여 추세 변화를 빨리 감지합니다.
• 단기 매매에 유리하며, 12일, 26일 EMA가 많이 사용됩니다.`,

    rsi: `상대강도지수는 과매수/과매도 상태를 판단합니다 (0-100).
• 70 이상: 과매수 구간 (매도 고려)
• 30 이하: 과매도 구간 (매수 고려)
• 다이버전스 패턴도 중요한 신호입니다.`,

    macd: `MACD는 추세의 변화와 모멘텀을 측정합니다.
• MACD선이 시그널선을 상향 돌파: 매수 신호
• MACD선이 시그널선을 하향 돌파: 매도 신호
• 히스토그램이 0선을 돌파하는 것도 중요한 신호입니다.`,

    bollinger: `볼린저 밴드는 변동성을 기반으로 상단/중단/하단 밴드를 그립니다.
• 상단 밴드 터치: 과매수 구간 (매도 고려)
• 하단 밴드 터치: 과매도 구간 (매수 고려)
• 밴드 폭이 좁아지면 큰 움직임이 예상됩니다.`,

    atr: `평균 진폭(ATR)은 가격 변동성을 측정합니다.
• ATR이 높으면 변동성이 크고, 낮으면 변동성이 작습니다.
• 손절가 설정이나 포지션 사이징에 활용됩니다.`,

    stochastic: `스토캐스틱은 현재가가 최근 가격 범위 내에서 어느 위치에 있는지 나타냅니다 (0-100).
• 80 이상: 과매수 (매도 고려)
• 20 이하: 과매도 (매수 고려)
• %K와 %D의 교차도 중요한 신호입니다.`,

    adx: `ADX는 추세의 강도를 측정합니다 (0-100).
• 25 이상: 강한 추세
• 25 미만: 약한 추세 또는 횡보
• ADX가 높을 때 추세 추종 전략이 효과적입니다.`,

    cci: `상품채널지수는 가격이 정상 범위를 벗어났는지 판단합니다.
• +100 이상: 과매수 (매도 고려)
• -100 이하: 과매도 (매수 고려)
• 극단적인 수치에서 반등 가능성이 높습니다.`,

    williams_r: `윌리엄스 %R은 과매수/과매도 상태를 나타냅니다 (-100 ~ 0).
• -20 이상: 과매수 (매도 고려)
• -80 이하: 과매도 (매수 고려)
• RSI와 유사하지만 계산 방식이 다릅니다.`,

    mfi: `자금흐름지수는 거래량을 고려한 RSI입니다 (0-100).
• 80 이상: 과매수 (매도 고려)
• 20 이하: 과매도 (매수 고려)
• 거래량 정보가 포함되어 RSI보다 정확할 수 있습니다.`,

    obv: `거래량 누적 지표는 가격 상승일의 거래량을 더하고 하락일의 거래량을 뺍니다.
• OBV가 상승: 매수 압력 증가
• OBV가 하락: 매도 압력 증가
• 가격과 OBV의 다이버전스가 중요합니다.`,

    volume_ma: `거래량 이동평균은 평균 거래량을 계산합니다.
• 현재 거래량 > 평균: 관심 증가 (매수 고려)
• 현재 거래량 < 평균: 관심 감소 (매도 고려)
• 거래량 급증은 큰 움직임의 전조입니다.`,

    vwap: `거래량 가중 평균 가격은 하루 동안의 평균 거래 가격입니다.
• 현재가 > VWAP: 강세 (매수 고려)
• 현재가 < VWAP: 약세 (매도 고려)
• 기관투자자들이 많이 사용하는 기준선입니다.`,

    ichimoku: `일목균형표는 5가지 선으로 추세와 지지/저항을 분석합니다.
• 전환선/기준선 교차: 추세 변화 신호
• 구름 위/아래: 강세/약세 구분
• 후행스팬: 과거 가격과 현재 비교`,

    bos: `Break of Structure는 이전 고점/저점을 돌파하는 현상입니다.
• 고점 돌파(break_high): 상승 추세 전환 신호 (매수)
• 저점 돌파(break_low): 하락 추세 전환 신호 (매도)
• lookback 기간 내 최고가/최저가를 기준으로 합니다.`,

    fvg: `Fair Value Gap은 가격이 빠르게 움직이면서 생긴 공백 구간입니다.
• 갭 내부(in_gap): 가격이 갭을 채우는 중
• 갭 위(above_gap): 갭을 채운 후 상승
• 갭 아래(below_gap): 갭을 채운 후 하락
• 갭은 지지/저항 역할을 합니다.`,

    order_block: `Order Block은 기관투자자의 주문이 집중된 구간입니다.
• 높은 거래량(volume_multiplier 배 이상) + 큰 몸통(2% 이상)
• 블록 내부(in_block): 가격이 블록 구간에 있을 때
• 블록 위/아래: 블록을 돌파한 후의 위치
• 이후 가격이 블록으로 되돌아올 때 반응합니다.`,

    liquidity_pool: `Liquidity Pool은 고점/저점이 여러 번 형성된 클러스터 구간입니다.
• 풀 근처(near_pool): 가격이 풀 구간에 접근
• 풀 스윕(sweep_pool): 풀을 돌파한 후 반등
• cluster_threshold: 클러스터로 인정할 거리 범위
• 풀은 강한 지지/저항 역할을 합니다.`,

    smart_money: `Smart Money Flow는 기관투자자의 동향을 추적합니다.
• 높은 거래량 + 상승 모멘텀: 매수 신호
• 높은 거래량 + 하락 모멘텀: 매도 신호
• period 기간의 평균 거래량과 비교합니다.
• 스마트머니의 움직임을 따라가면 수익성이 높습니다.`,

    consecutive_bearish: `연속 음봉은 종가가 시가보다 낮은 봉이 연속으로 나오는 패턴입니다.
• count 개수 이상 연속 음봉: 하락 추세 강화 (매도 고려)
• 고점에서 연속 음봉은 추세 전환 신호일 수 있습니다.
• 기본값 3일: 3일 연속 음봉이면 매도 신호`,

    price_from_high: `고점 대비 하락률은 최근 고점에서 현재가가 얼마나 하락했는지 계산합니다.
• lookback 기간 내 최고가를 기준으로 합니다.
• 하락률이 임계값 이상이면 매도 신호
• 예: 20일 고점 대비 5% 이상 하락 시 매도`,

    ma_cross_down: `이동평균선 데드크로스는 단기선이 장기선 아래로 교차하는 현상입니다.
• fast(단기선) < slow(장기선): 하락 추세 전환 (매도 신호)
• 골든크로스의 반대 개념입니다.
• 기본값: 5일선과 20일선`,

  };
  return details[indicatorId] || '상세 설명이 없습니다.';
};

export const IndicatorHelpModal: React.FC<IndicatorHelpModalProps> = ({
  isOpen,
  onClose,
  indicators,
  categories
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  if (!isOpen) return null;

  // 카테고리별 필터링
  const filteredIndicators = indicators.filter(ind => {
    const matchesCategory = selectedCategory === 'all' || ind.category === selectedCategory;
    const matchesSearch = ind.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ind.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content indicator-help-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📚 지표 설명 및 사용 방법</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {/* 검색 및 필터 */}
          <div className="help-filters">
            <input
              type="text"
              placeholder="🔍 지표 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input"
              style={{ flex: 1 }}
            />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="form-select"
              style={{ width: '200px' }}
            >
              <option value="all">전체 카테고리</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>

          {/* 지표 목록 */}
          <div className="indicator-list">
            {filteredIndicators.map(indicator => (
              <div key={indicator.id} className="indicator-item">
                <div className="indicator-header">
                  <h3>{indicator.name}</h3>
                  <span className="indicator-category">
                    {categories.find(c => c.id === indicator.category)?.name || indicator.category}
                  </span>
                </div>

                <p className="indicator-description">{indicator.description}</p>

                {/* 파라미터 */}
                {indicator.parameters.length > 0 && (
                  <div className="indicator-section">
                    <h4>⚙️ 파라미터</h4>
                    <div className="parameter-list">
                      {indicator.parameters.map(param => (
                        <div key={param.name} className="parameter-item">
                          <strong>{param.name}</strong>
                          <span className="parameter-info">
                            기본값: {param.default}
                            {param.min !== undefined && param.max !== undefined && 
                              ` (범위: ${param.min} ~ ${param.max})`}
                            {param.step && ` (단계: ${param.step})`}
                            {param.description && ` - ${param.description}`}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 연산자 */}
                <div className="indicator-section">
                  <h4>🔧 사용 가능한 연산자</h4>
                  <div className="operator-list">
                    {indicator.operators.map(op => (
                      <span key={op} className="operator-badge">
                        {getOperatorLabel(op)}
                      </span>
                    ))}
                  </div>
                </div>

                {/* 상세 설명 */}
                <div className="indicator-section">
                  <h4>💡 상세 설명</h4>
                  <div className="indicator-detail">
                    {getIndicatorDetail(indicator.id).split('\n').map((line, idx) => (
                      <p key={idx}>{line}</p>
                    ))}
                  </div>
                </div>

                {/* 사용 예시 */}
                <div className="indicator-section">
                  <h4>📝 사용 예시</h4>
                  <div className="usage-examples">
                    {indicator.category === 'trend' && (
                      <div className="example-item">
                        <strong>매수:</strong> {indicator.name} {indicator.operators[0]} 현재가
                        <br />
                        <strong>매도:</strong> {indicator.name} {indicator.operators[1] || indicator.operators[0]} 현재가
                      </div>
                    )}
                    {indicator.category === 'momentum' && (
                      <div className="example-item">
                        <strong>매수:</strong> {indicator.name} {'<'} 30 (과매도 구간)
                        <br />
                        <strong>매도:</strong> {indicator.name} {'>'} 70 (과매수 구간)
                      </div>
                    )}
                    {indicator.id === 'bos' && (
                      <div className="example-item">
                        <strong>매수:</strong> BOS break_high (고점 돌파)
                        <br />
                        <strong>매도:</strong> BOS break_low (저점 돌파)
                      </div>
                    )}
                    {indicator.id === 'order_block' && (
                      <div className="example-item">
                        <strong>매수:</strong> Order Block in_block (블록 내부 리테스트)
                        <br />
                        <strong>매도:</strong> Order Block below_block (블록 아래로 이탈)
                      </div>
                    )}
                    {indicator.id === 'consecutive_bearish' && (
                      <div className="example-item">
                        <strong>매도:</strong> 연속 음봉 {'>='} 3 (3일 연속 음봉)
                      </div>
                    )}
                    {indicator.id === 'price_from_high' && (
                      <div className="example-item">
                        <strong>매도:</strong> 고점 대비 하락률 {'>'} 5 (5% 이상 하락)
                      </div>
                    )}
                    {indicator.id === 'ma_cross_down' && (
                      <div className="example-item">
                        <strong>매도:</strong> 이동평균선 이탈 cross_below (데드크로스)
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {filteredIndicators.length === 0 && (
            <div className="no-results">
              검색 결과가 없습니다.
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-primary" onClick={onClose}>닫기</button>
        </div>
      </div>
    </div>
  );
};
