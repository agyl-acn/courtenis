"""
Build a Lambda deployment zip for the booking-agent backend.

Produces booking-agent/dist/lambda.zip whose ROOT contains src/ and all
dependency folders directly (so AWS Lambda can import `src.lambda_handler`).

We're building on Windows but Lambda runs Linux, so dependencies are
installed with cross-platform pip flags targeting the Lambda runtime
(Linux x86_64, CPython 3.12).

Lambda handler: src.lambda_handler.handler

Usage:
    py build_lambda.py
"""

import os
import shutil
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent          # booking-agent/
SRC_DIR = BASE_DIR / "src"
BUILD_DIR = BASE_DIR / "build"
DIST_DIR = BASE_DIR / "dist"
ZIP_PATH = DIST_DIR / "lambda.zip"
# Lambda uses the slim runtime-only requirements (no uvicorn — Mangum replaces it).
REQUIREMENTS = BASE_DIR / "requirements-lambda.txt"

# ─── Lambda runtime target ────────────────────────────────────────
PYTHON_VERSION = "3.12"
PLATFORM = "manylinux2014_x86_64"


def _force_rmtree(path: Path) -> None:
    """
    Delete a tree, clearing read-only flags and retrying — Windows/OneDrive
    can transiently lock or mark files read-only, causing PermissionError.
    """
    def on_error(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    for attempt in range(3):
        try:
            # Python 3.12+ renamed onerror -> onexc; pass both defensively.
            try:
                shutil.rmtree(path, onexc=lambda f, p, e: on_error(f, p, e))
            except TypeError:
                shutil.rmtree(path, onerror=on_error)
            return
        except PermissionError:
            if attempt == 2:
                raise
            time.sleep(1.5)  # let OneDrive/AV release the handle, then retry


def clean() -> None:
    """Remove any previous build/ and dist/lambda.zip for a fresh build."""
    if BUILD_DIR.exists():
        _force_rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    print(f"Clean build dir: {BUILD_DIR}")


def install_dependencies() -> None:
    """
    Install deps into build/ for the Lambda runtime (Linux x86_64, cp312).
    --only-binary=:all: forces manylinux wheels — no source builds that would
    otherwise produce Windows-native artifacts.
    """
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--platform", PLATFORM,
        "--target", str(BUILD_DIR),
        "--implementation", "cp",
        "--python-version", PYTHON_VERSION,
        "--only-binary=:all:",
        "-r", str(REQUIREMENTS),
    ]
    print("Installing dependencies for Lambda runtime...")
    print("  " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def copy_source() -> None:
    """Copy src/ into build/src/ so the package root contains it directly."""
    dest = BUILD_DIR / "src"
    shutil.copytree(
        SRC_DIR,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    print(f"Copied source: {SRC_DIR} -> {dest}")


def build_zip() -> None:
    """Zip the CONTENTS of build/ so the archive root holds src/ + deps."""
    print(f"Zipping -> {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in BUILD_DIR.rglob("*"):
            if path.is_file():
                # arcname is relative to build/, so build/ itself is not nested
                zf.write(path, path.relative_to(BUILD_DIR))


def verify() -> None:
    """Print the zip size and confirm the handler module is inside it."""
    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"\nBuilt {ZIP_PATH}")
    print(f"Size: {size_mb:.2f} MB")

    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = zf.namelist()

    handler_entry = "src/lambda_handler.py"
    if handler_entry in names:
        print(f"OK: {handler_entry} found in zip.")
    else:
        print(f"ERROR: {handler_entry} NOT found in zip!")
        sys.exit(1)

    print(f"Total entries in zip: {len(names)}")
    print("Handler: src.lambda_handler.handler")


def main() -> None:
    clean()
    install_dependencies()
    copy_source()
    build_zip()
    verify()


if __name__ == "__main__":
    main()
