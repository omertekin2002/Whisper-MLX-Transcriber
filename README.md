# Whisper MLX Transcriber

A self-contained macOS transcription app using OpenAI's Whisper Large-v3 model with Apple MLX acceleration.

## Features

Apple Silicon optimized with MLX for GPU-accelerated inference. The app is completely self-contained with the model, Python runtime, and FFmpeg bundled. Uses Whisper Large-v3 for high accuracy transcription. Simple drag and drop interface with real-time progress tracking. Export transcriptions to clipboard or save as text files. All processing happens locally on your machine with no internet connection required.

## Download

**[Download Whisper MLX Transcriber v1.0.0](https://drive.google.com/file/d/1JqbpoPmQIRNWqEBWyZahuJ1Eg_4ZgH9N/view?usp=sharing)** (3.7GB)

Download the DMG file, open it, and drag the app to your Applications folder. No installation or dependencies required.

## Building from Source

### Quick Setup

```bash
git clone https://github.com/omertekin2002/Whisper-MLX-Transcriber.git
cd Whisper-MLX-Transcriber
./install.sh
```

The script will check for Python 3.11+ and offer to install it along with Homebrew if needed. It then creates a virtual environment, installs dependencies, downloads the Whisper model (2.9GB), and builds the app.

The built app will be at: `dist/Whisper MLX Transcriber.app`

### Requirements

macOS with Apple Silicon and Git (comes with Xcode Command Line Tools). Python and other dependencies will be installed automatically by the script if needed.

### Manual Setup

<details>
<summary>Click to expand manual installation steps</summary>

Ensure Python 3.11+ is installed:
```bash
python3 --version  # Should be 3.11 or higher
```

If not installed:
```bash
brew install python@3.11
```

Clone the repository:
```bash
git clone https://github.com/omertekin2002/Whisper-MLX-Transcriber.git
cd Whisper-MLX-Transcriber
```

Create Python virtual environment:
```bash
python3 -m venv ../whisper_mlx_env
source ../whisper_mlx_env/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Download the Whisper model (2.9GB):
```bash
python prepare_model.py
```

Build the app:
```bash
./build_app.sh
```

The built app will be at: `dist/Whisper MLX Transcriber.app`

</details>

### FFmpeg Binary

The app includes a static arm64 FFmpeg binary (59MB) that only depends on system frameworks. It's already included in `bin/ffmpeg`.

To update it:
```bash
curl -L "https://ffmpeg.martin-riedl.de/redirect/latest/macos/arm64/release/ffmpeg.zip" -o ffmpeg.zip
unzip ffmpeg.zip && mv ffmpeg bin/ffmpeg && chmod +x bin/ffmpeg && rm ffmpeg.zip
```

## Usage

Launch the app and drag an audio file onto the window or click "Select File". Click "Transcribe" and wait for processing, which typically takes 1.2x the audio duration. Copy the transcription to clipboard or save as a text file.

Supported formats: MP3, WAV, M4A, M4B, FLAC, OGG, AAC

## Performance

Processes audio at approximately 0.83x real-time speed (1 minute of audio in about 50 seconds). Peak memory usage is around 4-5GB during transcription. Fully utilizes Apple Silicon Neural Engine and GPU.

## Troubleshooting

### App won't launch

If the app fails to launch, run the signature fix:
```bash
./fix_signatures.sh
```

This resolves code signature mismatches between bundled frameworks.

### "App is damaged" warning

macOS Gatekeeper may block unsigned apps. Right-click the app and select "Open" to bypass the warning on first launch.

For distribution, use the notarization script (requires Apple Developer account):
```bash
./sign_and_notarize.sh
```

## Architecture

Built with PySide6 (Qt for Python) for the UI. Uses MLX Whisper with Metal GPU acceleration for inference. The model is Whisper Large-v3 with 32 encoder and 32 decoder layers. Audio processing handled by FFmpeg, pydub, and mutagen. Packaged with PyInstaller using custom hooks.

## Distribution

The built app is fully self-contained with Python 3.11 runtime embedded, all dependencies bundled (125 dylibs, 260 .so files), 100MB Metal shader library for GPU kernels, 2.9GB Whisper model weights, and 59MB static FFmpeg binary. Total size is 3.7GB.

## License

MIT License - see LICENSE file for details

## Credits

[OpenAI Whisper](https://github.com/openai/whisper) - Original model  
[MLX](https://github.com/ml-explore/mlx) - Apple's ML framework  
[mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) - MLX implementation  
[FFmpeg](https://ffmpeg.org/) - Audio processing

## Contributing

Contributions welcome. Please open an issue or pull request.

## Support

For issues, questions, or feature requests, please [open an issue](../../issues).
