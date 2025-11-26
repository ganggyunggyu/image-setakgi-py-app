# 코드 개선점 분석 보고서

> 분석일: 2025-11-26
> 분석 대상: Image Setakgi 전체 프로젝트

## 요약

- 🔴 Critical: 3건
- 🟠 High: 5건
- 🟡 Medium: 7건
- 🟢 Low: 4건

---

## 🔴 Critical Issues

### [CRIT-001] JSON 파일 로드 시 예외 처리 누락

**위치**: `app/core/transform_history.py:16-17`

**문제**:
히스토리 파일이 손상되었거나 잘못된 JSON 형식일 때 `json.load()`가 `JSONDecodeError`를 발생시키면 전체 앱이 크래시됨

**현재 코드**:
```python
def load_history() -> dict[str, Any]:
    ensure_history_dir()
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)  # 예외 처리 없음
    return {}
```

**영향**:
- 파일이 손상되면 앱 시작 불가
- 사용자 데이터 손실 가능

**해결 방안**:
```python
def load_history() -> dict[str, Any]:
    ensure_history_dir()
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            # 손상된 파일 백업 후 초기화
            backup_path = HISTORY_FILE.with_suffix(".json.bak")
            HISTORY_FILE.rename(backup_path)
            return {}
    return {}
```

**검증 방법**:
- 손상된 JSON 파일로 앱 실행 테스트
- 정상 파일로 복구 가능 여부 확인

---

### [CRIT-002] QImage 메모리 참조 문제

**위치**: `app/core/preview.py:30-32`

**문제**:
`img.tobytes()`로 생성된 바이트 데이터가 QImage 생성 후 Python GC에 의해 해제될 수 있음. QImage는 데이터를 복사하지 않고 참조만 유지하므로, 원본 데이터가 해제되면 이미지가 깨짐

**현재 코드**:
```python
def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    # ...
    data = img.tobytes("raw", img.mode)
    qimage = QImage(data, img.width, img.height, qformat)
    return QPixmap.fromImage(qimage.copy())
```

**영향**:
- 간헐적 이미지 깨짐 현상
- 디버깅 어려운 메모리 관련 버그

**해결 방안**:
```python
def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    if img.mode == "RGBA":
        qformat = QImage.Format.Format_RGBA8888
    else:
        img = img.convert("RGB")
        qformat = QImage.Format.Format_RGB888

    # bytes_per_line을 명시적으로 계산하여 전달
    data = img.tobytes("raw", img.mode)
    bytes_per_line = img.width * len(img.mode)
    qimage = QImage(data, img.width, img.height, bytes_per_line, qformat)
    # copy()를 통해 데이터를 복사하여 안전하게 반환
    return QPixmap.fromImage(qimage.copy())
```

**검증 방법**:
- 연속 이미지 로드 테스트
- 메모리 프로파일링

---

### [CRIT-003] 행렬 연산 예외 처리 누락

**위치**: `app/core/image_ops.py:151-154`

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
- 변환 작업 중 데이터 손실

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

**위치**: `app/ui/main_window.py:402-404`

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

**위치**: `app/core/metadata.py:41`

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

**위치**: `app/core/config.py:30-34`

**문제**:
CRIT-001과 동일하게 손상된 설정 파일 처리 안됨

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

### [HIGH-004] 캡슐화 위반 - private 메서드 직접 호출

**위치**: `app/ui/options_panel.py:423, 472`

**문제**:
다른 위젯의 private 메서드 `_on_reset()`을 직접 호출함

**현재 코드**:
```python
def _reset_all_options(self):
    self._crop_widget._on_reset()  # private 메서드 직접 호출
```

**영향**:
- CropWidget 내부 구현 변경 시 OptionsPanel도 수정 필요
- 유지보수성 저하

**해결 방안**:
CropWidget에 public 메서드 추가:
```python
# CropWidget 클래스에 추가
def reset(self):
    """크롭 설정 초기화 (public API)"""
    self._on_reset()
```

그 후 OptionsPanel에서:
```python
def _reset_all_options(self):
    self._crop_widget.reset()  # public 메서드 사용
```

---

### [HIGH-005] closeEvent에서 스레드풀 대기 시 앱 멈춤 가능

**위치**: `app/ui/main_window.py:513`

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

### [MED-001] 여러 상태 변수 동기화 복잡성

**위치**: `app/ui/main_window.py:163-171`

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

### [MED-002] PreviewWorker와 PreviewThread 구조 불명확

**위치**: `app/core/preview.py:35-94`

**문제**:
PreviewWorker가 별도 객체로 존재하지만 PreviewThread 안에서만 사용됨. 이동할 수 있는 QObject 패턴도 사용하지 않음

**해결 방안**:
PreviewWorker를 PreviewThread에 병합하거나, moveToThread 패턴을 올바르게 적용

---

### [MED-003] 매번 히스토리 전체 파일 읽기/쓰기

**위치**: `app/core/transform_history.py:37-51`

**문제**:
`record_transform()` 호출마다 전체 파일을 읽고 다시 씀

**영향**:
- 히스토리가 커지면 성능 저하
- 디스크 I/O 과다

**해결 방안**:
메모리 캐싱 또는 append-only 로그 파일 방식 고려

---

### [MED-004] 파일 추가 시 중복 체크 O(n)

**위치**: `app/ui/main_window.py:336-341`

**문제**:
리스트에서 `in` 연산자로 중복 체크하면 O(n) 복잡도

**현재 코드**:
```python
for f in files:
    if f not in self._files:  # O(n) 체크
        self._files.append(f)
```

**해결 방안**:
set을 추가로 유지하여 O(1) 체크:
```python
# __init__에서
self._files_set: set[str] = set()

# _add_files에서
for f in files:
    if f not in self._files_set:
        self._files_set.add(f)
        self._files.append(f)
```

---

### [MED-005] 매번 border_rect 재생성

**위치**: `app/ui/graphics/view.py:168-173`

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

### [MED-006] 매직 값 하드코딩

**위치**: `app/core/metadata.py:85-108`

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

### [MED-007] 미사용 import

**위치**: 여러 파일

**문제**:
- `app/core/preview.py:5`: `io` 미사용
- `app/core/image_ops.py:3`: `List`, `Tuple` → 리터럴 타입 힌트 사용 가능 (Python 3.9+)

**해결 방안**:
미사용 import 제거, 모던 타입 힌트 문법 사용

---

## 🟢 Low Priority Issues

### [LOW-001] 타입 힌트 일관성

**위치**: 전체 프로젝트

**문제**:
일부 함수는 타입 힌트가 있고, 일부는 없음

**해결 방안**:
모든 public 함수에 타입 힌트 추가

---

### [LOW-002] 네이밍 일관성

**위치**: 전체 프로젝트

**문제**:
- 이벤트 핸들러: `_on_` 접두사와 `_handle_` 접두사 혼용
- 예: `_on_slider_change` vs `_handle_free_transform_move`

**해결 방안**:
네이밍 컨벤션 통일 (이벤트 핸들러는 `_on_`, 내부 처리 로직은 `_handle_`)

---

### [LOW-003] 스타일시트 상수화

**위치**: `app/ui/main_window.py:266-333`

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

### [LOW-004] 파일 확장자 상수화

**위치**: `app/ui/main_window.py:149`, `app/core/save_output.py:20`

**문제**:
지원 확장자가 여러 곳에 하드코딩됨

**해결 방안**:
```python
# constants.py
SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
```

---

## 개선 로드맵

### Phase 1: 긴급 수정 (Critical + High) - 안정성 확보
1. [ ] CRIT-001: transform_history.py JSON 예외 처리
2. [ ] CRIT-002: preview.py QImage 메모리 안전성
3. [ ] CRIT-003: image_ops.py 행렬 연산 예외 처리
4. [ ] HIGH-001: main_window.py 스레드 종료 타임아웃
5. [ ] HIGH-002: metadata.py bare except 수정
6. [ ] HIGH-003: config.py JSON 예외 처리
7. [ ] HIGH-004: options_panel.py 캡슐화 개선
8. [ ] HIGH-005: main_window.py closeEvent 타임아웃

### Phase 2: 품질 개선 (Medium) - 성능 및 유지보수성
1. [ ] MED-001: 상태 관리 리팩토링
2. [ ] MED-002: PreviewThread 구조 정리
3. [ ] MED-003: 히스토리 캐싱
4. [ ] MED-004: 파일 중복 체크 최적화
5. [ ] MED-005: border_rect 업데이트 최적화
6. [ ] MED-006: 매직 값 상수화
7. [ ] MED-007: 미사용 import 정리

### Phase 3: 리팩토링 (Low) - 코드 품질
1. [ ] LOW-001: 타입 힌트 일관성
2. [ ] LOW-002: 네이밍 컨벤션 통일
3. [ ] LOW-003: 스타일시트 분리
4. [ ] LOW-004: 상수 파일 통합

---

## 참고 사항

### 분석 방법론
- Python/Qt (PySide6) 체크리스트 기반 분석
- 정적 코드 분석
- 잠재적 런타임 에러 시나리오 검토

### 추가 권장 사항
1. **단위 테스트 추가**: 핵심 변환 로직(`image_ops.py`)에 대한 테스트 필요
2. **로깅 시스템 도입**: 에러 추적을 위한 로깅 추가
3. **설정 검증**: 설정값 로드 시 스키마 검증 추가 고려
