# -*- mode: python ; coding: utf-8 -*-
# vim: ft=python

a = Analysis(
    ["accb/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("accb/templates", "accb/templates"),
        ("accb/static", "accb/static"),
        ("schema.sql", "."),
        ("itabuna.json", "."),
        ("ilheus.json", "."),
    ],
    hiddenimports=["engineio.async_drivers.threading"],
    hookspath=["hooks"],
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
    [],
    exclude_binaries=True,
    name="accb-pm",
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
    icon="accb/static/icon.ico",
    uac_admin=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="accb-pm",
)
