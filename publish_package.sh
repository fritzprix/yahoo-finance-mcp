#!/bin/bash
# Publication script for yfin-mcp (Unix/Linux/macOS)
# This script builds and publishes the package to PyPI using uv

echo "========================================"
echo "Publishing yfin-mcp to PyPI"
echo "========================================"
echo ""

# Version bumping logic
BUMP_TYPE=$1
if [[ "$BUMP_TYPE" == "major" || "$BUMP_TYPE" == "minor" || "$BUMP_TYPE" == "patch" ]]; then
    echo "Step 0: Bumping version ($BUMP_TYPE)..."
    uv run scripts/bump_version.py $BUMP_TYPE
    if [ $? -ne 0 ]; then
        echo "[ERROR] Version bump failed."
        exit 1
    fi
    echo ""
fi

echo "Step 1: Cleaning dist directory..."
rm -rf dist/

echo "Step 2: Building package..."
uv build
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Build failed. Aborting."
    exit 1
fi

echo ""
echo "[SUCCESS] Build complete."
echo ""

read -p "Do you want to publish to PyPI now? (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" ]]; then
    echo ""
    echo "[INFO] Publication cancelled by user."
    exit 0
fi

echo ""
echo "Step 3: Publishing to PyPI via twine..."
echo ""
echo "[TIP] PyPI authentication now REQUIRES API tokens."
echo "[TIP] Username: '__token__'"
echo "[TIP] Password: 'pypi-YourTokenHere'"
echo ""

uv pip install twine
uv run twine upload dist/*
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Publication failed."
    echo "[INFO] Make sure your .pypirc is correct or set TWINE_PASSWORD/TWINE_USERNAME variables."
    exit 1
fi

echo ""
echo "[SUCCESS] Package published successfully!"
