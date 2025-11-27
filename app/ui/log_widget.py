"""변환 로그 위젯"""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QLabel,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import Qt


class LogWidget(QWidget):
    """변환 로그를 표시하는 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header_layout = QHBoxLayout()
        title = QLabel("변환 로그")
        title.setStyleSheet("font-weight: bold; color: #fff;")
        header_layout.addWidget(title)

        self._clear_btn = QPushButton("로그 지우기")
        self._clear_btn.setFixedWidth(80)
        self._clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(self._clear_btn)

        layout.addLayout(header_layout)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)
        self._log_text.setMinimumHeight(120)
        self._log_text.setMaximumHeight(200)
        layout.addWidget(self._log_text)

    def add_log(self, message: str, log_type: str = "info"):
        """로그 메시지 추가"""
        color_map = {
            "info": "#00ff00",
            "success": "#4caf50",
            "error": "#ff5252",
            "warning": "#ffc107",
        }
        color = color_map.get(log_type, "#00ff00")
        self._log_text.append(f'<span style="color: {color}">{message}</span>')
        self._log_text.verticalScrollBar().setValue(
            self._log_text.verticalScrollBar().maximum()
        )

    def clear(self):
        """로그 지우기"""
        self._log_text.clear()

    def add_separator(self):
        """구분선 추가"""
        self._log_text.append('<span style="color: #666">─' * 40 + "</span>")
