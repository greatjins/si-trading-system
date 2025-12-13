#!/usr/bin/env python3
"""
StrategyBuilderPage.tsx export 문제 수정
"""

def fix_export_issue():
    """export 구문 추가"""
    
    file_path = "frontend/src/pages/StrategyBuilderPage.tsx"
    
    # 파일 읽기
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        print("❌ 파일 읽기 실패")
        return
    
    # 파일이 너무 짧으면 문제가 있음
    if len(content) < 1000:
        print(f"❌ 파일이 손상됨 (길이: {len(content)})")
        print("파일을 백업에서 복원해야 합니다.")
        return
    
    # export 구문이 없으면 추가
    if 'export' not in content:
        # 컴포넌트 함수 찾기
        if 'const StrategyBuilderPage' in content:
            content += '\n\nexport { StrategyBuilderPage };'
        elif 'function StrategyBuilderPage' in content:
            content += '\n\nexport { StrategyBuilderPage };'
        else:
            content += '\n\nexport const StrategyBuilderPage = () => <div>전략 빌더</div>;'
    
    # 파일 쓰기
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ export 구문 수정 완료")

if __name__ == "__main__":
    fix_export_issue()