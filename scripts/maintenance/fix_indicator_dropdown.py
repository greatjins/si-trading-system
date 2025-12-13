#!/usr/bin/env python3
"""
지표 드롭다운 문제 빠른 수정
"""

def fix_dropdown_issue():
    """지표 드롭다운 문제 수정"""
    
    file_path = "frontend/src/pages/StrategyBuilderPage.tsx"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 지표 선택 드롭다운에 강제 스타일 추가
    old_select = '''                      <select
                        value={condition.indicator}
                        onChange={(e) => {
                          const newIndicator = indicators.find(ind => ind.id === e.target.value);
                          const updated = strategy.buyConditions.map((c) =>
                            c.id === condition.id ? { 
                              ...c, 
                              indicator: e.target.value,
                              operator: newIndicator?.operators[0] || '>',
                              period: newIndicator?.parameters.find(p => p.name === 'period')?.default
                            } : c
                          );
                          setStrategy({ ...strategy, buyConditions: updated });
                        }}
                        className="form-select"
                      >'''
    
    new_select = '''                      <select
                        value={condition.indicator || ''}
                        onChange={(e) => {
                          console.log('지표 변경:', e.target.value);
                          const newIndicator = indicators.find(ind => ind.id === e.target.value);
                          const updated = strategy.buyConditions.map((c) =>
                            c.id === condition.id ? { 
                              ...c, 
                              indicator: e.target.value,
                              operator: newIndicator?.operators[0] || '>',
                              period: newIndicator?.parameters.find(p => p.name === 'period')?.default
                            } : c
                          );
                          setStrategy({ ...strategy, buyConditions: updated });
                        }}
                        className="form-select"
                        style={{ 
                          minWidth: '200px', 
                          cursor: 'pointer',
                          backgroundColor: 'white',
                          border: '1px solid #ddd'
                        }}
                      >'''
    
    content = content.replace(old_select, new_select)
    
    # 매도조건도 동일하게 수정
    old_sell_select = '''                      <select
                        value={condition.indicator}
                        onChange={(e) => {
                          const newIndicator = indicators.find(ind => ind.id === e.target.value);
                          const updated = strategy.sellConditions.map((c) =>
                            c.id === condition.id ? { 
                              ...c, 
                              indicator: e.target.value,
                              operator: newIndicator?.operators[0] || '>',
                              period: newIndicator?.parameters.find(p => p.name === 'period')?.default
                            } : c
                          );
                          setStrategy({ ...strategy, sellConditions: updated });
                        }}
                        className="form-select"
                      >'''
    
    new_sell_select = '''                      <select
                        value={condition.indicator || ''}
                        onChange={(e) => {
                          console.log('매도 지표 변경:', e.target.value);
                          const newIndicator = indicators.find(ind => ind.id === e.target.value);
                          const updated = strategy.sellConditions.map((c) =>
                            c.id === condition.id ? { 
                              ...c, 
                              indicator: e.target.value,
                              operator: newIndicator?.operators[0] || '>',
                              period: newIndicator?.parameters.find(p => p.name === 'period')?.default
                            } : c
                          );
                          setStrategy({ ...strategy, sellConditions: updated });
                        }}
                        className="form-select"
                        style={{ 
                          minWidth: '200px', 
                          cursor: 'pointer',
                          backgroundColor: 'white',
                          border: '1px solid #ddd'
                        }}
                      >'''
    
    content = content.replace(old_sell_select, new_sell_select)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 지표 드롭다운 수정 완료")
    print("📝 변경사항:")
    print("   - 드롭다운 스타일 강화")
    print("   - 콘솔 로그 추가")
    print("   - value 기본값 설정")

if __name__ == "__main__":
    fix_dropdown_issue()