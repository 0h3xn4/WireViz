"""Build a self-contained, offline package with PyInstaller (one-folder) and archive it.

Run once per target OS (build on the oldest supported Linux for glibc compatibility).
Output: dist/harness-tool-<version>-<platform>.(zip|tar.gz)
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path

from harness_tool import __version__

ROOT = Path(__file__).resolve().parents[1]
EXCLUDES = ["PySide6.QtNetwork", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
            "PySide6.QtWebChannel", "PySide6.QtWebSockets", "PySide6.QtQml", "PySide6.QtQuick",
            "PySide6.QtPdf", "PySide6.QtSvg", "tkinter"]  # fmt: skip


def main() -> int:
    entry = ROOT / "packaging" / "gui_entry.py"
    work = ROOT / "build"
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
           "--name", "harness-tool", "--distpath", str(ROOT / "dist"), "--workpath", str(work),
           "--specpath", str(work), "--paths", str(ROOT / "src")]  # fmt: skip
    for mod in EXCLUDES:
        cmd += ["--exclude-module", mod]
    cmd.append(str(entry))
    if subprocess.run(cmd, check=False).returncode:
        return 1
    system = platform.system().lower()
    base = ROOT / "dist" / f"harness-tool-{__version__}-{system}-{platform.machine().lower()}"
    fmt = "zip" if system == "windows" else "gztar"
    archive = shutil.make_archive(str(base), fmt, root_dir=ROOT / "dist", base_dir="harness-tool")
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
