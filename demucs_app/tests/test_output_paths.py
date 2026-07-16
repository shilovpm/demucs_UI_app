import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from demucs_app.services.audio_validation import validate_output_root
from demucs_app.services.output_paths import create_job_output_dir, safe_track_name


class OutputPathTests(unittest.TestCase):
    def test_sanitizes_unsafe_filename_characters(self):
        self.assertEqual(safe_track_name(Path("bad:name?.mp3")), "bad-name")

    def test_adds_suffix_when_timestamp_collides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = Path("song.mp3")
            now = datetime(2026, 7, 15, 14, 30, 12)
            first = create_job_output_dir(source, root, now)
            second = create_job_output_dir(source, root, now)
            self.assertEqual(first.name, "song-20260715-143012")
            self.assertEqual(second.name, "song-20260715-143012-2")

    def test_prepares_a_custom_output_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "new-output-root"
            self.assertEqual(validate_output_root(root), root)
            self.assertTrue(root.is_dir())
