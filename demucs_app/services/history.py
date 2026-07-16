"""A small local history of recently completed jobs."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from demucs_app.models import JobResult


@dataclass(frozen=True)
class HistoryEntry:
    source_name: str
    output_dir: str
    completed_at: str
    mode: str
    profile: str


class HistoryStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (Path.home() / "Library" / "Application Support" / "Demucs Splitter" / "history.json")

    def load(self) -> list[HistoryEntry]:
        try:
            raw_entries = json.loads(self.path.read_text(encoding="utf-8"))
            return [HistoryEntry(**entry) for entry in raw_entries if Path(entry["output_dir"]).is_dir()]
        except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, KeyError):
            return []

    def add(self, result: JobResult) -> None:
        entry = HistoryEntry(
            source_name=result.source.name,
            output_dir=str(result.output_dir),
            completed_at=result.completed_at,
            mode=result.options.mode,
            profile=result.options.profile.label,
        )
        entries = [entry, *self.load()]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([asdict(item) for item in entries[:10]], indent=2), encoding="utf-8"
        )
