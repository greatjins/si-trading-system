# 현재 환경 정보

## 시스템 정보

- **OS**: Windows (PowerShell 5.1 기준)
- **PowerShell 버전**: 5.1.26100.7462 (Desktop Edition)
- **Git 버전**: 2.30.1.windows.1

## 인코딩 설정

### ✅ 올바르게 설정된 항목

- **코드 페이지**: 65001 (UTF-8) ✅
- **Console.OutputEncoding**: UTF-8 ✅
- **OutputEncoding**: UTF-8 ✅
- **Git i18n.commitencoding**: utf-8 ✅
- **Git i18n.logoutputencoding**: utf-8 ✅
- **Git core.quotepath**: false ✅
- **LANG 환경 변수**: C.UTF-8 ✅

### ❌ 문제가 있는 항목

- **System.Text.Encoding::Default**: **CP949 (한국어)** ❌
  - 이것이 PowerShell의 기본 인코딩입니다
  - `Out-File`이나 문자열 처리 시 기본적으로 CP949를 사용합니다
  - 이것이 한글 깨짐의 근본 원인입니다

## 문제 분석

### 왜 한글이 깨지는가?

1. **PowerShell의 기본 인코딩이 CP949**
   - `System.Text.Encoding::Default` = CP949
   - PowerShell이 문자열을 처리할 때 기본적으로 CP949 사용

2. **Git은 UTF-8을 기대**
   - Git 설정은 모두 UTF-8로 되어 있음
   - 하지만 PowerShell에서 전달되는 문자열이 CP949로 인코딩됨

3. **인코딩 변환 과정에서 문제 발생**
   ```
   PowerShell (CP949) → Git (UTF-8) → 저장소 (깨진 상태)
   ```

### 해결 방법

#### 방법 1: 명시적으로 UTF-8 사용 (권장)

```powershell
# Out-File 사용 시
"한글 메시지" | Out-File -Encoding utf8 commit_msg.txt

# 또는 .NET 메서드 사용 (BOM 없이)
[System.IO.File]::WriteAllText(
    "commit_msg.txt", 
    "한글 메시지", 
    [System.Text.UTF8Encoding]::new($false)
)
```

#### 방법 2: PowerShell 프로필에 함수 추가

```powershell
function git-commit-ko {
    param([string]$message)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText("commit_msg.txt", $message, $utf8NoBom)
    git commit -F commit_msg.txt
    Remove-Item commit_msg.txt
}

# 사용
git-commit-ko "docs: 한글 커밋 메시지"
```

#### 방법 3: 영문 메시지 사용

가장 확실한 방법:

```powershell
git commit -m "docs: Add Git commit message tips"
```

#### 방법 4: Git Bash 사용

Git Bash는 기본적으로 UTF-8 환경이므로 문제 없습니다.

## 현재 PowerShell 프로필

프로필 위치: `C:\Users\USER\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`

프로필에 이미 다음 설정이 추가되어 있습니다:
- `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`
- `$OutputEncoding = [System.Text.Encoding]::UTF8`
- `chcp 65001`

하지만 이것만으로는 부족합니다. `System.Text.Encoding::Default`는 시스템 레벨 설정이라 PowerShell 프로필로 변경할 수 없습니다.

## 결론

**현재 환경에서는 PowerShell에서 직접 한글 커밋 메시지를 작성하는 것이 근본적으로 어렵습니다.**

권장 사항:
1. **영문 커밋 메시지 사용** (가장 확실)
2. **Git Bash 사용** (한글 지원)
3. **VS Code 에디터 사용** (`git commit` 후 에디터에서 작성)
4. **함수 만들어서 사용** (위의 `git-commit-ko` 함수)

