# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

# SPECPATH is provided by PyInstaller and points to the directory
# containing this .spec file.
root = Path(SPECPATH).resolve().parent

block_cipher = None

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "pydantic",
    "sqlalchemy",
    "argon2",
    "argon2.low_level",
    "openpyxl",
    "pandas",
    "reportlab",
    "PyPDF2",
    "python_docx",
    "backend.main",
    "backend.settings",
    "backend.auth",
    "backend.db",
    "backend.services",
    "backend.domain",
]

analysis = Analysis(
    [str(root / "desktop" / "launcher.py")],
    pathex=[str(root), str(root / "backend"), str(root / "desktop")],
    binaries=[],
    datas=[
        (str(root / "backend"), "backend"),
        (str(root / "frontend" / "out"), "frontend"),
        (str(root / "desktop" / "icons" / "app.ico"), "icons"),
        (str(root / "desktop" / "assets" / "banner.txt"), "assets"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "selenium",
        "webdriver_manager",
        "pytest",
        "playwright",
        "google_patents_parser",
        "freq_analysis.commands_templates",
        "tkinter",
        "matplotlib",
    ],
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="MemBiosensors",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "desktop" / "icons" / "app.ico"),
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="mem_biosensors_portable",
)
