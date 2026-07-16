#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

FFMPEG=$(command -v ffmpeg || true)
FFPROBE=$(command -v ffprobe || true)
if [ -z "$FFMPEG" ] || [ -z "$FFPROBE" ]; then
  echo "ffmpeg and ffprobe are required to build Demucs Splitter.app" >&2
  exit 1
fi
FFMPEG=$(realpath "$FFMPEG")
FFPROBE=$(realpath "$FFPROBE")

./demucs_env/bin/pyinstaller \
  --noconfirm \
  --clean \
  --log-level ERROR \
  --windowed \
  --name "Demucs Splitter" \
  --icon "$ROOT/demucs_app/assets/icons/Demucs.icns" \
  --paths "$ROOT" \
  --add-data "$ROOT/demucs_app/assets:demucs_app/assets" \
  --add-binary "$FFMPEG:demucs_app/bin" \
  --add-binary "$FFPROBE:demucs_app/bin" \
  --collect-all demucs \
  --collect-all numpy \
  --collect-all soundfile \
  --collect-all torch \
  --collect-all torchaudio \
  --exclude-module=setuptools \
  --exclude-module=pip \
  --exclude-module=pkg_resources \
  --hidden-import=demucs.remote \
  --hidden-import=numpy.core \
  --hidden-import=numpy.core.multiarray \
  --hidden-import=numpy.core._multiarray_umath \
  demucs_app/__main__.py
