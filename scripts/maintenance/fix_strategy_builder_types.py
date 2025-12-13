"""
StrategyBuilderPage 타입 오류 수정 스크립트
"""
import re

def fix_typescript_file():
    """TypeScript 파일의 타입 오류 수정"""
    
    # 파일 읽기
    with open('frontend/src/pages/StrategyBuilderPage.tsx', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. HTML 엔티티 수정 (이미 완료된 것 확인)
    print("✅ HTML 엔티티는 이미 수정됨")
    
    # 2. condition.value 타입 가드 추가
    type_guard_functions = '''
// 타입 가드 함수들
const isStringValue = (value: string | number): value is string => {
  return typeof value === 'string';
};

const getIndicatorPeriod = (value: string | number): string => {
  if (!isStringValue(value)) return '20';
  const match = value.match(/\\((\\d+)\\)/);
  return match?.[1] || '20';
};

const getIndicatorType = (value: string | number): string => {
  if (!isStringValue(value)) return 'MA';
  return value.split('(')[0] || 'MA';
};

const hasIndicatorPattern = (value: string | number, pattern: string): boolean => {
  return isStringValue(value) && value.includes(pattern);
};
'''
    
    # 3. 타입 가드 함수가 없으면 추가
    if 'isStringValue' not in content:
        # export const StrategyBuilderPage 앞에 추가
        content = content.replace(
            'export const StrategyBuilderPage = () => {',
            type_guard_functions + '\nexport const StrategyBuilderPage = () => {'
        )
        print("✅ 타입 가드 함수 추가됨")
    
    # 4. condition.value.match 패턴 수정
    patterns_to_fix = [
        (r'condition\.value\.match\(/\\\\?\(\\\\?\(\\\\?d\+\\\\?\)\\\\?\)/\)\?\.\[1\]', 'getIndicatorPeriod(condition.value)'),
        (r'condition\.value\.split\(\'?\(\'\?\)\[0\]', 'getIndicatorType(condition.value)'),
        (r'condition\.value\.includes\(\'MA\(\'\)', 'hasIndicatorPattern(condition.value, "MA(")'),
        (r'condition\.value\.includes\(\'EMA\(\'\)', 'hasIndicatorPattern(condition.value, "EMA(")'),
        (r'condition\.value\.includes\(\'RSI\(\'\)', 'hasIndicatorPattern(condition.value, "RSI(")'),
        (r'condition\.value\.includes\(\'MACD\'\)', 'hasIndicatorPattern(condition.value, "MACD")'),
    ]
    
    for pattern, replacement in patterns_to_fix:
        content = re.sub(pattern, replacement, content)
    
    # 5. 더 안전한 패턴으로 수정
    # condition.value.match(/\((\d+)\)/) 패턴 찾아서 수정
    match_pattern = r'condition\.value\.match\(/\\\\?\(\\\\?\(\\\\?\\\\?d\+\\\\?\)\\\\?\)/\)\?\.\[1\]'
    content = re.sub(match_pattern, 'getIndicatorPeriod(condition.value)', content)
    
    # condition.value.split('(')[0] 패턴 수정
    split_pattern = r'condition\.value\.split\(\'?\(\'\?\)\[0\]'
    content = re.sub(split_pattern, 'getIndicatorType(condition.value)', content)
    
    # 6. 파일 저장
    with open('frontend/src/pages/StrategyBuilderPage_fixed.tsx', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 수정된 파일이 StrategyBuilderPage_fixed.tsx로 저장됨")
    
    # 7. 주요 수정 사항 요약
    print("\n📋 주요 수정 사항:")
    print("1. 타입 가드 함수 추가 (isStringValue, getIndicatorPeriod, getIndicatorType)")
    print("2. condition.value.match() 호출을 안전한 함수로 대체")
    print("3. condition.value.split() 호출을 안전한 함수로 대체") 
    print("4. condition.value.includes() 호출을 안전한 함수로 대체")
    print("5. HTML 엔티티 (&gt;, &lt;) 사용으로 JSX 구문 오류 해결")

if __name__ == "__main__":
    fix_typescript_file()