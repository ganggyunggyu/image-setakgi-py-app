import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.ui.main_window import MainWindow


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setApplicationName("Image Setakgi")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
