# Image Setakgi - 이미지 세탁기

> 현재 유지보수 중단 상태(archived)의 개인 프로젝트임. 마지막 커밋 이후 별도 업데이트 계획은 없고, 코드와 문서는 참고용으로만 유지함.

> **Windows 초보자?** 파이썬도 없는 맨땅 컴퓨터에서 시작하려면 → [Windows 완벽 설치 가이드](WINDOWS_SETUP_GUIDE.md)

## 프로젝트 개요

이미지 여러 장을 크롭·회전·색상·노이즈·원근 변형까지 한 번에 랜덤으로 적용해서 저장해야 하는 반복 작업이 있었음. 웹 기반 이미지 세탁기 서비스는 매번 파일을 업로드해야 하고 여러 장을 한 번에 처리하기 번거로워서, 폴더째 드래그해서 로컬에서 바로 배치 처리할 수 있는 데스크톱 앱으로 다시 만듦.

Python + PySide6 기반 크로스플랫폼(Windows/macOS/Linux) GUI 앱이고, PyInstaller로 단일 실행 파일(exe/앱)로 패키징해서 배포하는 구조임.

## 주요 기능

- **멀티 이미지 입력**: 드래그 앤 드랍, 파일 선택 다이얼로그 모두 지원
- **실시간 미리보기**: 옵션을 바꾸면 별도 스레드에서 즉시 미리보기 갱신 (UI 렉 방지)
- **포토샵 스타일 자유변형**: 미리보기 위에서 모서리 핸들을 드래그해 원근 변형, 1px 단위 조절, 비율 고정 토글
- **랜덤 변환**: 크롭/회전/노이즈/원근 오프셋/EXIF 날짜를 정해진 범위 안에서 무작위로 조합해 한 번에 적용 (`app/core/random_config.py`에서 범위 수치 직접 조절 가능)
- **EXIF 메타데이터 제어**: 읽기, 전체 삭제, 임의 값으로 덮어쓰기, 랜덤 카메라 정보 생성
- **출력 포맷 선택**: JPEG / PNG / WebP, 포맷별로 메타데이터 기록 방식이 다름
- **배치 처리 병렬화**: `ProcessPoolExecutor`로 여러 이미지를 동시에 변환
- **변환 기록**: 파일별 변환 이력을 JSON으로 저장해 나중에 확인 가능

## 기술 스택

| 영역 | 사용 기술 |
|------|-----------|
| 언어 | Python 3.10+ |
| GUI | PySide6 (Qt for Python) |
| 이미지 처리 | Pillow, numpy, opencv-python |
| 메타데이터 | piexif |
| 패키징 | PyInstaller |
| CI | GitHub Actions (`.github/workflows/build.yml`) |

`requirements.txt` 기준으로 고정된 최소 버전임.

```
PySide6>=6.6.0
Pillow>=10.0.0
numpy>=1.24.0
piexif>=1.1.3
pyinstaller>=6.0.0
opencv-python>=4.8.0
```

## 아키텍처 / 폴더 구조

```
app/
  main.py                        # 엔트리포인트, QApplication 초기화 및 아이콘 설정
  resources/
    icon.png                     # 앱 아이콘
  core/                          # UI에 의존하지 않는 순수 로직
    config.py                    # 설정 저장/로드 (~/.image_setakgi/config.json)
    constants.py                 # EXIF 태그 매핑, 랜덤 카메라 정보 등 상수
    image_ops.py                 # 크롭/회전/원근/색상/노이즈 변환 함수
    metadata.py                  # EXIF 읽기/쓰기/삭제, 포맷별 메타데이터 저장
    preview.py                   # 미리보기 생성 스레드
    random_config.py             # 랜덤 변환 범위 수치 (크롭/회전/노이즈/원근/날짜)
    random_transform.py          # 랜덤 변환 옵션 생성기
    save_output.py               # 출력 파일 저장, JPEG 흰 배경 자동 크롭
    transform_history.py         # 파일별 변환 기록 저장 (~/.image_setakgi/transform_history.json)
  ui/
    main_window.py                # 메인 윈도우, 파일 목록/옵션/미리보기 연결
    preview_widget.py             # 미리보기 래퍼 위젯 (graphics/view.py 사용)
    log_widget.py                 # 변환 로그 출력 위젯
    options_panel.py              # deprecated, app.ui.options로 이전됨 (하위 호환용)
    graphics/
      view.py                     # 자유변형 그래픽스 뷰 (핵심 인터랙션 로직)
      items.py                    # 씬에 올라가는 이미지/보더 아이템
      handles.py                  # 자유변형 코너 핸들
    options/
      options_panel.py             # 실제 옵션 패널 구현체
      crop_widget.py                # 크롭 옵션
      rotation_widget.py            # 회전 옵션
      perspective_widget.py         # 원근 오프셋 옵션
      random_config_panel.py        # 랜덤 변환 옵션
      output_format_panel.py        # 출력 포맷 선택
      exif_panel.py                  # EXIF 옵션
      slider_spinbox.py              # 슬라이더+스핀박스 복합 위젯
    widgets/
      busy_overlay.py               # 처리 중 로딩 오버레이
      file_list_widget.py           # 입력 파일 목록 위젯
    workers/
      batch_worker.py               # ProcessPoolExecutor 기반 배치 변환 워커
      transform_worker.py           # QRunnable 기반 단일 이미지 변환 워커
```

`app/ui/options_panel.py`, `app/ui/preview_widget.py`처럼 최상위에 남아있는 파일과 `options/`, `graphics/` 하위 폴더가 같이 존재하는 이유는 UI 모듈을 분리 리팩터링(`2e632b0 refactor(ui): 파일 분리 및 모듈 구조 개선`)하면서 이전 임포트 경로를 깨지 않으려고 얇은 재노출(re-export) 파일을 남겨뒀기 때문임.

## 설치 및 실행 방법

### 개발 모드

```bash
python3 -m venv venv

# macOS/Linux
source venv/bin/activate
# Windows (CMD)
venv\Scripts\activate.bat
# Windows (PowerShell)
venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m app.main
```

### 빌드 (독립 실행 파일)

**macOS**

```bash
chmod +x build_mac.sh   # 최초 1회
./build_mac.sh
```

빌드 결과: `dist/ImageSetakgi`

**Windows**

```batch
build_windows.bat
```

빌드 결과: `dist\ImageSetakgi.exe`

**수동 빌드 (공통)**

가상환경 활성화 후:

```bash
# macOS/Linux
pyinstaller --noconfirm --windowed --onefile --name "ImageSetakgi" --add-data "app:app" app/main.py

# Windows
pyinstaller --noconfirm --windowed --onefile --name "ImageSetakgi" --add-data "app;app" app/main.py
```

### GitHub Actions 자동 빌드

`.github/workflows/build.yml`이 Windows/macOS를 동시에 빌드함.

| 트리거 | 동작 |
|--------|------|
| `v*` 태그 푸시 | Windows + macOS 빌드 후 GitHub Release 자동 생성 |
| Actions 탭에서 수동 실행 (`workflow_dispatch`) | 빌드만 수행, Artifacts로 다운로드 가능 |
| 수동 실행 + `create_release` 체크 | 빌드 + Release 생성까지 |

```bash
git tag v1.0.0
git push origin v1.0.0
```

태그에 `beta`나 `alpha`가 들어가면 자동으로 Pre-release로 표시됨.

### 설정 파일 위치

| 파일 | 경로 | 설명 |
|------|------|------|
| 설정 | `~/.image_setakgi/config.json` | 마지막 옵션값, 입출력 폴더 경로 |
| 변환 기록 | `~/.image_setakgi/transform_history.json` | 파일별 변환 이력 |

## 트러블슈팅

프로젝트를 진행하면서 실제로 겪었던 문제와 고친 방식임.

### 배치 변환 중 프로세스 풀이 통째로 죽는 문제

`app/ui/workers/batch_worker.py`에서 `ProcessPoolExecutor`로 여러 이미지를 병렬 처리하는데, 기본 멀티프로세싱 컨텍스트로 실행하면 워커 프로세스가 죽으면서 `window error`가 나고 배치 작업 전체가 멈추는 문제가 있었음(`27cde3e fix: window error`).

세 커밋에 걸쳐 순차적으로 대응함.

1. `mp.get_context("spawn")`으로 명시적으로 spawn 방식을 지정하고 `BrokenProcessPool` 예외를 잡도록 함(`app/ui/workers/batch_worker.py:163`).
2. `BrokenProcessPool`이 일부 Python 버전에서 `concurrent.futures`에 없어서 import가 실패할 수 있어, 없으면 자체 예외 클래스로 대체하도록 방어 코드를 추가함(`app/ui/workers/batch_worker.py:8`).
3. 그래도 프로세스 풀 자체가 뜨지 않는 환경이 있어서, 병렬 처리가 실패하면 남은 파일들을 순차 처리로 폴백하도록 바꿈(`app/ui/workers/batch_worker.py:196`). 워커 초기화 시 OpenCV/BLAS 계열 스레드 환경변수(`OMP_NUM_THREADS` 등)를 모두 1로 고정해 프로세스 간 스레드 경합도 같이 줄임.

### 자유변형 코너를 극단적으로 옮기면 앱이 죽는 문제

`app/core/image_ops.py:246`의 `find_perspective_coeffs`는 원근 변환 계수를 구하려고 `np.linalg.inv()`로 역행렬을 계산하는데, 4개 코너가 일직선에 가깝게 모이면 특이 행렬(singular matrix)이 되어 `LinAlgError`가 발생하고 앱이 죽었음. `IMPROVEMENTS.md`에 CRIT-001로 기록된 이슈고, `d594f97 fix(core): IMPROVEMENTS.md 이슈 해결`에서 `LinAlgError`를 잡아 `None`을 반환하도록 하고, 호출부(`perspective_transform`)에서 `None`이면 원본 이미지를 그대로 반환하도록 방어 처리함(`app/core/image_ops.py:262`).

### 자유변형 뷰에서 이미지 교체 시 크래시

`app/ui/graphics/view.py`의 `set_image()`가 새 이미지를 그릴 때 `QGraphicsScene.clear()`를 먼저 호출해 이전 아이템들을 삭제한 다음에도 Python 쪽에서 이전 `QGraphicsPixmapItem` 참조(`self._image_item`)를 계속 들고 있어서, Qt가 이미 삭제한 C++ 객체에 접근하며 크래시가 났음. `scene.clear()` 호출 전에 `self._image_item = None`으로 Python 참조부터 끊도록 순서를 바꿔서 해결함(`app/ui/graphics/view.py:83-87`, `17ac074 fix`).

### 스마트폰으로 찍은 사진이 회전된 채로 로드됨

카메라로 찍은 사진 상당수는 실제 픽셀은 눕혀서 저장하고 EXIF Orientation 태그로 회전값만 기록하는데, `Image.open()`만으로는 그 태그를 반영하지 않아서 미리보기와 결과물이 촬영 방향과 다르게 나오는 문제가 있었음. 이미지를 불러오는 두 지점 모두에서 `ImageOps.exif_transpose()`를 거치도록 수정함(`app/ui/main_window.py:383`, `app/ui/main_window.py:611`, `18ac1c0 fix(worker): EXIF Orientation 자동 보정`).

### JPEG로 저장하면 원근/자유변형 여백에 흰 배경이 남음

원근 변형을 적용하면 회전한 사각형 바깥쪽에 빈 공간이 생기는데, 처음에는 이 공간을 흰색으로 채운 채 그대로 저장해서 결과물 가장자리에 부자연스러운 흰 테두리가 남았음. `8e66f02`에서 흰색 채우기 대신 투명(RGBA) 배경으로 변형한 뒤 alpha 채널 기준 bbox로 실제 콘텐츠 영역만 크롭하도록 바꿨고, JPEG처럼 투명도를 지원하지 않는 포맷으로 저장할 때는 `app/core/save_output.py:102`에서 순백색(255,255,255) 픽셀을 numpy로 감지해 한 번 더 가장자리를 크롭하도록 이중으로 처리함(`fe1d55c feat(save): JPEG 저장 시 흰색 배경 자동 제거`).

### 변환 기록 파일이 동시 쓰기로 깨짐

`app/core/transform_history.py`가 앱 전역에서 공유하는 `transform_history.json`에 여러 워커 스레드가 동시에 쓰기를 시도할 수 있는데, 락 없이 파일을 열고 쓰다 보니 내용이 깨지거나 `JSONDecodeError`로 앱이 죽는 경우가 있었음. `threading.Lock()`을 추가해 `record_transform()` 전체를 잠그도록 했고(`app/core/transform_history.py:8`, `app/core/transform_history.py:42`), 로드 시점에 JSON 파싱이 실패하면 예외를 던지는 대신 빈 딕셔너리로 복구하도록 해서 파일이 한 번 깨져도 앱이 계속 뜨게 만듦(`9083d6e fix(core): add thread-safety and error handling to transform history`).

### 포토샵 스타일 자유변형 재작성 후 원복

`b3a6501`에서 자유변형 뷰(`graphics/view.py`, `handles.py`)를 437줄에서 265줄로 줄이며 전면 재작성했으나, 2분 뒤 `7652d74`에서 바로 되돌림. 커밋 메시지에 구체적 사유는 남아있지 않지만, 같은 날 이후 커밋들에서 원근 오프셋/자유변형 관련 수정이 이어진 것으로 볼 때 재작성 버전이 기존 자유변형 동작(코너별 개별 오프셋 조절 등)을 깨뜨려서 원래 구현으로 되돌린 것으로 보임.

## 알려진 제약사항

- 자동화된 테스트 코드가 없음. `benchmark.py`가 있지만 이건 성능 측정용 스크립트고 회귀 테스트 용도는 아님.
- 배치 병렬 처리는 `ProcessPoolExecutor`가 실패하면 순차 처리로 폴백하도록 되어 있지만, 폴백 상태에서는 대량 이미지 처리 속도가 느려짐.
- 설정/변환 기록이 `~/.image_setakgi/`에 로컬 파일로만 저장되므로 여러 기기 간 동기화는 지원하지 않음.
- PyInstaller 빌드는 GitHub Actions에서 Windows/macOS 각각 네이티브 러너로 진행되며, 별도 코드 서명(codesign/notarization)은 설정되어 있지 않음.
- 현재 유지보수가 중단된 상태라 위 이슈들에 대한 추가 수정 계획은 없음.

## 라이선스

MIT License
