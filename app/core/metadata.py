import piexif
from PIL import Image
from PIL.PngImagePlugin import PngInfo
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
    """PNG용 tEXt 청크 메타데이터 생성

    Windows 탐색기는 PNG의 대부분 메타데이터를 무시하고,
    오직 'Creation Time' 텍스트 청크만 읽어서 "촬영 날짜(Date taken)"에 표시함.
    Make/Model/Software는 PNG에 넣어도 Windows에서 안 보임 (ExifTool 등에서는 보임)
    """
    metadata = PngInfo()

    # Windows "촬영 날짜(Date taken)" = PNG:CreationTime
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
    # None이 아니고 빈 딕셔너리가 아닐 때만 메타데이터 적용
    if metadata_overrides is not None and len(metadata_overrides) > 0:
        png_info = create_png_metadata(metadata_overrides)
        img.save(output_path, pnginfo=png_info)

        # 파일 시스템 타임스탬프도 변경
        dt_str = metadata_overrides.get("DateTimeOriginal") or metadata_overrides.get("datetime", "")
        if dt_str:
            set_file_times(output_path, dt_str)
    else:
        img.save(output_path)


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
        # 흰색 배경으로 합성
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if metadata_overrides is not None and len(metadata_overrides) > 0:
        exif_bytes = create_exif_bytes(metadata_overrides)
        img.save(output_path, quality=quality, optimize=True, exif=exif_bytes)

        # 파일 시스템 타임스탬프도 변경
        dt_str = metadata_overrides.get("DateTimeOriginal") or metadata_overrides.get("datetime", "")
        if dt_str:
            set_file_times(output_path, dt_str)
    else:
        img.save(output_path, quality=quality, optimize=True)


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
