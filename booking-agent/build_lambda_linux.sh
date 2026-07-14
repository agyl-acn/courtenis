#!/usr/bin/env bash
#
# Build the Lambda deployment zip on Linux (AWS CloudShell / Amazon Linux).
#
# Why Linux: mcp depends on `pywin32; sys_platform == "win32"`. Building on
# Windows for a Linux target fails because pip's --platform flag does not
# override environment-marker evaluation. On Linux the marker is false, so a
# plain `pip install` resolves the whole tree with native wheels — no hacks.
#
# Produces booking-agent/dist/lambda.zip whose ROOT contains src/ + deps
# directly, so Lambda can import `src.lambda_handler.handler`.
#
# Usage (from the booking-agent/ directory):
#   bash build_lambda_linux.sh

set -euo pipefail

# ─── Paths ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
DIST_DIR="$SCRIPT_DIR/dist"
ZIP_PATH="$DIST_DIR/lambda.zip"
REQUIREMENTS="$SCRIPT_DIR/requirements-lambda.txt"

# Packages the Lambda Python runtime already provides — never bundle them.
RUNTIME_PROVIDED=(boto3 botocore s3transfer jmespath)

# ─── 1. Clean build dir + old zip ─────────────────────────────────
echo "==> Cleaning build directory"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"
rm -f "$ZIP_PATH"

# ─── 2. Install dependencies (plain install — we're on Linux) ─────
echo "==> Installing dependencies into build/"
python3 -m pip install -r "$REQUIREMENTS" --target "$BUILD_DIR"

# ─── 3. Strip runtime-provided packages (safety net) ──────────────
echo "==> Stripping runtime-provided packages"
for pkg in "${RUNTIME_PROVIDED[@]}"; do
    rm -rf "$BUILD_DIR/$pkg"
    rm -rf "$BUILD_DIR/$pkg"-*.dist-info
done

# ─── 4. Copy source ───────────────────────────────────────────────
echo "==> Copying src/ into build/"
cp -r "$SCRIPT_DIR/src" "$BUILD_DIR/src"
# Drop any local __pycache__ that slipped in
find "$BUILD_DIR/src" -type d -name __pycache__ -prune -exec rm -rf {} +

# ─── 5. Zip contents of build/ (src/ at the archive root) ─────────
echo "==> Zipping -> $ZIP_PATH"
( cd "$BUILD_DIR" && zip -qr "$ZIP_PATH" . )

# ─── 6. Report ────────────────────────────────────────────────────
SIZE="$(du -h "$ZIP_PATH" | cut -f1)"
echo ""
echo "Built $ZIP_PATH"
echo "Size: $SIZE"
if unzip -l "$ZIP_PATH" | grep -q "src/lambda_handler.py"; then
    echo "OK: src/lambda_handler.py found in zip."
else
    echo "ERROR: src/lambda_handler.py NOT found in zip!" >&2
    exit 1
fi
echo "Handler: src.lambda_handler.handler"
