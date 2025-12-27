from huggingface_hub import snapshot_download
from pathlib import Path
import sys

MODELS = {
    "tiny": "mlx-community/whisper-tiny-mlx-4bit",
    "base": "mlx-community/whisper-base-mlx-4bit",
    "small": "mlx-community/whisper-small-mlx-4bit",
    "medium": "mlx-community/whisper-medium-mlx-4bit",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "turbo": "mlx-community/whisper-large-v3-turbo-mlx",
}

DEFAULT_MODEL = "large-v3"

def get_model_path(model_name: str) -> Path:
    base_dir = Path(__file__).resolve().parent / "Models"
    return base_dir / f"whisper-{model_name}-mlx"

def download_model(model_name: str):
    if model_name not in MODELS:
        print(f"Error: Model '{model_name}' not found. Available models: {', '.join(MODELS.keys())}")
        return False
    
    repo_id = MODELS[model_name]
    target_dir = get_model_path(model_name)
    
    print(f"Downloading model '{model_name}' to: {target_dir}")
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )
        print(f"Done downloading '{model_name}'.")
        return True
    except Exception as e:
        print(f"Error downloading model: {e}")
        return False

if __name__ == "__main__":
    model = DEFAULT_MODEL
    if len(sys.argv) > 1:
        model = sys.argv[1]
    
    download_model(model)
