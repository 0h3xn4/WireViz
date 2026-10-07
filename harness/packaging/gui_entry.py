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
    ok = ok and _generate_and_export(ctl, tmp)
    ctl.release()
    print("selftest ok" if ok else "selftest FAILED")
    return 0 if ok else 1


def _generate_and_export(ctl: object, tmp: Path) -> bool:
    """Generate harnesses, build every output type, verify them independently and write them."""
    from harness_tool.core.commands import apply_ops
    from harness_tool.core.generate.engine import plan_generation
    from harness_tool.core.outputs.build import build_outputs, write_outputs
    from harness_tool.core.outputs.verify import read_folder, verify_outputs

    project = ctl.project  # type: ignore[attr-defined]
    apply_ops(project, plan_generation(project).ops)
    built = build_outputs(project)
    if not verify_outputs(project, built.files).ok:
        return False
    write_outputs(project, tmp / "outputs", built)
    return verify_outputs(project, read_folder(tmp / "outputs")).ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    raise SystemExit(main())
