#!/bin/bash
set -euo pipefail

APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$APP_DIR"

# Clean prev build
rm -rf build dist "Whisper MLX Transcriber.spec"

# Build .app with bundled resources and MLX deps
"$APP_DIR/../whisper_mlx_env/bin/pyinstaller" \
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

# Fix code signatures to prevent launch issues
echo ""
echo "Fixing code signatures..."
"$APP_DIR/fix_signatures.sh"
