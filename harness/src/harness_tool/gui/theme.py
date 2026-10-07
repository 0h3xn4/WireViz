"""Theme: turns the design tokens into a Qt palette and style sheet (light, dark, UI scale)."""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QApplication

from harness_tool.gui.tokens import DARK, LIGHT, TYPE_SCALE

BASE_PX = TYPE_SCALE["base"]


class ThemeManager(QObject):
    """Holds the current theme and UI scale; widgets that custom-paint listen to `changed`."""

    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.name = "light"
        self.scale = 1.0

    @property
    def tokens(self) -> dict[str, str]:
        return DARK if self.name == "dark" else LIGHT

    def color(self, token: str) -> QColor:
        return QColor(self.tokens[token])

    def px(self, value: float) -> int:
        return max(1, round(value * self.scale))

    def apply(self, app: QApplication, name: str | None = None, scale: float | None = None) -> None:
        if name is not None:
            self.name = "dark" if name == "dark" else "light"
        if scale is not None:
            self.scale = max(1.0, min(2.0, scale))
        font = QFont(app.font())
        font.setPixelSize(self.px(BASE_PX))
        app.setFont(font)
        app.setStyleSheet(stylesheet(self.tokens, self.scale))
        self.changed.emit()


def stylesheet(t: dict[str, str], scale: float) -> str:
    def px(v: float) -> str:
        return f"{max(1, round(v * scale))}px"

    return f"""
QWidget {{ background: {t["bg"]}; color: {t["text"]}; font-size: {px(BASE_PX)}; }}
QMainWindow, QDialog {{ background: {t["bg"]}; }}
QToolBar {{ background: {t["surface"]}; border-bottom: 1px solid {t["border"]}; spacing: {px(4)}; padding: {px(4)}; }}
QMenuBar {{ background: {t["surface"]}; }}
QMenuBar::item:selected, QMenu::item:selected {{ background: {t["primary"]}; color: {t["on-primary"]}; }}
QMenu {{ background: {t["surface"]}; border: 1px solid {t["border"]}; }}
QMenu::item:disabled {{ color: {t["text-muted"]}; }}
QDockWidget {{ border: 1px solid {t["border"]}; }}
QDockWidget::title {{ background: {t["surface"]}; padding: {px(6)}; text-transform: uppercase; }}
QStatusBar {{ background: {t["surface"]}; color: {t["text-muted"]}; border-top: 1px solid {t["border"]}; }}
QStatusBar::item {{ border: none; }}
QPushButton, QToolButton {{ background: {t["surface"]}; border: 1px solid {t["border"]}; border-radius: {px(5)}; padding: {px(3)} {px(10)}; min-height: {px(22)}; }}
QPushButton:hover:enabled, QToolButton:hover:enabled {{ background: {t["surface-2"]}; }}
QPushButton:disabled, QToolButton:disabled {{ color: {t["text-muted"]}; border-color: {t["surface-2"]}; }}
QPushButton[primary="true"] {{ background: {t["primary"]}; color: {t["on-primary"]}; border-color: {t["primary"]}; font-weight: 600; }}
QPushButton[primary="true"]:hover:enabled {{ background: {t["primary"]}; }}
QPushButton[danger="true"] {{ border-color: {t["error"]}; color: {t["error"]}; }}
QToolButton:checked, QPushButton:checked {{ background: {t["primary"]}; color: {t["on-primary"]}; border-color: {t["primary"]}; }}
QPushButton:focus, QToolButton:focus, QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: 2px solid {t["focus"]}; }}
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{ background: {t["bg"]}; border: 1px solid {t["border"]}; border-radius: {px(5)}; padding: {px(3)} {px(6)}; min-height: {px(22)}; }}
QLineEdit[invalid="true"] {{ border: 2px solid {t["error"]}; }}
QComboBox QAbstractItemView {{ background: {t["bg"]}; selection-background-color: {t["primary"]}; selection-color: {t["on-primary"]}; }}
QTabWidget::pane {{ border: 1px solid {t["border"]}; top: -1px; }}
QTabBar::tab {{ background: {t["surface"]}; padding: {px(6)} {px(14)}; border: 1px solid {t["border"]}; border-bottom: none; }}
QTabBar::tab:selected {{ background: {t["bg"]}; font-weight: 600; border-top: 3px solid {t["primary"]}; }}
QTabBar::tab:focus {{ border: 2px solid {t["focus"]}; }}
QTableView, QListWidget {{ background: {t["bg"]}; alternate-background-color: {t["surface"]}; gridline-color: {t["surface-2"]}; selection-background-color: {t["primary"]}; selection-color: {t["on-primary"]}; border: 1px solid {t["border"]}; }}
QHeaderView::section {{ background: {t["surface"]}; color: {t["text-muted"]}; border: 0; border-bottom: 1px solid {t["border"]}; padding: {px(4)}; }}
QScrollArea {{ border: none; }}
QLabel[muted="true"] {{ color: {t["text-muted"]}; }}
QLabel[error="true"] {{ color: {t["error"]}; }}
QLabel[heading="true"] {{ color: {t["text-muted"]}; font-weight: 600; text-transform: uppercase; }}
QFrame[card="true"] {{ background: {t["bg"]}; border: 1px solid {t["border"]}; border-radius: {px(6)}; }}
QFrame[card="true"][severity="warning"] {{ border-left: {px(6)} solid {t["warning"]}; }}
QFrame[card="true"][severity="error"] {{ border-left: {px(6)} solid {t["error"]}; }}
QFrame[card="true"][severity="info"] {{ border-left: {px(6)} solid {t["info"]}; }}
QFrame[banner="true"] {{ background: {t["surface-2"]}; border: 1px solid {t["warning"]}; }}
QToolTip {{ background: {t["surface"]}; color: {t["text"]}; border: 1px solid {t["border"]}; }}
QProgressBar {{ border: 1px solid {t["border"]}; border-radius: {px(5)}; text-align: center; }}
QProgressBar::chunk {{ background: {t["primary"]}; }}
"""
