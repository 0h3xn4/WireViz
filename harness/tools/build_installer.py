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


def _pyinstaller(
    name: str, entry: Path, *, windowed: bool, extra_excludes: tuple[str, ...] = ()
) -> int:
    work = ROOT / "build"
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
           "--windowed" if windowed else "--console",
           "--name", name, "--distpath", str(ROOT / "dist"), "--workpath", str(work / name),
           "--specpath", str(work), "--paths", str(ROOT / "src")]  # fmt: skip
    for mod in (*EXCLUDES, *extra_excludes):
        cmd += ["--exclude-module", mod]
    cmd.append(str(entry))
    return subprocess.run(cmd, check=False).returncode


def main() -> int:
    packaging = ROOT / "packaging"
    if _pyinstaller("harness-tool", packaging / "gui_entry.py", windowed=True):
        return 1
    # Console command (validate/check/migrate); no Qt, so it stays small. Shipped inside the folder.
    if _pyinstaller(
        "harness",
        packaging / "cli_entry.py",
        windowed=False,
        extra_excludes=("PySide6", "shiboken6"),
    ):
        return 1
    shutil.copytree(
        ROOT / "dist" / "harness", ROOT / "dist" / "harness-tool" / "cli", dirs_exist_ok=True
    )
    shutil.rmtree(ROOT / "dist" / "harness", ignore_errors=True)
    system = platform.system().lower()
    base = ROOT / "dist" / f"harness-tool-{__version__}-{system}-{platform.machine().lower()}"
    fmt = "zip" if system == "windows" else "gztar"
    archive = shutil.make_archive(str(base), fmt, root_dir=ROOT / "dist", base_dir="harness-tool")
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
