# Text2QR Pro

A lightweight Kivy app that splits long text into sequential QR codes. It supports optional zlib + Base64 compression, loading a local text file, navigating generated QR codes, and saving one or all QR images as PNG files.

## Features

- Convert long text into a sequence of QR codes.
- Optional compression (enabled by default).
- Choose the target chunk length.
- Load text from `.txt`, `.md`, or `.py` files.
- Navigate through generated QR codes.
- Save the current QR code or all QR images as PNG files.
- Designed with Kivy for Android and desktop Python environments.

## Requirements

- Python 3.10 or newer recommended
- Kivy
- qrcode with Pillow support

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run on desktop

```bash
python app.py
```

## Android

This project uses Kivy. A common route to build an Android APK is Buildozer on Linux (or an appropriate Linux environment). The Android packaging configuration is not included yet; see the Kivy and Buildozer documentation for platform-specific setup.

The app attempts to save images in a `TextToQR` folder on external storage. Depending on Android version and packaging configuration, storage permissions or a scoped-storage-compatible save flow may be required.

## How the QR chunks work

Each QR contains a prefix such as `1/3|` followed by one chunk of the text payload. When compression is enabled, the payload is UTF-8 text compressed with zlib and encoded with Base64.

**Important:** this repository currently generates QR images only. It does not include a scanner or a decoder that automatically combines scanned chunks back into the original text. To reconstruct compressed text, collect all chunks in order, remove each `index/total|` prefix, concatenate the payload pieces, Base64-decode, zlib-decompress, and decode the result as UTF-8.

The selected chunk length is a target, not a guarantee that every QR payload fits. Large or non-ASCII uncompressed text may exceed QR capacity; use compression or a smaller chunk size if QR generation fails.

## Output

Generated PNG files are saved under `TextToQR` when external storage is available, or in the app's fallback data directory.

## License

This project is currently published without an explicit open-source license. Add a license file if you want to grant others clear permission to reuse, modify, and distribute the code.
