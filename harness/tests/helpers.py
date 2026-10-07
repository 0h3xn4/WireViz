"""Shared test helpers."""

import json
import shutil
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"
MINI3 = FIXTURES / "projects" / "mini3"


def copy_project(src: Path, dest: Path) -> Path:
    shutil.copytree(src, dest)
    return dest


def edit_json(path: Path, fn: Any) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    result = fn(data)
    path.write_text(json.dumps(data if result is None else result, indent=2), encoding="utf-8")
