"""Run Demucs Splitter with ``python -m demucs_app``."""

import sys

from demucs_app.services.runtime_paths import configure_runtime_paths


configure_runtime_paths()


def _run_separation_smoke_test(source: str, output_root: str) -> int:
    import json
    from pathlib import Path

    from demucs_app.models import JobOptions, QUALITY_PROFILES
    from demucs_app.services.history import HistoryStore
    from demucs_app.services.separation_runner import SeparationThread

    root = Path(output_root)
    profile = next(profile for profile in QUALITY_PROFILES if profile.key == "fast")
    options = JobOptions(Path(source), "four_stems", profile, "wav")
    outcomes = []
    thread = SeparationThread(
        options,
        HistoryStore(root / "smoke-history.json"),
        output_root=root,
    )
    thread.completed.connect(lambda result: outcomes.append(("completed", result)))
    thread.failed.connect(lambda message, details: outcomes.append(("failed", message, details)))
    thread.cancelled.connect(lambda: outcomes.append(("cancelled",)))
    thread.run()
    if outcomes and outcomes[0][0] == "completed":
        result = outcomes[0][1]
        payload = {
            "status": "completed",
            "output_dir": str(result.output_dir),
            "files": [str(path) for path in result.files],
        }
        exit_code = 0
    else:
        payload = {
            "status": outcomes[0][0] if outcomes else "unknown",
            "message": outcomes[0][1] if outcomes and len(outcomes[0]) > 1 else "",
            "details": outcomes[0][2] if outcomes and len(outcomes[0]) > 2 else "",
        }
        exit_code = 1
    root.mkdir(parents=True, exist_ok=True)
    (root / "smoke-result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return exit_code


def main() -> int:
    if "--self-check" in sys.argv:
        from demucs_app.services.runtime_checks import check_runtime_dependencies

        check_runtime_dependencies()
        return 0
    if "--smoke-separate" in sys.argv:
        index = sys.argv.index("--smoke-separate")
        try:
            source, output_root = sys.argv[index + 1:index + 3]
        except ValueError:
            return 2
        return _run_separation_smoke_test(source, output_root)

    from demucs_app.main_window import MainWindow, create_application

    app = create_application()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
