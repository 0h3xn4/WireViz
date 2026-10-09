"""Pictograms for the diagram: what a link carries and what a connector looks like.

Meaning must be readable at a glance, so it is drawn, not spelled: every kind of link has its own
small picture (a bolt for power, a wave for an analog signal, a bus for CAN, ...), and every family
of connector has its own outline (D-shaped, circular, RJ45, coax) with its pin dots.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF

from harness_design_studio.gui.tokens import style_category

LINK_GLYPH_W = 18.0
LINK_GLYPH_H = 14.0


def _line(p: QPainter, x1: float, y1: float, x2: float, y2: float) -> None:
    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _poly(p: QPainter, pts: list[tuple[float, float]]) -> None:
    p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))


def _path(p: QPainter, pts: list[tuple[float, float]]) -> None:
    path = QPainterPath(QPointF(*pts[0]))
    for x, y in pts[1:]:
        path.lineTo(x, y)
    p.drawPath(path)


# Each picture is drawn in a 18 x 14 box with the pen and brush already set.
def _bolt(p: QPainter) -> None:
    _poly(p, [(10, 0), (3, 8), (8, 8), (6, 14), (15, 5), (10, 5), (13, 0)])


def _ground(p: QPainter) -> None:
    _line(p, 9, 0, 9, 7)
    _line(p, 2, 7, 16, 7)
    _line(p, 5, 10, 13, 10)
    _line(p, 7.5, 13, 10.5, 13)


def _heater(p: QPainter) -> None:
    _path(p, [(0, 7), (3, 7), (5, 1), (8, 13), (11, 1), (14, 13), (15, 7), (18, 7)])


def _can(p: QPainter) -> None:  # a bus with a terminator at each end
    _line(p, 1, 4, 17, 4)
    _line(p, 1, 10, 17, 10)
    _line(p, 1, 2, 1, 12)
    _line(p, 17, 2, 17, 12)


def _diff(p: QPainter) -> None:  # a differential pair: two lines, opposite arrows
    _line(p, 1, 4, 16, 4)
    _line(p, 1, 10, 16, 10)
    _poly(p, [(17, 4), (12, 1), (12, 7)])
    _poly(p, [(1, 10), (6, 7), (6, 13)])


def _multidrop(p: QPainter) -> None:  # a bus with three drops
    _line(p, 1, 4, 17, 4)
    for x in (3, 9, 15):
        _line(p, x, 4, x, 12)
        p.drawEllipse(QPointF(x, 12), 1.6, 1.6)


def _stubs(p: QPainter) -> None:  # a dual bus with stubs
    _line(p, 1, 3, 17, 3)
    _line(p, 1, 6, 17, 6)
    for x in (5, 13):
        _line(p, x, 6, x, 13)


def _network(p: QPainter) -> None:  # a node linked to three more
    _line(p, 9, 7, 2, 2)
    _line(p, 9, 7, 16, 2)
    _line(p, 9, 7, 9, 13)
    p.drawEllipse(QPointF(9, 7), 3, 3)
    for x, y in ((2, 2), (16, 2), (9, 13)):
        p.drawRect(QRectF(x - 1.5, y - 1.5, 3, 3))


def _ethernet(p: QPainter) -> None:  # two boxes joined, the plug shape of RJ45
    p.drawRect(QRectF(1, 3, 6, 8))
    p.drawRect(QRectF(11, 3, 6, 8))
    _line(p, 7, 7, 11, 7)


def _clock(p: QPainter) -> None:  # clock and data
    _path(p, [(1, 5), (4, 5), (4, 1), (8, 1), (8, 5), (11, 5), (11, 1), (15, 1), (15, 5), (17, 5)])
    _path(p, [(1, 13), (6, 13), (6, 9), (13, 9), (13, 13), (17, 13)])


def _sine(p: QPainter) -> None:
    path = QPainterPath(QPointF(0, 7))
    path.cubicTo(3, -2, 6, -2, 9, 7)
    path.cubicTo(12, 16, 15, 16, 18, 7)
    p.drawPath(path)


def _square(p: QPainter) -> None:
    _path(p, [(0, 11), (4, 11), (4, 3), (9, 3), (9, 11), (14, 11), (14, 3), (18, 3)])


def _pyro(p: QPainter) -> None:  # a spark
    _poly(
        p,
        [
            (9, 0),
            (11, 5),
            (17, 3),
            (13, 8),
            (17, 13),
            (11, 11),
            (9, 14),
            (7, 11),
            (1, 13),
            (5, 8),
            (1, 3),
            (7, 5),
        ],
    )


def _thermo(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(7, 0.5, 4, 9), 2, 2)
    p.drawEllipse(QPointF(9, 11), 3, 3)


def _coax(p: QPainter) -> None:  # a ring around a core, with waves
    p.drawEllipse(QPointF(9, 7), 6, 6)
    p.setBrush(p.pen().color())
    p.drawEllipse(QPointF(9, 7), 2, 2)


_GLYPHS = {
    "power_primary": _bolt,
    "power_secondary": _bolt,
    "ground": _ground,
    "heater": _heater,
    "can": _can,
    "rs422": _diff,
    "rs485": _multidrop,
    "mil1553b": _stubs,
    "spacewire": _network,
    "ethernet": _ethernet,
    "lvds": _diff,
    "i2c": _clock,
    "analog": _sine,
    "discrete": _square,
    "pyro": _pyro,
    "thermistor": _thermo,
    "rf_coax": _coax,
}
_BY_CATEGORY = {
    "power": _bolt,
    "ground": _ground,
    "data": _can,
    "analog": _sine,
    "discrete": _square,
    "pyro": _pyro,
    "rf": _coax,
}


def draw_link_glyph(
    p: QPainter, x: float, y: float, type_id: str, category: str, color: QColor, scale: float = 1.0
) -> None:
    """The picture of a kind of link, its top left corner at (x, y)."""
    draw = _GLYPHS.get(type_id) or _BY_CATEGORY.get(style_category(category), _can)
    p.save()
    p.translate(x, y)
    p.scale(scale, scale)
    p.setPen(
        QPen(color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    )
    p.setBrush(QBrush(color) if draw in (_bolt, _pyro) else Qt.BrushStyle.NoBrush)
    draw(p)
    p.restore()


# ---- connectors ------------------------------------------------------------------------------
CONNECTOR_W = 40.0
CONNECTOR_H = 16.0


def _dots(p: QPainter, rect: QRectF, pins: int, filled: bool, ink: QColor, rows: int = 2) -> None:
    """Pin dots in rows inside `rect`: filled for a male (pins), hollow for a female (sockets)."""
    pins = max(pins, 1)
    shown = min(pins, 40 if rows == 2 else 8)
    per = [(shown + 1) // 2, shown // 2] if rows == 2 else [shown]
    r = 1.1 if per[0] <= 9 else 0.85
    p.save()
    p.setBrush(ink if filled else QColor(0, 0, 0, 0))
    p.setPen(QPen(ink, 0.8))
    for k, count in enumerate(per):
        if count == 0:
            continue
        y = rect.top() + rect.height() * (k + 0.5) / len(per)
        for j in range(count):
            p.drawEllipse(QPointF(rect.left() + rect.width() * (j + 0.5) / count, y), r, r)
    p.restore()


def draw_connector(
    p: QPainter, x: float, y: float, family: str, pins: int, gender: str, color: QColor, bg: QColor
) -> None:
    """A connector's outline (30 x 16), its top left corner at (x, y): the family shows in the
    shape, the pin count in the dots, the gender in the whole look: a male (pins) is solid, a female
    (sockets) an outline."""
    p.save()
    p.translate(x, y)
    p.setPen(
        QPen(color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    )
    male = gender == "male"
    p.setBrush(QBrush(color if male else bg))  # a male is drawn solid, a female as an outline
    detail = bg if male else color  # what is drawn inside the shell
    if family == "dsub":  # the tapered D, wide at the top, as wide as its pin count asks
        w = min(40.0, 22.0 + 0.8 * pins)
        x0 = (CONNECTOR_W - w) / 2
        _poly(p, [(x0, 1), (x0 + w, 1), (x0 + w - 4.5, 15), (x0 + 4.5, 15)])
        _dots(p, QRectF(x0 + 6, 3.6, w - 12, 8.8), pins, male, detail)
    elif family == "microd":  # the small, square-shouldered one: a cut bottom and a double rim
        w = min(40.0, 14.0 + 0.8 * pins)
        x0 = (CONNECTOR_W - w) / 2
        _poly(
            p,
            [(x0, 1), (x0 + w, 1), (x0 + w, 11.5), (x0 + w - 3.5, 15), (x0 + 3.5, 15), (x0, 11.5)],
        )
        p.setPen(QPen(detail, 0.7))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(x0 + 2.2, 3.2, w - 4.4, 8.6))
        _dots(p, QRectF(x0 + 3.5, 4.4, w - 7, 6.2), pins, male, detail)
    elif family == "circular":
        p.translate(5, 0)  # a round shell with a key and pins on the ring
        p.drawEllipse(QPointF(15, 8), 7.2, 7.2)
        p.setPen(QPen(color, 1.6))
        _line(p, 15, 0.8, 15, 3)  # the key
        p.setPen(QPen(detail, 1.0))
        p.setBrush(detail if male else QColor(0, 0, 0, 0))
        for k in range(min(max(pins, 3), 8)):
            import math

            a = 2 * math.pi * k / min(max(pins, 3), 8)
            p.drawEllipse(QPointF(15 + 4 * math.sin(a), 8 - 4 * math.cos(a)), 1.0, 1.0)
        p.setPen(QPen(color, 1.6))
        _line(p, 3, 8, 7.8, 8)  # a coupling nut either side
        _line(p, 22.2, 8, 27, 8)
    elif family == "rj45":
        p.translate(5, 0)  # the plug: a box with a latch and a row of contacts
        p.drawRect(QRectF(7, 3, 16, 12))
        p.drawRect(QRectF(11, 0.8, 8, 2.2))
        p.setPen(QPen(detail, 1.0))
        for k in range(8):
            _line(p, 9 + k * 1.7 + 0.5, 6, 9 + k * 1.7 + 0.5, 12)
        p.setPen(QPen(color, 1.6))
        _line(p, 1, 9, 7, 9)
        _line(p, 23, 9, 29, 9)
    elif family == "coax":
        p.translate(5, 0)  # concentric rings, a solid centre pin for a plug
        p.drawEllipse(QPointF(15, 8), 7.2, 7.2)
        p.setPen(QPen(detail, 1.0))
        p.setBrush(detail if male else QColor(0, 0, 0, 0))
        p.drawEllipse(QPointF(15, 8), 2.6, 2.6)
        p.setPen(QPen(color, 1.6))
        _line(p, 1, 8, 7.8, 8)
        _line(p, 22.2, 8, 29, 8)
    else:  # an unknown family: a plain box with its dots
        p.translate(5, 0)
        p.drawRoundedRect(QRectF(1, 1, 28, 14), 3, 3)
        _dots(p, QRectF(5, 4, 20, 8), pins, male, detail)
    p.restore()
