"""Runtime dependency checks for the UI and frozen-app smoke tests."""

import importlib
import shutil
import subprocess


REQUIRED_MODULES = (
    "numpy",
    "numpy.core.multiarray",
    "soundfile",
    "torch",
    "torchaudio",
)
REQUIRED_EXECUTABLES = ("ffmpeg", "ffprobe")


class RuntimeDependencyError(RuntimeError):
    def __init__(self, module_name: str, original: BaseException) -> None:
        super().__init__(f"Could not load {module_name}: {original}")
        self.module_name = module_name
        self.original = original


def check_runtime_dependencies() -> None:
    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except (ImportError, OSError) as error:
            raise RuntimeDependencyError(module_name, error) from error

    for executable in REQUIRED_EXECUTABLES:
        executable_path = shutil.which(executable)
        if executable_path is None:
            error = FileNotFoundError(f"{executable} is not available")
            raise RuntimeDependencyError(executable, error) from error
        try:
            subprocess.run(
                [executable_path, "-version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise RuntimeDependencyError(executable, error) from error
