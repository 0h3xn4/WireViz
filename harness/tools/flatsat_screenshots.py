# mypy: allow-untyped-calls, no-warn-unused-ignores
"""Pictures of the flatsat example in the real editor (offscreen) for docs/FLATSAT_EXAMPLE.md:
the whole diagram, and the same diagram with one unit in focus. Usage: python -m tools.flatsat_screenshots"""

import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from harness_design_studio.core import templates
from harness_design_studio.gui.main_window import MainWindow
from harness_design_studio.gui.theme import ThemeManager

OUT = Path(__file__).resolve().parents[1] / "docs" / "img"


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    tmp = Path(tempfile.mkdtemp())
    templates.create_project(tmp / "flatsat", "flatsat")
    win = MainWindow(
        QSettings(str(tmp / "ui.ini"), QSettings.Format.IniFormat), ThemeManager(), first_run=False
    )
    win.resize(1500, 950)
    win.show()
    app.processEvents()
    assert win.open_project(tmp / "flatsat")
    app.processEvents()
    win.view.fit()
    app.processEvents()
    win.view.grab().save(str(OUT / "flatsat-overview.png"))
    win.ctl.select("unit", "PDU2")
    app.processEvents()
    win.view.grab().save(str(OUT / "flatsat-focus.png"))
    print("flatsat-overview.png, flatsat-focus.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
