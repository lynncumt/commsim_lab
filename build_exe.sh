#!/usr/bin/env bash
# ── 通信原理仿真软件 — Linux/macOS build helper ─────────────────────────────
set -euo pipefail

echo "=================================================="
echo " 通信原理仿真软件 — Build Script"
echo "=================================================="

# 1. Install deps
echo "[1/3] Installing dependencies..."
pip install -r requirements.txt --quiet

# 2. Clean
echo "[2/3] Cleaning previous build..."
rm -rf build dist

# 3. PyInstaller
echo "[3/3] Running PyInstaller..."
python -m PyInstaller commsim.spec --noconfirm --clean

echo ""
echo "Build complete. Output:"
ls -lh dist/
