"""M7: Ubuntu packaging (D-110): install and uninstall scripts, desktop entry, icon and the .deb."""

import os
import shutil
import subprocess
import xml.etree.ElementTree as ET  # noqa: S405
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PK = ROOT / "packaging" / "ubuntu"


def fake_package(tmp: Path) -> Path:
    """A package folder as build_installer makes it, with stub programs instead of PyInstaller output."""
    pkg = tmp / "harness-tool"
    (pkg / "cli").mkdir(parents=True)
    (pkg / "_internal").mkdir()
    (pkg / "_internal" / "lib.txt").write_text("x")
    for exe in (pkg / "harness-tool", pkg / "cli" / "harness"):
        exe.write_text('#!/bin/sh\necho stub "$@"\n')
        exe.chmod(0o755)
    for item in PK.iterdir():
        if item.is_file():
            shutil.copy2(item, pkg / item.name)
    return pkg


def run_script(script: Path, tmp: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "HARNESS_INSTALL_ROOT": str(tmp / "root"), "HOME": str(tmp / "home")}
    return subprocess.run(
        ["sh", str(script), *args], capture_output=True, text=True, env=env, check=False
    )


def test_install_then_uninstall_leaves_nothing_behind(tmp_path: Path) -> None:
    pkg = fake_package(tmp_path)
    prefix = tmp_path / "opt"
    r = run_script(pkg / "install.sh", tmp_path, "--prefix", str(prefix))
    assert r.returncode == 0, r.stderr
    root = tmp_path / "root"
    assert (
        (prefix / "harness-tool").is_file()
        and (prefix / "cli" / "harness").is_file()
        and (prefix / "_internal" / "lib.txt").is_file()
    )
    link = root / "bin" / "harness-tool"
    assert link.is_symlink() and os.readlink(link) == str(prefix / "harness-tool")
    assert (root / "bin" / "harness").resolve() == (prefix / "cli" / "harness").resolve()
    desktop = (root / "share" / "applications" / "harness-tool.desktop").read_text()
    assert f"Exec={prefix}/harness-tool %f" in desktop and "@" not in desktop
    assert (root / "share" / "icons" / "harness-tool.svg").is_file()
    out = subprocess.run(
        [str(link), "--version"], capture_output=True, text=True, check=True
    ).stdout
    assert "stub" in out
    r = run_script(pkg / "uninstall.sh", tmp_path, "--prefix", str(prefix))
    assert r.returncode == 0 and not prefix.exists()
    assert not list((root).rglob("harness*"))


def test_reinstall_replaces_the_old_version(tmp_path: Path) -> None:
    pkg = fake_package(tmp_path)
    prefix = tmp_path / "opt"
    run_script(pkg / "install.sh", tmp_path, "--prefix", str(prefix))
    (prefix / "_internal" / "stale.txt").write_text("old")
    assert run_script(pkg / "install.sh", tmp_path, "--prefix", str(prefix)).returncode == 0
    assert not (prefix / "_internal" / "stale.txt").exists()


def test_scripts_reject_unknown_options(tmp_path: Path) -> None:
    pkg = fake_package(tmp_path)
    assert run_script(pkg / "install.sh", tmp_path, "--bogus").returncode == 2
    assert run_script(pkg / "uninstall.sh", tmp_path, "--bogus").returncode == 2


def test_desktop_entry_and_icon_are_valid() -> None:
    text = (PK / "harness-tool.desktop.in").read_text()
    for key in (
        "Type=Application",
        "Name=Harness tool",
        "Exec=@EXEC@",
        "Icon=@ICON@",
        "Terminal=false",
        "Categories=",
    ):
        assert key in text
    root = ET.fromstring((PK / "harness-tool.svg").read_text())  # noqa: S314
    assert root.tag.endswith("svg") and root.get("viewBox") == "0 0 64 64"


@pytest.mark.skipif(shutil.which("dpkg-deb") is None, reason="dpkg-deb not installed")
def test_deb_has_the_right_files_and_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    from harness_tool import __version__
    from tools.build_deb import build

    app = fake_package(tmp_path / "src")
    deb = build(app, tmp_path / "out")
    info = subprocess.run(
        ["dpkg-deb", "-I", str(deb)], capture_output=True, text=True, check=True
    ).stdout
    assert "Package: harness-tool" in info and "Architecture: amd64" in info
    assert f"Version: {__version__.replace('rc', '~rc')}" in info and "libxcb-cursor0" in info
    listing = subprocess.run(
        ["dpkg-deb", "-c", str(deb)], capture_output=True, text=True, check=True
    ).stdout
    for path in (
        "./opt/harness-tool/harness-tool",
        "./opt/harness-tool/cli/harness",
        "./usr/bin/harness-tool",
        "./usr/bin/harness",
        "./usr/share/applications/harness-tool.desktop",
        "./usr/share/icons/hicolor/scalable/apps/harness-tool.svg",
    ):
        assert path in listing, path
    assert "root/root" in listing  # owned by root, not by the build user
    again = build(app, tmp_path / "out2")
    assert again.read_bytes() == deb.read_bytes()  # reproducible


def test_container_recipes_are_valid_shell_and_name_the_right_base() -> None:
    cont = PK / "container"
    for script in ("build-in-container.sh", "clean-machine-test.sh"):
        assert (
            subprocess.run(
                ["sh", "-n", str(cont / script)], capture_output=True, check=False
            ).returncode
            == 0
        ), script
    assert "FROM ubuntu:22.04" in (cont / "Dockerfile.build-22.04").read_text()
    assert "--network none" in (cont / "clean-machine-test.sh").read_text()
    for script in ("install.sh", "uninstall.sh"):
        assert (
            subprocess.run(
                ["sh", "-n", str(PK / script)], capture_output=True, check=False
            ).returncode
            == 0
        )


def test_install_refuses_a_folder_without_the_built_program(tmp_path: Path) -> None:
    """Running install.sh from the source folder once left dangling links and reported success."""
    src = tmp_path / "source"
    src.mkdir()
    for item in PK.iterdir():
        if item.is_file():
            shutil.copy2(item, src / item.name)
    r = run_script(src / "install.sh", tmp_path)
    assert r.returncode == 1 and "no built program" in r.stderr
    assert not (tmp_path / "root").exists() and not (tmp_path / "home").exists()
