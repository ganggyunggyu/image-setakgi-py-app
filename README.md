# Image Setakgi - 이미지 세탁기

> **🪟 Windows 초보자?** 파이썬도 없는 맨땅 컴퓨터에서 시작하려면 → [**Windows 완벽 설치 가이드**](WINDOWS_SETUP_GUIDE.md)

로컬에서 동작하는 크로스플랫폼 이미지 변형 데스크톱 앱.
웹 기반 이미지 세탁기 서비스를 참고하여 Python + PySide6로 개발.

**지원 플랫폼**: Windows, macOS, Linux

---

## 기술 스택

- **Python** 3.10+
- **GUI**: PySide6
- **이미지 처리**: Pillow, numpy
- **메타데이터**: piexif
- **패키징**: PyInstaller

---

## 핵심 기능

### 1. 멀티 이미지 입력
- 드래그 앤 드랍 지원
- 파일 선택 다이얼로그

### 2. 실시간 미리보기
- 옵션 변경 시 즉시 미리보기 업데이트
- 별도 스레드에서 처리 (UI 렉 방지)

### 3. 포토샵 스타일 자유변형
- 미리보기 이미지 모서리 드래그로 크기 조절
- 1px 단위 정밀 조절
- 비율 고정 기능 (🔗 버튼)

### 4. EXIF 메타데이터
- 읽기/전체 삭제/덮어쓰기
- 랜덤 EXIF 생성

### 5. 변환 기록
- 파일별 JSON 기록 저장
- `~/.image_setakgi/transform_history.json`

---

## 빠른 시작 (4줄이면 끝)

```bash
python -m venv venv
# Windows:
venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python -m app.main
```

---

## 개발 모드 실행

### 1. 가상환경 생성
```bash
python -m venv venv
```

### 2. 가상환경 활성화

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 실행
```bash
python -m app.main
```

---

## 빌드 방법 (독립 실행 파일)

### Windows

#### 준비사항
- Python 3.10+ 설치 완료
- 가상환경 활성화 완료
- **처음이라면**: [Windows 완벽 설치 가이드](WINDOWS_SETUP_GUIDE.md) 참고

#### 빌드 실행
```batch
build_windows.bat
```

**빌드 결과**: `dist\ImageSetakgi.exe`

**실행 방법**:
```batch
# 명령 프롬프트에서:
dist\ImageSetakgi.exe

# 또는 탐색기에서:
# dist 폴더 → ImageSetakgi.exe 더블클릭
```

---

### macOS

#### 빌드 실행
```bash
# 실행 권한 부여 (최초 1회)
chmod +x build_mac.sh

# 빌드
./build_mac.sh
```

**빌드 결과**: `dist/ImageSetakgi`

**실행 방법**:
```bash
# 터미널에서:
./dist/ImageSetakgi

# 또는 Finder에서:
# dist 폴더 → ImageSetakgi 더블클릭
```

---

### 수동 빌드 (공통)

가상환경 활성화 후:

**macOS/Linux:**
```bash
pyinstaller --noconfirm --windowed --onefile \
    --name "ImageSetakgi" \
    --add-data "app:app" \
    app/main.py
```

**Windows:**
```batch
pyinstaller --noconfirm --windowed --onefile ^
    --name "ImageSetakgi" ^
    --add-data "app;app" ^
    app/main.py
```

---

## GitHub Actions 자동 빌드

macOS에서 Windows exe 파일을 빌드하거나, 그 반대의 경우 GitHub Actions를 활용하면 편리하다.

### 워크플로우 개요

| 파일 | 설명 |
|------|------|
| `.github/workflows/build.yml` | Windows + macOS 동시 빌드 및 릴리즈 자동화 |

### 트리거 조건

| 트리거 | 동작 |
|--------|------|
| `v*` 태그 푸시 (예: `v1.0.0`) | Windows + macOS 빌드 → GitHub Release 자동 생성 |
| 수동 실행 (workflow_dispatch) | 빌드만 수행 (Artifacts 다운로드 가능) |
| 수동 실행 + `create_release` 체크 | 빌드 + Release 생성 |

### 빌드 결과물

| 플랫폼 | 파일명 | 설명 |
|--------|--------|------|
| Windows | `ImageSetakgi-Windows.exe` | 독립 실행 파일 |
| macOS | `ImageSetakgi-macOS` | 독립 실행 파일 |

### 사용법

#### 1. 릴리즈 생성 (태그 푸시)

```bash
# 변경사항 커밋
git add .
git commit -m "release: v1.0.0"
git push

# 태그 생성 및 푸시 → 자동 빌드 + 릴리즈
git tag v1.0.0
git push origin v1.0.0
```

태그가 푸시되면:
1. Windows와 macOS에서 동시에 빌드 시작
2. 빌드 완료 후 GitHub Release 자동 생성
3. 실행 파일이 Release에 첨부됨

#### 2. 수동 빌드 (테스트용)

1. GitHub 저장소 → **Actions** 탭
2. 왼쪽 메뉴에서 **Build & Release** 선택
3. **Run workflow** 버튼 클릭
4. (선택) `릴리즈 생성 여부` 체크
5. **Run workflow** 클릭

#### 3. Artifacts 다운로드

빌드가 완료되면:
1. **Actions** 탭 → 해당 워크플로우 실행 클릭
2. 하단 **Artifacts** 섹션에서 다운로드
   - `ImageSetakgi-Windows.exe`
   - `ImageSetakgi-macOS`

### 버전 태그 네이밍 규칙

| 태그 형식 | 릴리즈 타입 | 예시 |
|-----------|-------------|------|
| `v1.0.0` | 정식 릴리즈 | `v1.0.0`, `v2.1.3` |
| `v1.0.0-beta` | 프리릴리즈 (베타) | `v1.0.0-beta`, `v2.0.0-beta.1` |
| `v1.0.0-alpha` | 프리릴리즈 (알파) | `v1.0.0-alpha` |

`beta` 또는 `alpha`가 포함된 태그는 자동으로 **Pre-release**로 표시됨.

### 주의사항

- GitHub Actions 무료 사용량: 월 2,000분 (public repo는 무제한)
- Windows 빌드: 약 3~5분 소요
- macOS 빌드: 약 3~5분 소요
- 빌드 실패 시 Actions 탭에서 로그 확인 가능

---

## 폴더 구조

```
/app
  main.py                 # 엔트리포인트
  /ui
    __init__.py
    main_window.py        # 메인 윈도우
    preview_widget.py     # 미리보기 + 자유변형 핸들
    options_panel.py      # 옵션 패널 (크기, 회전, 색상, 노이즈, EXIF)
  /core
    __init__.py
    config.py             # 설정 저장/로드
    image_ops.py          # 이미지 변환 함수
    preview.py            # 미리보기 스레드
    metadata.py           # EXIF 읽기/쓰기/삭제
    transform_history.py  # 파일별 변환 기록
    save_output.py        # 출력 파일 저장
  /assets                 # 아이콘 등 리소스
```

---

## 설정 파일 위치

| 파일 | 경로 | 설명 |
|------|------|------|
| 설정 | `~/.image_setakgi/config.json` | 마지막 옵션값, 폴더 경로 등 |
| 변환 기록 | `~/.image_setakgi/transform_history.json` | 파일별 변환 이력 |

---

## 개발 규칙

- PySide6 Signal/Slot 패턴 사용
- 이미지 처리는 별도 스레드 (QThread, QThreadPool)
- 설정은 앱 종료 시 자동 저장

---

## 문제 해결

### Windows에서 Python이 인식되지 않음
```
'python'은(는) 내부 또는 외부 명령...
```
→ [Windows 완벽 설치 가이드](WINDOWS_SETUP_GUIDE.md#python이-인식되지-않음) 참고

### PowerShell 스크립트 실행 에러
```
이 시스템에서 스크립트를 실행할 수 없으므로...
```
→ [Windows 완벽 설치 가이드](WINDOWS_SETUP_GUIDE.md#가상환경-활성화-실패-powershell) 참고

### 빌드 후 실행 파일이 바로 꺼짐
- 명령 프롬프트/터미널에서 실행하여 에러 메시지 확인:
```bash
# Windows:
dist\ImageSetakgi.exe

# macOS:
./dist/ImageSetakgi
```

---

## 라이선스

MIT License
