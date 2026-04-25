from __future__ import annotations

import shutil
import tempfile
import threading
import time
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from transcriber import (
    DEFAULT_MODEL,
    EST_SPEED_FACTOR,
    LANGUAGES,
    MODELS,
    download_model,
    ensure_ffmpeg_on_path,
    estimate_duration_seconds,
    get_model_path,
    is_model_available,
    resolve_language,
    transcribe_audio,
)

APP_DIR = Path(__file__).resolve().parent
WEB_DIR = APP_DIR / "web"
UPLOAD_DIR = Path(tempfile.gettempdir()) / "whisper_mlx_transcriber"


@dataclass
class Job:
    id: str
    filename: str
    model: str
    language: str | None
    created_at: float = field(default_factory=time.time)
    status: str = "queued"
    stage: str = "Waiting"
    progress: int = 0
    started_at: float | None = None
    completed_at: float | None = None
    estimated_seconds: float | None = None
    transcript: str = ""
    error: str | None = None


app = FastAPI(title="Whisper MLX Transcriber", version="2.0.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

_jobs: dict[str, Job] = {}
_jobs_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="transcribe")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(WEB_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/api/config")
def config() -> dict:
    return {
        "defaultModel": DEFAULT_MODEL,
        "models": [
            {
                "name": name,
                "repo": repo,
                "available": is_model_available(name),
                "path": str(get_model_path(name)),
            }
            for name, repo in MODELS.items()
        ],
        "languages": [{"label": label, "code": code or "auto"} for label, code in LANGUAGES.items()],
    }


@app.post("/api/transcriptions")
def create_transcription(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_MODEL),
    language: str = Form("auto"),
) -> dict:
    if model not in MODELS:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model}")

    try:
        language_code = resolve_language(language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = uuid.uuid4().hex
    safe_name = Path(file.filename or "audio").name or "audio"
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    audio_path = job_dir / safe_name

    try:
        with audio_path.open("wb") as target:
            shutil.copyfileobj(file.file, target)
    except Exception:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise
    finally:
        file.file.close()

    job = Job(id=job_id, filename=safe_name, model=model, language=language_code)
    with _jobs_lock:
        _jobs[job_id] = job

    _executor.submit(_run_job, job_id, audio_path)
    return {"jobId": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = _get_job(job_id)
    return _serialize_job(job)


@app.get("/api/jobs/{job_id}/transcript")
def get_transcript(job_id: str) -> PlainTextResponse:
    job = _get_job(job_id)
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="Transcript is not ready")

    stem = Path(job.filename).stem or "transcript"
    headers = {"Content-Disposition": f'attachment; filename="{stem} - Transcript.txt"'}
    return PlainTextResponse(job.transcript, headers=headers)


def run_server(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    import uvicorn

    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{display_host}:{port}"
    print(f"Whisper MLX Transcriber running at {url}", flush=True)

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    uvicorn.run(app, host=host, port=port, log_level="info")


def _run_job(job_id: str, audio_path: Path) -> None:
    _update_job(job_id, status="running", stage="Preparing", started_at=time.time(), progress=2)
    try:
        ensure_ffmpeg_on_path()
        job = _get_job(job_id)

        if not is_model_available(job.model):
            _update_job(job_id, stage=f"Downloading {job.model}", progress=3)
            download_model(job.model)

        estimate = estimate_duration_seconds(audio_path)
        _update_job(job_id, stage="Transcribing", estimated_seconds=estimate, progress=5)
        transcript = transcribe_audio(audio_path, model_name=job.model, language=job.language, download_if_missing=False)
        _update_job(
            job_id,
            status="completed",
            stage="Complete",
            progress=100,
            transcript=transcript,
            completed_at=time.time(),
        )
    except Exception as exc:
        _update_job(
            job_id,
            status="failed",
            stage="Failed",
            progress=100,
            error=str(exc),
            completed_at=time.time(),
        )
    finally:
        shutil.rmtree(audio_path.parent, ignore_errors=True)


def _get_job(job_id: str) -> Job:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _update_job(job_id: str, **changes: object) -> None:
    with _jobs_lock:
        job = _jobs[job_id]
        for key, value in changes.items():
            setattr(job, key, value)


def _serialize_job(job: Job) -> dict:
    progress = job.progress
    if job.status == "running" and job.stage == "Transcribing" and job.started_at and job.estimated_seconds:
        elapsed = time.time() - job.started_at
        projected = max(job.estimated_seconds * EST_SPEED_FACTOR, 1.0)
        progress = max(progress, min(95, int((elapsed / projected) * 100)))

    return {
        "id": job.id,
        "filename": job.filename,
        "model": job.model,
        "language": job.language or "auto",
        "status": job.status,
        "stage": job.stage,
        "progress": progress,
        "createdAt": job.created_at,
        "startedAt": job.started_at,
        "completedAt": job.completed_at,
        "estimatedSeconds": job.estimated_seconds,
        "transcript": job.transcript,
        "error": job.error,
    }
