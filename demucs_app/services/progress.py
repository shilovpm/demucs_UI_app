"""Progress normalization and copy rotation independent from Qt widgets."""


PROGRESS_MESSAGES = (
    "Listening for the drums...",
    "Leaning into the details...",
    "Finding the lovely vocals...",
    "Separating the low end...",
    "Giving every stem its space...",
    "Balancing the remaining instruments...",
    "Putting the final touches on...",
)


def progress_from_callback(update: dict) -> int:
    """Map Demucs chunk callbacks to a monotonic, conservative percentage."""
    audio_length = max(1, int(update.get("audio_length", 1)))
    models = max(1, int(update.get("models", 1)))
    shifts = max(1, int(update.get("shifts", 1)))
    model_index = min(models - 1, max(0, int(update.get("model_idx_in_bag", 0))))
    shift_index = min(shifts - 1, max(0, int(update.get("shift_idx", 0))))
    offset = min(audio_length, max(0, int(update.get("segment_offset", 0))))
    completed = model_index * shifts + shift_index + (offset / audio_length)
    return min(99, max(0, int((completed / (models * shifts)) * 100)))


def message_for_progress(progress: int) -> str:
    if progress < 1:
        return "Preparing your session..."
    return PROGRESS_MESSAGES[min(len(PROGRESS_MESSAGES) - 1, progress * len(PROGRESS_MESSAGES) // 100)]


def format_elapsed(seconds: float) -> str:
    whole = max(0, int(seconds))
    minutes, seconds = divmod(whole, 60)
    return f"{minutes}:{seconds:02d} elapsed"


def format_remaining(seconds: float | None) -> str:
    if seconds is None or seconds < 1:
        return "Estimating time remaining..."
    whole = int(seconds)
    minutes, seconds = divmod(whole, 60)
    return f"About {minutes}:{seconds:02d} remaining"
