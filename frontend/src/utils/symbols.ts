/**
 * 종목 코드 → 종목명 매핑 유틸
 * TODO: 나중에 백엔드에서 심볼 메타데이터를 주면 이 매핑을 제거하거나 자동화할 수 있음
 */

// 최소 기본 매핑 (필요 시 확장)
const SYMBOL_NAME_MAP: Record<string, string> = {
  '005930': '삼성전자',
  // 여기에 자주 쓰는 종목들을 추가할 수 있음
};

/**
 * 종목 코드로 종목명을 반환
 * - 없으면 null
 */
export const getSymbolName = (symbol: string | undefined | null): string | null => {
  if (!symbol) return null;
  return SYMBOL_NAME_MAP[symbol] ?? null;
};


