#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python >/dev/null 2>&1; then
  echo "Python 3.11+ is required to build the desktop bundle." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js 20+ is required to build the frontend assets." >&2
  exit 1
fi

echo "[1/6] Building frontend assets..."
(cd frontend && npm ci && npm run build)

echo "[2/6] Installing desktop dependencies..."
python -m pip install -r desktop/requirements-desktop.txt

echo "[3/6] Packaging the application with PyInstaller..."
pyinstaller desktop/mem_biosensors.spec --clean --noconfirm

mkdir -p dist/mem_biosensors_portable
if [ -d frontend/out ]; then
  cp -R frontend/out/. dist/mem_biosensors_portable/frontend/
fi
cp desktop/README.md dist/mem_biosensors_portable/README.txt
cp desktop/icons/app.ico dist/mem_biosensors_portable/app.ico

if [ -f dist/mem_biosensors_portable/MemBiosensors.exe ]; then
  cp dist/mem_biosensors_portable/MemBiosensors.exe dist/mem_biosensors_portable/mem_biosensors.exe
fi

cat > dist/mem_biosensors_portable/start.bat <<'EOF'
@echo off
start "" "%~dp0mem_biosensors.exe"
EOF

cat > dist/mem_biosensors_portable/stop.bat <<'EOF'
@echo off
taskkill /f /im mem_biosensors.exe /t >nul 2>&1
EOF

cat > dist/mem_biosensors_portable/UNINSTALL.bat <<'EOF'
@echo off
rmdir /S /Q "%~dp0data" 2>nul
rmdir /S /Q "%~dp0logs" 2>nul
del /Q "%~dp0README.txt" 2>nul
del /Q "%~dp0start.bat" 2>nul
del /Q "%~dp0stop.bat" 2>nul
del /Q "%~dp0UNINSTALL.bat" 2>nul
del /Q "%~dp0mem_biosensors.exe" 2>nul
EOF

echo "[4/6] Packaging archive..."
python - <<'PY'
from pathlib import Path
import shutil
import hashlib
root = Path.cwd()
dist_dir = root / 'dist' / 'mem_biosensors_portable'
out_zip = root / 'desktop' / 'dist' / 'MemBiosensors_Portable.zip'
out_zip.parent.mkdir(parents=True, exist_ok=True)
shutil.make_archive(str(out_zip.with_suffix('')), 'zip', dist_dir)
print(f'Created {out_zip}')
print('SHA256', hashlib.sha256(out_zip.read_bytes()).hexdigest())
PY
