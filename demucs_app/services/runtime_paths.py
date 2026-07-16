"""Configure paths to executables bundled with the frozen application."""

import os
from pathlib import Path


def bundled_tools_directory() -> Path:
    return Path(__file__).resolve().parents[1] / "bin"


def configure_runtime_paths() -> Path | None:
    tools_directory = bundled_tools_directory()
    if not tools_directory.is_dir():
        return None

    current_path = os.environ.get("PATH", "")
    path_entries = [entry for entry in current_path.split(os.pathsep) if entry]
    tools_path = str(tools_directory)
    if tools_path not in path_entries:
        os.environ["PATH"] = os.pathsep.join([tools_path, *path_entries])
    return tools_directory
