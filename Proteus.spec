# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['proteus\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('proteus.default.ini', '.')],
    hiddenimports=['trieregex'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    Tree('resources', prefix='resources'),
    Tree('profiles', prefix='profiles'),
    Tree('spellchecker', prefix='spellchecker'),
    a.datas,
    [],
    name='Proteus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='resources/themes/light/icons/proteus_logo.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
