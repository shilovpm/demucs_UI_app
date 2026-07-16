"""Shared application data structures."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


SeparationMode = Literal["four_stems", "vocals_instrumental"]
OutputFormat = Literal["wav", "mp3", "flac"]


@dataclass(frozen=True)
class QualityProfile:
    key: str
    label: str
    model_name: str
    description: str


QUALITY_PROFILES = (
    QualityProfile("fast", "Fast", "mdx_extra_q", "Quicker separation with a lighter model."),
    QualityProfile("balanced", "Balanced", "htdemucs", "A reliable balance of speed and quality."),
    QualityProfile("best", "Best quality", "htdemucs_ft", "The most detailed result, with a longer wait."),
)


@dataclass(frozen=True)
class JobOptions:
    source: Path
    mode: SeparationMode
    profile: QualityProfile
    output_format: OutputFormat
    mp3_bitrate: int = 320
    output_root: Path | None = None

    @property
    def stem_count(self) -> int:
        return 2 if self.mode == "vocals_instrumental" else 4


@dataclass(frozen=True)
class AudioMetadata:
    duration_seconds: float | None
    file_size: int


@dataclass(frozen=True)
class JobResult:
    source: Path
    output_dir: Path
    files: tuple[Path, ...]
    options: JobOptions
    started_at: str
    completed_at: str
