"""Build a .deb from dist/harness-tool (run tools.build_installer first).
Reproducible: fixed file times (SOURCE_DATE_EPOCH or the last commit), root ownership, xz.
Usage: python -m tools.build_deb"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from harness_tool import __version__

ROOT = Path(__file__).resolve().parents[1]
DEPENDS = "libegl1, libgl1, libxkbcommon0, libxkbcommon-x11-0, libfontconfig1, libdbus-1-3, libxcb-cursor0"


def control(size_kb: int) -> str:
    return (
        "Package: harness-tool\n"
        f"Version: {__version__.replace('rc', '~rc')}\n"
        "Section: science\nPriority: optional\nArchitecture: amd64\n"
        f"Depends: {DEPENDS}\n"
        f"Installed-Size: {size_kb}\n"
        "Maintainer: Harness tool maintainers <noreply@example.invalid>\n"
        "Description: Offline spacecraft electrical harness design tool\n"
        " Designs harnesses from a block diagram, checks them, writes drawings and\n"
        " lists, and keeps a change-controlled record. Never uses the network.\n"
    )


def epoch() -> int:
    if os.environ.get("SOURCE_DATE_EPOCH"):
        return int(os.environ["SOURCE_DATE_EPOCH"])
    out = subprocess.run(
        ["git", "log", "-1", "--format=%ct"], capture_output=True, text=True, check=False, cwd=ROOT
    )
    return (
        int(out.stdout.strip() or 0)
        if out.returncode == 0 and out.stdout.strip()
        else 1_700_000_000
    )


def build(app: Path, out_dir: Path) -> Path:
    stage = Path(tempfile.mkdtemp(prefix="deb-")) / f"harness-tool_{__version__}_amd64"
    opt = stage / "opt" / "harness-tool"
    shutil.copytree(app, opt, symlinks=True)
    (stage / "usr" / "bin").mkdir(parents=True)
    (stage / "usr" / "bin" / "harness-tool").symlink_to("/opt/harness-tool/harness-tool")
    (stage / "usr" / "bin" / "harness").symlink_to("/opt/harness-tool/cli/harness")
    pk = ROOT / "packaging" / "ubuntu"
    apps = stage / "usr" / "share" / "applications"
    apps.mkdir(parents=True)
    (apps / "harness-tool.desktop").write_text(
        (pk / "harness-tool.desktop.in")
        .read_text()
        .replace("@EXEC@", "/usr/bin/harness-tool")
        .replace("@ICON@", "harness-tool")
    )
    icons = stage / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
    icons.mkdir(parents=True)
    shutil.copy(pk / "harness-tool.svg", icons / "harness-tool.svg")
    size_kb = sum(f.stat().st_size for f in stage.rglob("*") if f.is_file()) // 1024
    (stage / "DEBIAN").mkdir()
    (stage / "DEBIAN" / "control").write_text(control(size_kb))
    stamp = epoch()
    for path in [stage, *stage.rglob("*")]:
        os.utime(path, (stamp, stamp), follow_symlinks=False)
        if not path.is_symlink():
            path.chmod(0o755 if path.is_dir() or os.access(path, os.X_OK) else 0o644)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"harness-tool_{__version__}_amd64.deb"
    subprocess.run(
        ["dpkg-deb", "--root-owner-group", "-Zxz", "--build", str(stage), str(target)], check=True
    )
    shutil.rmtree(stage.parent, ignore_errors=True)
    return target


def main() -> int:
    app = ROOT / "dist" / "harness-tool"
    if not (app / "harness-tool").is_file():
        print("run `python -m tools.build_installer` first", file=sys.stderr)
        return 1
    print(build(app, ROOT / "dist"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
