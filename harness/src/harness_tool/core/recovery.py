"""Autosave journal: the latest state of an open project, kept inside the project folder.

After a crash or power loss the journal holds everything up to the last committed change. It lives
in `<project>/.harness-recovery/` (never outside the project folder, never in logs).
"""

import contextlib
import json
from pathlib import Path

from .errors import SaveError
from .io.canonical import dumps
from .io.fs import atomic_write_bytes, long_path
from .io.layout import serialize
from .io.loader import LoadResult, load_from_files
from .model import Project

JOURNAL_DIR = ".harness-recovery"
JOURNAL_FILE = "session.json"


def journal_path(root: Path | str) -> Path:
    return long_path(Path(root)) / JOURNAL_DIR / JOURNAL_FILE


def write_journal(
    project: Project, root: Path | str, *, base_fingerprint: str | None = None
) -> None:
    files = {rel: data.decode("utf-8") for rel, data in serialize(project).items()}
    payload = {"base_fingerprint": base_fingerprint, "files": files}
    atomic_write_bytes(journal_path(root), dumps(payload), backup=False)


def clear_journal(root: Path | str) -> None:
    path = journal_path(root)
    path.unlink(missing_ok=True)
    with contextlib.suppress(OSError):
        path.parent.rmdir()


def has_journal(root: Path | str) -> bool:
    return journal_path(root).is_file()


def journal_differs_from_disk(root: Path | str) -> bool:
    """True if the journal holds changes that were never saved to the project files."""
    try:
        payload = json.loads(journal_path(root).read_text(encoding="utf-8"))
        base = Path(root)
        disk = serialize(load_from_files(_read_files(base)).project)
        return {k: v.encode() for k, v in payload["files"].items()} != disk
    except (OSError, ValueError, KeyError, TypeError, AttributeError, SaveError):
        return False


def _read_files(base: Path) -> dict[str, object]:
    from .io.loader import read_tree

    parsed, _, _ = read_tree(base)
    return parsed


def read_journal(root: Path | str) -> LoadResult | None:
    """Load the journalled state, or None if there is no usable journal."""
    path = journal_path(root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        files = {rel: json.loads(text) for rel, text in payload["files"].items()}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
    return load_from_files(files)
