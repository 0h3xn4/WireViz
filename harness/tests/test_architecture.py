"""REQ-ARCH-01: the headless core must not depend on GUI or CLI code."""

import ast
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "src" / "harness_tool" / "core"
FORBIDDEN_PREFIXES = (
    "harness_tool.gui",
    "harness_tool.cli",
    "PySide6",
    "PyQt5",
    "PyQt6",
    "shiboken",
)


def _imports(path: Path) -> list[str]:
    out: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.append(node.module)
    return out


def test_core_has_no_gui_or_cli_imports() -> None:
    bad = [
        f"{p.name}: {m}"
        for p in CORE.rglob("*.py")
        for m in _imports(p)
        if m.startswith(FORBIDDEN_PREFIXES)
    ]
    assert not bad, bad
