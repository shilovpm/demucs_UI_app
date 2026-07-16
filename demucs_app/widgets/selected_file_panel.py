"""Compact selected-file state that also accepts replacement drops."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QSizePolicy


class SelectedFilePanel(QFrame):
    files_dropped = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("filePanel")
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _set_dragging(self, dragging: bool) -> None:
        self.setProperty("dragging", dragging)
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            self._set_dragging(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._set_dragging(False)
        event.accept()

    def dropEvent(self, event) -> None:
        self._set_dragging(False)
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.files_dropped.emit(paths)
        event.acceptProposedAction()
