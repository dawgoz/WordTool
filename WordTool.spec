# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Order Document Filler (Streamlit).

Usage:
    pyinstaller --clean --noconfirm WordTool.spec
"""

import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

datas = []
binaries = []
hiddenimports = []

# Streamlit ships static assets, JS bundles, and dynamic imports that PyInstaller
# cannot discover on its own. `collect_all` grabs them for the packages below.
for pkg in (
    "streamlit",
    "altair",
    "docxtpl",
    "docx",
    "num2words",
    "docx2pdf",
):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# num2words dynamically imports its per-language modules.
hiddenimports += collect_submodules("num2words")

# Ship our own source files so the launcher can find them via `sys._MEIPASS`.
datas += [
    ("app.py", "."),
    ("lt_numbers.py", "."),
    ("pdf_convert.py", "."),
]

# Windows-only extras for docx2pdf (COM automation of Word).
if sys.platform.startswith("win"):
    for pkg in ("win32com", "pywintypes", "pythoncom"):
        try:
            d, b, h = collect_all(pkg)
            datas += d
            binaries += b
            hiddenimports += h
        except Exception:
            pass


a = Analysis(
    ["run_app.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WordTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # keep a console window so startup errors are visible
    disable_windowed_traceback=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="WordTool",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="WordTool.app",
        icon=None,
        bundle_identifier="com.wordtool.app",
        info_plist={
            "CFBundleName": "WordTool",
            "CFBundleDisplayName": "Order Document Filler",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
            # Ensure macOS treats the app as a foreground GUI app, so the
            # Streamlit browser tab and any TCC prompts belong to WordTool.
            "LSUIElement": False,
            "LSBackgroundOnly": False,
            # Reasons shown in macOS permission dialogs. Without these,
            # unsigned apps can be silently denied Automation access.
            "NSAppleEventsUsageDescription": (
                "WordTool uses Microsoft Word to convert your filled "
                "document into a PDF."
            ),
            "NSDesktopFolderUsageDescription": (
                "WordTool needs access to save the generated PDF."
            ),
            "NSDocumentsFolderUsageDescription": (
                "WordTool needs access to save the generated PDF."
            ),
            "NSDownloadsFolderUsageDescription": (
                "WordTool needs access to save the generated PDF."
            ),
        },
    )
