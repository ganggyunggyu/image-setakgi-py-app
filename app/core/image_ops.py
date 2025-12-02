import math
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageEnhance
import cv2

def get_inscribed_rect_size(orig_w: int, orig_h: int, angle_deg: float) -> tuple[int, int]:
    """회전 후 빈 공간 없이 추출 가능한 최대 직사각형 크기 (원본 비율 유지)"""
    if angle_deg == 0:
        return orig_w, orig_h

    angle = math.radians(abs(angle_deg))
    cos_a = abs(math.cos(angle))
    sin_a = abs(math.sin(angle))

    # cos(2θ) = cos²θ - sin²θ
    cos_2a = cos_a * cos_a - sin_a * sin_a

    if abs(cos_2a) < 1e-10:
        # 45도 근처
        scale = 1 / math.sqrt(2)
        return int(orig_w * scale), int(orig_h * scale)

    # 원본 비율 유지 최대 내접 직사각형
    if orig_w * sin_a >= orig_h * cos_a:
        new_w = (orig_w * cos_a - orig_h * sin_a) / cos_2a
        new_h = new_w * orig_h / orig_w
    else:
        new_h = (orig_h * cos_a - orig_w * sin_a) / cos_2a
        new_w = new_h * orig_w / orig_h

    # 음수/너무 작은 값 방지 (큰 각도에서 발생)
    if new_w <= 10 or new_h <= 10:
        scale = cos_a
        return max(10, int(orig_w * scale)), max(10, int(orig_h * scale))

    return int(new_w), int(new_h)


def rotate_and_crop(img: Image.Image, angle: float) -> Image.Image:
    """회전 후 빈 공간 없이 중앙 크롭"""
    if angle == 0:
        return img.copy()

    orig_w, orig_h = img.size

    # 회전 (expand=True로 전체 이미지 보존)
    rotated = img.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)
    rot_w, rot_h = rotated.size

    # 내접 직사각형 크기 계산
    crop_w, crop_h = get_inscribed_rect_size(orig_w, orig_h, angle)

    # 중앙 크롭
    left = (rot_w - crop_w) // 2
    top = (rot_h - crop_h) // 2
    right = left + crop_w
    bottom = top + crop_h

    return rotated.crop((left, top, right, bottom))


def crop_edges(
    img: Image.Image,
    top: int = 0,
    bottom: int = 0,
    left: int = 0,
    right: int = 0,
) -> Image.Image:
    if top == 0 and bottom == 0 and left == 0 and right == 0:
        return img.copy()

    w, h = img.size

    # 음수 값이 있으면 패딩 추가
    if top < 0 or bottom < 0 or left < 0 or right < 0:
        pad_top = abs(min(0, top))
        pad_bottom = abs(min(0, bottom))
        pad_left = abs(min(0, left))
        pad_right = abs(min(0, right))

        new_w = w + pad_left + pad_right
        new_h = h + pad_top + pad_bottom

        # 짝수 크기 보정
        if new_w % 2 == 1:
            new_w += 1
            pad_right += 1
        if new_h % 2 == 1:
            new_h += 1
            pad_bottom += 1

        # 패딩은 흰색 배경 (JPEG 호환)
        if img.mode != "RGB":
            img = img.convert("RGB")

        new_img = Image.new("RGB", (new_w, new_h), (255, 255, 255))
        new_img.paste(img, (pad_left, pad_top))
        return new_img

    # 양수 값은 크롭
    new_left = min(left, w - 1)
    new_top = min(top, h - 1)
    new_right = max(new_left + 1, w - right)
    new_bottom = max(new_top + 1, h - bottom)

    out_w = new_right - new_left
    out_h = new_bottom - new_top

    if out_w % 2 == 1:
        new_right -= 1
    if out_h % 2 == 1:
        new_bottom -= 1

    new_right = max(new_left + 2, new_right)
    new_bottom = max(new_top + 2, new_bottom)

    return img.crop((new_left, new_top, new_right, new_bottom))


def resize_image(
    img: Image.Image,
    width: Optional[int] = None,
    height: Optional[int] = None,
    keep_ratio: bool = True,
) -> Image.Image:
    if width is None and height is None:
        return img.copy()

    orig_w, orig_h = img.size

    if keep_ratio:
        if width and height:
            ratio = min(width / orig_w, height / orig_h)
            new_w = int(orig_w * ratio)
            new_h = int(orig_h * ratio)
        elif width:
            ratio = width / orig_w
            new_w = width
            new_h = int(orig_h * ratio)
        else:
            ratio = height / orig_h
            new_w = int(orig_w * ratio)
            new_h = height
    else:
        new_w = width if width else orig_w
        new_h = height if height else orig_h

    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def rotate_image(img: Image.Image, angle: float, expand: bool = True) -> Image.Image:
    if angle == 0:
        return img.copy()
    return img.rotate(-angle, expand=expand, resample=Image.Resampling.BICUBIC)


def adjust_brightness(img: Image.Image, factor: int) -> Image.Image:
    if factor == 0:
        return img.copy()
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(1 + factor / 100)


def adjust_contrast(img: Image.Image, factor: int) -> Image.Image:
    if factor == 0:
        return img.copy()
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(1 + factor / 100)


def adjust_saturation(img: Image.Image, factor: int) -> Image.Image:
    if factor == 0:
        return img.copy()
    enhancer = ImageEnhance.Color(img)
    return enhancer.enhance(1 + factor / 100)


def add_noise(img: Image.Image, intensity: float) -> Image.Image:
    if intensity == 0:
        return img.copy()

    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, intensity, arr.shape)
    noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy)


def apply_transforms(
    img: Image.Image,
    rotation: float = 0.0,
    brightness: int = 0,
    contrast: int = 0,
    saturation: int = 0,
    noise: float = 0,
    perspective_corners: Optional[List[Tuple[float, float]]] = None,
    crop: Optional[dict] = None,
) -> Image.Image:
    """이미지 변환 적용

    노이즈는 저장 시점(crop_background 후)에 적용됨
    → noise 값은 result.info["noise"]에 저장
    """
    result = img.copy()
    orig_size = None

    if result.mode not in ("RGB", "RGBA"):
        result = result.convert("RGB")

    if crop:
        result = crop_edges(
            result,
            top=crop.get("top", 0),
            bottom=crop.get("bottom", 0),
            left=crop.get("left", 0),
            right=crop.get("right", 0),
        )

    if perspective_corners and len(perspective_corners) == 4:
        result = perspective_transform(result, perspective_corners)

    if rotation != 0:
        result = rotate_and_crop(result, rotation)
        result.info["rotation"] = rotation  # 저장 시 내접 크롭용

    if brightness != 0:
        result = adjust_brightness(result, brightness)

    if contrast != 0:
        result = adjust_contrast(result, contrast)

    if saturation != 0:
        result = adjust_saturation(result, saturation)

    # 노이즈는 crop_background 후에 적용하기 위해 info에 저장
    if noise > 0:
        result.info["noise"] = noise

    if orig_size:
        result.info["orig_size"] = orig_size

    return result


def find_perspective_coeffs(
    source_coords: List[Tuple[float, float]],
    target_coords: List[Tuple[float, float]]
) -> Optional[Tuple]:
    """원근 변환 계수 계산. 특이 행렬이면 None 반환."""
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


def perspective_transform(
    img: Image.Image,
    corners: List[Tuple[float, float]]
) -> Image.Image:
    """원근 변형 후 빈 공간 없이 중앙 크롭"""
    if len(corners) != 4:
        return img.copy()

    orig_w, orig_h = img.size

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    img_rgba = img.convert("RGBA")

    source_corners = [
        (0, 0),
        (orig_w, 0),
        (orig_w, orig_h),
        (0, orig_h)
    ]

    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    output_w = int(max_x - min_x)
    output_h = int(max_y - min_y)

    if output_w <= 0 or output_h <= 0:
        return img.copy()

    adjusted_corners = [(x - min_x, y - min_y) for x, y in corners]

    coeffs = find_perspective_coeffs(source_corners, adjusted_corners)
    if coeffs is None:
        return img.copy()

    result = img_rgba.transform(
        (output_w, output_h),
        Image.Transform.PERSPECTIVE,
        coeffs,
        Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0, 0)
    )

    # 투명 영역 크롭은 저장 시점에서 처리 (crop_transparent)
    # orig_size 저장 안 함 - 내접 직사각형 크롭이 크기 조절함

    return result


def _detect_bg_color(
    np_img: np.ndarray, sample_size: int = 10, white_thresh: int = 200
) -> str:
    """모서리 샘플링으로 배경색 자동 감지 (white/black)"""
    try:
        import cv2
    except ImportError:
        return "black"

    h, w = np_img.shape[:2]
    s = min(sample_size, h // 2, w // 2)

    corners = [
        np_img[0:s, 0:s],
        np_img[0:s, w - s : w],
        np_img[h - s : h, 0:s],
        np_img[h - s : h, w - s : w],
    ]

    means = []
    for c in corners:
        if c.size == 0:
            continue
        gray = cv2.cvtColor(c, cv2.COLOR_RGB2GRAY) if c.ndim == 3 else c
        means.append(float(gray.mean()))

    if not means:
        return "black"

    avg = float(np.mean(means))
    return "white" if avg >= white_thresh else "black"


def crop_background(
    img: Image.Image,
    threshold: int = 12,
    padding: int = 0,
    min_area: int = 1000,
    morph_kernel: tuple[int, int] = (5, 5),
) -> Image.Image:
    """배경 크롭 (검정/흰색 자동 감지)

    - threshold: 밝기 기준값 (작을수록 더 어두운 픽셀을 전경으로 판단)
    - padding: 크롭 결과에 추가로 남길 픽셀 수
    - min_area: 전경 영역이 이보다 작으면 크롭하지 않음
    - morph_kernel: 노이즈 제거용 모폴로지 커널 크기
    """

    np_img = np.array(img.convert("RGB"))
    h, w = np_img.shape[:2]

    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    bg_color = _detect_bg_color(np_img)

    if bg_color == "white":
        _, fg = cv2.threshold(gray, 255 - threshold, 255, cv2.THRESH_BINARY_INV)
    else:
        _, fg = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

    # 노이즈 제거
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, morph_kernel)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel, iterations=2)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img

    # 병합 바운딩박스 계산
    x_min, y_min, x_max, y_max = w, h, 0, 0
    total_area = 0

    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        total_area += cw * ch
        x_min = min(x_min, x)
        y_min = min(y_min, y)
        x_max = max(x_max, x + cw)
        y_max = max(y_max, y + ch)

    if total_area < min_area:
        return img

    # padding 적용 및 경계 보정
    x_min = max(0, int(x_min - padding))
    y_min = max(0, int(y_min - padding))
    x_max = min(w, int(x_max + padding))
    y_max = min(h, int(y_max + padding))

    if x_min == 0 and y_min == 0 and x_max == w and y_max == h:
        return img

    return img.crop((x_min, y_min, x_max, y_max))


def crop_transparent(img: Image.Image, min_alpha: int = 10) -> Image.Image:
    """RGBA 이미지에서 투명 영역을 제거하는 내접 직사각형 크롭

    perspective_transform 후 빈 공간(alpha=0) 제거용
    - 최대 면적 직사각형 찾기 (샘플링으로 O(n) 최적화)
    """
    if img.mode != "RGBA":
        return img

    alpha = np.array(img.split()[3])
    h, w = alpha.shape
    opaque = alpha >= min_alpha

    # 각 행에서 불투명 픽셀의 시작/끝 위치 찾기
    row_left = np.full(h, w, dtype=np.int32)
    row_right = np.zeros(h, dtype=np.int32)

    for y in range(h):
        cols = np.where(opaque[y, :])[0]
        if len(cols) > 0:
            row_left[y] = cols[0]
            row_right[y] = cols[-1] + 1

    # 유효한 행만 사용
    valid_mask = row_right > row_left
    if not np.any(valid_mask):
        return img

    valid_indices = np.where(valid_mask)[0]
    if len(valid_indices) == 0:
        return img

    # 샘플링할 행 선택 (최대 200개)
    n_samples = min(200, len(valid_indices))
    sample_step = max(1, len(valid_indices) // n_samples)
    sampled_rows = valid_indices[::sample_step]

    best_area = 0
    best_rect = (0, 0, w, h)

    for top_row in sampled_rows:
        left_max = row_left[top_row]
        right_min = row_right[top_row]

        for bottom_row in range(top_row, valid_indices[-1] + 1, sample_step):
            if row_right[bottom_row] <= row_left[bottom_row]:
                continue

            left_max = max(left_max, row_left[bottom_row])
            right_min = min(right_min, row_right[bottom_row])

            if left_max >= right_min:
                break

            width = right_min - left_max
            height = bottom_row - top_row + 1
            area = width * height

            if area > best_area:
                best_area = area
                best_rect = (int(left_max), top_row, int(right_min), bottom_row + 1)

    left, top, right, bottom = best_rect

    if left >= right or top >= bottom or best_area == 0:
        bbox = img.split()[3].point(lambda p: 255 if p >= min_alpha else 0).getbbox()
        if bbox:
            return img.crop(bbox)
        return img

    if left == 0 and top == 0 and right == w and bottom == h:
        return img

    return img.crop((left, top, right, bottom))


def get_image_info(filepath: str) -> dict:
    try:
        with Image.open(filepath) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
            }
    except Exception as e:
        return {"error": str(e)}
