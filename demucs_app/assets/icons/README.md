# Demucs macOS app icon

## Concept
One mixed audio signal enters from the left and is separated into four stems on the right:
vocals, drums, bass, and other.

## Included
- `demucs_icon_master_1024.png` — flattened 1024×1024 production master.
- `demucs_icon_default_1024.png`, `dark`, `mono` — appearance previews.
- `AppIcon.appiconset/` — ready to drag into an Xcode asset catalog.
- `Demucs.icns` — legacy macOS icon file (created).
- `demucs_icon_source.svg` — editable vector source.
- `icon_composer_layers/` — three SVG layers for Apple Icon Composer.
- `preview.png` — size and wallpaper preview.

## Xcode
Replace the existing `AppIcon.appiconset` in Assets.xcassets with the included folder,
or copy its PNG files and `Contents.json`.

## Icon Composer
Import the three SVG files in numerical order. Keep the background layer at the back,
the white input/splitter in the middle, and colored stem outputs in front.
Configure Default, Dark, and Mono appearances in Icon Composer.

## Design notes
- No text: remains recognizable at Dock and Finder sizes.
- Standard rounded macOS enclosure with transparent margin and restrained shadow.
- Strong monochrome silhouette; color is secondary rather than required for recognition.
