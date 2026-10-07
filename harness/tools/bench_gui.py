# mypy: allow-untyped-calls
"""Time editor interactions on a stress-size project (offscreen). Usage: python -m tools.bench_gui"""

import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication

from harness_tool.gui.canvas import DiagramView
from harness_tool.gui.controller import EditorController
from harness_tool.gui.main_window import MainWindow
from harness_tool.gui.theme import ThemeManager
from tools.bench_stress import build


def ms(fn):  # type: ignore[no-untyped-def]
    t = time.perf_counter()
    fn()
    QApplication.processEvents()
    return round((time.perf_counter() - t) * 1000)


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    theme = ThemeManager()
    assert isinstance(app, QApplication)
    theme.apply(app, "light", 1.0)
    from PySide6.QtCore import QSettings

    win = MainWindow(
        QSettings(str(Path(tempfile.mkdtemp()) / "ui.ini"), QSettings.Format.IniFormat),
        theme,
        first_run=False,
    )
    win.resize(1440, 900)
    win.show()
    ctl: EditorController = win.ctl
    view: DiagramView = win.view
    project = build()
    print("install + autoplace", ms(lambda: ctl._install(project, None, None)), "ms")
    print("fit (all 200 units, 2000 links visible)", ms(view.fit), "ms")
    for name, fn in (
        ("select unit", lambda: ctl.select("unit", "U005")),
        ("select other unit", lambda: ctl.select("unit", "U006")),
        ("rename unit name", lambda: ctl.update_unit("U001", name="renamed")),
        ("move unit", lambda: ctl.move_unit("U003", 500, 300)),
        ("add unit", lambda: ctl.add_unit("computer")),
        ("undo", ctl.undo),
        ("redo", ctl.redo),
        ("full repaint (grab)", lambda: view.grab()),
    ):
        print(
            f"{name:28}",
            [ms(fn) for _ in range(3)] if name not in ("add unit", "undo", "redo") else ms(fn),
            "ms",
        )
    win.tabs.setCurrentIndex(0)
    print("problems tab visible: change", ms(lambda: ctl.update_unit("U002", name="x")), "ms")
    win.tabs.setCurrentIndex(2)
    print("table tab visible: change", ms(lambda: ctl.update_unit("U002", name="y")), "ms")
    ctl.release()


if __name__ == "__main__":
    main()
