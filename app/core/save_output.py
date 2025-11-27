from pathlib import Path
from PIL import Image
from typing import Optional

from .metadata import save_jpeg_with_metadata


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


def get_unique_filename(output_dir: Path, original_name: str) -> Path:
    """JPEG로 저장 - 원본 파일명 유지"""
    stem = Path(original_name).stem
    candidate = output_dir / f"{stem}.jpg"

    counter = 1
    while candidate.exists():
        candidate = output_dir / f"{stem}_{counter}.jpg"
        counter += 1

    return candidate


def save_transformed_image(
    img: Image.Image,
    output_dir: Path,
    original_name: str,
    metadata_overrides: Optional[dict] = None,
) -> Path:
    """JPEG 저장 - EXIF DateTimeOriginal 메타데이터 포함"""
    output_path = get_unique_filename(output_dir, original_name)
    save_jpeg_with_metadata(img, str(output_path), metadata_overrides)
    return output_path


class OutputManager:
    def __init__(self, base_dir: str, options: dict = None):
        self.output_dir = create_output_folder(base_dir, options)
        self.saved_files: list[Path] = []

    def save(
        self,
        img: Image.Image,
        original_name: str,
        metadata_overrides: Optional[dict] = None,
    ) -> Path:
        """JPEG로 저장 - metadata_overrides에 DateTimeOriginal 키로 날짜 전달"""
        path = save_transformed_image(
            img, self.output_dir, original_name, metadata_overrides
        )
        self.saved_files.append(path)
        return path

    def get_saved_count(self) -> int:
        return len(self.saved_files)

    def get_output_dir(self) -> Path:
        return self.output_dir
