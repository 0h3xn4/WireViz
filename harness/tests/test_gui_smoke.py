import pytest

pytest.importorskip("PySide6")
pytestmark = pytest.mark.gui


def test_window_opens(qtbot) -> None:  # type: ignore[no-untyped-def]
    from harness_design_studio.gui.app import create_window
    from harness_design_studio.gui.strings import APP_TITLE

    win = create_window()
    qtbot.addWidget(win)
    win.show()
    assert APP_TITLE in win.windowTitle()
