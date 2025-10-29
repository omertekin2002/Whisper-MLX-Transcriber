import sys
import os
import time
from pathlib import Path
from shutil import which
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QFileDialog, QHBoxLayout, QProgressBar
)
from PySide6.QtCore import Qt, QObject, QThread, Signal, QTimer

import mlx_whisper

APP_TITLE = "Whisper MLX Transcriber"
EST_SPEED_FACTOR = 1.2  # estimated processing time = duration * factor (keeps UI under 100% until done)
MIN_EST_SECONDS = 30.0  # if duration probing fails, use at least 30s to drive progress


def resource_path(relative: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative)


def embedded_model_dir() -> str:
    path = resource_path(os.path.join("Models", "whisper-large-v3-mlx"))
    return path


def embedded_ffmpeg_path() -> str | None:
    candidate = Path(resource_path(os.path.join("bin", "ffmpeg")))
    return str(candidate) if candidate.exists() else None


def ensure_ffmpeg_on_path() -> None:
    sys_ffmpeg = which("ffmpeg")
    if sys_ffmpeg:
        sys_dir = os.path.dirname(sys_ffmpeg)
        os.environ["PATH"] = f"{sys_dir}:{os.environ.get('PATH','')}"
        return
    bndl = embedded_ffmpeg_path()
    if bndl:
        bdir = os.path.dirname(bndl)
        os.environ["PATH"] = f"{os.environ.get('PATH','')}:{bdir}"
        return
    raise RuntimeError("ffmpeg not found. Please install via Homebrew: brew install ffmpeg")


def get_audio_duration_seconds(file_path: str) -> float | None:
    # Try pydub (ffmpeg)
    try:
        ensure_ffmpeg_on_path()
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0
    except Exception:
        pass
    # Try mutagen (no ffmpeg)
    try:
        from mutagen import File as MutagenFile
        mf = MutagenFile(file_path)
        if mf is not None and getattr(mf, 'info', None) and getattr(mf.info, 'length', None):
            return float(mf.info.length)
    except Exception:
        pass
    return None


class DropLabel(QLabel):
    def __init__(self, on_file_selected):
        super().__init__("Drop audio file here or click 'Select File'")
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.on_file_selected = on_file_selected
        self.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #888;
                color: #aaa;
                padding: 30px;
                font-size: 16px;
                border-radius: 8px;
            }
            """
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            local_path = urls[0].toLocalFile()
            if local_path:
                self.on_file_selected(local_path)


class TranscribeWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, audio_path: str, model_dir: str):
        super().__init__()
        self.audio_path = audio_path
        self.model_dir = model_dir

    def run(self):
        try:
            ensure_ffmpeg_on_path()
            result = mlx_whisper.transcribe(
                self.audio_path,
                path_or_hf_repo=self.model_dir,
                language=None
            )
            txt = result.get("text", "")
            self.finished.emit(txt)
        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(900, 720)

        self.current_file: str | None = None
        self.thread: QThread | None = None
        self.worker: TranscribeWorker | None = None

        # progress tracking
        self.progress_timer: QTimer | None = None
        self.progress_start_time: float = 0.0
        self.progress_total_seconds: float | None = None

        layout = QVBoxLayout(self)

        title = QLabel("🎙️ Whisper Large‑v3 (MLX) Transcriber")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        self.drop = DropLabel(self.on_file_selected)
        layout.addWidget(self.drop)

        btn_row = QHBoxLayout()
        self.select_btn = QPushButton("📁 Select File")
        self.select_btn.clicked.connect(self.select_file)
        btn_row.addWidget(self.select_btn)

        self.transcribe_btn = QPushButton("▶️ Transcribe")
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.clicked.connect(self.transcribe)
        btn_row.addWidget(self.transcribe_btn)

        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_text)
        btn_row.addWidget(self.copy_btn)

        self.save_btn = QPushButton("💾 Save TXT")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_text)
        btn_row.addWidget(self.save_btn)

        layout.addLayout(btn_row)

        self.status = JLabel = QLabel("Ready")
        self.status.setStyleSheet("color: #666;")
        layout.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text, 1)

    def on_file_selected(self, path: str):
        self.current_file = path
        name = os.path.basename(path)
        self.drop.setText(f"✓ {name}\nClick 'Transcribe' to start")
        self.status.setText(f"Loaded: {name}")
        self.transcribe_btn.setEnabled(True)

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Audio", "", "Audio Files (*.mp3 *.wav *.m4a *.m4b *.flac *.ogg *.aac);;All Files (*.*)")
        if path:
            self.on_file_selected(path)

    def set_busy(self, busy: bool, determinate: bool):
        self.transcribe_btn.setEnabled(not busy)
        self.select_btn.setEnabled(not busy)
        self.copy_btn.setEnabled(False if busy else bool(self.text.toPlainText()))
        self.save_btn.setEnabled(False if busy else bool(self.text.toPlainText()))
        self.progress.setVisible(busy)
        if busy:
            if determinate:
                self.progress.setMinimum(0)
                self.progress.setMaximum(100)
                self.progress.setValue(0)
            else:
                self.progress.setMinimum(0)
                self.progress.setMaximum(0)  # indeterminate
        else:
            self.progress.setMaximum(100)
            self.progress.setValue(100)

    def _cleanup_thread(self):
        if self.thread:
            self.thread.quit()
            self.thread.wait(100)
        self.thread = None
        self.worker = None
        # stop progress timer
        if self.progress_timer:
            self.progress_timer.stop()
            self.progress_timer.deleteLater()
            self.progress_timer = None

    def _tick_progress(self):
        if self.progress_total_seconds is None:
            return
        elapsed = time.time() - self.progress_start_time
        est_total = self.progress_total_seconds * EST_SPEED_FACTOR
        pct = int(min(95, max(1, (elapsed / est_total) * 100)))
        self.progress.setValue(pct)

    def transcribe(self):
        if not self.current_file:
            return
        model_dir = embedded_model_dir()
        if not os.path.isdir(model_dir):
            self.status.setText("Embedded model not found. Please run the Model Prep step.")
            return

        self.text.clear()
        self.text.setPlainText("Processing... this may take a few minutes...\n")

        # determine duration for determinate progress; force determinate with fallback
        dur = get_audio_duration_seconds(self.current_file)
        if dur is None:
            # fallback: use conservative estimate based on file size (~1MB ≈ 60s for speech) capped
            try:
                size_mb = max(1.0, os.path.getsize(self.current_file) / (1024 * 1024))
                dur = max(MIN_EST_SECONDS, min(size_mb * 60.0, 3 * 3600.0))
                self.status.setText("Transcribing… (estimated)")
            except Exception:
                dur = MIN_EST_SECONDS
                self.status.setText("Transcribing… (estimated)")
        else:
            self.status.setText("Transcribing…")

        self.progress_total_seconds = dur
        self.progress_start_time = time.time()
        self.set_busy(True, determinate=True)

        if self.progress_timer is None:
            self.progress_timer = QTimer(self)
            self.progress_timer.timeout.connect(self._tick_progress)
        if not self.progress_timer.isActive():
            self.progress_timer.start(200)

        # worker thread
        self.thread = QThread(self)
        self.worker = TranscribeWorker(self.current_file, model_dir)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_transcribe_done)
        self.worker.failed.connect(self.on_transcribe_error)
        self.worker.finished.connect(self._cleanup_thread)
        self.worker.failed.connect(self._cleanup_thread)
        self.thread.start()

    def on_transcribe_done(self, txt: str):
        self.text.setPlainText(txt)
        self.status.setText("✓ Transcription complete")
        self.copy_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.set_busy(False, determinate=True)

    def on_transcribe_error(self, err: str):
        self.text.setPlainText(f"Error: {err}")
        self.status.setText("Error during transcription")
        self.set_busy(False, determinate=True)

    def copy_text(self):
        QApplication.clipboard().setText(self.text.toPlainText())
        self.status.setText("Copied to clipboard")

    def save_text(self):
        default = "transcript.txt"
        if self.current_file:
            base = Path(self.current_file).stem
            default = f"{base} - Transcript.txt"
        path, _ = QFileDialog.getSaveFileName(self, "Save Transcript", default, "Text Files (*.txt)")
        if path:
            Path(path).write_text(self.text.toPlainText(), encoding="utf-8")
            self.status.setText(f"Saved: {path}")


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
