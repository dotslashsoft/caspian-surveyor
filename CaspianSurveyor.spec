# -*- mode: python ; coding: utf-8 -*-


core_analysis = Analysis(
    ['caspian_surveyor.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

overlay_analysis = Analysis(
    ['ui/cs_overlay.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

core_pyz = PYZ(core_analysis.pure)
overlay_pyz = PYZ(overlay_analysis.pure)

core_exe = EXE(
    core_pyz,
    core_analysis.scripts,
    [],
    exclude_binaries=True,
    name='CaspianSurveyor',
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
    icon='CaspianSurveyor.ico',
    version='version_info.txt',
)

overlay_exe = EXE(
    overlay_pyz,
    overlay_analysis.scripts,
    [],
    exclude_binaries=True,
    name='CaspianOverlay',
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
    icon='CaspianSurveyor.ico',
    version='version_info.txt',
)

coll = COLLECT(
    core_exe,
    overlay_exe,
    core_analysis.binaries,
    core_analysis.datas,
    overlay_analysis.binaries,
    overlay_analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CaspianSurveyor',
)
