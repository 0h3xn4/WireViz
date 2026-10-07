"""File-system safety: atomic writes, safe names, long Windows paths, single-instance lock."""

import errno
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import time
import unicodedata
from pathlib import Path
from types import TracebackType

from harness_tool.core.errors import ProjectLockedError, SaveError
from harness_tool.core.ids import RESERVED

LOCK_NAME = ".harness.lock"


def long_path(path: Path) -> Path:
    """On Windows, prefix absolute paths with `\\\\?\\` so paths over 260 characters work."""
    if sys.platform == "win32":
        text = str(path.resolve())
        if not text.startswith("\\\\?\\"):
            prefix = "\\\\?\\UNC\\" if text.startswith("\\\\") else "\\\\?\\"
            return Path(prefix + (text[2:] if text.startswith("\\\\") else text))
    return path


def slug(name: str) -> str:
    """File-name-safe, lower-case grouping name. Only groups files; loading never depends on it."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9_-]+", "-", text).strip("-")
    if not text:
        text = "x" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:8]
    if text.split(".")[0] in RESERVED:
        text = "_" + text
    return text[:60]


def _explain(exc: OSError, path: Path) -> str:
    code = exc.errno
    if code == errno.ENOSPC:
        return f"The disk is full, so '{path.name}' could not be saved."
    if code in (errno.EACCES, errno.EPERM, errno.EROFS):
        return f"The folder is read-only or you lack permission to write '{path.name}'."
    if code == errno.ENAMETOOLONG:
        return f"The path to '{path.name}' is too long for this file system."
    return f"'{path.name}' could not be saved ({exc.strerror or 'file system error'})."


def atomic_write_bytes(path: Path, data: bytes, *, backup: bool = True) -> None:
    """Write via temp file, flush, fsync and rename. A crash never leaves a half-written file."""
    target = long_path(path)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        if backup and target.exists():
            shutil.copyfile(target, target.with_name(target.name + ".bak"))
        os.replace(tmp, target)
        _fsync_dir(target.parent)
    except OSError as exc:
        tmp.unlink(missing_ok=True)
        raise SaveError(_explain(exc, path)) from exc


def _fsync_dir(directory: Path) -> None:
    if sys.platform == "win32":
        return
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:  # some network file systems refuse; the rename itself already succeeded
        pass
    finally:
        os.close(fd)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class ProjectLock:
    """Detects the same project open twice. The lock file holds only pid, host and start time."""

    def __init__(self, root: Path) -> None:
        self.path = long_path(root) / LOCK_NAME
        self._held = False

    def acquire(self) -> None:
        info = {"pid": os.getpid(), "host": platform.node(), "since": int(time.time())}
        for _ in range(2):
            try:
                with open(self.path, "x", encoding="utf-8") as fh:
                    json.dump(info, fh)
                self._held = True
                return
            except FileExistsError:
                if self._is_live_foreign_lock():
                    raise ProjectLockedError(
                        "This project is already open in another instance of the tool. "
                        "Close it there first, or open this copy read-only."
                    ) from None
                self.path.unlink(missing_ok=True)  # stale lock from a crashed session
            except OSError as exc:
                raise SaveError(_explain(exc, self.path)) from exc
        raise ProjectLockedError("Could not take the project lock; try again.")

    def _is_live_foreign_lock(self) -> bool:
        try:
            info = json.loads(self.path.read_text(encoding="utf-8"))
            pid, host = int(info["pid"]), str(info["host"])
        except (OSError, ValueError, KeyError, TypeError):
            return False  # unreadable lock: treat as stale
        if host != platform.node():
            return True  # another machine (shared drive): cannot verify, assume alive
        return _pid_alive(pid)  # includes this very process: a second open must be refused

    def release(self) -> None:
        if self._held:
            self.path.unlink(missing_ok=True)
            self._held = False

    def __enter__(self) -> "ProjectLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.release()
