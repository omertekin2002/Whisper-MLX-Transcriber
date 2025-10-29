#!/bin/bash
set -euo pipefail

# Fix code signature issues in the .app bundle
# This script strips and re-signs all binaries with adhoc signatures

APP_PATH="/Users/omertekin/Desktop/MLX_Server/WhisperMLXApp/dist/Whisper MLX Transcriber.app"

if [[ ! -d "$APP_PATH" ]]; then
  echo "Error: App not found at: $APP_PATH" >&2
  exit 1
fi

echo "==> Fixing code signatures for: $APP_PATH"

echo "[1/3] Removing quarantine attributes..."
xattr -cr "$APP_PATH" 2>/dev/null || true

echo "[2/3] Signing all Mach-O binaries..."
find "$APP_PATH/Contents" -type f -exec sh -c '
  if file "$1" 2>/dev/null | grep -q "Mach-O"; then
    codesign -f -s - "$1" 2>&1 | grep -v "replacing existing signature" || true
  fi
' _ {} \;

echo "[3/3] Signing main executable and app bundle..."
codesign -f -s - "$APP_PATH/Contents/MacOS/Whisper MLX Transcriber"
codesign -f -s - "$APP_PATH"

echo "✓ Code signature fix completed!"
echo ""
echo "Verifying signature..."
if codesign --verify --deep --strict "$APP_PATH" 2>&1; then
  echo "✓ Signature verified successfully!"
else
  echo "⚠ Warning: Signature verification failed, but app may still work"
fi
