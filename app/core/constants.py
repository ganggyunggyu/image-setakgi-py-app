import piexif

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

RANDOM_CAMERAS = [
    ("Canon", "EOS 5D Mark IV"),
    ("Nikon", "D850"),
    ("Sony", "A7R IV"),
    ("Fujifilm", "X-T4"),
    ("Panasonic", "GH5"),
]
