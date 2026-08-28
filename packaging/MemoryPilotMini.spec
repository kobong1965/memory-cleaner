# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path(SPECPATH).parent
source_root = project_root / "src"
assets_root = project_root / "assets"
qml_root = source_root / "memory_pilot" / "ui" / "qml"

a = Analysis(
    [str(source_root / "memory_pilot" / "mini.py")],
    pathex=[str(source_root)],
    binaries=[],
    datas=[
        (str(qml_root), "qml"),
        (str(assets_root / "MemoryPilot.ico"), "assets"),
    ],
    hiddenimports=[
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuickControls2",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "_tkinter"],
    noarchive=False,
    optimize=1,
)
# Qt 6.11 uses the Windows system ICU. A different application's unversioned
# ICU DLL can be discovered through PATH during analysis and must not shadow it.
a.binaries = [
    entry for entry in a.binaries
    if Path(entry[0]).name.casefold() not in {"icuuc.dll", "icudt78.dll"}
]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MemoryPilotMini",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="x86_64",
    codesign_identity=None,
    entitlements_file=None,
    manifest=str(project_root / "packaging" / "app.manifest"),
    icon=str(assets_root / "MemoryPilot.ico"),
)
