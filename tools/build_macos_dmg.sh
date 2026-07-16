#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
APP_NAME="Demucs Splitter.app"
APP_PATH="$ROOT/dist/$APP_NAME"
OUTPUT_DIR="$ROOT/release"
DMG_PATH="$OUTPUT_DIR/Demucs-Splitter-macOS-arm64.dmg"
STAGING_DIR=$(mktemp -d "${TMPDIR:-/tmp}/demucs-splitter-dmg.XXXXXX")

cleanup() {
  rm -rf "$STAGING_DIR"
}
trap cleanup EXIT HUP INT TERM

if [ "${SKIP_APP_BUILD:-0}" != "1" ]; then
  sh "$ROOT/tools/build_macos_app.sh"
fi

if [ ! -d "$APP_PATH" ]; then
  echo "$APP_PATH does not exist. Build the macOS app first." >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
cp -R "$APP_PATH" "$STAGING_DIR/$APP_NAME"
ln -s /Applications "$STAGING_DIR/Applications"

hdiutil create \
  -volname "Demucs Splitter" \
  -srcfolder "$STAGING_DIR" \
  -format UDZO \
  -ov \
  "$DMG_PATH"

echo "Created $DMG_PATH"
