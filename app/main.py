import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from app.ui.main_window import MainWindow


def get_icon_path() -> Path:
    """아이콘 경로 반환"""
    # 개발 환경: app/resources/icon.png
    dev_path = Path(__file__).parent / "resources" / "icon.png"
    if dev_path.exists():
        return dev_path

    # ico 파일도 확인
    ico_path = Path(__file__).parent / "resources" / "icon.ico"
    if ico_path.exists():
        return ico_path

    return dev_path  # 없어도 일단 경로 반환


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setApplicationName("Image Setakgi")
    app.setApplicationVersion("1.0.0")

    # 앱 아이콘 설정
    icon_path = get_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
