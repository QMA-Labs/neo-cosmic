# Cross-platform PyInstaller recipe. Build separately on Windows and Linux.
import sys

a = Analysis(
    ["src/neo/app/main.py"],
    pathex=["src"],
    binaries=[],
    datas=[("src/neo/app/assets", "neo/app/assets")],
    hiddenimports=["mss.windows" if sys.platform == "win32" else "mss.linux"],
    excludes=[
        "PySide6.Qt3DCore",
        "PySide6.QtBluetooth",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtDesigner",
        "PySide6.QtMultimedia",
        "PySide6.QtPdf",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtSql",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
    ],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="NEO",
    console=False,
    onefile=True,
    upx=False,
)
