"""Main window and screen orchestration."""

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from demucs_app.screens.error_screen import ErrorScreen
from demucs_app.screens.import_screen import ImportScreen
from demucs_app.screens.progress_screen import ProgressScreen
from demucs_app.screens.success_screen import SuccessScreen
from demucs_app.services.history import HistoryStore
from demucs_app.services.separation_runner import SeparationThread


APP_STYLE = """
QMainWindow { background: #f7faf8; }
QWidget { color: #20312e; font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif; font-size: 14px; }
QLabel#appTitle { color: #113b34; font-size: 30px; font-weight: 700; }
QLabel#screenTitle { color: #113b34; font-size: 28px; font-weight: 700; }
QLabel#dropTitle { color: #113b34; font-size: 19px; font-weight: 600; }
QLabel#progressMessage { color: #167466; font-size: 17px; font-weight: 600; }
QLabel#progressPercent { color: #20312e; font-weight: 700; }
QLabel#fileName { color: #113b34; font-size: 15px; font-weight: 650; }
QLabel#sectionTitle { color: #42625c; font-size: 12px; font-weight: 700; }
QLabel#optionLabel { color: #42625c; font-size: 12px; font-weight: 650; }
QLabel#muted { color: #627973; }
QLabel#feedback[error='true'], QLabel#errorMessage { color: #b34731; font-weight: 600; }
QLabel#feedback[error='false'] { color: #167466; font-weight: 600; }
QFrame#dropZone { background: #edf7f4; border: 2px dashed #9bc9bf; border-radius: 8px; }
QFrame#dropZone[dragging='true'] { background: #ddf1eb; border-color: #167466; }
QFrame#filePanel, QFrame#optionsPanel { background: #ffffff; border: 1px solid #d9e6e1; border-radius: 8px; }
QFrame#filePanel[dragging='true'] { background: #edf7f4; border: 2px dashed #167466; }
QPushButton { border-radius: 6px; padding: 9px 15px; font-weight: 650; }
QPushButton#primaryButton { background: #167466; color: white; border: 1px solid #167466; min-width: 138px; }
QPushButton#primaryButton:hover { background: #0f6256; }
QPushButton#primaryButton:disabled { background: #a9bbb6; border-color: #a9bbb6; }
QPushButton#secondaryButton { background: white; color: #195d52; border: 1px solid #a8c9c1; }
QPushButton#textButton { background: transparent; color: #9b4a3a; border: 0; }
QComboBox { background: white; border: 1px solid #c8dad5; border-radius: 5px; padding: 0 34px 0 9px; min-width: 118px; }
QComboBox[compact='true'] { min-width: 64px; }
QComboBox:hover { background: #fbfdfc; border-color: #77aa9e; }
QComboBox:focus, QComboBox:on { border-color: #167466; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 30px; border: 0; background: transparent; }
QComboBox::down-arrow { image: url("__COMBO_ARROW__"); width: 12px; height: 12px; }
QListView#comboPopup { background: white; border: 1px solid #b8cec8; border-radius: 5px; padding: 4px; outline: 0; }
QListView#comboPopup::item { color: #20312e; min-height: 34px; padding: 0 10px; border-radius: 4px; }
QListView#comboPopup::item:hover { background: #edf7f4; color: #113b34; }
QListView#comboPopup::item:selected { background: #d7ece6; color: #113b34; }
QListView#comboPopup::item:selected:hover { background: #c8e5dc; color: #113b34; }
QLineEdit#outputPath { background: #f8fbfa; border: 1px solid #c8dad5; border-radius: 5px; padding: 0 9px; color: #42625c; }
QProgressBar { border: 0; background: #dceae5; border-radius: 6px; min-height: 12px; max-height: 12px; }
QProgressBar::chunk { background: #167466; border-radius: 6px; }
QListWidget#recentList, QListWidget#filesList { background: white; border: 1px solid #d9e6e1; border-radius: 7px; padding: 4px; }
QListWidget::item { padding: 6px; border-radius: 4px; }
QListWidget::item:selected { background: #dcefe9; color: #113b34; }
QLabel#emptyHistory { color: #7a8e89; background: #f1f6f4; border-radius: 6px; padding: 12px; }
QToolButton#detailsToggle { color: #42625c; border: 0; padding: 5px; }
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Demucs Splitter")
        self.resize(860, 680)
        self.setMinimumSize(800, 650)
        self.history = HistoryStore()
        self.thread: SeparationThread | None = None
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.import_screen = ImportScreen(self.history)
        self.progress_screen = ProgressScreen()
        self.success_screen = SuccessScreen()
        self.error_screen = ErrorScreen()
        for screen in (self.import_screen, self.progress_screen, self.success_screen, self.error_screen):
            self.stack.addWidget(screen)
        self.import_screen.start_requested.connect(self.start_job)
        self.progress_screen.cancel_requested.connect(self.cancel_job)
        self.success_screen.split_another_requested.connect(self.show_import)
        self.error_screen.back_requested.connect(self.show_import)
        self.show_import()

    def show_import(self) -> None:
        self.import_screen.load_history()
        self.stack.setCurrentWidget(self.import_screen)

    def start_job(self, options) -> None:
        if self.thread and self.thread.isRunning():
            return
        self.progress_screen.reset()
        self.stack.setCurrentWidget(self.progress_screen)
        self.thread = SeparationThread(options, self.history, self)
        self.thread.phase_changed.connect(self.progress_screen.set_phase)
        self.thread.progress_changed.connect(self.progress_screen.set_progress)
        self.thread.time_changed.connect(self.progress_screen.set_time)
        self.thread.completed.connect(self._job_completed)
        self.thread.failed.connect(self._job_failed)
        self.thread.cancelled.connect(self._job_cancelled)
        self.thread.start()

    def cancel_job(self) -> None:
        if self.thread and self.thread.isRunning():
            self.progress_screen.cancelling()
            self.thread.request_cancel()

    def _job_completed(self, result) -> None:
        self.success_screen.set_result(result)
        self.stack.setCurrentWidget(self.success_screen)
        self.thread = None

    def _job_failed(self, message: str, details: str) -> None:
        self.error_screen.show_error(message, details)
        self.stack.setCurrentWidget(self.error_screen)
        self.thread = None

    def _job_cancelled(self) -> None:
        self.thread = None
        self.import_screen._show_feedback("Separation cancelled.", error=False)
        self.show_import()


def create_application() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Demucs Splitter")
    assets = Path(__file__).resolve().parent / "assets"
    app.setWindowIcon(QIcon(str(assets / "icons" / "demucs_icon_default_1024.png")))
    app.setStyleSheet(APP_STYLE.replace("__COMBO_ARROW__", (assets / "ui" / "chevron-down.svg").as_posix()))
    return app
