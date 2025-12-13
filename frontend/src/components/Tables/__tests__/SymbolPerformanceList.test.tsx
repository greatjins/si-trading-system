/**
 * SymbolPerformanceList 컴포넌트 테스트
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { SymbolPerformanceList } from '../SymbolPerformanceList';
import { SymbolPerformance } from '../../../types/backtest';

// 테스트용 샘플 데이터
const mockPerformances: SymbolPerformance[] = [
  {
    symbol: '005930',
    name: '삼성전자',
    total_return: 15.5,
    trade_count: 5,
    win_rate: 80.0,
    profit_factor: 2.5,
    avg_holding_period: 10,
    total_pnl: 1500000
  },
  {
    symbol: '000660',
    name: 'SK하이닉스',
    total_return: -8.2,
    trade_count: 3,
    win_rate: 33.3,
    profit_factor: 0.8,
    avg_holding_period: 7,
    total_pnl: -820000
  },
  {
    symbol: '035420',
    name: 'NAVER',
    total_return: 22.1,
    trade_count: 4,
    win_rate: 75.0,
    profit_factor: 3.2,
    avg_holding_period: 12,
    total_pnl: 2210000
  }
];

describe('SymbolPerformanceList', () => {
  const mockOnSymbolClick = jest.fn();

  beforeEach(() => {
    mockOnSymbolClick.mockClear();
  });

  test('종목 리스트가 올바르게 렌더링된다', () => {
    render(
      <SymbolPerformanceList 
        performances={mockPerformances}
        onSymbolClick={mockOnSymbolClick}
      />
    );

    // 헤더 확인
    expect(screen.getByText('종목코드')).toBeInTheDocument();
    expect(screen.getByText('종목명')).toBeInTheDocument();
    expect(screen.getByText('수익률')).toBeInTheDocument();
    expect(screen.getByText('거래횟수')).toBeInTheDocument();
    expect(screen.getByText('승률')).toBeInTheDocument();
    expect(screen.getByText('손익비')).toBeInTheDocument();
    expect(screen.getByText('총손익')).toBeInTheDocument();

    // 데이터 확인
    expect(screen.getByText('005930')).toBeInTheDocument();
    expect(screen.getByText('삼성전자')).toBeInTheDocument();
    expect(screen.getByText('15.50%')).toBeInTheDocument();
    expect(screen.getByText('5회')).toBeInTheDocument();
    expect(screen.getByText('80.0%')).toBeInTheDocument();
    expect(screen.getByText('2.50')).toBeInTheDocument();
    expect(screen.getByText('1,500,000원')).toBeInTheDocument();

    expect(screen.getByText('000660')).toBeInTheDocument();
    expect(screen.getByText('SK하이닉스')).toBeInTheDocument();
    expect(screen.getByText('-8.20%')).toBeInTheDocument();

    expect(screen.getByText('035420')).toBeInTheDocument();
    expect(screen.getByText('NAVER')).toBeInTheDocument();
    expect(screen.getByText('22.10%')).toBeInTheDocument();
  });

  test('종목 클릭 시 핸들러가 호출된다', () => {
    render(
      <SymbolPerformanceList 
        performances={mockPerformances}
        onSymbolClick={mockOnSymbolClick}
      />
    );

    // 첫 번째 종목 행 클릭
    const firstRow = screen.getByText('005930').closest('tr');
    fireEvent.click(firstRow!);

    expect(mockOnSymbolClick).toHaveBeenCalledWith('005930');
    expect(mockOnSymbolClick).toHaveBeenCalledTimes(1);
  });

  test('정렬 기능이 올바르게 작동한다', () => {
    render(
      <SymbolPerformanceList 
        performances={mockPerformances}
        onSymbolClick={mockOnSymbolClick}
      />
    );

    // 수익률 컬럼 헤더 클릭 (기본: 내림차순)
    const returnHeader = screen.getByText('수익률').closest('th');
    
    // 초기 상태에서는 NAVER(22.1%)가 첫 번째에 있어야 함
    const rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('NAVER'); // 헤더 제외하고 첫 번째 데이터 행

    // 수익률 헤더 클릭 (오름차순으로 변경)
    fireEvent.click(returnHeader!);
    
    // SK하이닉스(-8.2%)가 첫 번째에 있어야 함
    const updatedRows = screen.getAllByRole('row');
    expect(updatedRows[1]).toHaveTextContent('SK하이닉스');
  });

  test('로딩 상태가 올바르게 표시된다', () => {
    render(
      <SymbolPerformanceList 
        performances={[]}
        onSymbolClick={mockOnSymbolClick}
        loading={true}
      />
    );

    expect(screen.getByText('종목별 성과를 불러오는 중...')).toBeInTheDocument();
    expect(screen.queryByText('종목코드')).not.toBeInTheDocument();
  });

  test('데이터가 없을 때 메시지가 표시된다', () => {
    render(
      <SymbolPerformanceList 
        performances={[]}
        onSymbolClick={mockOnSymbolClick}
        loading={false}
      />
    );

    expect(screen.getByText('거래된 종목이 없습니다.')).toBeInTheDocument();
    expect(screen.queryByText('종목코드')).not.toBeInTheDocument();
  });

  test('요약 정보가 올바르게 계산된다', () => {
    render(
      <SymbolPerformanceList 
        performances={mockPerformances}
        onSymbolClick={mockOnSymbolClick}
      />
    );

    // 총 종목 수: 3개
    expect(screen.getByText('3개')).toBeInTheDocument();
    
    // 수익 종목: 2개 (삼성전자, NAVER)
    const profitableCount = screen.getAllByText('2개')[0]; // 첫 번째 "2개"
    expect(profitableCount).toBeInTheDocument();
    
    // 손실 종목: 1개 (SK하이닉스)
    expect(screen.getByText('1개')).toBeInTheDocument();
    
    // 평균 수익률: (15.5 + (-8.2) + 22.1) / 3 = 9.8%
    expect(screen.getByText('9.80%')).toBeInTheDocument();
  });

  test('수익률에 따른 색상 클래스가 올바르게 적용된다', () => {
    render(
      <SymbolPerformanceList 
        performances={mockPerformances}
        onSymbolClick={mockOnSymbolClick}
      />
    );

    // 양수 수익률은 positive 클래스
    const positiveReturn = screen.getByText('15.50%');
    expect(positiveReturn).toHaveClass('positive');

    // 음수 수익률은 negative 클래스
    const negativeReturn = screen.getByText('-8.20%');
    expect(negativeReturn).toHaveClass('negative');
  });

  test('승률에 따른 색상 클래스가 올바르게 적용된다', () => {
    render(
      <SymbolPerformanceList 
        performances={mockPerformances}
        onSymbolClick={mockOnSymbolClick}
      />
    );

    // 50% 이상 승률은 good-rate 클래스
    const goodWinRate = screen.getByText('80.0%');
    expect(goodWinRate).toHaveClass('good-rate');

    // 50% 미만 승률은 poor-rate 클래스
    const poorWinRate = screen.getByText('33.3%');
    expect(poorWinRate).toHaveClass('poor-rate');
  });

  test('손익비에 따른 색상 클래스가 올바르게 적용된다', () => {
    render(
      <SymbolPerformanceList 
        performances={mockPerformances}
        onSymbolClick={mockOnSymbolClick}
      />
    );

    // 1 이상 손익비는 good-ratio 클래스
    const goodRatio = screen.getByText('2.50');
    expect(goodRatio).toHaveClass('good-ratio');

    // 1 미만 손익비는 poor-ratio 클래스
    const poorRatio = screen.getByText('0.80');
    expect(poorRatio).toHaveClass('poor-ratio');
  });
});