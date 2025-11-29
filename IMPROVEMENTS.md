# 코드 개선점 분석 보고서

> 분석일: 2025-11-28
> 이전 분석일: 2025-11-26
> 분석 대상: Image Setakgi 전체 프로젝트

## 요약

- 🔴 Critical: 1건 (이전 3건 → 2건 해결됨)
- 🟠 High: 4건 (이전 5건 → 1건 해결됨)
- 🟡 Medium: 8건 (이전 7건 + 신규 1건)
- 🟢 Low: 5건 (이전 4건 + 신규 1건)

### 해결된 이슈

- ✅ CRIT-001: transform_history.py JSON 예외 처리 추가됨
- ✅ CRIT-002: preview.py QImage bytes_per_line 명시적 계산 추가됨
- ✅ HIGH-004: CropWidget의 _on_reset()이 public reset() 메서드로 사용됨

---

## 🔴 Critical Issues

### [CRIT-001] 행렬 연산 예외 처리 누락

**위치**: [image_ops.py:243-248](app/core/image_ops.py#L243-L248)

**문제**:
원근 변환 계수 계산 시 `np.linalg.inv()`가 singular matrix(역행렬이 존재하지 않는 행렬)에서 `LinAlgError`를 발생시킴

**현재 코드**:
```python
def find_perspective_coeffs(
    source_coords: List[Tuple[float, float]],
    target_coords: List[Tuple[float, float]]
) -> Tuple:
    # ...
    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)  # singular matrix 시 크래시
    return tuple(np.array(res).reshape(8))
```

**영향**:
- 사용자가 코너를 특정 위치로 이동 시 앱 크래시
- 4개의 코너가 일직선이나 한 점으로 모이면 발생

**해결 방안**:
```python
def find_perspective_coeffs(
    source_coords: List[Tuple[float, float]],
    target_coords: List[Tuple[float, float]]
) -> Optional[Tuple]:
    try:
        matrix = []
        for s, t in zip(source_coords, target_coords):
            matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
            matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])

        A = np.matrix(matrix, dtype=np.float32)
        B = np.array(source_coords).reshape(8)

        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        return tuple(np.array(res).reshape(8))
    except np.linalg.LinAlgError:
        return None
```

**검증 방법**:
- 4개의 코너를 일직선 또는 한 점으로 모았을 때 크래시 여부 확인

---

## 🟠 High Priority Issues

### [HIGH-001] 스레드 종료 처리 불안정

**위치**: [main_window.py:354-357](app/ui/main_window.py#L354-L357)

**문제**:
`quit()`와 `wait()` 호출 시 타임아웃 없이 무한 대기할 수 있음

**현재 코드**:
```python
if self._preview_thread and self._preview_thread.isRunning():
    self._preview_thread.quit()
    self._preview_thread.wait()  # 타임아웃 없음
```

**영향**:
- 스레드가 응답하지 않으면 UI 프리징
- 앱 강제 종료 필요

**해결 방안**:
```python
if self._preview_thread and self._preview_thread.isRunning():
    self._preview_thread.quit()
    if not self._preview_thread.wait(3000):  # 3초 타임아웃
        self._preview_thread.terminate()
        self._preview_thread.wait()
```

---

### [HIGH-002] bare except 사용

**위치**: [metadata.py:53](app/core/metadata.py#L53)

**문제**:
`except:` 는 `SystemExit`, `KeyboardInterrupt` 등 모든 예외를 잡아버려 예상치 못한 동작 발생

**현재 코드**:
```python
try:
    value = value.decode("utf-8", errors="ignore").strip("\x00")
except:
    value = str(value)
```

**해결 방안**:
```python
try:
    value = value.decode("utf-8", errors="ignore").strip("\x00")
except (UnicodeDecodeError, AttributeError):
    value = str(value)
```

---

### [HIGH-003] config.py JSON 로드 시 예외 처리 누락

**위치**: [config.py:29-34](app/core/config.py#L29-L34)

**문제**:
손상된 설정 파일 처리 안됨

**현재 코드**:
```python
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        saved = json.load(f)  # 예외 처리 없음
```

**해결 방안**:
```python
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(saved)
            return merged
    except (json.JSONDecodeError, OSError):
        pass  # 기본값 사용
return DEFAULT_CONFIG.copy()
```

---

### [HIGH-004] closeEvent에서 스레드풀 대기 시 앱 멈춤 가능

**위치**: [main_window.py:636-639](app/ui/main_window.py#L636-L639)

**문제**:
`waitForDone()` 타임아웃 없이 호출하면 작업 완료까지 UI 블록

**현재 코드**:
```python
def closeEvent(self, event):
    save_config(self._config)
    self._thread_pool.waitForDone()  # 무한 대기 가능
    super().closeEvent(event)
```

**해결 방안**:
```python
def closeEvent(self, event):
    save_config(self._config)
    self._thread_pool.waitForDone(5000)  # 5초 타임아웃
    super().closeEvent(event)
```

---

## 🟡 Medium Priority Issues

### [MED-001] dropEvent 코드 중복

**위치**:
- [main_window.py:607-634](app/ui/main_window.py#L607-L634)
- [file_list_widget.py:54-80](app/ui/widgets/file_list_widget.py#L54-L80)

**문제**:
MainWindow와 FileListWidget에서 거의 동일한 dropEvent 로직이 중복됨

**현재 코드**:
```python
# MainWindow
def dropEvent(self, event: QDropEvent):
    files = []
    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    for url in event.mimeData().urls():
        # ... 동일한 로직 반복

# FileListWidget
def dropEvent(self, event: QDropEvent):
    files = []
    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    for url in event.mimeData().urls():
        # ... 동일한 로직 반복
```

**해결 방안**:
유틸리티 함수로 추출:
```python
# utils/file_utils.py
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

def extract_image_files_from_urls(urls) -> list[str]:
    """URL 목록에서 이미지 파일 경로 추출"""
    files = []
    for url in urls:
        path = url.toLocalFile()
        if not path:
            continue
        p = Path(path)
        if p.is_dir():
            for f in p.iterdir():
                if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                    files.append(str(f))
        elif p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            files.append(path)
    return sorted(files) if files else []
```

---

### [MED-002] image_extensions 상수 중복 정의

**위치**:
- [main_window.py:294](app/ui/main_window.py#L294)
- [main_window.py:611](app/ui/main_window.py#L611)
- [file_list_widget.py:57](app/ui/widgets/file_list_widget.py#L57)

**문제**:
지원 확장자가 여러 곳에 하드코딩됨

**해결 방안**:
중앙 상수 파일에서 관리:
```python
# app/core/constants.py
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
```

---

### [MED-003] 여러 상태 변수 동기화 복잡성

**위치**: [main_window.py:49-62](app/ui/main_window.py#L49-L62)

**문제**:
여러 Optional 변수들(`_current_file`, `_current_image`, `_perspective_corners`, `_loading_new_image`)의 상태가 동기화되어야 하지만 관리가 분산됨

**현재 코드**:
```python
self._files: list[str] = []
self._current_file: Optional[str] = None
self._current_image: Optional[Image.Image] = None
self._preview_thread: Optional[PreviewThread] = None
self._perspective_corners: Optional[list] = None
self._loading_new_image = False
```

**해결 방안**:
상태를 하나의 데이터 클래스로 묶어 관리:
```python
@dataclass
class EditorState:
    current_file: Optional[str] = None
    current_image: Optional[Image.Image] = None
    perspective_corners: Optional[list] = None
    is_loading: bool = False

    def reset(self):
        self.current_file = None
        self.current_image = None
        self.perspective_corners = None
        self.is_loading = False
```

---

### [MED-004] PreviewThread 시그널 연결 해제 없음

**위치**: [main_window.py:366-368](app/ui/main_window.py#L366-L368)

**문제**:
매번 새로운 PreviewThread를 생성하고 시그널을 연결하지만, 이전 스레드의 시그널은 명시적으로 disconnect 하지 않음

**현재 코드**:
```python
self._preview_thread = PreviewThread(self)
# ...
self._preview_thread.preview_ready.connect(self._on_preview_ready)
self._preview_thread.preview_error.connect(self._on_preview_error)
```

**해결 방안**:
이전 스레드 정리 시 시그널도 disconnect:
```python
if self._preview_thread:
    try:
        self._preview_thread.preview_ready.disconnect()
        self._preview_thread.preview_error.disconnect()
    except (TypeError, RuntimeError):
        pass  # 이미 연결 해제됨
```

---

### [MED-005] PreviewWorker와 PreviewThread 구조 불명확

**위치**: [preview.py:38-98](app/core/preview.py#L38-L98)

**문제**:
PreviewWorker가 별도 객체로 존재하지만 PreviewThread 안에서만 사용됨. 이동할 수 있는 QObject 패턴도 사용하지 않음

**해결 방안**:
PreviewWorker를 PreviewThread에 병합하거나, moveToThread 패턴을 올바르게 적용

---

### [MED-006] 매직 값 하드코딩

**위치**: [metadata.py:98-104](app/core/metadata.py#L98-L104)

**문제**:
카메라 목록, 연도 범위 등이 코드에 하드코딩됨

**해결 방안**:
상수 파일 또는 설정 파일로 분리:
```python
# constants.py
CAMERA_MODELS = [
    ("Canon", "EOS 5D Mark IV"),
    ("Nikon", "D850"),
    # ...
]
RANDOM_YEAR_RANGE = (2018, 2024)
```

---

### [MED-007] 매번 border_rect 재생성

**위치**: [view.py:166-182](app/ui/graphics/view.py#L166-L182)

**문제**:
자유변형 모드에서 핸들 위치 업데이트마다 border를 삭제하고 새로 생성함

**해결 방안**:
QGraphicsPathItem의 path만 업데이트:
```python
if isinstance(self._border_rect, QGraphicsPathItem):
    self._border_rect.setPath(path)
else:
    # 최초 생성 시만 새로 만듦
```

---

### [MED-008] Deprecated 파일 존재

**위치**: [options_panel.py](app/ui/options_panel.py)

**문제**:
`options_panel.py`가 deprecated이고 `app.ui.options`로 리팩토링되었지만, 파일이 그대로 남아있음

**현재 코드**:
```python
"""
Deprecated: This module is kept for backward compatibility.
Use app.ui.options instead.
"""

from app.ui.options import (
    SliderWithSpinBox,
    # ...
)
```

**해결 방안**:
1. 해당 파일을 import하는 곳이 있는지 확인
2. 없다면 파일 삭제
3. 있다면 import 경로를 새 모듈로 변경

---

## 🟢 Low Priority Issues

### [LOW-001] 타입 힌트 일관성

**위치**: 전체 프로젝트

**문제**:
일부 함수는 타입 힌트가 있고, 일부는 없음
- `list[str]` vs `List[str]` 혼용
- `Optional[type]` vs `type | None` 혼용

**해결 방안**:
모던 Python (3.10+) 스타일로 통일:
```python
# 권장 스타일
def process(items: list[str], value: int | None = None) -> dict[str, Any]:
    ...
```

---

### [LOW-002] 네이밍 일관성

**위치**: 전체 프로젝트

**문제**:
- 이벤트 핸들러: `_on_` 접두사와 `_handle_` 접두사 혼용
- 예: `_on_slider_change` vs `_handle_free_transform_move`
- JSON 키: snake_case와 camelCase 혼용 (`metadataActions`)

**해결 방안**:
네이밍 컨벤션 통일:
- 이벤트 핸들러: `_on_` 접두사
- 내부 처리 로직: `_handle_` 접두사
- JSON 키: snake_case 통일

---

### [LOW-003] 스타일시트 상수화

**위치**: [main_window.py:176-243](app/ui/main_window.py#L176-L243)

**문제**:
긴 스타일시트 문자열이 메서드 안에 직접 작성됨

**해결 방안**:
별도 파일 또는 상수로 분리:
```python
# styles.py
MAIN_WINDOW_STYLE = """
QMainWindow { ... }
"""
```

---

### [LOW-004] 미사용 import

**위치**: [image_ops.py:5](app/core/image_ops.py#L5)

**문제**:
- `io` 모듈 미사용
- `List`, `Tuple` → 리터럴 타입 힌트 사용 가능 (Python 3.9+)

**해결 방안**:
미사용 import 제거:
```python
# 제거
import io

# 변경 전
from typing import Optional, List, Tuple

# 변경 후
from typing import Optional
```

---

### [LOW-005] random_config.py의 타입 불일치

**위치**: [random_config.py:7-8](app/core/random_config.py#L7-L8)

**문제**:
`ROTATION_RANGE`와 `PERSPECTIVE_RANGE`가 int로 정의되어 있지만, 사용하는 곳에서는 float으로 기대함

**현재 코드**:
```python
ROTATION_RANGE = 3      # int
PERSPECTIVE_RANGE = 6   # int
```

**해결 방안**:
```python
ROTATION_RANGE = 3.0    # float
PERSPECTIVE_RANGE = 6.0 # float
```

---

## 개선 로드맵

### Phase 1: 긴급 수정 (Critical + High) - 안정성 확보
1. [ ] CRIT-001: image_ops.py 행렬 연산 예외 처리
2. [ ] HIGH-001: main_window.py 스레드 종료 타임아웃
3. [ ] HIGH-002: metadata.py bare except 수정
4. [ ] HIGH-003: config.py JSON 예외 처리
5. [ ] HIGH-004: main_window.py closeEvent 타임아웃

### Phase 2: 품질 개선 (Medium) - 성능 및 유지보수성
1. [ ] MED-001: dropEvent 중복 코드 추출
2. [ ] MED-002: image_extensions 상수화
3. [ ] MED-003: 상태 관리 리팩토링
4. [ ] MED-004: PreviewThread 시그널 정리
5. [ ] MED-005: PreviewThread 구조 정리
6. [ ] MED-006: 매직 값 상수화
7. [ ] MED-007: border_rect 업데이트 최적화
8. [ ] MED-008: Deprecated 파일 정리

### Phase 3: 리팩토링 (Low) - 코드 품질
1. [ ] LOW-001: 타입 힌트 일관성
2. [ ] LOW-002: 네이밍 컨벤션 통일
3. [ ] LOW-003: 스타일시트 분리
4. [ ] LOW-004: 미사용 import 정리
5. [ ] LOW-005: random_config 타입 수정

---

## 참고 사항

### 이전 분석 대비 개선된 점

1. **transform_history.py**: JSON 로드 시 예외 처리 추가됨
2. **preview.py**: QImage 생성 시 bytes_per_line 명시적 계산
3. **options_panel.py**: 모듈 분리로 코드 구조 개선

### 추가 권장 사항

1. **단위 테스트 추가**: 핵심 변환 로직(`image_ops.py`)에 대한 테스트 필요
2. **로깅 시스템 도입**: 에러 추적을 위한 로깅 추가
3. **설정 검증**: 설정값 로드 시 스키마 검증 추가 고려
4. **상수 파일 통합**: `constants.py`로 하드코딩된 값들 중앙 관리
