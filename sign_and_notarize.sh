#!/bin/zsh
set -euo pipefail

# Configuration: set these before running
TEAM_ID="YOUR_TEAM_ID"               # e.g. ABCDE12345
APPLE_ID="your-apple-id@example.com" # Apple ID used for notarytool
APP_PASSWORD="@keychain:AC_PASSWORD" # or use a keychain profile via notarytool store-credentials
APP_PATH="/Users/omertekin/Desktop/MLX_Server/WhisperMLXApp/dist/Whisper MLX Transcriber.app"
ENTITLEMENTS="/Users/omertekin/Desktop/MLX_Server/WhisperMLXApp/entitlements.plist"
IDENTITY="Developer ID Application: Your Name (${TEAM_ID})"

if [[ ! -d "$APP_PATH" ]]; then
  echo "App not found at: $APP_PATH" >&2
  exit 1
fi

echo "[1/6] Cleaning extended attributes (quarantine)"
xattr -cr "$APP_PATH" || true

echo "[2/6] Signing nested content"
# Sign helper: function to sign binaries if they exist
sign_if_exists() {
  local target="$1"
  if [[ -e "$target" ]]; then
    echo "  signing: $target"
    codesign --force --options runtime --timestamp \
      --entitlements "$ENTITLEMENTS" \
      --sign "$IDENTITY" "$target"
  fi
}

# Find and sign dylibs, frameworks, executables inside Frameworks and Resources
find "$APP_PATH/Contents" \( -name "*.dylib" -or -name "*.so" -or -perm +111 -type f \) -print0 | while IFS= read -r -d '' f; do
  # Skip non-mach-o files (e.g., text/python files with exec bit)
  if file "$f" | grep -q "Mach-O"; then
    sign_if_exists "$f"
  fi
done

# Explicitly sign the main launcher binary
sign_if_exists "$APP_PATH/Contents/MacOS/Whisper MLX Transcriber"

echo "[3/6] Sign the .app bundle"
codesign --force --options runtime --timestamp \
  --entitlements "$ENTITLEMENTS" \
  --sign "$IDENTITY" "$APP_PATH"

echo "[4/6] Verify code signature"
codesign --verify --deep --strict --verbose=2 "$APP_PATH"
spctl --assess --type execute --verbose "$APP_PATH" || true

echo "[5/6] Notarize with notarytool"
# Create a zip for submission
ZIP_PATH="${APP_PATH%.app}.zip"
rm -f "$ZIP_PATH"
/usr/bin/ditto -c -k --keepParent "$APP_PATH" "$ZIP_PATH"

# Submit for notarization; requires Xcode CLTs and credentials
xcrun notarytool submit "$ZIP_PATH" \
  --apple-id "$APPLE_ID" \
  --team-id "$TEAM_ID" \
  --password "$APP_PASSWORD" \
  --wait

echo "[6/6] Staple the ticket"
xcrun stapler staple "$APP_PATH"
echo "Done."


