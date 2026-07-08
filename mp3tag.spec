# PyInstaller spec — Ramseverywhere MP3 Tag GUI
# Build: python -m PyInstaller mp3tag.spec

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None
root = Path(SPECPATH)

datas = [
    (str(root / "config.yaml"), "."),
    (str(root / "assets" / "app_icon.ico"), "assets"),
]
binaries = []
hiddenimports = ["PIL._tkinter_finder", "tkinter", "tkinter.ttk"]

for pkg in ("customtkinter",):
    tmp = collect_all(pkg)
    datas += tmp[0]
    binaries += tmp[1]
    hiddenimports += tmp[2]

a = Analysis(
    [str(root / "gui.py")],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Ramseverywhere_MP3_Tag",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "assets" / "app_icon.ico") if (root / "assets" / "app_icon.ico").exists() else None,
)