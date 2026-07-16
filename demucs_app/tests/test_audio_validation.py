import unittest

from demucs_app.services.audio_validation import estimate_output_bytes, format_duration


class AudioValidationTests(unittest.TestCase):
    def test_estimates_four_stems(self):
        estimate = estimate_output_bytes(60, 4)
        self.assertGreater(estimate, 40_000_000)

    def test_unknown_duration_has_no_estimate(self):
        self.assertEqual(estimate_output_bytes(None, 4), 0)

    def test_formats_duration(self):
        self.assertEqual(format_duration(65), "1:05")
        self.assertEqual(format_duration(3661), "1:01:01")
