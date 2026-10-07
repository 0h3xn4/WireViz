"""GUI entry point (M0: an empty window)."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

from harness_tool.gui import strings


def create_window() -> QMainWindow:
    if QApplication.instance() is None:
        QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle(strings.APP_TITLE)
    label = QLabel(strings.EMPTY_STATE)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(label)
    window.resize(1200, 800)
    return window


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = create_window()
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
