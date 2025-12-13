#!/usr/bin/env python3
"""
사용하지 않는 함수들 제거
"""

def clean_unused_functions():
    """사용하지 않는 함수들 제거"""
    
    file_path = "frontend/src/pages/StrategyBuilderPage.tsx"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 사용하지 않는 함수들과 타입들 제거
    lines = content.split('\n')
    cleaned_lines = []
    skip_until_closing = False
    brace_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 제거할 함수들 시작점 감지
        if any(func in line for func in [
            'const createDefaultConditionValue',
            'const createIndicatorValue', 
            'const createPriceValue',
            'const createNumericValue',
            'const conditionValueToString',
            'const stringToConditionValue'
        ]):
            skip_until_closing = True
            brace_count = 0
            
        # 제거할 타입들
        elif any(type_def in line for type_def in [
            'type ConditionValueType',
            'interface IndicatorValue',
            'interface ConditionValue'
        ]):
            # 타입 정의는 세미콜론이나 중괄호까지 스킵
            if '{' in line:
                skip_until_closing = True
                brace_count = line.count('{') - line.count('}')
            else:
                # 한 줄 타입 정의
                i += 1
                continue
                
        if skip_until_closing:
            # 중괄호 카운팅
            brace_count += line.count('{') - line.count('}')
            
            # 함수 끝 감지
            if (brace_count <= 0 and '};' in line) or (brace_count == 0 and '}' in line):
                skip_until_closing = False
                i += 1
                continue
        else:
            cleaned_lines.append(line)
            
        i += 1
    
    content = '\n'.join(cleaned_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 사용하지 않는 함수들 제거 완료")

if __name__ == "__main__":
    clean_unused_functions()