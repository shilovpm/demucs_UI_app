import unittest

from demucs_app.services.progress import message_for_progress, progress_from_callback


class ProgressTests(unittest.TestCase):
    def test_progress_is_bounded_below_completion(self):
        value = progress_from_callback(
            {"audio_length": 1000, "models": 1, "shifts": 1, "segment_offset": 1000}
        )
        self.assertEqual(value, 99)

    def test_message_is_available(self):
        self.assertIn("...", message_for_progress(50))
