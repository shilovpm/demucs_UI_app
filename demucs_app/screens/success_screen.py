"""Completion view with direct Finder access."""

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from demucs_app.models import JobResult


class SuccessScreen(QWidget):
    split_another_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.result: JobResult | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(70, 62, 70, 46)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Your stems are ready")
        title.setObjectName("screenTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description = QLabel()
        self.description.setObjectName("muted")
        self.description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.files = QListWidget()
        self.files.setObjectName("filesList")
        self.files.setMaximumHeight(170)
        self.open_folder = QPushButton("Open folder")
        self.open_folder.setObjectName("primaryButton")
        self.open_folder.clicked.connect(self._open_folder)
        another = QPushButton("Split another file")
        another.setObjectName("secondaryButton")
        another.clicked.connect(self.split_another_requested)
        layout.addWidget(title)
        layout.addWidget(self.description)
        layout.addSpacing(6)
        layout.addWidget(QLabel("Created files", objectName="sectionTitle"))
        layout.addWidget(self.files)
        layout.addWidget(self.open_folder, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(another, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_result(self, result: JobResult) -> None:
        self.result = result
        self.description.setText(f"Saved in {result.output_dir}")
        self.files.clear()
        for file in result.files:
            self.files.addItem(QListWidgetItem(file.name))

    def _open_folder(self) -> None:
        if self.result:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.result.output_dir)))
