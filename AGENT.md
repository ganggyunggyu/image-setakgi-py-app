# Image Setakgi - 이미지 세탁기

## 프로젝트 개요

로컬에서 동작하는 Windows용 이미지 변형 데스크톱 앱.
웹 기반 이미지 세탁기 서비스를 참고하여 Python + PySide6로 개발.

## 기술 스택

- **Python** 3.10+
- **GUI**: PySide6
- **이미지 처리**: Pillow, numpy
- **메타데이터**: piexif
- **패키징**: PyInstaller

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
- Shift 유사 비율 고정 기능

### 4. EXIF 메타데이터
- 읽기/전체 삭제/덮어쓰기
- 랜덤 EXIF 생성

### 5. 변환 기록
- 파일별 JSON 기록 저장
- `~/.image_setakgi/transform_history.json`

## 실행 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# 실행
python -m app.main
```

## exe 빌드

```bash
pyinstaller --noconfirm --windowed --onefile --name "ImageSetakgi" app/main.py
```

## 설정 파일 위치

- 설정: `~/.image_setakgi/config.json`
- 변환 기록: `~/.image_setakgi/transform_history.json`

## 개발 규칙

- PySide6 Signal/Slot 패턴 사용
- 이미지 처리는 별도 스레드 (QThread, QThreadPool)
- 설정은 앱 종료 시 자동 저장
