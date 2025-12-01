import piexif
from PIL import Image
from typing import Optional
from datetime import datetime
import random
import os
import platform


# Windows 속성 "자세히" 탭 매핑:
# - JPG: Windows 'Date taken' = EXIF DateTimeOriginal
# - PNG: Windows 'Date taken' = PNG tEXt chunk 'Creation Time'
# - NTFS '만든 날짜/수정한 날짜' = 파일 시스템 타임스탬프 (set_file_times로 변경 가능)
#
# 날짜 포맷: "YYYY:MM:DD HH:MM:SS" (예: "2025:11:27 14:30:00")

READABLE_TAGS = {
    # 0th IFD (ImageIFD) - 기본 이미지 정보
    "DateTime": (piexif.ImageIFD.DateTime, "0th"),  # 파일 수정 시간
    "Make": (piexif.ImageIFD.Make, "0th"),  # → Windows "카메라 제조업체"
    "Model": (piexif.ImageIFD.Model, "0th"),  # → Windows "카메라 모델"
    "Software": (piexif.ImageIFD.Software, "0th"),  # → Windows "프로그램 이름"
    "Artist": (piexif.ImageIFD.Artist, "0th"),  # → Windows "작성자"
    "Copyright": (piexif.ImageIFD.Copyright, "0th"),  # → Windows "저작권"
    "ImageDescription": (piexif.ImageIFD.ImageDescription, "0th"),  # → Windows "제목"
    # Exif IFD - 촬영 정보
    "DateTimeOriginal": (piexif.ExifIFD.DateTimeOriginal, "Exif"),  # → Windows "촬영 날짜" ⭐
    "DateTimeDigitized": (piexif.ExifIFD.DateTimeDigitized, "Exif"),  # 디지털화 시간
    "ExposureTime": (piexif.ExifIFD.ExposureTime, "Exif"),
    "FNumber": (piexif.ExifIFD.FNumber, "Exif"),
    "ISOSpeedRatings": (piexif.ExifIFD.ISOSpeedRatings, "Exif"),
    "FocalLength": (piexif.ExifIFD.FocalLength, "Exif"),
}


def read_exif(filepath: str) -> dict:
    try:
        with Image.open(filepath) as img:
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
                        except (UnicodeDecodeError, AttributeError):
                            value = str(value)
                    result[name] = value

            return result
    except (OSError, IOError) as e:
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


def save_jpeg_with_metadata(
    img: Image.Image,
    output_path: str,
    metadata_overrides: Optional[dict] = None,
    quality: int = 75,
):
    """JPEG 파일을 EXIF 메타데이터와 함께 저장

    Windows 탐색기 "촬영 날짜" = EXIF DateTimeOriginal
    quality=75: 파일 크기 최소화 (원본 대비 25~40%)
    """
    # RGBA → RGB 변환 (JPEG는 투명도 지원 안 함)
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if metadata_overrides is not None and len(metadata_overrides) > 0:
        exif_bytes = create_exif_bytes(metadata_overrides)
        img.save(output_path, quality=quality, optimize=True, exif=exif_bytes)

        dt_str = metadata_overrides.get("DateTimeOriginal") or metadata_overrides.get("datetime", "")
        if dt_str:
            set_file_times(output_path, dt_str)
    else:
        img.save(output_path, quality=quality, optimize=True)


def save_webp_with_metadata(
    img: Image.Image,
    output_path: str,
    metadata_overrides: Optional[dict] = None,
    quality: int = 80,
):
    """WebP 파일을 메타데이터와 함께 저장

    WebP는 EXIF를 지원하지만 Windows 탐색기에서 "촬영 날짜"로 표시되지 않음.
    대신 파일 시스템 타임스탬프(만든 날짜/수정한 날짜)를 변경하여 대응.
    quality=80: 손실 압축 (JPEG 대비 더 작은 파일 크기)
    """
    # WebP는 RGBA를 직접 지원하므로 RGB 변환 불필요
    # 단, 모드가 지원되지 않는 경우만 변환
    if img.mode not in ("RGB", "RGBA", "L", "LA"):
        img = img.convert("RGBA") if "A" in img.mode else img.convert("RGB")

    save_kwargs = {
        "quality": quality,
        "method": 4,  # 압축 품질 (0-6, 높을수록 느리지만 작은 파일)
    }

    if metadata_overrides is not None and len(metadata_overrides) > 0:
        # WebP도 EXIF 지원 (Pillow 9.2+)
        try:
            exif_bytes = create_exif_bytes(metadata_overrides)
            save_kwargs["exif"] = exif_bytes
        except Exception:
            pass  # EXIF 실패해도 저장은 계속

        img.save(output_path, "WEBP", **save_kwargs)

        # 파일 시스템 타임스탬프 변경 (Windows 탐색기 날짜 표시용)
        dt_str = metadata_overrides.get("DateTimeOriginal") or metadata_overrides.get("datetime", "")
        if dt_str:
            set_file_times(output_path, dt_str)
    else:
        img.save(output_path, "WEBP", **save_kwargs)


def set_file_times(filepath: str, datetime_str: str):
    """파일의 만든 날짜/수정한 날짜를 변경

    - Windows: 만든 날짜 + 수정한 날짜 모두 변경
    - macOS/Linux: 수정한 날짜만 변경 (만든 날짜는 OS 제한)
    """
    try:
        # EXIF 형식 파싱
        dt = datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
        timestamp = dt.timestamp()

        # 수정 날짜 변경 (모든 플랫폼)
        os.utime(filepath, (timestamp, timestamp))

        # Windows: 만든 날짜도 변경
        if platform.system() == "Windows":
            _set_windows_file_times(filepath, timestamp)

    except ValueError:
        pass  # 날짜 파싱 실패


def _set_windows_file_times(filepath: str, timestamp: float):
    """Windows 전용: 만든 날짜/수정한 날짜/접근한 날짜 모두 변경"""
    try:
        import ctypes
        from ctypes import wintypes

        # FILETIME 구조체
        class FILETIME(ctypes.Structure):
            _fields_ = [("dwLowDateTime", wintypes.DWORD),
                        ("dwHighDateTime", wintypes.DWORD)]

        # Windows API 상수
        GENERIC_WRITE = 0x40000000
        FILE_SHARE_READ = 0x1
        FILE_SHARE_WRITE = 0x2
        OPEN_EXISTING = 3
        FILE_ATTRIBUTE_NORMAL = 0x80
        INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

        kernel32 = ctypes.windll.kernel32

        # CreateFileW 반환 타입 설정
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
        ]

        # 파일 핸들 열기
        handle = kernel32.CreateFileW(
            filepath,
            GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            None
        )

        if handle == INVALID_HANDLE_VALUE:
            return

        try:
            # Python timestamp → Windows FILETIME 변환
            # Windows epoch: 1601-01-01, Unix epoch: 1970-01-01
            EPOCH_DIFF = 116444736000000000  # 100ns intervals
            ft_value = int((timestamp * 10000000) + EPOCH_DIFF)

            filetime = FILETIME()
            filetime.dwLowDateTime = ft_value & 0xFFFFFFFF
            filetime.dwHighDateTime = (ft_value >> 32) & 0xFFFFFFFF

            # SetFileTime 타입 설정
            kernel32.SetFileTime.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(FILETIME),
                ctypes.POINTER(FILETIME),
                ctypes.POINTER(FILETIME)
            ]
            kernel32.SetFileTime.restype = wintypes.BOOL

            # 만든 날짜, 접근 날짜, 수정 날짜 모두 설정
            kernel32.SetFileTime(
                handle,
                ctypes.byref(filetime),  # 만든 날짜
                ctypes.byref(filetime),  # 접근 날짜
                ctypes.byref(filetime)   # 수정 날짜
            )
        finally:
            kernel32.CloseHandle(handle)

    except Exception:
        pass  # Windows API 실패해도 os.utime은 이미 성공
