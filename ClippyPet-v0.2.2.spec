# -*- mode: python ; coding: utf-8 -*-
# onefile 打包：素材与运行时全部打进单个 exe
# settings.json 由程序在运行时写入 exe 旁（APP_DIR = sys.executable 目录）

a = Analysis(
    ['clippy_pet.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ClippyPet-v0.2.2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['clippy.ico'],
)