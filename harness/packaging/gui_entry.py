"""PyInstaller entry point. `--selftest` exercises the real editor offscreen and exits (used by CI).

The self-test opens the sample, adds a unit, connects two units, saves to a temp folder, reloads it
and checks the result, so a broken package fails loudly instead of showing an empty window.
"""

import os
import sys
import tempfile
from pathlib import Path

from harness_tool.gui.app import create_window, main


def selftest() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QSettings

    from harness_tool.core.io.loader import load_project

    tmp = Path(tempfile.mkdtemp())
    win = create_window(QSettings(str(tmp / "ui.ini"), QSettings.Format.IniFormat), first_run=False)
    win.show()
    ctl = win.ctl
    uid = ctl.add_unit("sensor")
    ctl.begin_connect("rs422")
    ctl.pick("OBC")
    ctl.pick(uid or "ST1")
    ctl.save_as(tmp / "project")
    loaded = load_project(tmp / "project")
    ok = (
        uid in loaded.project.units
        and len(loaded.project.interfaces) == 3
        and not loaded.has_errors
    )
    ctl.release()
    print("selftest ok" if ok else "selftest FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    raise SystemExit(main())
