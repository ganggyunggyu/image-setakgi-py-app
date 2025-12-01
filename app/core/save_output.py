from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from .metadata import save_jpeg_with_metadata, save_webp_with_metadata


def create_output_folder(base_dir: str, options: dict = None) -> Path:
    parts = []

    if options:
        if options.get("random"):
            parts.append("랜덤변환")
        else:
            crop = options.get("crop", {})
            crop_val = crop.get("top", 0)
            if crop_val != 0:
                parts.append(f"크롭{crop_val}")

            rotation = options.get("rotation", 0)
            if rotation != 0:
                parts.append(f"회전{rotation}")

            brightness = options.get("brightness", 0)
            if brightness != 0:
                parts.append(f"밝기{brightness}")

            contrast = options.get("contrast", 0)
            if contrast != 0:
                parts.append(f"대비{contrast}")

            saturation = options.get("saturation", 0)
            if saturation != 0:
                parts.append(f"채도{saturation}")

            noise = options.get("noise", 0)
            if noise != 0:
                parts.append(f"노이즈{noise}")

    if not parts:
        parts.append("output")

    folder_name = "_".join(parts)
    output_dir = Path(base_dir) / folder_name

    if output_dir.exists():
        counter = 1
        while (Path(base_dir) / f"{folder_name}_{counter}").exists():
            counter += 1
        output_dir = Path(base_dir) / f"{folder_name}_{counter}"

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_unique_filename(output_dir: Path, original_name: str, output_format: str = "jpeg") -> Path:
    """포맷에 맞는 파일명 생성"""
    stem = Path(original_name).stem
    ext = ".webp" if output_format == "webp" else ".jpg"
    candidate = output_dir / f"{stem}{ext}"

    counter = 1
    while candidate.exists():
        candidate = output_dir / f"{stem}_{counter}{ext}"
        counter += 1

    return candidate


def save_transformed_image(
    img: Image.Image,
    output_dir: Path,
    original_name: str,
    metadata_overrides: Optional[dict] = None,
    output_format: str = "jpeg",
) -> Path:
    """이미지 저장 - 포맷별 메타데이터 처리"""
    output_path = get_unique_filename(output_dir, original_name, output_format)

    # JPG에서는 자유변형/랜덤변형으로 생긴 흰색 배경을 제거하기 위해
    # 완전 흰색(255,255,255)만 남은 가장자리를 자동 크롭
    if output_format == "jpeg":
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        data = np.array(img)
        # 내용 픽셀 = 알파 있음(투명 아님) AND 순백색 아님
        non_bg_mask = (
            (data[..., 3] != 0)
            & (
                (data[..., 0] != 255)
                | (data[..., 1] != 255)
                | (data[..., 2] != 255)
            )
        )

        if non_bg_mask.any():
            ys, xs = np.nonzero(non_bg_mask)
            top, bottom = ys.min(), ys.max()
            left, right = xs.min(), xs.max()
            img = img.crop((left, top, right + 1, bottom + 1))

    if output_format == "webp":
        save_webp_with_metadata(img, str(output_path), metadata_overrides)
    else:
        save_jpeg_with_metadata(img, str(output_path), metadata_overrides)

    return output_path


class OutputManager:
    def __init__(self, base_dir: str, options: dict = None):
        self.output_dir = create_output_folder(base_dir, options)
        self.output_format = options.get("output_format", "jpeg") if options else "jpeg"
        self.saved_files: list[Path] = []

    def save(
        self,
        img: Image.Image,
        original_name: str,
        metadata_overrides: Optional[dict] = None,
    ) -> Path:
        """이미지 저장 - 설정된 포맷으로 저장"""
        path = save_transformed_image(
            img, self.output_dir, original_name, metadata_overrides, self.output_format
        )
        self.saved_files.append(path)
        return path

    def get_saved_count(self) -> int:
        return len(self.saved_files)

    def get_output_dir(self) -> Path:
        return self.output_dir
