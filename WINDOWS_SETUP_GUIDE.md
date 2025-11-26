# 🪟 Windows 완벽 설치 가이드

> 파이썬도 없는 맨땅 윈도우 컴퓨터에서 Image Setakgi를 실행하는 방법

---

## 📋 목차

1. [필수 프로그램 설치](#1-필수-프로그램-설치)
2. [프로젝트 다운로드](#2-프로젝트-다운로드)
3. [개발 모드로 실행](#3-개발-모드로-실행)
4. [독립 실행 파일 빌드](#4-독립-실행-파일-빌드)
5. [문제 해결](#5-문제-해결)

---

## 1. 필수 프로그램 설치

### 1-1. Python 설치

#### 다운로드
1. 브라우저에서 [python.org/downloads](https://www.python.org/downloads/) 접속
2. **"Download Python 3.12.x"** 버튼 클릭 (3.10 이상이면 됨)
3. 다운로드한 `python-3.12.x-amd64.exe` 실행

#### 설치 옵션 (중요!)
- ✅ **"Add python.exe to PATH"** 체크박스 **반드시 체크**
- "Install Now" 클릭

#### 설치 확인
```cmd
python --version
```
**출력 예시**: `Python 3.12.7`

```cmd
pip --version
```
**출력 예시**: `pip 24.x from ...`

> 만약 `'python'은(는) 내부 또는 외부 명령...` 에러가 나면:
> - 시스템을 재시작하거나
> - "환경 변수"에서 Python 경로를 수동으로 추가해야 함

---

### 1-2. Git 설치 (선택사항)

Git이 없어도 ZIP 다운로드로 가능하지만, Git이 있으면 편리합니다.

#### 다운로드
1. [git-scm.com/download/win](https://git-scm.com/download/win) 접속
2. **"64-bit Git for Windows Setup"** 다운로드
3. 설치 시 모든 옵션 기본값으로 진행

#### 설치 확인
```cmd
git --version
```
**출력 예시**: `git version 2.47.x.windows.1`

---

## 2. 프로젝트 다운로드

### 방법 A: Git 사용 (추천)

```cmd
# 1. 원하는 폴더로 이동 (예: C:\Users\내이름\Documents)
cd C:\Users\%USERNAME%\Documents

# 2. 프로젝트 복제
git clone https://github.com/your-username/image-setakgi-py-app.git

# 3. 프로젝트 폴더로 이동
cd image-setakgi-py-app
```

### 방법 B: ZIP 다운로드

1. GitHub 저장소 페이지에서 **"Code"** → **"Download ZIP"** 클릭
2. 다운로드한 `image-setakgi-py-app-main.zip` 압축 해제
3. 명령 프롬프트에서 해당 폴더로 이동:

```cmd
cd C:\Users\%USERNAME%\Downloads\image-setakgi-py-app-main
```

---

## 3. 개발 모드로 실행

### 3-1. 명령 프롬프트 열기

1. 프로젝트 폴더에서 **Shift + 우클릭**
2. **"PowerShell 여기에서 열기"** 또는 **"명령 프롬프트 여기에서 열기"** 선택

또는:

1. `Win + R` → `cmd` 입력 → 엔터
2. `cd` 명령으로 프로젝트 폴더로 이동

### 3-2. 가상환경 생성

```cmd
python -m venv venv
```

> 시간이 조금 걸립니다 (30초~1분). 완료되면 `venv` 폴더가 생성됩니다.

### 3-3. 가상환경 활성화

**PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

**명령 프롬프트(CMD):**
```cmd
venv\Scripts\activate.bat
```

> 활성화되면 프롬프트 앞에 `(venv)` 표시가 나타납니다:
> ```
> (venv) C:\...\image-setakgi-py-app>
> ```

**🚨 PowerShell에서 "스크립트 실행이 금지되어 있습니다" 에러 발생 시:**

```powershell
# 관리자 권한으로 PowerShell 열고:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3-4. 의존성 설치

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

> 설치되는 패키지:
> - PySide6 (GUI)
> - Pillow (이미지 처리)
> - numpy (수치 연산)
> - piexif (EXIF 메타데이터)
> - pyinstaller (빌드 도구)

### 3-5. 실행

```cmd
python -m app.main
```

이미지 변형 앱 창이 열립니다! 🎉

---

## 4. 독립 실행 파일 빌드

### 4-1. 자동 빌드 스크립트 사용 (가장 쉬움)

```cmd
# 가상환경 활성화 상태에서:
build_windows.bat
```

**빌드 과정:**
1. 가상환경 생성 (없으면)
2. 가상환경 활성화
3. 의존성 설치
4. PyInstaller로 .exe 빌드

**빌드 결과:**
- `dist\ImageSetakgi.exe` 파일 생성 (단일 실행 파일)

### 4-2. 실행 파일 실행

```cmd
# 명령 프롬프트에서:
dist\ImageSetakgi.exe

# 또는 탐색기에서:
# dist 폴더 → ImageSetakgi.exe 더블클릭
```

### 4-3. 수동 빌드 (선택사항)

```cmd
# 가상환경 활성화 후:
pyinstaller ^
    --noconfirm ^
    --windowed ^
    --onefile ^
    --name "ImageSetakgi" ^
    --add-data "app;app" ^
    app/main.py
```

---

## 5. 문제 해결

### Python이 인식되지 않음

```
'python'은(는) 내부 또는 외부 명령...
```

**해결 방법:**

1. Python을 다시 설치하되 **"Add python.exe to PATH"** 체크
2. 또는 시스템 환경 변수에 수동으로 추가:
   - `제어판` → `시스템` → `고급 시스템 설정`
   → `환경 변수` → `Path` 편집
   → `C:\Users\사용자명\AppData\Local\Programs\Python\Python312` 추가
   → `C:\Users\사용자명\AppData\Local\Programs\Python\Python312\Scripts` 추가

### 가상환경 활성화 실패 (PowerShell)

```
이 시스템에서 스크립트를 실행할 수 없으므로...
```

**해결 방법:**

```powershell
# PowerShell을 관리자 권한으로 실행:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### pip 설치 중 에러

```
error: Microsoft Visual C++ 14.0 or greater is required
```

**해결 방법:**

1. [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 다운로드
2. 설치 시 **"C++ 빌드 도구"** 선택

### pyinstaller 빌드 실패

```
ModuleNotFoundError: No module named 'PySide6'
```

**해결 방법:**

가상환경이 활성화되어 있는지 확인:
```cmd
# 프롬프트 앞에 (venv) 있어야 함
(venv) C:\...>

# 없으면:
venv\Scripts\activate.bat
```

### 앱 실행 시 창이 바로 꺼짐

- 명령 프롬프트에서 실행하면 에러 메시지 확인 가능:
```cmd
dist\ImageSetakgi.exe
```

---

## 📚 추가 명령어

### 가상환경 비활성화
```cmd
deactivate
```

### 프로젝트 폴더 내용 확인
```cmd
dir
```

### 프로젝트 업데이트 (Git 사용 시)
```cmd
git pull origin main
```

### 의존성 재설치
```cmd
pip install --force-reinstall -r requirements.txt
```

### 빌드 캐시 삭제 후 재빌드
```cmd
rmdir /s /q build dist
del /q *.spec
build_windows.bat
```

---

## ✅ 빠른 체크리스트

- [ ] Python 3.10+ 설치 완료
- [ ] `python --version` 명령어 작동
- [ ] 프로젝트 다운로드 완료
- [ ] 가상환경 생성 (`python -m venv venv`)
- [ ] 가상환경 활성화 (`venv\Scripts\activate.bat`)
- [ ] 의존성 설치 (`pip install -r requirements.txt`)
- [ ] 앱 실행 성공 (`python -m app.main`)
- [ ] (선택) 빌드 성공 (`build_windows.bat`)

---

## 🎯 최소 명령어로 실행하기

프로젝트 폴더에서 PowerShell/CMD 열고:

```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python -m app.main
```

끝! 4줄이면 실행됩니다.

---

**문제가 생기면**: 에러 메시지를 복사해서 구글/ChatGPT에 검색하세요!
