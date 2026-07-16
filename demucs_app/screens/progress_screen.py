"""Live separation status."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from demucs_app.services.progress import format_elapsed, format_remaining, message_for_progress
from demucs_app.widgets.progress_animation import ProgressAnimation


class ProgressScreen(QWidget):
    cancel_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(70, 78, 70, 60)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Separating your track")
        title.setObjectName("screenTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message = QLabel("Preparing your session...")
        self.message.setObjectName("progressMessage")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.animation = ProgressAnimation()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.percentage = QLabel("0%")
        self.percentage.setObjectName("progressPercent")
        self.percentage.setFixedWidth(46)
        self.percentage.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        progress_row = QHBoxLayout()
        progress_row.setContentsMargins(0, 0, 0, 0)
        progress_row.setSpacing(12)
        progress_row.addWidget(self.progress)
        progress_row.addWidget(self.percentage)
        self.time = QLabel("Estimating time remaining...")
        self.time.setObjectName("muted")
        self.time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cancel = QPushButton("Cancel")
        self.cancel.setObjectName("secondaryButton")
        self.cancel.clicked.connect(self.cancel_requested)
        layout.addWidget(title)
        layout.addWidget(self.message)
        layout.addWidget(self.animation)
        layout.addLayout(progress_row)
        layout.addWidget(self.time)
        layout.addSpacing(10)
        layout.addWidget(self.cancel, alignment=Qt.AlignmentFlag.AlignCenter)

    def reset(self) -> None:
        self.progress.setValue(0)
        self.percentage.setText("0%")
        self.message.setText("Preparing your session...")
        self.time.setText("Estimating time remaining...")
        self.cancel.setEnabled(True)

    def set_phase(self, message: str) -> None:
        self.message.setText(message)

    def set_progress(self, value: int) -> None:
        value = max(0, min(100, value))
        self.progress.setValue(value)
        self.percentage.setText(f"{value}%")
        if value > 0 and value < 100:
            self.message.setText(message_for_progress(value))

    def set_time(self, elapsed: float, remaining: object) -> None:
        remaining_value = remaining if isinstance(remaining, (float, int)) else None
        self.time.setText(f"{format_elapsed(elapsed)} | {format_remaining(remaining_value)}")

    def cancelling(self) -> None:
        self.cancel.setEnabled(False)
        self.message.setText("Cancelling separation...")
