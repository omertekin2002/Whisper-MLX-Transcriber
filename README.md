# Whisper MLX Transcriber

A self-contained macOS transcription app using OpenAI's Whisper Large-v3 model with Apple MLX acceleration. Zero dependencies, zero installation - just download and run.

![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![MLX](https://img.shields.io/badge/MLX-Accelerated-orange)

## Features

- 🚀 **Apple Silicon Optimized** - Leverages MLX for GPU-accelerated inference
- 📦 **Zero Dependencies** - Everything bundled: model, Python runtime, FFmpeg
- 🎯 **High Accuracy** - Uses Whisper Large-v3 (best available model)
- 🖱️ **Drag & Drop** - Simple, intuitive interface
- 📊 **Progress Tracking** - Real-time progress with duration estimation
- 💾 **Export Options** - Copy to clipboard or save as text file
- 🔒 **Privacy First** - 100% offline, no data leaves your machine

## Download Pre-Built App

**[Download Latest Release](../../releases)** (3.7GB)

Simply download the `.app`, drag to Applications, and run. No installation required.

## Building from Source

### One-Command Installation

The easiest way to build the app - just run:

```bash
git clone https://github.com/YOUR_USERNAME/Whisper-MLX-Transcriber.git
cd Whisper-MLX-Transcriber
./install.sh
```

**That's it!** The script will:
- ✅ Check if you have Python 3.11+ (and offer to install it if you don't)
- ✅ Install Homebrew automatically if needed
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Download the Whisper model (~2.9GB)
- ✅ Build the app

**No prior setup needed** - the script handles everything, even if you don't have Python or Homebrew installed.

The built app will be at: `dist/Whisper MLX Transcriber.app`

### Requirements

- **macOS** with Apple Silicon (M1/M2/M3/M4)
- **Git** (comes with Xcode Command Line Tools)

That's all! Python and other dependencies will be installed automatically by the script if needed.

### Manual Setup

If you prefer to install dependencies yourself:

<details>
<summary>Click to expand manual installation steps</summary>

1. **Ensure Python 3.11+ is installed**
```bash
python3 --version  # Should be 3.11 or higher
```

If not installed:
```bash
brew install python@3.11
```

2. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/Whisper-MLX-Transcriber.git
cd Whisper-MLX-Transcriber
```

3. **Create Python virtual environment**
```bash
python3 -m venv ../whisper_mlx_env
source ../whisper_mlx_env/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Download the Whisper model**
```bash
python prepare_model.py
```

This downloads ~2.9GB of model weights to `Models/whisper-large-v3-mlx/`

6. **Build the app**
```bash
./build_app.sh
```

The built app will be at: `dist/Whisper MLX Transcriber.app`

</details>

### FFmpeg Binary

The app includes a static arm64 FFmpeg binary (59MB) that only depends on system frameworks. It's already included in `bin/ffmpeg`.

If you need to update it:
```bash
curl -L "https://ffmpeg.martin-riedl.de/redirect/latest/macos/arm64/release/ffmpeg.zip" -o ffmpeg.zip
unzip ffmpeg.zip && mv ffmpeg bin/ffmpeg && chmod +x bin/ffmpeg && rm ffmpeg.zip
```

## Usage

1. Launch the app
2. Drag an audio file onto the window (or click "Select File")
3. Click "Transcribe"
4. Wait for processing (typically 1.2x audio duration)
5. Copy or save the transcription

**Supported formats:** MP3, WAV, M4A, M4B, FLAC, OGG, AAC

## Performance

- **Speed:** ~0.83x real-time (processes 1 minute of audio in ~50 seconds)
- **Memory:** ~4-5GB peak during transcription
- **GPU:** Fully utilizes Apple Silicon Neural Engine and GPU

## Troubleshooting

### App won't launch

If the app fails to launch silently, run the signature fix:
```bash
./fix_signatures.sh
```

This resolves code signature mismatches between bundled frameworks.

### "App is damaged" warning

macOS Gatekeeper may block unsigned apps. Right-click the app and select "Open" to bypass.

For distribution, use the notarization script:
```bash
./sign_and_notarize.sh
```

(Requires Apple Developer account)

## Architecture

- **UI:** PySide6 (Qt for Python)
- **ML Engine:** MLX Whisper with Metal GPU acceleration
- **Model:** Whisper Large-v3 (32 encoder + 32 decoder layers)
- **Audio:** FFmpeg + pydub/mutagen
- **Packaging:** PyInstaller with custom hooks

## Distribution

The built app is fully self-contained:
- Python 3.11 runtime embedded
- All dependencies bundled (125 dylibs, 260 .so files)
- 100MB Metal shader library for GPU kernels
- 2.9GB Whisper model weights
- 59MB static FFmpeg binary

Total size: 3.7GB

## License

MIT License - see LICENSE file for details

## Credits

- [OpenAI Whisper](https://github.com/openai/whisper) - Original model
- [MLX](https://github.com/ml-explore/mlx) - Apple's ML framework
- [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) - MLX implementation
- [FFmpeg](https://ffmpeg.org/) - Audio processing

## Contributing

Contributions welcome! Please open an issue or PR.

## Support

For issues, questions, or feature requests, please [open an issue](../../issues).
