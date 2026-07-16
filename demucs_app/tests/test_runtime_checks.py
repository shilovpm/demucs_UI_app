import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from demucs_app.models import JobOptions, QUALITY_PROFILES
from demucs_app.services import runtime_checks
from demucs_app.services.history import HistoryStore
from demucs_app.services.runtime_checks import RuntimeDependencyError, check_runtime_dependencies
from demucs_app.services.runtime_paths import configure_runtime_paths
from demucs_app.services.separation_runner import SeparationThread


class RuntimeCheckTests(unittest.TestCase):
    def test_reports_the_dependency_that_cannot_be_loaded(self):
        with patch("demucs_app.services.runtime_checks.importlib.import_module") as import_module:
            import_module.side_effect = [object(), ModuleNotFoundError("missing compatibility module")]
            with self.assertRaises(RuntimeDependencyError) as context:
                check_runtime_dependencies()
        self.assertEqual(context.exception.module_name, "numpy.core.multiarray")

    def test_current_environment_passes(self):
        check_runtime_dependencies()

    def test_reports_a_missing_ffmpeg_executable(self):
        with patch.object(runtime_checks.importlib, "import_module", return_value=object()), patch.object(
            runtime_checks.shutil, "which", return_value=None
        ):
            with self.assertRaises(RuntimeDependencyError) as context:
                check_runtime_dependencies()
        self.assertEqual(context.exception.module_name, "ffmpeg")

    def test_bundled_tools_are_prepended_to_path(self):
        with TemporaryDirectory() as directory, patch(
            "demucs_app.services.runtime_paths.bundled_tools_directory", return_value=Path(directory)
        ), patch.dict(os.environ, {"PATH": "/usr/bin:/bin"}):
            self.assertEqual(configure_runtime_paths(), Path(directory))
            self.assertEqual(os.environ["PATH"].split(os.pathsep)[0], directory)

    def test_mdx_profile_uses_cpu_when_mps_is_available(self):
        profile = next(profile for profile in QUALITY_PROFILES if profile.key == "fast")
        options = JobOptions(Path("song.mp3"), "four_stems", profile, "wav")
        with TemporaryDirectory() as directory:
            thread = SeparationThread(options, HistoryStore(Path(directory) / "history.json"))
            with patch("torch.cuda.is_available", return_value=False), patch(
                "torch.backends.mps.is_available", return_value=True
            ):
                self.assertEqual(thread._device(), "cpu")
