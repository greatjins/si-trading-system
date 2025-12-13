#!/usr/bin/env python3
"""
StrategyBuilderPage.tsx 타입 오류 간단 수정
"""

def fix_typescript_errors():
    """타입 오류를 간단하게 수정"""
    
    file_path = "frontend/src/pages/StrategyBuilderPage.tsx"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 간단한 문자열 치환으로 수정
    replacements = [
        # match 메서드 사용 부분
        ("condition.value.match(/\\(\\d+\\)/)", "(typeof condition.value === 'string' ? condition.value.match(/\\(\\d+\\)/) : null)"),
        
        # split 메서드 사용 부분
        ("condition.value.split('(')[0]", "(typeof condition.value === 'string' ? condition.value.split('(')[0] : 'MA')"),
        
        # includes 메서드 결과 비교 부분 - 더 안전하게
        ("value={condition.value.includes('MA(') ? 'MA'", "value={(typeof condition.value === 'string' && condition.value.includes('MA(')) ? 'MA'"),
        ("condition.value.includes('EMA(') ? 'EMA'", "(typeof condition.value === 'string' && condition.value.includes('EMA(')) ? 'EMA'"),
        ("condition.value.includes('RSI(') ? 'RSI'", "(typeof condition.value === 'string' && condition.value.includes('RSI(')) ? 'RSI'"),
        ("condition.value.includes('MACD') ? 'MACD'", "(typeof condition.value === 'string' && condition.value.includes('MACD')) ? 'MACD'"),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 타입 오류 간단 수정 완료")

if __name__ == "__main__":
    fix_typescript_errors()