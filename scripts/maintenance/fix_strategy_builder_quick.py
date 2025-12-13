#!/usr/bin/env python3
"""
StrategyBuilderPage.tsx 타입 오류 빠른 수정
"""

def fix_typescript_errors():
    """타입 오류를 빠르게 수정"""
    
    file_path = "frontend/src/pages/StrategyBuilderPage.tsx"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 타입 가드 추가
    fixes = [
        # condition.value.match 사용 부분
        ("condition.value.match(/\\(\\d+\\)/)", "typeof condition.value === 'string' ? condition.value.match(/\\(\\d+\\)/) : null"),
        
        # condition.value.split 사용 부분  
        ("condition.value.split('(')[0]", "typeof condition.value === 'string' ? condition.value.split('(')[0] : 'MA'"),
        
        # condition.value.includes 사용 부분
        ("condition.value.includes('MA(')", "typeof condition.value === 'string' && condition.value.includes('MA(')"),
        ("condition.value.includes('EMA(')", "typeof condition.value === 'string' && condition.value.includes('EMA(')"),
        ("condition.value.includes('RSI(')", "typeof condition.value === 'string' && condition.value.includes('RSI(')"),
        ("condition.value.includes('MACD')", "typeof condition.value === 'string' && condition.value.includes('MACD')"),
    ]
    
    for old, new in fixes:
        content = content.replace(old, new)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 타입 오류 수정 완료")

if __name__ == "__main__":
    fix_typescript_errors()