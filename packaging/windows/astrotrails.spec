# SPDX-License-Identifier: GPL-3.0-or-later
# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for astrotrails.

Produces two single-file executables in dist/:

- astrotrails-<ver>-win64.exe      (GUI, no console window)
- astrotrails-<ver>-win64-cli.exe  (CLI, keeps a console)

The bundled ffmpeg binary from imageio-ffmpeg ships inside each executable,
so end-users do NOT need ffmpeg installed separately.
"""
from pathlib import Path
import imageio_ffmpeg

block_cipher = None
repo_root = Path(SPECPATH).resolve().parents[1]
version = (repo_root / "astrotrails" / "_version.py").read_text().split('"')[1]

# Pull in the imageio-ffmpeg binary so runtime resolution works offline.
ffmpeg_binary = Path(imageio_ffmpeg.get_ffmpeg_exe())
ffmpeg_datas = [(str(ffmpeg_binary), "imageio_ffmpeg/binaries")]

icon = str(repo_root / "packaging" / "assets" / "astrotrails.ico")

# ----------------------------------------------------------------- GUI build
gui_analysis = Analysis(
    [str(repo_root / "astrotrails" / "gui.py")],
    pathex=[str(repo_root)],
    binaries=[],
    datas=ffmpeg_datas,
    hiddenimports=[
        "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets",
        "astrotrails", "astrotrails.cli",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "test"],
    cipher=block_cipher,
)
gui_pyz = PYZ(gui_analysis.pure, gui_analysis.zipped_data, cipher=block_cipher)
gui_exe = EXE(
    gui_pyz,
    gui_analysis.scripts,
    gui_analysis.binaries,
    gui_analysis.datas,
    name=f"astrotrails-{version}-win64",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon,
    disable_windowed_traceback=False,
)

# ----------------------------------------------------------------- CLI build
cli_analysis = Analysis(
    [str(repo_root / "astrotrails" / "cli.py")],
    pathex=[str(repo_root)],
    binaries=[],
    datas=ffmpeg_datas,
    hiddenimports=["astrotrails"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "test", "PyQt6"],
    cipher=block_cipher,
)
cli_pyz = PYZ(cli_analysis.pure, cli_analysis.zipped_data, cipher=block_cipher)
cli_exe = EXE(
    cli_pyz,
    cli_analysis.scripts,
    cli_analysis.binaries,
    cli_analysis.datas,
    name=f"astrotrails-{version}-win64-cli",
    debug=False,
    strip=False,
    upx=False,
    console=True,
    icon=icon,
)
