#!/bin/bash
set -euo pipefail

# Get directory of this script
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$APP_DIR"

# Try to use parent directory for venv, but fallback to local if not writable
VENV_DIR="$APP_DIR/../whisper_mlx_env"
if [ ! -w "$APP_DIR/.." ]; then
    echo "Parent directory not writable, using local venv directory..."
    VENV_DIR="$APP_DIR/whisper_mlx_env"
fi

# --- Environment Setup Check ---

# 1. Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found at $VENV_DIR"
    echo "Attempting to set up environment..."

    # 2. Find Python 3.11+
    PYTHON_CMD=""
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        # Check version
        VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=$(echo $VER | cut -d. -f1)
        MINOR=$(echo $VER | cut -d. -f2)
        if [[ $MAJOR -eq 3 && $MINOR -ge 11 ]]; then
            PYTHON_CMD="python3"
        fi
    fi

    if [ -z "$PYTHON_CMD" ]; then
        echo "❌ Error: Python 3.11+ is required but not found."
        echo "Please install Python 3.11 and try again."
        echo "You can run ./install.sh for an interactive installation helper."
        exit 1
    fi

    echo "Using $PYTHON_CMD..."

    # 3. Create venv
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    echo "Created virtual environment."

    # 4. Install dependencies
    source "$VENV_DIR/bin/activate"
    echo "Installing dependencies..."
    pip install --upgrade pip --quiet
    pip install -r requirements.txt

else
    source "$VENV_DIR/bin/activate"
fi

# 5. Check/Download Model
if [ ! -d "$APP_DIR/Models/whisper-large-v3-mlx" ]; then
    echo "Model not found. Downloading..."
    # We can't actually download 3GB in this sandbox environment probably, and verify it fully
    # But the script logic is what matters.
    # In sandbox, I'll mock this step if I run it.
    echo "Running prepare_model.py (mocking if in test env)"
    if [ "${TEST_ENV:-0}" -eq 1 ]; then
        mkdir -p Models/whisper-large-v3-mlx
        touch Models/whisper-large-v3-mlx/config.json
    else
        python prepare_model.py
    fi
fi

# --- Build ---

# Clean prev build
rm -rf build dist "Whisper MLX Transcriber.spec"

echo "Building app with PyInstaller..."

# Build .app with bundled resources and MLX deps
# Note: We are inside the venv now (or sourced it), so we can use 'pyinstaller' directly
# or use the full path to be safe.
"$VENV_DIR/bin/pyinstaller" \
  --name "Whisper MLX Transcriber" \
  --windowed \
  --clean \
  --add-data "Models:Models" \
  --add-binary "bin/ffmpeg:bin" \
  --hidden-import mlx \
  --hidden-import mlx._reprlib_fix \
  --hidden-import mlx_whisper \
  --hidden-import pydub \
  --collect-all mlx \
  --collect-all mlx_metal \
  --collect-all mlx_whisper \
  --collect-all pydub \
  main.py

# Result: dist/Whisper MLX Transcriber.app

echo "Built app at: $APP_DIR/dist/Whisper MLX Transcriber.app"

# Sign the app ad-hoc (required for Apple Silicon)
echo "Signing app ad-hoc..."
# Check if codesign exists (it won't on linux sandbox)
if command -v codesign &> /dev/null; then
    codesign --force --deep -s - "$APP_DIR/dist/Whisper MLX Transcriber.app"
else
    echo "Warning: 'codesign' not found, skipping signing (normal on Linux/Windows)"
fi
