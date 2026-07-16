"""Predictable, collision-safe directories for separated stem files."""

import re
from datetime import datetime
from pathlib import Path


def default_output_root() -> Path:
    return Path.home() / "Music" / "Demucs Stems"


def safe_track_name(source: Path) -> str:
    name = source.stem.strip()
    name = re.sub(r"[<>:\\/*?|\x00-\x1f]", "-", name)
    name = re.sub(r"\s+", " ", name).strip(" .-")
    return (name or "untitled-track")[:72]


def create_job_output_dir(source: Path, root: Path | None = None, now: datetime | None = None) -> Path:
    root = Path(root) if root is not None else default_output_root()
    timestamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    base = f"{safe_track_name(source)}-{timestamp}"
    candidate = root / base
    index = 2
    while candidate.exists():
        candidate = root / f"{base}-{index}"
        index += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate
