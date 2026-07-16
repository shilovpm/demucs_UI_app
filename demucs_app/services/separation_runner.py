"""Background Demucs execution with Qt signals for a responsive interface."""

import errno
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path

import soundfile
import torch
from PySide6.QtCore import QThread, Signal

from demucs.api import LoadAudioError, Separator, save_audio
from demucs.pretrained import ModelLoadingError
from demucs_app.models import JobOptions, JobResult
from demucs_app.services.history import HistoryStore
from demucs_app.services.output_paths import create_job_output_dir
from demucs_app.services.progress import progress_from_callback
from demucs_app.services.runtime_checks import RuntimeDependencyError, check_runtime_dependencies


class SeparationThread(QThread):
    phase_changed = Signal(str)
    progress_changed = Signal(int)
    time_changed = Signal(float, object)
    completed = Signal(object)
    failed = Signal(str, str)
    cancelled = Signal()

    def __init__(
        self,
        options: JobOptions,
        history: HistoryStore,
        parent=None,
        output_root: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.options = options
        self.history = history
        self.output_root = output_root
        self._cancel_requested = threading.Event()
        self._started_at = 0.0
        self._last_progress = 0

    def request_cancel(self) -> None:
        self._cancel_requested.set()

    def _device(self) -> str:
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            if self.options.profile.model_name.startswith("mdx"):
                return "cpu"
            return "mps"
        return "cpu"

    def _on_progress(self, update: dict) -> None:
        if self._cancel_requested.is_set():
            raise KeyboardInterrupt
        progress = max(self._last_progress, progress_from_callback(update))
        self._last_progress = progress
        elapsed = time.monotonic() - self._started_at
        remaining = (elapsed / (progress / 100) - elapsed) if progress >= 3 else None
        self.progress_changed.emit(progress)
        self.time_changed.emit(elapsed, remaining)

    def _save_stems(self, origin, stems: dict, separator: Separator, output_dir: Path) -> tuple[Path, ...]:
        if self.options.mode == "vocals_instrumental":
            vocals = stems["vocals"]
            instrumental = origin.new_zeros(origin.shape)
            for name, stem in stems.items():
                if name != "vocals":
                    instrumental += stem
            stems_to_save = {"vocals": vocals, "instrumental": instrumental}
        else:
            stems_to_save = stems

        self.phase_changed.emit("Saving your stems...")
        files = []
        for name, stem in stems_to_save.items():
            if self._cancel_requested.is_set():
                raise KeyboardInterrupt
            destination = output_dir / f"{name}.{self.options.output_format}"
            if self.options.output_format == "mp3":
                save_audio(
                    stem,
                    destination,
                    samplerate=separator.samplerate,
                    bitrate=self.options.mp3_bitrate,
                    clip="rescale",
                    bits_per_sample=16,
                )
            else:
                scale = max(1.01 * float(stem.abs().max()), 1.0)
                audio = (stem / scale).detach().cpu().transpose(0, 1).numpy()
                soundfile.write(destination, audio, separator.samplerate, subtype="PCM_16")
            files.append(destination)
        return tuple(files)

    def run(self) -> None:
        output_dir: Path | None = None
        self._started_at = time.monotonic()
        started_at = datetime.now().isoformat(timespec="seconds")
        try:
            check_runtime_dependencies()
            self.phase_changed.emit("Preparing your session...")
            output_root = self.output_root if self.output_root is not None else self.options.output_root
            output_dir = create_job_output_dir(self.options.source, root=output_root)
            self.phase_changed.emit("Loading the separation model...")
            separator = Separator(
                model=self.options.profile.model_name,
                device=self._device(),
                shifts=1,
                overlap=0.25,
                split=True,
                jobs=0,
                progress=False,
                callback=self._on_progress,
                callback_arg={"shifts": 1},
            )
            if self._cancel_requested.is_set():
                raise KeyboardInterrupt
            self.phase_changed.emit("Listening to your track...")
            origin, stems = separator.separate_audio_file(self.options.source)
            files = self._save_stems(origin, stems, separator, output_dir)
            self.progress_changed.emit(100)
            self.time_changed.emit(time.monotonic() - self._started_at, 0.0)
            result = JobResult(
                source=self.options.source,
                output_dir=output_dir,
                files=files,
                options=self.options,
                started_at=started_at,
                completed_at=datetime.now().isoformat(timespec="seconds"),
            )
            try:
                self.history.add(result)
            except OSError:
                # The output files are already valid even if local history cannot be updated.
                pass
            self.completed.emit(result)
        except KeyboardInterrupt:
            if output_dir is not None:
                shutil.rmtree(output_dir, ignore_errors=True)
            self.cancelled.emit()
        except RuntimeDependencyError as error:
            if output_dir is not None:
                shutil.rmtree(output_dir, ignore_errors=True)
            self.failed.emit(
                "This copy of Demucs Splitter is incomplete. Please rebuild or reinstall the app.",
                str(error),
            )
        except ModelLoadingError as error:
            if output_dir is not None:
                shutil.rmtree(output_dir, ignore_errors=True)
            self.failed.emit(
                "We could not download the separation model. Check your internet connection and try again.",
                str(error),
            )
        except LoadAudioError as error:
            if output_dir is not None:
                shutil.rmtree(output_dir, ignore_errors=True)
            self.failed.emit("We could not read this audio file.", str(error))
        except OSError as error:
            if output_dir is not None:
                shutil.rmtree(output_dir, ignore_errors=True)
            message = "There is not enough free space to save the stems." if error.errno == errno.ENOSPC else "The separation could not be completed."
            self.failed.emit(message, str(error))
        except Exception as error:  # Keep unexpected model errors from taking down the UI.
            if output_dir is not None:
                shutil.rmtree(output_dir, ignore_errors=True)
            self.failed.emit("The separation could not be completed.", str(error))
