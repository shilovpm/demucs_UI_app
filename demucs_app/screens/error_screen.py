"""Recoverable errors without exposing a terminal."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QToolButton, QVBoxLayout, QWidget


class ErrorScreen(QWidget):
    back_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 90, 80, 70)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Something needs your attention")
        title.setObjectName("screenTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message = QLabel()
        self.message.setObjectName("errorMessage")
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details = QLabel()
        self.details.setObjectName("muted")
        self.details.setWordWrap(True)
        self.details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details.hide()
        self.details_toggle = QToolButton()
        self.details_toggle.setObjectName("detailsToggle")
        self.details_toggle.setText("Show technical details")
        self.details_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.details_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.details_toggle.setCheckable(True)
        self.details_toggle.toggled.connect(self._toggle_details)
        self.details_toggle.hide()
        back = QPushButton("Try another file")
        back.setObjectName("primaryButton")
        back.clicked.connect(self.back_requested)
        layout.addWidget(title)
        layout.addWidget(self.message)
        layout.addWidget(self.details_toggle, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.details)
        layout.addSpacing(12)
        layout.addWidget(back, alignment=Qt.AlignmentFlag.AlignCenter)

    def show_error(self, message: str, details: str) -> None:
        self.message.setText(message)
        self.details.setText(details)
        self.details.hide()
        self.details_toggle.setChecked(False)
        self.details_toggle.setVisible(bool(details))

    def _toggle_details(self, checked: bool) -> None:
        self.details.setVisible(checked)
        self.details_toggle.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )
        self.details_toggle.setText("Hide technical details" if checked else "Show technical details")
