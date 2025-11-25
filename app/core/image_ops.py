import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Optional
import io


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
) -> Image.Image:
    result = img.copy()

    if img.mode == "RGBA":
        result = result.convert("RGB")

    if width or height:
        result = resize_image(result, width, height, keep_ratio)

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
