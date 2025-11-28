#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "Whisper MLX Transcriber - Installation"
echo "=========================================="
echo ""

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ Error: This app only works on macOS"
    exit 1
fi

# Check if running on Apple Silicon
if [[ "$(uname -m)" != "arm64" ]]; then
    echo "❌ Error: This app requires Apple Silicon (M1/M2/M3/M4)"
    echo "   Your system: $(uname -m)"
    exit 1
fi

# Function to check if Homebrew is installed
check_homebrew() {
    if command -v brew &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to install Homebrew
install_homebrew() {
    echo "📦 Homebrew not found. Installing Homebrew..."
    echo "   (This is needed to install Python)"
    echo ""
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    echo "   ✓ Homebrew installed successfully"
}

# Function to install Python
install_python() {
    echo "🐍 Installing Python 3.11..."
    brew install python@3.11
    echo "   ✓ Python 3.11 installed successfully"
}

# Determine python command
PYTHON_CMD="python3"
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
fi

# Check for Python 3.11+
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "⚠️  Python 3 is not installed"
    echo ""
    read -p "Would you like to install Python automatically? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Check if Homebrew is installed
        if ! check_homebrew; then
            install_homebrew
        fi
        install_python
        # Update PYTHON_CMD
        if command -v python3.11 &> /dev/null; then
            PYTHON_CMD="python3.11"
        else
            PYTHON_CMD="python3"
        fi
    else
        echo ""
        echo "❌ Python is required to build this app."
        echo "   Install manually from: https://www.python.org/downloads/"
        echo "   Or run this script again and choose 'y' for automatic installation"
        exit 1
    fi
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 11 ]]; then
    echo "⚠️  Python $PYTHON_VERSION found, but 3.11+ is required"
    echo ""
    read -p "Would you like to install Python 3.11 automatically? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if ! check_homebrew; then
            install_homebrew
        fi
        install_python
        # Update PYTHON_CMD and VERSION after installation
        if command -v python3.11 &> /dev/null; then
            PYTHON_CMD="python3.11"
        else
            PYTHON_CMD="python3"
        fi
        PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    else
        echo ""
        echo "❌ Python 3.11+ is required (found $PYTHON_VERSION)"
        echo "   Install from: https://www.python.org/downloads/"
        exit 1
    fi
fi

echo "✓ Python $PYTHON_VERSION detected using $PYTHON_CMD"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create virtual environment
VENV_DIR="../whisper_mlx_env"
echo ""
echo "[1/4] Creating virtual environment..."
if [[ -d "$VENV_DIR" ]]; then
    echo "   Virtual environment already exists, skipping..."
else
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "   ✓ Virtual environment created at $VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo ""
echo "[2/4] Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "[3/4] Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt --quiet
echo "   ✓ All dependencies installed"

# Download model
echo ""
echo "[4/4] Downloading Whisper Large-v3 model..."
if [[ -d "Models/whisper-large-v3-mlx" ]]; then
    echo "   Model already exists, skipping download..."
else
    echo "   This will download ~2.9GB of data..."
    python prepare_model.py
    echo "   ✓ Model downloaded successfully"
fi

# Build the app
echo ""
echo "=========================================="
echo "Building the app..."
echo "=========================================="
./build_app.sh

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "The app is located at:"
echo "   $SCRIPT_DIR/dist/Whisper MLX Transcriber.app"
echo ""
echo "To install:"
echo "   1. Open Finder"
echo "   2. Navigate to: $SCRIPT_DIR/dist/"
echo "   3. Drag 'Whisper MLX Transcriber.app' to your Applications folder"
echo ""
echo "Or run this command:"
echo "   open dist/"
echo ""
