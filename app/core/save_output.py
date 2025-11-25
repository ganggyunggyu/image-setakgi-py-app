from pathlib import Path
from datetime import datetime
from PIL import Image
from typing import Optional

from .metadata import save_with_exif, remove_exif, create_exif_bytes


def create_output_folder(base_dir: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(base_dir) / f"output_{timestamp}"
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
    output_path = get_unique_filename(output_dir, original_name)

    if img.mode == "RGBA" and output_path.suffix.lower() in [".jpg", ".jpeg"]:
        img = img.convert("RGB")

    if exif_bytes and output_path.suffix.lower() in [".jpg", ".jpeg"]:
        save_with_exif(img, str(output_path), exif_bytes, quality)
    else:
        img.save(str(output_path), quality=quality)

    return output_path


class OutputManager:
    def __init__(self, base_dir: str):
        self.output_dir = create_output_folder(base_dir)
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
