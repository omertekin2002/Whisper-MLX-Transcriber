#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "Whisper MLX Transcriber - Local Setup"
echo "=========================================="
echo ""

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: this project is built for macOS."
    exit 1
fi

if [[ "$(uname -m)" != "arm64" ]]; then
    echo "Error: MLX requires Apple Silicon."
    echo "Current architecture: $(uname -m)"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

find_python() {
    for candidate in python3.11 python3.12 python3.13 python3; do
        if command -v "$candidate" >/dev/null 2>&1; then
            "$candidate" - <<'PY' >/dev/null 2>&1 && { echo "$candidate"; return 0; }
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
        fi
    done
    return 1
}

PYTHON_CMD="$(find_python || true)"
if [[ -z "$PYTHON_CMD" ]]; then
    echo "Error: Python 3.11+ is required."
    echo "Install it with Homebrew: brew install python@3.12"
    exit 1
fi

PYTHON_VERSION="$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/.venv}"

echo "Using Python $PYTHON_VERSION via $PYTHON_CMD"
echo ""
echo "[1/3] Creating virtual environment"
if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "[2/3] Installing dependencies"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "[3/3] Setup complete"
echo ""
echo "Start the web interface:"
echo "  source .venv/bin/activate"
echo "  python main.py"
echo ""
echo "Optional: download the default model now:"
echo "  python main.py download-model"
echo ""
