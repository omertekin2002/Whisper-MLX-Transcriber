from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from shutil import which

MODELS = {
    "tiny": "mlx-community/whisper-tiny-mlx-4bit",
    "base": "mlx-community/whisper-base-mlx-4bit",
    "small": "mlx-community/whisper-small-mlx-4bit",
    "medium": "mlx-community/whisper-medium-mlx-4bit",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "turbo": "mlx-community/whisper-large-v3-turbo-mlx",
}

DEFAULT_MODEL = "large-v3"

LANGUAGES = {
    "Auto-Detect": None,
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Dutch": "nl",
    "Turkish": "tr",
    "Russian": "ru",
    "Japanese": "ja",
    "Chinese": "zh",
    "Korean": "ko",
}

APP_DIR = Path(__file__).resolve().parent
MODEL_DIR = APP_DIR / "Models"
EST_SPEED_FACTOR = 1.2
MIN_EST_SECONDS = 30.0

_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def get_model_path(model_name: str) -> Path:
    _validate_model_name(model_name)
    return MODEL_DIR / f"whisper-{model_name}-mlx"


def is_model_available(model_name: str) -> bool:
    model_path = get_model_path(model_name)
    return model_path.is_dir() and any(model_path.iterdir())


def download_model(model_name: str, hf_token: str | None = None) -> Path:
    _validate_model_name(model_name)

    from huggingface_hub import snapshot_download

    target_dir = get_model_path(model_name)
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading '{model_name}' from {MODELS[model_name]}")
    snapshot_download(repo_id=MODELS[model_name], local_dir=str(target_dir), token=_resolve_hf_token(hf_token))
    return target_dir


def ensure_model(model_name: str, download_if_missing: bool = True, hf_token: str | None = None) -> Path:
    model_path = get_model_path(model_name)
    if is_model_available(model_name):
        return model_path
    if not download_if_missing:
        raise FileNotFoundError(f"Model '{model_name}' is not downloaded. Run: python main.py download-model {model_name}")
    return download_model(model_name, hf_token=hf_token)


def resolve_language(language: str | None) -> str | None:
    if language is None:
        return None

    normalized = language.strip().lower()
    if not normalized or normalized == "auto":
        return None

    known_codes = {code for code in LANGUAGES.values() if code}
    if normalized in known_codes:
        return normalized

    for label, code in LANGUAGES.items():
        key = label.lower().replace(" ", "-")
        if normalized == key:
            return code

    raise ValueError(f"Unsupported language '{language}'")


def embedded_ffmpeg_path() -> Path | None:
    candidate = APP_DIR / "bin" / "ffmpeg"
    return candidate if candidate.exists() else None


def ensure_ffmpeg_on_path() -> Path:
    system_ffmpeg = which("ffmpeg")
    if system_ffmpeg:
        _prepend_path(Path(system_ffmpeg).parent)
        return Path(system_ffmpeg)

    bundled = embedded_ffmpeg_path()
    if bundled:
        _prepend_path(bundled.parent)
        return bundled

    raise RuntimeError("ffmpeg not found. Install ffmpeg or keep the bundled bin/ffmpeg in this repo.")


def get_audio_duration_seconds(file_path: str | Path) -> float | None:
    path = Path(file_path)
    duration = _duration_from_mutagen(path)
    if duration is not None:
        return duration
    return _duration_from_ffmpeg(path)


def estimate_duration_seconds(file_path: str | Path) -> float:
    duration = get_audio_duration_seconds(file_path)
    if duration is not None:
        return duration

    try:
        size_mb = max(1.0, Path(file_path).stat().st_size / (1024 * 1024))
        return max(MIN_EST_SECONDS, min(size_mb * 60.0, 3 * 3600.0))
    except OSError:
        return MIN_EST_SECONDS


def transcribe_audio(
    audio_path: str | Path,
    model_name: str = DEFAULT_MODEL,
    language: str | None = None,
    download_if_missing: bool = True,
    hf_token: str | None = None,
) -> str:
    path = Path(audio_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    ensure_ffmpeg_on_path()
    model_path = ensure_model(model_name, download_if_missing=download_if_missing, hf_token=hf_token)
    language_code = resolve_language(language)

    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(path),
        path_or_hf_repo=str(model_path),
        language=language_code,
    )
    return result.get("text", "").strip()


def _duration_from_mutagen(path: Path) -> float | None:
    try:
        from mutagen import File as MutagenFile

        media = MutagenFile(path)
        if media is not None and getattr(media, "info", None):
            length = getattr(media.info, "length", None)
            if length:
                return float(length)
    except Exception:
        return None
    return None


def _duration_from_ffmpeg(path: Path) -> float | None:
    try:
        ffmpeg = ensure_ffmpeg_on_path()
        proc = subprocess.run(
            [str(ffmpeg), "-hide_banner", "-i", str(path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
    except Exception:
        return None

    match = _DURATION_RE.search(proc.stderr + proc.stdout)
    if not match:
        return None

    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _prepend_path(directory: Path) -> None:
    directory = directory.resolve()
    entries = [Path(item).resolve() for item in os.environ.get("PATH", "").split(os.pathsep) if item]
    if directory not in entries:
        os.environ["PATH"] = f"{directory}{os.pathsep}{os.environ.get('PATH', '')}"


def _resolve_hf_token(hf_token: str | None) -> str | None:
    token = (hf_token or "").strip()
    if token:
        return token

    for env_name in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        token = os.environ.get(env_name, "").strip()
        if token:
            return token
    return None


def _validate_model_name(model_name: str) -> None:
    if model_name not in MODELS:
        available = ", ".join(sorted(MODELS))
        raise ValueError(f"Unknown model '{model_name}'. Available models: {available}")
