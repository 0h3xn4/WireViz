"""REQ-OFFLINE-01: the application never touches the network (static and runtime checks)."""

import ast
import os
import subprocess
import sys
import textwrap
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "harness_tool"

BANNED_MODULES = {
    "socket", "ssl", "http", "urllib", "urllib3", "requests", "httpx", "aiohttp",
    "ftplib", "smtplib", "telnetlib", "xmlrpc", "websocket", "websockets", "asyncio",
}  # fmt: skip
BANNED_QT = {"QtNetwork", "QtWebEngineCore", "QtWebEngineWidgets", "QtWebChannel", "QtWebSockets"}


def _imported_names(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{a.name}" for a in node.names)
    return names


def test_no_network_imports_in_source() -> None:
    offenders: list[str] = []
    for path in SRC.rglob("*.py"):
        for name in _imported_names(path):
            parts = name.split(".")
            if parts[0] in BANNED_MODULES or BANNED_QT & set(parts):
                offenders.append(f"{path.relative_to(SRC)}: {name}")
    assert not offenders, offenders


def test_scanner_detects_banned_import(tmp_path: Path) -> None:
    f = tmp_path / "bad.py"
    f.write_text("import socket\nfrom urllib import request\nfrom PySide6.QtNetwork import X\n")
    names = _imported_names(f)
    assert "socket" in names and "urllib" in names and "PySide6.QtNetwork" in names


def test_runtime_sockets_blocked_cli_and_gui() -> None:
    """Run the CLI and an offscreen GUI window with sockets patched to raise."""
    code = textwrap.dedent(
        """
        import socket, sys

        def _blocked(*a, **k):
            raise AssertionError("network access attempted")

        socket.socket = _blocked
        socket.create_connection = _blocked
        socket.getaddrinfo = _blocked

        from harness_tool.cli.main import main
        assert main(["--version"]) == 0

        from harness_tool.gui.app import create_window
        win = create_window()
        win.show()
        assert win.windowTitle()
        banned = [m for m in sys.modules if m.endswith(("QtNetwork", "QtWebEngineCore"))]
        assert not banned, banned
        """
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        capture_output=True, text=True, timeout=120, check=False,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": str(SRC.parent)},
    )  # fmt: skip
    assert result.returncode == 0, result.stdout + result.stderr
