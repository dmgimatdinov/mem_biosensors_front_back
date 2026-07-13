@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0.."
cd /d "%ROOT%"

where python >nul 2>nul
if errorlevel 1 (
    echo Python 3.11+ is required to build the desktop bundle.
    exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
    echo Node.js 20+ is required to build the frontend assets.
    exit /b 1
)

if not exist "frontend\package.json" (
    echo Missing frontend/package.json
    exit /b 1
)

if not exist "desktop\icons\app.ico" (
    echo Missing desktop/icons/app.ico
    exit /b 1
)

echo [1/6] Building frontend assets...
cd frontend && call npm ci && call npm run build
if errorlevel 1 exit /b 1
cd /d "%ROOT%"

echo [2/6] Installing desktop dependencies...
python -m pip install -r desktop/requirements-desktop.txt
if errorlevel 1 exit /b 1

echo [3/6] Packaging the application with PyInstaller...
pyinstaller desktop/mem_biosensors.spec --clean --noconfirm
if errorlevel 1 exit /b 1

if not exist "dist\mem_biosensors_portable" mkdir "dist\mem_biosensors_portable"
if exist "frontend\out" xcopy /E /I /Y "frontend\out" "dist\mem_biosensors_portable\frontend\"

copy /Y "desktop\README.md" "dist\mem_biosensors_portable\README.txt"
copy /Y "desktop\icons\app.ico" "dist\mem_biosensors_portable\app.ico"

set "APP_EXE=dist\mem_biosensors_portable\MemBiosensors.exe"
if exist "dist\mem_biosensors_portable\MemBiosensors.exe" copy /Y "dist\mem_biosensors_portable\MemBiosensors.exe" "dist\mem_biosensors_portable\mem_biosensors.exe"

set "START_BAT=dist\mem_biosensors_portable\start.bat"
(
    echo @echo off
    echo start "" "%~dp0mem_biosensors.exe"
) > "%START_BAT%"

set "STOP_BAT=dist\mem_biosensors_portable\stop.bat"
(
    echo @echo off
    echo taskkill /f /im mem_biosensors.exe /t >nul 2^>^&1
) > "%STOP_BAT%"

set "UNINSTALL_BAT=dist\mem_biosensors_portable\UNINSTALL.bat"
(
    echo @echo off
    echo rmdir /S /Q "%~dp0data" 2^>nul
    echo rmdir /S /Q "%~dp0logs" 2^>nul
    echo del /Q "%~dp0README.txt" 2^>nul
    echo del /Q "%~dp0start.bat" 2^>nul
    echo del /Q "%~dp0stop.bat" 2^>nul
    echo del /Q "%~dp0UNINSTALL.bat" 2^>nul
    echo del /Q "%~dp0mem_biosensors.exe" 2^>nul
) > "%UNINSTALL_BAT%"

echo [4/6] Packaging archive...
for %%I in (.) do set "CURRENT_DIR=%%~fI"
python -c "from pathlib import Path; import shutil, zipfile, os; root=Path(r'%ROOT%'); dist=root/'dist'/'mem_biosensors_portable'; out=root/'desktop'/'dist'/'MemBiosensors_Portable.zip'; out.parent.mkdir(parents=True, exist_ok=True); shutil.make_archive(str(out.with_suffix('')), 'zip', dist); print(f'Created {out}')"
if errorlevel 1 exit /b 1

echo [5/6] Calculating archive checksum...
python -c "from pathlib import Path; import hashlib; p=Path(r'%ROOT%/desktop/dist/MemBiosensors_Portable.zip'); data=p.read_bytes(); print('SHA256', hashlib.sha256(data).hexdigest())"
if errorlevel 1 exit /b 1

echo Build completed successfully.
