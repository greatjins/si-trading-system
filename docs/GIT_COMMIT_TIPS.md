# Git 커밋 메시지 작성 팁 (Windows PowerShell)

## 문제점

PowerShell에서 `git commit -m "한글 메시지"`로 직접 입력하면 인코딩 문제로 한글이 깨집니다.

## 해결 방법

### 방법 1: 파일로 커밋 메시지 작성 (권장)

```powershell
# 1. UTF-8 인코딩으로 메시지 파일 생성
"docs: 한글 커밋 메시지" | Out-File -Encoding utf8 commit_msg.txt

# 2. 파일로 커밋
git commit -F commit_msg.txt

# 3. 파일 삭제
Remove-Item commit_msg.txt
```

또는 한 줄로:

```powershell
"docs: 한글 커밋 메시지" | Out-File -Encoding utf8 commit_msg.txt; git commit -F commit_msg.txt; Remove-Item commit_msg.txt
```

### 방법 2: VS Code 에디터 사용

```powershell
# VS Code가 PATH에 있는 경우
git commit

# VS Code가 열리면 한글로 메시지 작성 후 저장
```

### 방법 3: Git Bash 사용

Git Bash를 사용하면 기본적으로 UTF-8 환경이므로 문제가 없습니다.

```bash
git commit -m "docs: 한글 커밋 메시지"
```

### 방법 4: 영문 메시지 사용

가장 간단한 방법은 커밋 메시지를 영문으로 작성하는 것입니다.

```powershell
git commit -m "docs: Add Git encoding fix guide"
```

## 권장 워크플로우

1. **짧은 메시지**: 영문 사용 또는 파일 사용
2. **긴 메시지**: VS Code 에디터 사용 (`git commit`)
3. **일관성**: 팀과 협의하여 커밋 메시지 규칙 정하기

## 참고

- PowerShell의 `-m` 옵션은 인코딩 변환 과정에서 문제가 발생할 수 있습니다.
- 파일로 작성하면 UTF-8로 저장되어 문제가 없습니다.
- VS Code 에디터를 사용하면 자동으로 UTF-8로 저장됩니다.

