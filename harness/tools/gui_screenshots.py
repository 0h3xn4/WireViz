# mypy: allow-untyped-calls, no-warn-unused-ignores
"""Render screenshots of the real Qt editor (offscreen) into docs/ux/qt for the UX review."""

import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QPushButton

from harness_design_studio.gui.main_window import MainWindow
from harness_design_studio.gui.theme import ThemeManager

OUT = Path(__file__).resolve().parents[1] / "docs" / "ux" / "qt"
CSV = (
    "Interface,Type,From unit,To unit,Redundancy\nIF-010,Primary power,PCDU,OBC,nominal\n"
    "IF-011,CAN,OBC,RW1,nominal\nIF-012,RS-422,OBC,PCDU,nominal\nIF-013,RS-423,OBC,RW1,nominal\n"
    "IF-TM-RW1,Discrete / bilevel,OBC,PCDU,nominal\nIF-014,Primary power,PCDU,GHOST,nominal\n"
)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    settings = QSettings(str(Path(tempfile.mkdtemp()) / "ui.ini"), QSettings.Format.IniFormat)
    win = MainWindow(settings, ThemeManager(), first_run=False)
    win.ask_choice = lambda t, x, b: 1  # type: ignore[assignment]
    win.resize(1440, 900)
    win.show()

    def shot(name: str, widget: object = None) -> None:
        app.processEvents()
        (widget or win).grab().save(str(OUT / f"{name}.png"))  # type: ignore[attr-defined]
        print(name)

    def btn(name: str) -> QPushButton:
        b = win.findChild(QPushButton, name)
        assert b is not None
        return b

    app.processEvents()
    win.view.fit()
    win.tour.start()
    shot("01-first-run-tour")
    win.tour.stop()
    shot("02-guided-main")
    btn("add-sensor").click()
    btn("type-can").click()
    win.ctl.pick("OBC")
    shot("03-connect-compatible-highlight")
    win.ctl.end_connect()
    win.ctl.set_mode("expert")
    btn("type-power_primary").click()
    shot("04-expert-connectors")
    win.ctl.end_connect()
    win.ctl.select("unit", "RW1")
    shot("05-expert-properties")
    win.ctl.set_mode("guided")
    win.ctl.redundant_copy("RW1")
    win.tabs.setCurrentIndex(0)
    shot("06-redundant-copy-and-problems")
    win.ctl.select("interface", "IF-TM-RW1")
    win.tabs.setCurrentIndex(2)
    shot("07-interface-table")

    def import_dialog(d):  # type: ignore[no-untyped-def]
        d.resize(900, 640)
        d.text.setPlainText(CSV)
        d.show()
        shot("08-import-preview", d)

    win.run_dialog = lambda d: (import_dialog(d), 0)[1]  # type: ignore[assignment,no-untyped-call]
    win.import_flow()
    win.ctl.select("unit", "OBC")

    def delete_dialog(d):  # type: ignore[no-untyped-def]
        d.show()
        shot("09-delete-impact", d)

    win.run_dialog = lambda d: (delete_dialog(d), 0)[1]  # type: ignore[assignment,misc]
    win.delete_btn.click()
    from harness_design_studio.core import checks

    f = checks.open_findings(win.ctl.project)
    cross = next(x for x in f if x.can_waive)

    def waive_dialog(d):  # type: ignore[no-untyped-def]
        d.show()
        d.text.setPlainText("short")
        d.ok.click()
        shot("10-waiver-requires-justification", d)

    win.run_dialog = lambda d: (waive_dialog(d), 0)[1]  # type: ignore[assignment,misc]
    win.waive_flow(cross)

    def palette(d):  # type: ignore[no-untyped-def]
        d.show()
        d.input.setText("conn")
        shot("11-command-palette", d)

    win.run_dialog = lambda d: (palette(d), 0)[1]  # type: ignore[assignment,misc]
    win.open_commands()
    win.act_dark.trigger()
    shot("12-dark-theme")
    win.act_dark.trigger()
    win.scale_actions[150].trigger()
    shot("13-scale-150")
    win.scale_actions[100].trigger()
    win.ctl.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
