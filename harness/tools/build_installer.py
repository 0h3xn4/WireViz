"""Build a self-contained, offline package with PyInstaller (one-folder) and archive it.

Ubuntu only (D-110). Build on Ubuntu 22.04 so the package also starts on 24.04 (glibc).
Output: dist/harness-tool-<version>-linux-<arch>.tar.gz
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
            "PySide6.QtPdf", "PySide6.QtSvg", "tkinter",
            # development tools that PyInstaller would otherwise pull in from the build environment
            "mypy", "pydantic.mypy", "hypothesis", "pytest", "_pytest", "lxml", "setuptools",
            "pkg_resources", "attr", "attrs", "pip"]  # fmt: skip
FORBIDDEN = {"mypy", "hypothesis", "pytest", "_pytest", "lxml", "setuptools", "pip", "ruff"}


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
    cmd += [
        "--hidden-import",
        "defusedxml",
    ]  # openpyxl imports it only if present: XML bomb protection
    guide = ROOT / "src" / "harness_tool" / "resources" / "guide"
    cmd += ["--add-data", f"{guide}:harness_tool/resources/guide"]
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
    app = ROOT / "dist" / "harness-tool"
    leaked = sorted(
        p.name for base in (app / "_internal", app / "cli" / "_internal") if base.is_dir()
        for p in base.iterdir() if p.name.split(".")[0] in FORBIDDEN
    )  # fmt: skip
    if leaked:
        print(
            f"error: development tools ended up in the package: {', '.join(leaked)}",
            file=sys.stderr,
        )
        return 1
    from tools.collect_licences import collect

    collect(app / "LICENSES")
    for item in (
        ROOT / "packaging" / "ubuntu"
    ).iterdir():  # install scripts, desktop file, icon, readme
        if item.is_file():
            shutil.copy2(item, ROOT / "dist" / "harness-tool" / item.name)
    system = platform.system().lower()
    base = ROOT / "dist" / f"harness-tool-{__version__}-{system}-{platform.machine().lower()}"
    fmt = "gztar"
    archive = shutil.make_archive(str(base), fmt, root_dir=ROOT / "dist", base_dir="harness-tool")
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
