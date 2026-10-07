"""Bundled resources (the offline user guide)."""

import sys
from pathlib import Path


def guide_path() -> Path | None:
    """The bundled user guide (HTML), also inside a PyInstaller build; None if it is missing."""
    roots = [Path(__file__).parent]
    frozen = getattr(sys, "_MEIPASS", None)
    if frozen:
        roots.insert(0, Path(frozen) / "harness_tool" / "resources")
    for root in roots:
        candidate = root / "guide" / "index.html"
        if candidate.is_file():
            return candidate
    return None
