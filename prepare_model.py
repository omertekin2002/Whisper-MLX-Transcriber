from huggingface_hub import snapshot_download
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "Models" / "whisper-large-v3-mlx"

print(f"Downloading model to: {TARGET}")
TARGET.parent.mkdir(parents=True, exist_ok=True)

snapshot_download(
    repo_id="mlx-community/whisper-large-v3-mlx",
    local_dir=str(TARGET),
    local_dir_use_symlinks=False,
)

print("Done.")
