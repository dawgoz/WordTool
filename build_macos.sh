#!/usr/bin/env bash
# Build a macOS .app bundle of WordTool.
# Run from the project root:
#   chmod +x build_macos.sh
#   ./build_macos.sh

set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Installing dependencies..."
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m pip install -r requirements-dev.txt

echo "Cleaning previous build output..."
rm -rf build dist

echo "Running PyInstaller..."
./.venv/bin/pyinstaller --clean --noconfirm WordTool.spec

echo ""
echo "Build complete."
echo "Launch the app with: open ./dist/WordTool.app"
