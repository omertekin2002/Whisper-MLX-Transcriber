# Whisper MLX Transcriber

A local Apple Silicon transcription tool using Whisper models through MLX. It now runs as a Python script with a locally hosted web interface instead of a packaged desktop app.

## What It Does

- Starts a local browser UI at `http://127.0.0.1:8765`
- Uploads audio to the local Python process
- Downloads selected Whisper MLX models on first use
- Runs transcription locally with `mlx-whisper`
- Lets you copy or download the transcript as text
- Also works from the terminal for one-off transcription jobs

Supported audio formats depend on FFmpeg, with common formats including MP3, WAV, M4A, M4B, FLAC, OGG, and AAC.

## Requirements

- macOS on Apple Silicon
- Python 3.11+
- The bundled `bin/ffmpeg`, or another `ffmpeg` available on `PATH`

## Setup

```bash
git clone https://github.com/omertekin2002/Whisper-MLX-Transcriber.git
cd Whisper-MLX-Transcriber
./install.sh
```

Start the local web interface:

```bash
source .venv/bin/activate
python main.py
```

Then open `http://127.0.0.1:8765` if your browser does not open automatically.

## CLI Usage

List configured models:

```bash
python main.py models
```

Download a model:

```bash
python main.py download-model large-v3
```

Transcribe an audio file:

```bash
python main.py transcribe ~/Desktop/audio.m4a --model large-v3 --language auto --output transcript.txt
```

Start the web server on a different port:

```bash
python main.py serve --port 9000
```

## Models

Models are downloaded into `Models/`, which is intentionally ignored by git because the files are large.

Configured models:

- `tiny`
- `base`
- `small`
- `medium`
- `large-v3`
- `turbo`

The default model is `large-v3`.

## Project Layout

```text
main.py          CLI entry point
server.py        FastAPI local web server and transcription job queue
transcriber.py   FFmpeg, model, language, and mlx-whisper integration
prepare_model.py Compatibility wrapper for downloading models
web/             Static browser interface
bin/ffmpeg       Bundled arm64 FFmpeg binary
```

## Notes

The server keeps transcription jobs in memory. If you restart the process, old job results disappear. Uploaded audio files are copied into a temporary directory while a job runs and removed afterward.

## License

MIT License - see [LICENSE](LICENSE).
