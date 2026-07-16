"""Audio-file checks performed before a long Demucs job begins."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from demucs_app.models import AudioMetadata


SUPPORTED_SUFFIXES = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"}


class ValidationError(ValueError):
    """A user-facing validation failure."""


def validate_output_root(output_root: Path) -> Path:
    """Create the selected root and verify that the app can write to it."""
    output_root = Path(output_root).expanduser()
    try:
        output_root.mkdir(parents=True, exist_ok=True)
        if not output_root.is_dir():
            raise OSError(f"Not a directory: {output_root}")
        with tempfile.NamedTemporaryFile(dir=output_root):
            pass
    except OSError as error:
        raise ValidationError(
            "We could not prepare the output folder. Check that you can write to the selected folder."
        ) from error
    return output_root


def estimate_output_bytes(duration_seconds: float | None, stem_count: int) -> int:
    """Estimate the storage required for 44.1 kHz, stereo, 16-bit stem files."""
    if duration_seconds is None:
        return 0
    bytes_per_second = 44_100 * 2 * 2
    return int(duration_seconds * bytes_per_second * stem_count * 1.25)


def format_bytes(value: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{value} B"


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "Unknown duration"
    whole_seconds = max(0, int(round(seconds)))
    minutes, seconds = divmod(whole_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _probe_duration(path: Path) -> float | None:
    """Use ffprobe when available; Demucs also uses it for broad format support."""
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path is None:
        return None
    try:
        completed = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        payload = json.loads(completed.stdout)
        duration = payload.get("format", {}).get("duration")
        return float(duration) if duration is not None else None
    except FileNotFoundError:
        return None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError):
        raise ValidationError("We could not read this audio file.")


def validate_audio(path: Path, output_root: Path, stem_count: int) -> AudioMetadata:
    path = Path(path).expanduser()
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValidationError("That file format is not supported.")
    if not path.exists() or not path.is_file():
        raise ValidationError("The selected file is no longer available.")
    if not path.stat().st_size:
        raise ValidationError("We could not read this audio file.")

    duration = _probe_duration(path)
    estimated_size = estimate_output_bytes(duration, stem_count)
    try:
        output_root = validate_output_root(output_root)
        free_space = shutil.disk_usage(output_root).free
    except OSError as error:
        raise ValidationError(
            "We could not prepare the output folder. Check that you can write to the selected folder."
        ) from error
    if estimated_size and free_space < estimated_size:
        raise ValidationError("There is not enough free space to save the stems.")
    return AudioMetadata(duration_seconds=duration, file_size=path.stat().st_size)
