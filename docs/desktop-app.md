# Demucs Splitter

## Run from the project

```sh
demucs_env/bin/python -m pip install -r requirements.txt -r requirements_gui.txt
demucs_env/bin/python -m demucs_app
```

The app accepts one MP3, WAV, FLAC, M4A, AAC, or OGG file at a time. The default output root is
`~/Music/Demucs Stems`, and it can be changed with **Choose folder** before starting. Each completed
job is saved in its own timestamped folder and can be opened from the success screen.

## Build the macOS app

```sh
sh tools/build_macos_app.sh
```

The resulting application is at `dist/Demucs Splitter.app` and uses the icon assets stored in
`demucs_app/assets/icons`. The build also bundles `ffmpeg` and `ffprobe` from the current `PATH`, so
both tools must be installed on the build machine. The first use of a model may need an internet
connection so Demucs can download its model weights.
