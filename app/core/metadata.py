import piexif
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from typing import Optional
from datetime import datetime
import random


READABLE_TAGS = {
    "DateTime": (piexif.ExifIFD.DateTimeOriginal, "0th"),
    "Make": (piexif.ImageIFD.Make, "0th"),
    "Model": (piexif.ImageIFD.Model, "0th"),
    "Software": (piexif.ImageIFD.Software, "0th"),
    "Artist": (piexif.ImageIFD.Artist, "0th"),
    "Copyright": (piexif.ImageIFD.Copyright, "0th"),
    "ImageDescription": (piexif.ImageIFD.ImageDescription, "0th"),
    "DateTimeOriginal": (piexif.ExifIFD.DateTimeOriginal, "Exif"),
    "DateTimeDigitized": (piexif.ExifIFD.DateTimeDigitized, "Exif"),
    "ExposureTime": (piexif.ExifIFD.ExposureTime, "Exif"),
    "FNumber": (piexif.ExifIFD.FNumber, "Exif"),
    "ISOSpeedRatings": (piexif.ExifIFD.ISOSpeedRatings, "Exif"),
    "FocalLength": (piexif.ExifIFD.FocalLength, "Exif"),
}


def read_exif(filepath: str) -> dict:
    try:
        img = Image.open(filepath)
        if "exif" not in img.info:
            return {"_raw": None, "_error": None}

        exif_dict = piexif.load(img.info["exif"])
        result = {"_raw": exif_dict}

        for name, (tag_id, ifd) in READABLE_TAGS.items():
            ifd_data = exif_dict.get(ifd, {})
            if tag_id in ifd_data:
                value = ifd_data[tag_id]
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8", errors="ignore").strip("\x00")
                    except:
                        value = str(value)
                result[name] = value

        return result
    except Exception as e:
        return {"_raw": None, "_error": str(e)}


def remove_exif(img: Image.Image) -> Image.Image:
    data = list(img.getdata())
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(data)
    return clean_img


def create_exif_bytes(overrides: dict) -> bytes:
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    for name, value in overrides.items():
        if name.startswith("_"):
            continue
        if name in READABLE_TAGS:
            tag_id, ifd = READABLE_TAGS[name]
            if isinstance(value, str):
                value = value.encode("utf-8")
            if ifd == "0th":
                exif_dict["0th"][tag_id] = value
            elif ifd == "Exif":
                exif_dict["Exif"][tag_id] = value

    return piexif.dump(exif_dict)


def apply_exif_overrides(img: Image.Image, overrides: dict) -> Image.Image:
    clean = remove_exif(img)
    if not overrides:
        return clean

    exif_bytes = create_exif_bytes(overrides)
    clean.info["exif"] = exif_bytes
    return clean


def generate_random_exif() -> dict:
    cameras = [
        ("Canon", "EOS 5D Mark IV"),
        ("Nikon", "D850"),
        ("Sony", "A7R IV"),
        ("Fujifilm", "X-T4"),
        ("Panasonic", "GH5"),
    ]
    make, model = random.choice(cameras)

    year = random.randint(2018, 2024)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    dt_str = f"{year}:{month:02d}:{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

    return {
        "Make": make,
        "Model": model,
        "DateTimeOriginal": dt_str,
        "Software": "Adobe Photoshop CC 2024",
    }


def save_with_exif(
    img: Image.Image,
    output_path: str,
    exif_bytes: Optional[bytes] = None,
    quality: int = 95,
):
    if exif_bytes:
        img.save(output_path, quality=quality, exif=exif_bytes)
    else:
        img.save(output_path, quality=quality)


def create_png_metadata(overrides: dict) -> PngInfo:
    """PNG용 tEXt 청크 메타데이터 생성"""
    metadata = PngInfo()

    # Windows가 인식하는 PNG 메타데이터 키
    # Creation Time: Windows "Date taken" 에 표시됨
    if "DateTimeOriginal" in overrides or "datetime" in overrides:
        dt_str = overrides.get("DateTimeOriginal") or overrides.get("datetime", "")
        if dt_str:
            # EXIF 형식(2024:01:01 12:00:00)을 ISO 형식으로 변환
            try:
                dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                # Windows PNG Creation Time 형식
                metadata.add_text("Creation Time", dt.strftime("%Y-%m-%dT%H:%M:%S"))
            except ValueError:
                metadata.add_text("Creation Time", dt_str)

    if "Make" in overrides or "make" in overrides:
        make = overrides.get("Make") or overrides.get("make", "")
        if make:
            metadata.add_text("Source", make)

    if "Model" in overrides or "model" in overrides:
        model = overrides.get("Model") or overrides.get("model", "")
        if model:
            metadata.add_text("Comment", model)

    if "Software" in overrides:
        metadata.add_text("Software", overrides["Software"])

    return metadata


def save_png_with_metadata(
    img: Image.Image,
    output_path: str,
    metadata_overrides: Optional[dict] = None,
):
    """PNG 파일을 메타데이터와 함께 저장"""
    if metadata_overrides:
        png_info = create_png_metadata(metadata_overrides)
        img.save(output_path, pnginfo=png_info)
    else:
        img.save(output_path)
