import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QStyleOptionViewItem

from demucs_app.models import AudioMetadata
from demucs_app.main_window import MainWindow
from demucs_app.screens.error_screen import ErrorScreen
from demucs_app.screens.import_screen import ImportScreen
from demucs_app.screens.progress_screen import ProgressScreen
from demucs_app.services.history import HistoryStore


class UiStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        history = HistoryStore(Path(self.temporary_directory.name) / "history.json")
        self.screen = ImportScreen(history)

    def tearDown(self):
        self.screen.deleteLater()
        self.temporary_directory.cleanup()

    def test_selected_file_replaces_the_large_drop_zone(self):
        metadata = AudioMetadata(duration_seconds=65, file_size=1024)
        with patch("demucs_app.screens.import_screen.validate_audio", return_value=metadata):
            self.screen._set_file(Path("song.mp3"))
        self.assertTrue(self.screen.drop_zone.isHidden())
        self.assertFalse(self.screen.file_panel.isHidden())
        self.assertEqual(self.screen.file_name.text(), "song.mp3")

    def test_remove_restores_the_drop_zone(self):
        metadata = AudioMetadata(duration_seconds=65, file_size=1024)
        with patch("demucs_app.screens.import_screen.validate_audio", return_value=metadata):
            self.screen._set_file(Path("song.mp3"))
        self.screen.clear_file()
        self.assertFalse(self.screen.drop_zone.isHidden())
        self.assertTrue(self.screen.file_panel.isHidden())

    def test_empty_history_uses_compact_state(self):
        self.assertTrue(self.screen.recent.isHidden())
        self.assertFalse(self.screen.recent_empty.isHidden())

    def test_error_details_are_hidden_until_requested(self):
        error_screen = ErrorScreen()
        error_screen.show_error("A friendly error", "A technical error")
        self.assertTrue(error_screen.details.isHidden())
        self.assertFalse(error_screen.details_toggle.isHidden())
        error_screen.details_toggle.setChecked(True)
        self.assertFalse(error_screen.details.isHidden())
        error_screen.deleteLater()

    def test_custom_output_folder_is_attached_to_the_job(self):
        metadata = AudioMetadata(duration_seconds=65, file_size=1024)
        output_root = Path(self.temporary_directory.name) / "custom-output"
        emitted = []
        self.screen.start_requested.connect(emitted.append)
        self.screen._set_output_root(output_root)
        with patch("demucs_app.screens.import_screen.validate_audio", return_value=metadata):
            self.screen._set_file(Path("song.mp3"))
            self.screen._start()
        self.assertEqual(self.screen.output_path.text(), str(output_root))
        self.assertEqual(emitted[0].output_root, output_root)

    def test_progress_percentage_is_outside_the_progress_bar(self):
        progress_screen = ProgressScreen()
        progress_screen.set_progress(67)
        self.assertFalse(progress_screen.progress.isTextVisible())
        self.assertEqual(progress_screen.percentage.text(), "67%")
        progress_screen.deleteLater()

    def test_combo_boxes_keep_readable_height_with_mp3_options(self):
        self.screen.mode.combo.setCurrentIndex(1)
        self.screen.quality.combo.setCurrentIndex(2)
        self.screen.output.combo.setCurrentIndex(1)
        self.screen.bitrate.combo.setCurrentIndex(2)
        self.screen.resize(800, 650)
        self.screen.show()
        self.app.processEvents()
        for combo in (
            self.screen.mode.combo,
            self.screen.quality.combo,
            self.screen.output.combo,
            self.screen.bitrate.combo,
        ):
            self.assertEqual(combo.height(), 36)
            text_width = combo.fontMetrics().horizontalAdvance(combo.currentText())
            self.assertGreaterEqual(combo.width(), text_width + 45)
        self.assertEqual(self.screen.output_path.height(), 36)

    def test_main_window_prevents_the_settings_row_from_becoming_too_narrow(self):
        window = MainWindow()
        self.assertGreaterEqual(window.minimumWidth(), 800)
        window.deleteLater()

    def test_combo_popup_supports_hover_and_comfortable_rows(self):
        combo = self.screen.mode.combo
        view = combo.view()
        index = combo.model().index(0, 0)
        item_height = view.itemDelegate().sizeHint(QStyleOptionViewItem(), index).height()
        self.assertEqual(view.objectName(), "comboPopup")
        self.assertTrue(view.hasMouseTracking())
        self.assertTrue(view.viewport().hasMouseTracking())
        self.assertGreaterEqual(item_height, 34)
