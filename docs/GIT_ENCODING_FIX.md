# Git 한글 인코딩 문제 해결 가이드

## 근본적인 이유

Windows에서 Git 커밋 메시지나 파일명의 한글이 깨지는 이유:

### 1. **인코딩 불일치**
- Windows 기본 코드페이지: CP949 (EUC-KR 계열)
- Git 기본 인코딩: UTF-8
- PowerShell 기본 인코딩: 시스템 설정에 따라 다름

### 2. **터미널 인코딩 문제**
- PowerShell이 CP949로 설정되어 있으면 UTF-8 메시지가 깨짐
- Git이 커밋 메시지를 받을 때 이미 깨진 상태로 받음

### 3. **Git 설정 누락**
- `core.quotepath`: 파일명의 비ASCII 문자 처리
- `i18n.commitencoding`: 커밋 메시지 인코딩
- `i18n.logoutputencoding`: 로그 출력 인코딩

## 해결 방법

### 1. Git 전역 설정 (이미 적용됨)

```bash
# 파일명의 비ASCII 문자를 그대로 표시
git config --global core.quotepath false

# 커밋 메시지 인코딩
git config --global i18n.commitencoding utf-8

# 로그 출력 인코딩
git config --global i18n.logoutputencoding utf-8
```

### 2. PowerShell 인코딩 설정

PowerShell 프로필에 다음을 추가:

```powershell
# PowerShell 프로필 위치 확인
$PROFILE

# 프로필에 추가할 내용
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
```

또는 매번 실행:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

### 3. 환경 변수 설정 (시스템 레벨)

시스템 환경 변수에 추가:
- `LANG=ko_KR.UTF-8`
- `LC_ALL=ko_KR.UTF-8`

또는 PowerShell에서:

```powershell
[Environment]::SetEnvironmentVariable("LANG", "ko_KR.UTF-8", "User")
[Environment]::SetEnvironmentVariable("LC_ALL", "ko_KR.UTF-8", "User")
```

### 4. VS Code를 Git 에디터로 사용 (권장)

```bash
git config --global core.editor "code --wait"
```

이렇게 하면 커밋 메시지를 VS Code에서 작성할 수 있어 인코딩 문제가 없습니다.

### 5. 커밋 메시지 작성 시 주의사항

- **직접 입력**: PowerShell에서 직접 입력하면 깨질 수 있음
- **에디터 사용**: `git commit` (에디터 열림) 또는 `git commit -m "메시지"` (짧은 메시지)
- **VS Code 사용**: `code` 에디터 사용 시 UTF-8로 저장됨

## 테스트

다음 명령으로 테스트:

```bash
# 한글 파일명 테스트
echo "테스트" > 한글파일.txt
git add 한글파일.txt
git commit -m "한글 커밋 메시지 테스트"
git log --oneline -1
```

## 추가 팁

### Git Bash 사용
Git Bash를 사용하면 기본적으로 UTF-8 환경이므로 문제가 적습니다.

### WSL 사용
WSL(Windows Subsystem for Linux)을 사용하면 Linux 환경이므로 UTF-8이 기본입니다.

## 참고

- Git 공식 문서: https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration
- Windows 인코딩: https://docs.microsoft.com/en-us/windows/win32/intl/code-page-identifiers

