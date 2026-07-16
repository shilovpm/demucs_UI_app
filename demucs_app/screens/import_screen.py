"""File import and intentionally compact job options."""

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from demucs_app.models import QUALITY_PROFILES, JobOptions
from demucs_app.services.audio_validation import (
    ValidationError,
    format_bytes,
    format_duration,
    validate_audio,
    validate_output_root,
)
from demucs_app.services.history import HistoryStore
from demucs_app.services.output_paths import default_output_root
from demucs_app.widgets.combo_box import ModernComboBox
from demucs_app.widgets.drop_zone import DropZone
from demucs_app.widgets.selected_file_panel import SelectedFilePanel


class ImportScreen(QWidget):
    start_requested = Signal(object)

    def __init__(self, history: HistoryStore, parent=None) -> None:
        super().__init__(parent)
        self.history = history
        self.selected_path: Path | None = None
        self.output_root = default_output_root()
        self._build()
        self.load_history()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(46, 38, 46, 32)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title = QLabel("Demucs Splitter")
        title.setObjectName("appTitle")
        intro = QLabel("Turn one song into clean, usable stems.")
        intro.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(intro)

        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._receive_files)
        layout.addWidget(self.drop_zone)

        self.file_panel = SelectedFilePanel()
        self.file_panel.files_dropped.connect(self._receive_files)
        file_layout = QHBoxLayout(self.file_panel)
        file_layout.setContentsMargins(18, 14, 18, 14)
        details = QVBoxLayout()
        self.file_name = QLabel()
        self.file_name.setObjectName("fileName")
        self.file_details = QLabel()
        self.file_details.setObjectName("muted")
        details.addWidget(self.file_name)
        details.addWidget(self.file_details)
        file_layout.addLayout(details)
        file_layout.addStretch()
        replace = QPushButton("Replace")
        replace.setObjectName("secondaryButton")
        replace.clicked.connect(self.drop_zone.choose_file)
        remove = QPushButton("Remove")
        remove.setObjectName("textButton")
        remove.clicked.connect(self.clear_file)
        file_layout.addWidget(replace)
        file_layout.addWidget(remove)
        self.file_panel.hide()
        layout.addWidget(self.file_panel)

        options = QFrame()
        options.setObjectName("optionsPanel")
        options.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        options_layout = QGridLayout(options)
        options_layout.setContentsMargins(18, 14, 18, 14)
        options_layout.setHorizontalSpacing(12)
        options_layout.setVerticalSpacing(10)
        self.mode = self._option("Mode", [("Four stems", "four_stems"), ("Vocals + instrumental", "vocals_instrumental")])
        self.quality = self._option("Quality", [(profile.label, profile.key) for profile in QUALITY_PROFILES])
        output_settings = QWidget()
        output_settings_layout = QHBoxLayout(output_settings)
        output_settings_layout.setContentsMargins(0, 0, 0, 0)
        output_settings_layout.setSpacing(10)
        self.output = self._option(
            "Output format",
            [("WAV", "wav"), ("MP3", "mp3"), ("FLAC", "flac")],
            compact=True,
        )
        self.bitrate = self._option(
            "MP3 quality",
            [("192 kbps", "192"), ("256 kbps", "256"), ("320 kbps", "320")],
            compact=True,
        )
        output_settings_layout.addWidget(self.output, 4)
        output_settings_layout.addWidget(self.bitrate, 5)
        self.output.combo.currentIndexChanged.connect(self._update_bitrate_visibility)
        options_layout.addWidget(self.mode, 0, 0)
        options_layout.addWidget(self.quality, 0, 1)
        options_layout.addWidget(output_settings, 0, 2)

        destination = QWidget()
        destination_layout = QGridLayout(destination)
        destination_layout.setContentsMargins(0, 0, 0, 0)
        destination_layout.setHorizontalSpacing(10)
        destination_layout.setVerticalSpacing(4)
        destination_label = QLabel("Save to")
        destination_label.setObjectName("optionLabel")
        self.output_path = QLineEdit(str(self.output_root))
        self.output_path.setObjectName("outputPath")
        self.output_path.setReadOnly(True)
        self.output_path.setFixedHeight(36)
        self.output_path.setToolTip(str(self.output_root))
        choose_output = QPushButton("Choose folder")
        choose_output.setObjectName("secondaryButton")
        choose_output.setFixedHeight(36)
        choose_output.clicked.connect(self._choose_output_folder)
        destination_layout.addWidget(destination_label, 0, 0, 1, 2)
        destination_layout.addWidget(self.output_path, 1, 0)
        destination_layout.addWidget(choose_output, 1, 1)
        destination_layout.setColumnStretch(0, 1)
        options_layout.addWidget(destination, 1, 0, 1, 3)
        options_layout.setColumnStretch(0, 6)
        options_layout.setColumnStretch(1, 5)
        options_layout.setColumnStretch(2, 7)
        layout.addWidget(options)
        self._update_bitrate_visibility()

        self.feedback = QLabel()
        self.feedback.setObjectName("feedback")
        self.feedback.setWordWrap(True)
        self.feedback.hide()

        start_row = QHBoxLayout()
        self.start_button = QPushButton("Start splitting")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self._start)
        start_row.addWidget(self.feedback)
        start_row.addStretch(1)
        start_row.addWidget(self.start_button)
        layout.addLayout(start_row)

        recent_title = QLabel("Recent splits")
        recent_title.setObjectName("sectionTitle")
        self.recent = QListWidget()
        self.recent.setObjectName("recentList")
        self.recent.setMaximumHeight(128)
        self.recent.itemActivated.connect(self._open_recent)
        self.recent_empty = QLabel("No recent splits yet")
        self.recent_empty.setObjectName("emptyHistory")
        self.recent_empty.setFixedHeight(48)
        layout.addWidget(recent_title)
        layout.addWidget(self.recent_empty)
        layout.addWidget(self.recent)

    def _option(self, label: str, values: list[tuple[str, str]], compact: bool = False) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        title = QLabel(label)
        title.setObjectName("optionLabel")
        combo = ModernComboBox()
        combo.setProperty("compact", compact)
        if compact:
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(5)
        for text, value in values:
            combo.addItem(text, value)
        layout.addWidget(title)
        layout.addWidget(combo)
        container.combo = combo
        return container

    def _update_bitrate_visibility(self) -> None:
        self.bitrate.setVisible(self.output.combo.currentData() == "mp3")

    def _receive_files(self, paths: list[Path]) -> None:
        if len(paths) != 1:
            self._show_feedback("Please add one file at a time.", error=True)
            return
        self._set_file(paths[0])

    def _choose_output_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose output folder",
            str(self.output_root),
            QFileDialog.Option.ShowDirsOnly,
        )
        if selected:
            self._set_output_root(Path(selected))

    def _set_output_root(self, path: Path) -> None:
        try:
            output_root = validate_output_root(path)
            if self.selected_path is not None:
                validate_audio(self.selected_path, output_root, self._stem_count())
        except ValidationError as error:
            self._show_feedback(str(error), error=True)
            return
        self.output_root = output_root
        self.output_path.setText(str(output_root))
        self.output_path.setToolTip(str(output_root))
        if self.selected_path is not None:
            self._show_feedback("Ready to split", error=False)

    def _set_file(self, path: Path) -> None:
        try:
            metadata = validate_audio(path, self.output_root, self._stem_count())
        except ValidationError as error:
            self._show_feedback(str(error), error=True)
            return
        self.selected_path = path
        self.file_name.setText(path.name)
        self.file_details.setText(f"{format_duration(metadata.duration_seconds)} | {format_bytes(metadata.file_size)}")
        self.drop_zone.hide()
        self.file_panel.show()
        self.start_button.setEnabled(True)
        self._show_feedback("Ready to split", error=False)

    def _stem_count(self) -> int:
        return 2 if self.mode.combo.currentData() == "vocals_instrumental" else 4

    def _show_feedback(self, text: str, error: bool) -> None:
        self.feedback.setText(text)
        self.feedback.setProperty("error", error)
        self.feedback.style().unpolish(self.feedback)
        self.feedback.style().polish(self.feedback)
        self.feedback.show()

    def clear_file(self) -> None:
        self.selected_path = None
        self.drop_zone.show()
        self.file_panel.hide()
        self.feedback.hide()
        self.start_button.setEnabled(False)

    def _start(self) -> None:
        if self.selected_path is None:
            return
        try:
            validate_audio(self.selected_path, self.output_root, self._stem_count())
        except ValidationError as error:
            self._show_feedback(str(error), error=True)
            return
        profile_key = self.quality.combo.currentData()
        profile = next(profile for profile in QUALITY_PROFILES if profile.key == profile_key)
        options = JobOptions(
            source=self.selected_path,
            mode=self.mode.combo.currentData(),
            profile=profile,
            output_format=self.output.combo.currentData(),
            mp3_bitrate=int(self.bitrate.combo.currentData()),
            output_root=self.output_root,
        )
        self.start_requested.emit(options)

    def load_history(self) -> None:
        self.recent.clear()
        entries = self.history.load()
        if not entries:
            self.recent.hide()
            self.recent_empty.show()
            return
        self.recent_empty.hide()
        self.recent.show()
        for entry in entries:
            item = QListWidgetItem(f"{entry.source_name}  |  {entry.profile}  |  {entry.completed_at}")
            item.setData(Qt.ItemDataRole.UserRole, entry.output_dir)
            self.recent.addItem(item)

    def _open_recent(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
