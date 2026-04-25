# Whisper MLX Transcriber

A local transcription tool for Apple Silicon Macs. It uses Whisper models through MLX and runs as a Python script with a locally hosted web interface.

The app does not send audio to a remote transcription service. Audio is uploaded to the local Python server, processed on your Mac, and removed from the temporary upload folder after the job finishes.

## Requirements

- macOS on Apple Silicon
- Python 3.11 or newer
- Internet access for the first model download
- Optional Hugging Face token for authenticated model downloads
- Enough disk space for Whisper model files
- The bundled `bin/ffmpeg`, or another `ffmpeg` available on `PATH`

## Quick Start

```bash
git clone https://github.com/omertekin2002/Whisper-MLX-Transcriber.git
cd Whisper-MLX-Transcriber
./install.sh
source .venv/bin/activate
python main.py
```

Then open:

```text
http://127.0.0.1:8765
```

The browser usually opens automatically. If it does not, open the URL manually.

## First Transcription

1. Start the server with `python main.py`.
2. Drop an audio file into the browser UI or choose one from the file picker.
3. Pick a model and language.
4. Click `Transcribe`.

If the selected model is not already in `Models/`, it downloads automatically before transcription starts. The default model is `large-v3`, which is several GB. Pick `tiny`, `base`, or `small` for a faster first run.

The web UI includes an optional `HF Token` field. The token is sent only with that transcription request and is used only when a model download is needed. You can leave it empty, but authenticated downloads can avoid rate limits and may be faster.

After a transcription finishes, the server waits 30 seconds for another job. If no new transcription starts in that window, it releases Python and MLX/Metal transcription memory caches.

Supported audio formats depend on FFmpeg. Common formats include MP3, WAV, M4A, M4B, FLAC, OGG, and AAC.

## Common Commands

Start the web interface:

```bash
source .venv/bin/activate
python main.py
```

Start without opening a browser:

```bash
python main.py serve --no-open
```

Use a different port:

```bash
python main.py serve --port 9000
```

List models and whether they are downloaded:

```bash
python main.py models
```

Download the default model ahead of time:

```bash
python main.py download-model
```

Download a specific model:

```bash
python main.py download-model small
```

Download with a Hugging Face token:

```bash
python main.py download-model small --hf-token hf_your_token_here
```

Transcribe from the terminal:

```bash
python main.py transcribe ~/Desktop/audio.m4a --model small --language auto --output transcript.txt
```

You can also provide a token through `HF_TOKEN` or `HUGGING_FACE_HUB_TOKEN` instead of passing `--hf-token`.

Print CLI help:

```bash
python main.py --help
```

## Models

Models are stored in `Models/`, which is ignored by git because the files are large.

Available model choices:

- `tiny`
- `base`
- `small`
- `medium`
- `large-v3`
- `turbo`

The default is `large-v3`.

## Project Layout

```text
main.py          CLI entry point
server.py        FastAPI local web server and transcription job queue
transcriber.py   FFmpeg, model, language, and mlx-whisper integration
prepare_model.py Compatibility wrapper for downloading models
web/             Static browser interface
bin/ffmpeg       Bundled arm64 FFmpeg binary
install.sh       Creates .venv and installs Python dependencies
```

## Cleanup

Remove the local Python environment:

```bash
rm -rf .venv
```

Remove downloaded models:

```bash
rm -rf Models
```

## License

MIT License - see [LICENSE](LICENSE).
