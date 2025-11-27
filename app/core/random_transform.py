"""랜덤 변형 값 생성기"""
import random
from datetime import datetime, timedelta
from typing import Optional

from .random_config import (
    CROP_RANGE,
    ROTATION_RANGE,
    NOISE_RANGE,
    PERSPECTIVE_RANGE,
    DATE_DAYS_BACK,
)


def generate_random_crop(max_range: float = CROP_RANGE) -> int:
    """±max_range 범위 내에서 랜덤 크롭 값 생성 (정수)"""
    return round(random.uniform(-max_range, max_range))


def generate_random_rotation(max_range: float = ROTATION_RANGE) -> float:
    """±max_range 범위 내에서 랜덤 회전 값 생성 (소수점 1자리)"""
    return round(random.uniform(-max_range, max_range), 1)


def generate_random_noise(max_range: float = NOISE_RANGE) -> int:
    """0~max_range 범위 내에서 랜덤 노이즈 값 생성"""
    return round(random.uniform(0, max_range))


def generate_random_perspective(
    width: int, height: int, max_offset: float = PERSPECTIVE_RANGE
) -> list[tuple[float, float]]:
    """자유변형 코너에 ±max_offset 범위의 랜덤 오프셋 적용 (소수점 1자리)"""
    base_corners = [
        (0, 0),
        (width, 0),
        (width, height),
        (0, height),
    ]
    return [
        (
            round(x + random.uniform(-max_offset, max_offset), 1),
            round(y + random.uniform(-max_offset, max_offset), 1),
        )
        for x, y in base_corners
    ]


def generate_random_datetime(days_back: int = DATE_DAYS_BACK) -> str:
    """오늘 기준 days_back일 전까지의 랜덤 날짜 생성"""
    now = datetime.now()
    random_days = random.uniform(0, days_back)
    random_date = now - timedelta(days=random_days)
    return random_date.strftime("%Y:%m:%d %H:%M:%S")


class RandomTransformConfig:
    """랜덤 변형 설정 - random_config.py에서 값 조절 가능"""

    def __init__(
        self,
        crop_range: float = CROP_RANGE,
        rotation_range: float = ROTATION_RANGE,
        noise_range: float = NOISE_RANGE,
        perspective_range: float = PERSPECTIVE_RANGE,
        date_days_back: int = DATE_DAYS_BACK,
    ):
        self.crop_range = crop_range
        self.rotation_range = rotation_range
        self.noise_range = noise_range
        self.perspective_range = perspective_range
        self.date_days_back = date_days_back


def generate_random_options(
    config: RandomTransformConfig,
    image_width: int,
    image_height: int,
    include_perspective: bool = True,
    include_date: bool = True,
) -> dict:
    """이미지별 랜덤 변형 옵션 생성"""
    crop_val = generate_random_crop(config.crop_range)
    rotation = generate_random_rotation(config.rotation_range)
    noise = generate_random_noise(config.noise_range)

    options = {
        "crop": {
            "top": crop_val,
            "bottom": crop_val,
            "left": crop_val,
            "right": crop_val,
        },
        "rotation": rotation,
        "noise": noise,
        "brightness": 0,
        "contrast": 0,
        "saturation": 0,
    }

    if include_perspective:
        options["perspective_corners"] = generate_random_perspective(
            image_width, image_height, config.perspective_range
        )

    if include_date:
        options["exif"] = {
            "remove_all": False,
            "override": True,
            "make": "",
            "model": "",
            "datetime": generate_random_datetime(config.date_days_back),
        }

    return options


def format_random_log(filename: str, options: dict) -> str:
    """랜덤 변형 로그 포맷"""
    crop = options.get("crop", {}).get("top", 0)
    rotation = options.get("rotation", 0)
    noise = options.get("noise", 0)

    parts = [f"[{filename}]"]
    parts.append(f"크롭:{crop:+d}px")
    parts.append(f"회전:{rotation:+.1f}°")
    parts.append(f"노이즈:{noise}")

    perspective = options.get("perspective_corners")
    if perspective:
        offsets = []
        for i, (x, y) in enumerate(perspective):
            offsets.append(f"({x:.1f},{y:.1f})")
        parts.append(f"자유변형:{','.join(offsets)}")

    exif = options.get("exif", {})
    if exif.get("override") and exif.get("datetime"):
        parts.append(f"날짜:{exif['datetime']}")

    return " | ".join(parts)
