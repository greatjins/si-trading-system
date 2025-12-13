#!/usr/bin/env python3
"""
StrategyBuilderPage.tsx 타입 오류 완전 수정
"""
import re

def fix_typescript_errors():
    """타입 오류를 완전히 수정"""
    
    file_path = "frontend/src/pages/StrategyBuilderPage.tsx"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. condition.value.match 사용 부분 수정
    content = re.sub(
        r'condition\.value\.match\(/\\?\(\\?\\?d\+\\?\)\\?/\)',
        "typeof condition.value === 'string' ? condition.value.match(/\\(\\d+\\)/) : null",
        content
    )
    
    # 2. condition.value.split 사용 부분 수정
    content = re.sub(
        r'condition\.value\.split\(\'?\(\'\?\)\[0\]',
        "typeof condition.value === 'string' ? condition.value.split('(')[0] : 'MA'",
        content
    )
    
    # 3. 불린 비교 오류 수정 - includes 결과를 문자열과 비교하는 부분
    content = re.sub(
        r'typeof condition\.value === \'string\' && condition\.value\.includes\(\'([^\']+)\'\) \? \'([^\']+)\' :',
        r"typeof condition.value === 'string' && condition.value.includes('\1') ? '\2' :",
        content
    )
    
    # 4. ConditionValue 타입 관련 오류 수정 - 사용하지 않는 함수들 제거
    lines = content.split('\n')
    filtered_lines = []
    skip_function = False
    
    for line in lines:
        # 사용하지 않는 함수들 제거
        if 'const createDefaultConditionValue' in line or 'const createIndicatorValue' in line or \
           'const createPriceValue' in line or 'const createNumericValue' in line or \
           'const conditionValueToString' in line or 'const stringToConditionValue' in line:
            skip_function = True
            continue
        
        if skip_function and line.strip() == '};':
            skip_function = False
            continue
            
        if skip_function:
            continue
            
        filtered_lines.append(line)
    
    content = '\n'.join(filtered_lines)
    
    # 5. ConditionValue 인터페이스와 관련 타입들 제거
    content = re.sub(r'type ConditionValueType = \'number\' \| \'price\' \| \'indicator\';?\n', '', content)
    content = re.sub(r'interface IndicatorValue \{[^}]+\}\n', '', content)
    content = re.sub(r'interface ConditionValue \{[^}]+\}\n', '', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 타입 오류 완전 수정 완료")

if __name__ == "__main__":
    fix_typescript_errors()