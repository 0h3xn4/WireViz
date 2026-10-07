"""REQ-PERF-01: the editor stays responsive at stress size (200 units, 2,000 interfaces, 20,000 wires).

Bounds are generous (about 3x the targets) so loaded CI machines do not flake; the real numbers
come from `python -m tools.bench_gui` and are recorded in docs/demos/M2.md.
"""

import time

import pytest

from tests.helpers import time_limit

pytestmark = [pytest.mark.gui, pytest.mark.perf]

from PySide6.QtWidgets import QApplication  # noqa: E402

from tests.gui_helpers import make_window  # noqa: E402
from tools.bench_stress import build  # noqa: E402


def elapsed_ms(fn) -> float:  # type: ignore[no-untyped-def]
    t = time.perf_counter()
    fn()
    QApplication.processEvents()
    return (time.perf_counter() - t) * 1000


@pytest.fixture
def stress(qtbot, tmp_path):  # type: ignore[no-untyped-def]
    win = make_window(tmp_path)
    qtbot.addWidget(win)
    win.ctl._install(build(), None, None)
    win.view.fit()
    QApplication.processEvents()
    return win


def test_scene_has_all_items(stress) -> None:  # type: ignore[no-untyped-def]
    assert len(stress.view.dscene.unit_items) == 200 and len(stress.view.dscene.link_items) == 2000


def test_selection_is_fast(stress) -> None:  # type: ignore[no-untyped-def]
    elapsed_ms(lambda: stress.ctl.select("unit", "U005"))  # warm-up
    t = min(elapsed_ms(lambda k=k: stress.ctl.select("unit", f"U0{k:02d}")) for k in range(10, 14))
    assert t < time_limit(150), t


def test_edit_is_responsive(stress) -> None:  # type: ignore[no-untyped-def]
    elapsed_ms(lambda: stress.ctl.update_unit("U001", name="warm"))
    t = min(elapsed_ms(lambda k=k: stress.ctl.update_unit("U001", name=f"n{k}")) for k in range(3))
    assert t < time_limit(400), t


def test_loading_a_stress_project_is_reasonable(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    win = make_window(tmp_path)
    qtbot.addWidget(win)
    t = elapsed_ms(lambda: win.ctl._install(build(), None, None))
    assert t < time_limit(5000), t


def test_problems_panel_is_capped(stress) -> None:  # type: ignore[no-untyped-def]
    from PySide6.QtWidgets import QFrame

    stress.tabs.setCurrentIndex(0)
    QApplication.processEvents()
    cards = [f for f in stress.problems.findChildren(QFrame) if f.property("card")]
    assert 0 < len(cards) <= 25
