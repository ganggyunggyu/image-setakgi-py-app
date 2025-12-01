import numpy as np
import math
from PIL import Image, ImageEnhance, ImageFilter
from typing import Optional, List, Tuple
import io


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
    result = img.copy()
    orig_size = None  # perspective_transform용 원본 크기

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
        orig_size = result.info.get("orig_size")

    if rotation != 0:
        result = rotate_and_crop(result, rotation)

    if brightness != 0:
        result = adjust_brightness(result, brightness)

    if contrast != 0:
        result = adjust_contrast(result, contrast)

    if saturation != 0:
        result = adjust_saturation(result, saturation)

    if noise > 0:
        result = add_noise(result, noise)

    # perspective_transform 원본 크기 복원 (다른 변환에서 info 사라짐)
    if orig_size:
        result.info["orig_size"] = orig_size

    return result


def find_perspective_coeffs(
    source_coords: List[Tuple[float, float]],
    target_coords: List[Tuple[float, float]]
) -> Tuple:
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])

    A = np.matrix(matrix, dtype=np.float32)
    B = np.array(source_coords).reshape(8)

    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return tuple(np.array(res).reshape(8))


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

    result = img_rgba.transform(
        (output_w, output_h),
        Image.Transform.PERSPECTIVE,
        coeffs,
        Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0, 0)
    )

    bbox = result.split()[-1].getbbox()

    if bbox:
        result = result.crop(bbox)

    # 원본 크기 정보를 info에 저장 (저장 시 포맷별 처리용)
    result.info["orig_size"] = (orig_w, orig_h)

    return result


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
