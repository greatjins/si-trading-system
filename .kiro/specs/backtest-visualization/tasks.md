# Implementation Plan

## 📊 진행 상황 요약 (2024-12-11)

### ✅ 완료된 주요 기능 (태스크 1-12)
- **백엔드 아키텍처**: TradeAnalyzer 클래스 및 5개 API 엔드포인트 완성
- **프론트엔드 핵심 페이지**: 
  - BacktestResultPage (개별 결과 분석)
  - BacktestComparisonPage (다중 백테스트 비교)
- **데이터 시각화**: 
  - EquityCurveChart (Recharts 기반 자산 곡선)
  - PriceChart (lightweight-charts 기반 캔들스틱)
  - ComparisonChart (다중 전략 성과 비교)
  - SymbolPerformanceList (정렬 기능 포함)
  - TradeHistoryTable (거래 내역 분석)
- **모달 시스템**: SymbolDetailModal (차트+테이블 통합)
- **라우팅**: 완전한 네비게이션 시스템 + 비교 페이지
- **UI/UX 시스템**: 
  - 반응형 레이아웃 (모바일~데스크톱)
  - 에러 바운더리 및 에러 처리
  - 로딩 스피너 및 빈 상태 컴포넌트
  - 다크 모드 및 프린트 스타일 지원

### 🎯 다음 우선순위
1. **태스크 13**: 테스트 코드 작성
2. **태스크 14**: 문서화 및 최종 검토
3. **배포 준비**: 프로덕션 최적화

---

- [x] 1. Backend - 데이터 분석 및 모델 구현

  - [x] 1.1 TradeAnalyzer 클래스 구현
    - 종목별 거래 그룹화 로직
    - 매수/매도 매칭 알고리즘 (FIFO)
    - 종목별 메트릭 계산 (수익률, 승률, 손익비)
    - _Requirements: 7.2, 7.4_
  


  - [x] 1.2 데이터 모델 추가 (utils/types.py)




    - SymbolPerformance 데이터클래스
    - CompletedTrade 데이터클래스
    - SymbolDetail 데이터클래스
    - BacktestResultDetail 데이터클래스

    - _Requirements: 7.2, 7.3_

- [x] 2. Backend - API 엔드포인트 구현

  - [x] 2.1 백테스트 결과 상세 조회 API
    - GET /api/backtest/results/{backtest_id}
    - BacktestResultDetail 반환
    - 자산 곡선 및 타임스탬프 포함
    - _Requirements: 4.1, 4.2, 7.1_
  
  - [x] 2.2 종목별 성과 리스트 API
    - GET /api/backtest/results/{backtest_id}/symbols
    - List[SymbolPerformance] 반환
    - TradeAnalyzer로 메트릭 계산
    - _Requirements: 1.1, 1.2, 7.2, 7.4_
  
  - [x] 2.3 종목 상세 정보 API
    - GET /api/backtest/results/{backtest_id}/symbols/{symbol}
    - SymbolDetail 반환 (완결된 거래 포함)
    - 추가 메트릭 (avg_buy_price, avg_sell_price, avg_holding_days) 포함
    - _Requirements: 3.1, 3.2, 7.3_
  
  - [x] 2.4 종목 OHLC 데이터 API
    - GET /api/backtest/results/{backtest_id}/ohlc/{symbol}
    - 백테스트 기간의 OHLC 데이터 반환
    - _Requirements: 2.2, 7.5_
  
  - [x] 2.5 백테스트 비교 API
    - POST /api/backtest/results/compare
    - 여러 백테스트 결과 비교
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 3. Backend - 백테스트 엔진 개선






  - [x] 3.1 equity_timestamps 저장 추가

    - BacktestEngine._update_equity()에서 타임스탬프 기록
    - BacktestResult에 equity_timestamps 필드 추가
    - _Requirements: 4.2, 4.4_
  
  - [x] 3.2 종목명 조회 기능 추가


    - StockMasterModel에서 종목명 조회
    - SymbolPerformance에 name 필드 포함
    - _Requirements: 1.2_

- [x] 4. Frontend - 타입 정의



  - [x] 4.1 백테스트 결과 타입 정의 (types/backtest.ts)


    - SymbolPerformance 인터페이스
    - CompletedTrade 인터페이스
    - SymbolDetail 인터페이스
    - BacktestResultDetail 인터페이스
    - OHLC 인터페이스
    - _Requirements: 1.1, 2.1, 3.1_

- [x] 5. Frontend - 백테스트 결과 페이지

  - [x] 5.1 BacktestResultPage 컴포넌트 생성
    - 백테스트 결과 로딩 로직
    - 레이아웃 구성 (자산 곡선 + 종목 리스트)
    - 종목 클릭 핸들러
    - 에러 처리 및 로딩 상태 관리
    - _Requirements: 1.1, 4.1_
  
  - [x] 5.2 라우팅 설정
    - /backtest/results/:backtestId 경로 추가
    - BacktestPage에서 결과 페이지로 이동 링크
    - ProtectedRoute 인증 체크 포함
    - _Requirements: 1.1_

- [x] 6. Frontend - 자산 곡선 차트
  - [x] 6.1 EquityCurveChart 컴포넌트 생성
    - Recharts LineChart 사용
    - 자산 곡선 렌더링
    - MDD 구간 하이라이트 (Area 컴포넌트)
    - 호버 시 날짜/금액 툴팁
    - 초기 자본 기준선 및 차트 정보 표시
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 7. Frontend - 종목 성과 리스트
  - [x] 7.1 SymbolPerformanceList 컴포넌트 생성
    - 종목 리스트 테이블 렌더링
    - 수익률에 따른 색상 구분 (녹색/빨간색)
    - 클릭 이벤트 핸들러
    - 요약 정보 표시 (총 종목 수, 수익/손실 종목, 평균 수익률)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 7.2 정렬 기능 구현
    - 컬럼 헤더 클릭 시 정렬
    - 오름차순/내림차순 토글
    - 정렬 상태 표시 (화살표 아이콘)
    - 반응형 디자인 지원
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 8. Frontend - 종목 상세 모달
  - [x] 8.1 SymbolDetailModal 컴포넌트 생성
    - 모달 레이아웃 (헤더, 차트, 테이블)
    - 종목 상세 데이터 로딩
    - 닫기 버튼 및 ESC 키 핸들러
    - PriceChart 및 TradeHistoryTable 통합
    - _Requirements: 1.5, 2.1, 3.1_

- [x] 9. Frontend - 가격 차트 + 매매 마커
  - [x] 9.1 차트 라이브러리 설치
    - lightweight-charts 패키지 설치
    - React 래퍼 컴포넌트 작성
    - _Requirements: 2.1_
  
  - [x] 9.2 PriceChart 컴포넌트 생성
    - 캔들스틱 차트 렌더링
    - 매수 마커 표시 (↑ 녹색)
    - 매도 마커 표시 (↓ 빨간색)
    - 마커 호버 시 툴팁 (가격, 수량, 시간, P&L)
    - 반응형 차트 크기 조정 및 에러 처리
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_



- [x] 10. Frontend - 거래 내역 테이블
  - [x] 10.1 TradeHistoryTable 컴포넌트 생성
    - 완결된 거래 테이블 렌더링
    - 진입/청산 날짜, 가격, 수량, 수익률, 보유 기간 표시
    - 수익/손실 색상 구분
    - 행 클릭 시 차트 하이라이트
    - 컬럼별 정렬 기능 (날짜, 수익률, 손익, 보유기간)
    - 거래 통계 표시 및 반응형 디자인
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 11. Frontend - 백테스트 비교 기능
  - [x] 11.1 BacktestComparisonPage 컴포넌트 생성
    - 백테스트 목록 표시 (카드 형태)
    - 다중 선택 체크박스
    - 비교 버튼 및 상세보기 링크
    - 라우팅 설정 (/backtest/compare)
    - _Requirements: 7.1_
  
  - [x] 11.2 비교 차트 렌더링
    - ComparisonChart 컴포넌트 (Recharts 기반)
    - 여러 자산 곡선 오버레이
    - 범례 표시 및 색상 구분
    - 메트릭 비교 테이블
    - 커스텀 툴팁 및 최고 성과 하이라이트
    - _Requirements: 7.2, 7.3, 7.4, 7.5_

- [x] 12. 스타일링 및 UI/UX 개선
  - [x] 12.1 CSS 스타일 작성
    - 반응형 레이아웃 (모바일, 태블릿, 데스크톱)
    - 다크 모드 지원 (prefers-color-scheme)
    - 전용 백테스트 시각화 스타일시트
    - 프린트 스타일 지원
    - _Requirements: 1.1, 2.1, 3.1_
  
  - [x] 12.2 에러 처리 UI
    - ErrorBoundary 컴포넌트 (React 에러 캐치)
    - LoadingSpinner 컴포넌트 (다양한 크기)
    - ErrorMessage 컴포넌트 (재시도 기능)
    - EmptyState 컴포넌트 (빈 데이터 상태)
    - 전역 에러 처리 적용
    - _Requirements: 1.1, 2.1_

- [x] 13. 테스트


  - [x] 13.1 Backend 유닛 테스트



    - TradeAnalyzer 테스트
    - API 엔드포인트 테스트
    - _Requirements: 7.2, 7.3, 7.4_
  
  - [x] 13.2 Frontend 컴포넌트 테스트


    - 종목 리스트 렌더링 테스트
    - 정렬 기능 테스트
    - 모달 열기/닫기 테스트
    - _Requirements: 1.1, 5.1_
  
  - [x] 13.3 통합 테스트


    - 백테스트 실행 → 결과 조회 플로우
    - 종목 클릭 → 상세 보기 플로우
    - _Requirements: 1.5, 2.1, 3.1_

- [x] 14. 문서화 및 최종 검토



  - [x] 14.1 API 문서 업데이트


    - 새 엔드포인트 문서화
    - 요청/응답 예시 추가
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [x] 14.2 사용자 가이드 작성


    - 백테스트 결과 분석 방법
    - 차트 인터랙션 설명
    - _Requirements: 1.1, 2.1, 3.1_
