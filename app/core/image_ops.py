import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Optional, List, Tuple
import io


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
    new_left = min(left, w - 1)
    new_top = min(top, h - 1)
    new_right = max(new_left + 1, w - right)
    new_bottom = max(new_top + 1, h - bottom)

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


def add_noise(img: Image.Image, intensity: int) -> Image.Image:
    if intensity == 0:
        return img.copy()

    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, intensity, arr.shape)
    noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy)


def apply_transforms(
    img: Image.Image,
    width: Optional[int] = None,
    height: Optional[int] = None,
    keep_ratio: bool = True,
    rotation: float = 0.0,
    brightness: int = 0,
    contrast: int = 0,
    saturation: int = 0,
    noise: int = 0,
    perspective_corners: Optional[List[Tuple[float, float]]] = None,
    crop: Optional[dict] = None,
) -> Image.Image:
    result = img.copy()

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
        result = rotate_image(result, rotation)

    if brightness != 0:
        result = adjust_brightness(result, brightness)

    if contrast != 0:
        result = adjust_contrast(result, contrast)

    if saturation != 0:
        result = adjust_saturation(result, saturation)

    if noise > 0:
        result = add_noise(result, noise)

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
    if len(corners) != 4:
        return img.copy()

    orig_w, orig_h = img.size

    # 원근 변형은 항상 RGBA로 처리 (투명 배경 보존)
    if img.mode != "RGBA":
        img = img.convert("RGBA")

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

    result = img.transform(
        (output_w, output_h),
        Image.Transform.PERSPECTIVE,
        coeffs,
        Image.Resampling.BICUBIC,
        fillcolor=(255, 255, 255, 0)
    )

    # 원근 변형 결과는 항상 RGBA로 반환 (PNG로 저장하여 투명도 보존)
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
