from pathlib import Path
from datetime import datetime
from PIL import Image
from typing import Optional

from .metadata import save_with_exif, remove_exif, create_exif_bytes


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
    stem = Path(original_name).stem
    suffix = Path(original_name).suffix.lower()

    if suffix not in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        suffix = ".jpg"

    base_name = f"{stem}_mod"
    candidate = output_dir / f"{base_name}{suffix}"

    counter = 1
    while candidate.exists():
        candidate = output_dir / f"{base_name}_{counter}{suffix}"
        counter += 1

    return candidate


def save_transformed_image(
    img: Image.Image,
    output_dir: Path,
    original_name: str,
    exif_bytes: Optional[bytes] = None,
    quality: int = 95,
) -> Path:
    # RGBA 이미지는 투명도 보존을 위해 PNG로 저장
    if img.mode == "RGBA":
        stem = Path(original_name).stem
        original_name = f"{stem}.png"

    output_path = get_unique_filename(output_dir, original_name)

    # PNG는 EXIF를 지원하지 않으므로 JPEG만 EXIF 저장
    if exif_bytes and output_path.suffix.lower() in [".jpg", ".jpeg"]:
        save_with_exif(img, str(output_path), exif_bytes, quality)
    else:
        img.save(str(output_path), quality=quality)

    return output_path


class OutputManager:
    def __init__(self, base_dir: str, options: dict = None):
        self.output_dir = create_output_folder(base_dir, options)
        self.saved_files: list[Path] = []

    def save(
        self,
        img: Image.Image,
        original_name: str,
        exif_bytes: Optional[bytes] = None,
        quality: int = 95,
    ) -> Path:
        path = save_transformed_image(
            img, self.output_dir, original_name, exif_bytes, quality
        )
        self.saved_files.append(path)
        return path

    def get_saved_count(self) -> int:
        return len(self.saved_files)

    def get_output_dir(self) -> Path:
        return self.output_dir
