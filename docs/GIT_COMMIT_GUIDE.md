# Git 커밋 메시지 작성 가이드

## 한글 커밋 메시지 작성 방법

PowerShell에서 한글 커밋 메시지가 깨지는 문제를 해결하기 위해 파일을 사용합니다.

### 방법 1: commit_msg.txt 파일 사용 (권장)

```bash
# 1. commit_msg.txt 파일에 한글 메시지 작성
# 파일 내용 예시:
# feat: 전략 타입 설정 기능 추가
# 
# - 전략 빌더 UI에 단일 종목/포트폴리오 선택 옵션 추가
# - BaseStrategy.is_portfolio_strategy() 개선

# 2. 파일로 커밋
git commit -F commit_msg.txt

# 3. 파일 삭제
rm commit_msg.txt
```

### 방법 2: 영어로 작성

```bash
git commit -m "feat: Add strategy type configuration"
```

### 커밋 메시지 형식

```
<type>: <subject>

<body>

<footer>
```

#### Type 종류
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 업무 수정, 패키지 매니저 설정 등

#### 예시

```
feat: 전략 타입(is_portfolio) 설정 기능 추가

- 전략 빌더 UI에 단일 종목/포트폴리오 선택 옵션 추가
- BaseStrategy.is_portfolio_strategy()에서 params의 is_portfolio 우선 확인
- StrategyFactory에서 config의 is_portfolio를 parameters에 자동 복사
```

## 참고

- PowerShell에서 `git commit -m "한글"`을 직접 사용하면 인코딩 문제로 깨질 수 있습니다
- 파일을 사용하면 UTF-8로 정확하게 저장됩니다
- Git Bash나 다른 터미널에서는 한글이 정상적으로 작동할 수 있습니다

