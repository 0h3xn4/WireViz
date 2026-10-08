"""Block-diagram canvas: zone lanes, unit boxes, interface links, minimap."""

import math

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QLabel,
    QStyleOptionGraphicsItem,
    QToolTip,
    QWidget,
)

from harness_tool.core import edit
from harness_tool.gui import strings
from harness_tool.gui.controller import Delta, EditorController
from harness_tool.gui.theme import ThemeManager
from harness_tool.gui.tokens import CATEGORIES, style_category

W = edit.UNIT_W
HEADER_H = 30
PORT_ROW = 22
GRID = 10


def facing_side(lane: int, lanes: int) -> str:
    """Connectors sit on the edge that faces the middle of the diagram."""
    return "right" if lane <= (lanes - 1) // 2 else "left"


class UnitItem(QGraphicsItem):
    def __init__(self, scene: "DiagramScene", unit_id: str) -> None:
        super().__init__()
        self.dscene = scene
        self.unit_id = unit_id
        self._press_pos: QPointF | None = None
        self._moved = False
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setZValue(2)

    # ---- geometry ---------------------------------------------------------------------------
    @property
    def ctl(self) -> EditorController:
        return self.dscene.ctl

    def connectors(self) -> list:  # type: ignore[type-arg]
        return edit.unit_connectors(self.ctl.project, self.unit_id)

    def height(self) -> float:
        if self.ctl.mode == "expert":
            return 46 + PORT_ROW * len(self.connectors())
        n = len(self.dscene.adjacent(self.unit_id))
        return 70 + 14 * max(0, n - 2)

    def lane(self) -> int:
        return edit.lane_index(self.dscene.zone_count, self.pos().x())

    def side(self) -> str:
        return facing_side(self.lane(), self.dscene.zone_count)

    def boundingRect(self) -> QRectF:
        return QRectF(-14, -30, W + 28, self.height() + 70)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(QRectF(-8, 0, W + 16, self.height()))
        return path

    def port_y(self, index: int) -> float:
        return 46 + index * PORT_ROW + PORT_ROW / 2 - 4

    def port_rect(self, index: int) -> QRectF:
        x = W - 7 if self.side() == "right" else -7
        return QRectF(x, self.port_y(index) - 7, 14, 14)

    def port_at(self, pos: QPointF) -> str | None:
        if self.ctl.mode != "expert":
            return None
        for k, c in enumerate(self.connectors()):
            if self.port_rect(k).adjusted(-6, -4, 6, 4).contains(pos) or QRectF(
                0, self.port_y(k) - 11, W, 22
            ).contains(pos):
                return str(c.id)
        return None

    def anchor(self, connector_id: str | None, interface_id: str) -> QPointF:
        x = self.pos().x() + (W if self.side() == "right" else 0)
        h = self.height()
        if self.ctl.mode == "expert" and connector_id is not None:
            ids = [c.id for c in self.connectors()]
            if connector_id in ids:
                return QPointF(x, self.pos().y() + self.port_y(ids.index(connector_id)))
        adj = self.dscene.adjacent(self.unit_id)
        k = adj.index(interface_id) if interface_id in adj else 0
        slot = (h - 44) / max(1, len(adj))
        return QPointF(x, self.pos().y() + 36 + (k + 0.5) * slot)

    # ---- state shown on the item ------------------------------------------------------------
    def _compat_reason(self) -> tuple[str, str]:
        """(state, reason): state is 'from', 'ok', 'no' or '' when the connect tool is idle."""
        ctl = self.ctl
        if ctl.tool != "connect" or ctl.connect_type is None:
            return "", ""
        if ctl.connect_from and ctl.connect_from.unit_id == self.unit_id:
            return "from", ""
        if ctl.mode == "guided":
            c = ctl.unit_compat(self.unit_id)
            return ("ok", "") if c.ok else ("no", c.short or c.why)
        if ctl.unit_has_valid_connector(self.unit_id):
            return "ok", ""
        name = ctl.project.interface_types[ctl.connect_type].name
        return "no", f"No free {name} connector"

    def _auto_connectors(self) -> set[str]:
        out: set[str] = set()
        for i in self.ctl.project.interfaces.values():
            out.update(
                e.connector_id
                for e in i.endpoints
                if e.auto and e.unit_id == self.unit_id and e.connector_id
            )
        return out

    # ---- painting ---------------------------------------------------------------------------
    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None
    ) -> None:
        th = self.dscene.theme
        ctl = self.ctl
        unit = ctl.project.units.get(self.unit_id)
        if unit is None:
            return
        state, reason = self._compat_reason()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height()
        if option.levelOfDetailFromTransform(painter.worldTransform()) < 0.45 and not reason:
            self._paint_overview(painter, th, unit, state)
            return
        selected = (
            ctl.selection is not None
            and ctl.selection.kind == "unit"
            and ctl.selection.id == self.unit_id
        )
        faded = state == "no"
        painter.setOpacity(0.55 if faded else 1.0)
        body = QRectF(0, 0, W, h)
        pen = QPen(th.color("border"), 2)
        if unit.side == "redundant":
            pen.setStyle(Qt.PenStyle.DashLine)
        if state == "ok":
            pen = QPen(th.color("primary"), 3)
        if state == "from":
            pen = QPen(th.color("primary"), 4, Qt.PenStyle.DashLine)
        if selected:
            pen = QPen(th.color("primary"), 4, pen.style())
        painter.setPen(pen)
        painter.setBrush(QBrush(th.color("surface")))
        painter.drawRoundedRect(body, 8, 8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(th.color("surface-2")))
        painter.drawRoundedRect(QRectF(1, 1, W - 2, HEADER_H), 7, 7)
        painter.drawRect(QRectF(1, HEADER_H - 8, W - 2, 9))
        bold = QFont(painter.font())
        bold.setBold(True)
        small = QFont(painter.font())
        small.setPixelSize(th.px(11))
        painter.setFont(bold)
        painter.setPen(th.color("text"))
        painter.drawText(QRectF(10, 0, W - 80, HEADER_H), Qt.AlignmentFlag.AlignVCenter, unit.id)
        painter.setFont(small)
        painter.setPen(th.color("text-muted"))
        tag = (
            "FROM" if state == "from" else ("REDUNDANT" if unit.side == "redundant" else "NOMINAL")
        )
        painter.drawText(
            QRectF(W - 90, 0, 80, HEADER_H),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            tag,
        )
        if ctl.mode == "expert":
            self._paint_ports(painter, small, th, state)
        else:
            painter.drawText(QRectF(10, 36, W - 20, 16), Qt.AlignmentFlag.AlignVCenter, unit.name)
            n = len(self.connectors())
            painter.drawText(
                QRectF(10, 52, W - 20, 16), Qt.AlignmentFlag.AlignVCenter, f"{n} connectors (auto)"
            )
        painter.setOpacity(1.0)
        if reason:
            painter.setPen(th.color("error"))
            painter.setFont(bold)
            painter.drawText(
                QRectF(0, h + 4, W + 12, 36),
                Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                f"✕ {reason}",
            )
        mark = ctl.diff_marks.get(self.unit_id)
        if mark:
            painter.setPen(QPen(th.color("warning"), 5, Qt.PenStyle.DotLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(body.adjusted(-7, -7, 7, 7), 12, 12)
            painter.setFont(bold)
            painter.setPen(th.color("warning"))
            painter.drawText(QRectF(0, -24, W, 16), Qt.AlignmentFlag.AlignRight, mark.upper())
        if self.hasFocus():
            painter.setPen(QPen(th.color("focus"), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(body.adjusted(-4, -4, 4, 4), 10, 10)

    def _paint_overview(
        self, painter: QPainter, th: ThemeManager, unit: object, state: str
    ) -> None:
        """Zoomed far out: a plain box and the ID only (fast for diagrams with hundreds of units)."""
        selected = (
            self.ctl.selection is not None
            and self.ctl.selection.kind == "unit"
            and self.ctl.selection.id == self.unit_id
        )
        pen = QPen(
            th.color("primary") if selected or state in ("ok", "from") else th.color("border"),
            4 if selected else 2,
        )
        painter.setPen(pen)
        painter.setBrush(QBrush(th.color("surface")))
        painter.drawRect(QRectF(0, 0, W, self.height()))
        font = QFont(painter.font())
        font.setBold(True)
        font.setPixelSize(22)
        painter.setFont(font)
        painter.setPen(th.color("text"))
        painter.drawText(
            QRectF(8, 0, W - 16, self.height()), Qt.AlignmentFlag.AlignVCenter, self.unit_id
        )

    def _paint_ports(self, painter: QPainter, small: QFont, th: ThemeManager, state: str) -> None:
        ctl = self.ctl
        auto = self._auto_connectors()
        painter.setFont(small)
        right = self.side() == "right"
        for k, c in enumerate(self.connectors()):
            rect = self.port_rect(k)
            compat = (
                ctl.connector_compat(c.id)
                if state in ("ok", "no", "from") and ctl.connect_type
                else None
            )
            valid = bool(compat and compat.ok and state != "from")
            pen = QPen(th.color("border"), 2)
            if c.id in auto:
                pen = QPen(th.color("auto-fill"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(QBrush(th.color("primary") if valid else th.color("bg")))
            painter.drawRoundedRect(rect, 3, 3)
            painter.setPen(
                th.color("text") if (compat is None or valid) else th.color("text-muted")
            )
            label = QRectF(12, self.port_y(k) - 9, W - 24, 18)
            align = Qt.AlignmentFlag.AlignVCenter | (
                Qt.AlignmentFlag.AlignRight if right else Qt.AlignmentFlag.AlignLeft
            )
            painter.drawText(label, align, c.name)
            painter.setPen(th.color("text-muted"))
            icons = " ".join(
                CATEGORIES[style_category(ctl.project.interface_types[t].category)]["icon"]
                for t in c.carries
                if t in ctl.project.interface_types
            )
            painter.drawText(
                label,
                Qt.AlignmentFlag.AlignVCenter
                | (Qt.AlignmentFlag.AlignLeft if right else Qt.AlignmentFlag.AlignRight),
                icons,
            )

    # ---- interaction ------------------------------------------------------------------------
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        ctl = self.ctl
        self.setFocus()
        if ctl.tool == "connect":
            ctl.pick(self.unit_id, self.port_at(event.pos()))
            event.accept()
            return
        ctl.select("unit", self.unit_id)
        self._press_pos = self.pos()
        self._moved = False
        if ctl.read_only:
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self._press_pos is not None and self.pos() != self._press_pos and not self.ctl.read_only:
            self.ctl.move_unit(self.unit_id, self.pos().x(), self.pos().y())
        self._press_pos = None

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and isinstance(
            value, QPointF
        ):
            if self.ctl.read_only and self._press_pos is not None:
                return self._press_pos
            return QPointF(round(value.x() / GRID) * GRID, round(value.y() / GRID) * GRID)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.dscene.relink(self.unit_id)
        return super().itemChange(change, value)

    def hoverMoveEvent(self, event: object) -> None:
        _, reason = self._compat_reason()
        tip = reason
        if self.ctl.mode == "expert" and self.ctl.tool == "connect" and self.ctl.connect_type:
            cid = self.port_at(event.pos())  # type: ignore[attr-defined]
            if cid:
                c = self.ctl.connector_compat(cid)
                tip = "" if c.ok else c.why
        if tip:
            QToolTip.showText(event.screenPos(), tip)  # type: ignore[attr-defined]
        else:
            u = self.ctl.project.units.get(self.unit_id)
            self.setToolTip(f"{u.id}: {u.name}" if u else "")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        ctl = self.ctl
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            if ctl.tool == "connect":
                ctl.pick(self.unit_id, self._first_valid_port())
            else:
                ctl.select("unit", self.unit_id)
            event.accept()
            return
        nudge = {
            Qt.Key.Key_Left: (-GRID, 0),
            Qt.Key.Key_Right: (GRID, 0),
            Qt.Key.Key_Up: (0, -GRID),
            Qt.Key.Key_Down: (0, GRID),
        }
        if (
            key in nudge
            and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            and ctl.tool == "select"
            and not ctl.read_only
        ):
            dx, dy = nudge[key]  # type: ignore[index]
            ctl.move_unit(self.unit_id, self.pos().x() + dx, self.pos().y() + dy)
            event.accept()
            return
        super().keyPressEvent(event)

    def _first_valid_port(self) -> str | None:
        if self.ctl.mode != "expert":
            return None
        return next((c.id for c in self.connectors() if self.ctl.connector_compat(c.id).ok), None)


class LinkItem(QGraphicsPathItem):
    def __init__(self, scene: "DiagramScene", interface_id: str) -> None:
        super().__init__()
        self.dscene = scene
        self.interface_id = interface_id
        self._chip = QRectF()
        self._chip_placed = False
        self.ends: QLineF | None = None  # straight line between the two anchors (for the map)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
        self.setAcceptHoverEvents(True)

    def update_path(self) -> bool:
        """Recompute the curve and label spot. Returns False (and leaves the item alone, so it is
        not repainted) when the curve did not change: renaming a unit must not repaint its links."""
        ctl = self.dscene.ctl
        i = ctl.project.interfaces.get(self.interface_id)
        a_item = self.dscene.unit_items.get(i.endpoints[0].unit_id) if i else None
        b_item = self.dscene.unit_items.get(i.endpoints[1].unit_id) if i else None
        if i is None or a_item is None or b_item is None:
            self.prepareGeometryChange()
            self.setPath(QPainterPath())
            self.ends = None
            return True
        p1 = a_item.anchor(i.endpoints[0].connector_id, i.id)
        p2 = b_item.anchor(i.endpoints[1].connector_id, i.id)
        self.ends = QLineF(p1, p2)
        da = 1 if a_item.side() == "right" else -1
        db = 1 if b_item.side() == "right" else -1
        same = a_item.side() == b_item.side()
        reach = 70 if same else max(50, abs(p2.x() - p1.x()) / 2)
        c1 = QPointF(p1.x() + da * reach, p1.y())
        c2 = QPointF(p2.x() + db * reach, p2.y())
        path = QPainterPath(p1)
        path.cubicTo(c1, c2, p2)
        if path == self.path() and self._chip_placed:
            return False
        self.prepareGeometryChange()
        self.setPath(path)
        idx = self.dscene.link_order(i.id)
        t0 = 0.35 + 0.1 * (idx % 4)
        width = 30 + 7.5 * len(i.id)
        center = path.pointAtPercent(t0)
        for k in range(9):  # slide along the link until the label sits on free space
            t = min(0.8, max(0.2, t0 + (0.07 * ((k + 1) // 2)) * (1 if k % 2 else -1)))
            cand = path.pointAtPercent(t)
            if self.dscene.chip_free(QRectF(cand.x() - width / 2, cand.y() - 11, width, 22), i.id):
                center = cand
                break
        self._chip_center = center
        self._chip_placed = True
        self.dscene.chip_place(i.id, QRectF(center.x() - width / 2, center.y() - 11, width, 22))
        return True

    def shape(self) -> QPainterPath:
        stroker = QPainterPathStroker()
        stroker.setWidth(14)
        return stroker.createStroke(self.path())

    def boundingRect(self) -> QRectF:
        return super().boundingRect().adjusted(-120, -20, 120, 20)

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None
    ) -> None:
        ctl = self.dscene.ctl
        th = self.dscene.theme
        i = ctl.project.interfaces.get(self.interface_id)
        if i is None or self.path().isEmpty():
            return
        t = ctl.project.interface_types.get(i.type_id)
        cat = style_category(t.category if t else "data")
        info = CATEGORIES[cat]
        color = th.color(f"cat-{cat}")
        selected = (
            ctl.selection is not None
            and ctl.selection.kind == "interface"
            and ctl.selection.id == i.id
        )
        far = option.levelOfDetailFromTransform(painter.worldTransform()) < 0.5 and not selected
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, not far)
        marked = i.id in ctl.diff_marks
        if marked:  # a wide, dotted halo in the warning colour (not colour alone: also dotted)
            halo = QPen(th.color("warning"), float(info["weight"]) + 8, Qt.PenStyle.DotLine)
            painter.setPen(halo)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.path())
        pen = QPen(color, float(info["weight"]) + (2 if selected else 0))
        if i.redundancy == "redundant":
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())
        if far:  # zoomed out: lines only, no labels
            return
        c = self._chip_center
        font = QFont(painter.font())
        font.setPixelSize(th.px(11))
        text_w = QFontMetrics(font).horizontalAdvance(i.id)
        width = 30 + text_w
        rect = QRectF(c.x() - width / 2, c.y() - 11, width, 22)
        self._chip = rect
        painter.setBrush(QBrush(th.color("bg")))
        painter.setPen(QPen(color, 3 if selected else 2))
        painter.drawRoundedRect(rect, 11, 11)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(
            QRectF(rect.x() + 7, rect.y(), 14, 22), Qt.AlignmentFlag.AlignVCenter, info["icon"]
        )
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(th.color("text"))
        painter.drawText(
            QRectF(rect.x() + 22, rect.y(), text_w + 4, 22), Qt.AlignmentFlag.AlignVCenter, i.id
        )
        if self.hasFocus():
            painter.setPen(QPen(th.color("focus"), 3))
            painter.drawRoundedRect(rect.adjusted(-3, -3, 3, 3), 13, 13)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.dscene.ctl.tool == "connect":
            event.ignore()
            return
        self.setFocus()
        self.dscene.ctl.select("interface", self.interface_id)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.dscene.ctl.select("interface", self.interface_id)
            event.accept()
            return
        super().keyPressEvent(event)

    def hoverEnterEvent(self, event: object) -> None:
        i = self.dscene.ctl.project.interfaces.get(self.interface_id)
        if i:
            self.setToolTip(f"{i.id}: {i.name}")


class ZoneItem(QGraphicsItem):
    def __init__(self, scene: "DiagramScene", index: int) -> None:
        super().__init__()
        self.dscene = scene
        self.index = index
        self.setZValue(-10)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, edit.LANE_WIDTH - 10, self.dscene.lane_height)

    def paint(
        self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None
    ) -> None:
        th = self.dscene.theme
        zones = edit.effective_zones(self.dscene.ctl.project)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(th.color("surface-2"), 1))
        fill = QColor(th.color("surface"))
        fill.setAlpha(150)
        painter.setBrush(QBrush(fill))
        painter.drawRoundedRect(self.boundingRect(), 8, 8)
        font = QFont(painter.font())
        font.setBold(True)
        font.setPixelSize(th.px(12))
        painter.setFont(font)
        painter.setPen(th.color("text-muted"))
        name = zones[self.index].upper() if self.index < len(zones) else ""
        painter.drawText(QRectF(10, 4, 300, 20), Qt.AlignmentFlag.AlignVCenter, name)


class DiagramScene(QGraphicsScene):
    def __init__(self, ctl: EditorController, theme: ThemeManager) -> None:
        super().__init__()
        self.ctl = ctl
        self.theme = theme
        self.unit_items: dict[str, UnitItem] = {}
        self.link_items: dict[str, LinkItem] = {}
        self._chips: dict[tuple[int, int], list[tuple[str, QRectF]]] = {}
        self._chip_rects: dict[str, QRectF] = {}
        self.zone_items: list[ZoneItem] = []
        self.lane_height = 700.0
        self._adj: dict[str, list[str]] = {}
        self._order: dict[str, int] = {}
        self.zone_count = len(edit.effective_zones(ctl.project))
        self._last_sel: object = None
        ctl.changed.connect(self.apply)
        ctl.selectionChanged.connect(self._on_selection)
        ctl.marksChanged.connect(self.refresh_all)
        ctl.connectChanged.connect(self._repaint_units)
        ctl.modeChanged.connect(self.refresh_all)
        theme.changed.connect(lambda: self.update())
        self.rebuild()

    def adjacent(self, unit_id: str) -> list[str]:
        return self._adj.get(unit_id, [])

    # ---- label placement: a coarse grid of placed link labels, so they do not overlap ------------
    CELL = 120.0

    def _cells(self, r: QRectF) -> list[tuple[int, int]]:
        x0, x1 = int(r.left() // self.CELL), int(r.right() // self.CELL)
        y0, y1 = int(r.top() // self.CELL), int(r.bottom() // self.CELL)
        return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]

    def chip_free(self, rect: QRectF, own: str) -> bool:
        pad = rect.adjusted(-3, -3, 3, 3)
        for cell in self._cells(pad):
            for other, r in self._chips.get(cell, ()):
                if other != own and r.intersects(pad):
                    return False
        return True

    def chip_forget(self, interface_id: str) -> None:
        rect = self._chip_rects.pop(interface_id, None)
        if rect is None:
            return
        for cell in self._cells(rect):
            self._chips[cell] = [c for c in self._chips.get(cell, []) if c[0] != interface_id]

    def chip_place(self, interface_id: str, rect: QRectF) -> None:
        self.chip_forget(interface_id)
        self._chip_rects[interface_id] = rect
        for cell in self._cells(rect):
            self._chips.setdefault(cell, []).append((interface_id, rect))

    def link_order(self, interface_id: str) -> int:
        return self._order.get(interface_id, 0)

    def _rebuild_adjacency(self) -> None:
        adj: dict[str, list[str]] = {}
        order: dict[str, int] = {}
        for k, i in enumerate(sorted(self.ctl.project.interfaces.values(), key=lambda x: x.id)):
            order[i.id] = k
            for e in i.endpoints:
                adj.setdefault(e.unit_id, []).append(i.id)
        self._adj = adj
        self._order = order

    def rebuild(self) -> None:
        self.clear()
        self.unit_items.clear()
        self.link_items.clear()
        self._chips.clear()
        self._chip_rects.clear()
        self.zone_items.clear()
        self._rebuild_adjacency()
        self._sync_zones()
        project = self.ctl.project
        for uid in sorted(project.units):
            self._add_unit(uid)
        for iid in sorted(project.interfaces):
            self._add_link(iid)
        self._update_extent()

    def _add_unit(self, uid: str) -> None:
        item = UnitItem(self, uid)
        x, y = edit.position_of(self.ctl.project, uid)
        self.addItem(item)
        item.setPos(x, y)
        self.unit_items[uid] = item

    def _add_link(self, iid: str) -> None:
        link = LinkItem(self, iid)
        self.addItem(link)
        self.link_items[iid] = link
        link.update_path()

    def _sync_zones(self) -> None:
        n = len(edit.effective_zones(self.ctl.project))
        self.zone_count = n
        while len(self.zone_items) > n:
            self.removeItem(self.zone_items.pop())
        while len(self.zone_items) < n:
            z = ZoneItem(self, len(self.zone_items))
            self.addItem(z)
            self.zone_items.append(z)
        for k, z in enumerate(self.zone_items):
            where = QPointF(edit.LANE_X0 + k * edit.LANE_WIDTH, 0)
            if z.pos() != where:
                z.setPos(where)
            # (a zone item is as tall as the diagram: repainting all of them on every edit made
            # each edit repaint every unit and link)

    def _update_extent(self) -> None:
        bottom = max(
            (it.pos().y() + it.height() + 60 for it in self.unit_items.values()), default=0
        )
        # in steps, so adding or undoing one unit rarely resizes the scene (which repaints it all)
        height = max(700.0, math.ceil((bottom + 40) / LANE_STEP) * LANE_STEP)
        if height != self.lane_height:
            self.lane_height = height
            for z in self.zone_items:
                z.prepareGeometryChange()
        width = max(1, len(self.zone_items)) * edit.LANE_WIDTH + 2 * edit.LANE_X0
        rect = QRectF(0, 0, width, self.lane_height)
        if rect != self.sceneRect():
            self.setSceneRect(rect)

    def apply(self, delta: Delta) -> None:
        if delta.full:
            self.rebuild()
            return
        project = self.ctl.project
        self._rebuild_adjacency()
        self._sync_zones()
        for uid in delta.units:
            item = self.unit_items.get(uid)
            if uid in project.units:
                x, y = edit.position_of(project, uid)
                if item is None:
                    self._add_unit(uid)
                else:
                    item.prepareGeometryChange()
                    if (item.pos().x(), item.pos().y()) != (x, y):
                        item.setPos(x, y)
                    item.update()
            elif item is not None:
                self.removeItem(item)
                del self.unit_items[uid]
        for iid in delta.interfaces:
            link = self.link_items.get(iid)
            if iid in project.interfaces:
                if link is None:
                    self._add_link(iid)
                else:
                    link.update_path()
            elif link is not None:
                self.removeItem(link)
                self.chip_forget(iid)
                del self.link_items[iid]
        for uid in delta.units:  # heights may have changed: relink neighbours
            self.relink(uid)
        self._update_extent()

    def relink(self, unit_id: str) -> None:
        for iid in self._adj.get(unit_id, []):
            link = self.link_items.get(iid)
            if link is not None:
                link.update_path()

    def refresh_all(self) -> None:
        for it in self.unit_items.values():
            it.prepareGeometryChange()
            it.update()
        for link in self.link_items.values():
            link.update_path()
        self.update()

    def _repaint_units(self) -> None:
        for it in self.unit_items.values():
            it.update()

    def _on_selection(self) -> None:
        """Repaint only the previously and the newly selected item (not the whole diagram)."""
        for sel in (self._last_sel, self.ctl.selection):
            if sel is None:
                continue
            item = (self.unit_items if sel.kind == "unit" else self.link_items).get(sel.id)  # type: ignore[attr-defined]
            if item is not None:
                item.update()
        self._last_sel = self.ctl.selection


LANE_STEP = 256.0  # lane height grows in steps of this many pixels
MAP_DELAY_MS = 400  # the overview map repaints this long after the last change


class MiniMap(QWidget):
    """Small overview of the whole diagram; click to centre the main view there.

    It draws plain boxes and lines straight from the item positions instead of showing the scene a
    second time: painting 2,200 real items in a tiny view cost about 300 ms at stress size."""

    def __init__(self, main: "DiagramView") -> None:
        super().__init__(main)
        self.main = main
        self.setFixedSize(190, 130)
        self.setAccessibleName(strings.MINIMAP)
        self.setToolTip(strings.MINIMAP)
        self._lag = QTimer(self)
        self._lag.setSingleShot(True)
        self._lag.setInterval(MAP_DELAY_MS)
        self._lag.timeout.connect(self._catch_up)
        main.scene().changed.connect(self._scene_changed)
        main.scene().sceneRectChanged.connect(lambda _r: self.update())

    def viewport(self) -> "MiniMap":
        return self  # (the earlier version was a graphics view; callers update its viewport)

    def refit(self) -> None:
        self.update()

    def _scene_changed(self, _regions: object) -> None:
        if self.isVisible():
            self._lag.start()  # restarts: the map catches up when the edits pause

    def _catch_up(self) -> None:
        if self.isVisible():
            self.update()

    def _scale(self) -> tuple[float, float, float]:
        """(scale, x offset, y offset) that fit the scene into the widget."""
        rect = self.main.scene().sceneRect()
        if not rect.isValid() or rect.isEmpty():
            return 1.0, 0.0, 0.0
        scale = min((self.width() - 2) / rect.width(), (self.height() - 2) / rect.height())
        return (
            scale,
            (self.width() - rect.width() * scale) / 2 - rect.x() * scale,
            (self.height() - rect.height() * scale) / 2 - rect.y() * scale,
        )

    def paintEvent(self, event: object) -> None:
        theme = self.main.theme
        scene = self.main.dscene
        painter = QPainter(self)
        painter.fillRect(self.rect(), theme.color("bg"))
        scale, dx, dy = self._scale()
        painter.translate(dx, dy)
        painter.scale(scale, scale)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(theme.color("surface"))
        for k in range(len(scene.zone_items)):
            painter.drawRect(
                QRectF(
                    edit.LANE_X0 + k * edit.LANE_WIDTH, 0, edit.LANE_WIDTH - 10, scene.lane_height
                )
            )
        painter.setPen(QPen(theme.color("border"), 0))
        painter.drawLines([ln for ln in (lk.ends for lk in scene.link_items.values()) if ln])
        painter.setBrush(theme.color("surface"))
        painter.setPen(QPen(theme.color("text"), 0))
        painter.drawRects(
            [QRectF(it.pos().x(), it.pos().y(), W, it.height()) for it in scene.unit_items.values()]
        )
        view_rect = self.main.mapToScene(self.main.viewport().rect()).boundingRect()
        painter.setPen(QPen(theme.color("primary"), 0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(view_rect)
        painter.resetTransform()
        painter.setPen(QPen(theme.color("border"), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        scale, dx, dy = self._scale()
        pos = event.position()
        self.main.centerOn(QPointF((pos.x() - dx) / scale, (pos.y() - dy) / scale))
        self.update()


class DiagramView(QGraphicsView):
    def __init__(self, ctl: EditorController, theme: ThemeManager) -> None:
        self.ctl = ctl
        self.theme = theme
        self.dscene = DiagramScene(ctl, theme)
        super().__init__(self.dscene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setAccessibleName(strings.CANVAS)
        self.setAccessibleDescription(strings.CANVAS_HELP)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.empty = QLabel(strings.EMPTY_CANVAS, self.viewport())
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setWordWrap(True)
        self.empty.setProperty("muted", True)
        self.empty.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.minimap = MiniMap(self)
        self.minimap_wanted = True  # the View menu can switch it off
        self._fit_scale = 0.25
        ctl.changed.connect(self._on_changed)
        ctl.selectionChanged.connect(self._announce)
        theme.changed.connect(self._restyle)
        self._on_changed(None)
        self._announce()

    def _announce(self) -> None:
        """Qt does not expose graphics items to screen readers, so the view itself says what it
        holds, what is selected, and where the full accessible alternative is."""
        p = self.ctl.project
        self.setAccessibleName(
            strings.CANVAS_NAME.format(
                strings.units_text(len(p.units)), strings.interfaces_text(len(p.interfaces))
            )
        )
        sel = self.ctl.selection
        picked = strings.CANVAS_SELECTED.format(sel.kind, sel.id) if sel else strings.CANVAS_NONE
        self.setAccessibleDescription(f"{picked} {strings.CANVAS_HELP}")

    def _restyle(self) -> None:
        self.setBackgroundBrush(QBrush(self.theme.color("bg")))
        self.viewport().update()

    def _on_changed(self, delta: object) -> None:
        self._announce()
        if getattr(delta, "full", False):
            QTimer.singleShot(0, self.fit)  # a newly opened project starts fitted to the window
        self.empty.setVisible(not self.ctl.project.units)
        self._layout_overlays()
        self._update_minimap_visibility()
        if getattr(delta, "full", False):
            # The map shares the scene, so a local edit repaints only the changed items there; it
            # is refitted when the scene rectangle changes. Forcing a repaint of the whole map on
            # every edit repainted every item and cost about half of an edit at stress size.
            self.minimap.refit()
            self.minimap.viewport().update()

    def set_minimap_wanted(self, wanted: bool) -> None:
        self.minimap_wanted = wanted
        self._update_minimap_visibility()

    def _update_minimap_visibility(self) -> None:
        # it covers the bottom right corner, so a small view hides it automatically
        room = self.viewport().height() >= 300 and self.viewport().width() >= 420
        self.minimap.setVisible(self.minimap_wanted and room and len(self.ctl.project.units) > 0)

    def _layout_overlays(self) -> None:
        r = self.viewport().rect()
        self.empty.setGeometry(r.adjusted(60, 60, -60, -60))
        self.minimap.move(
            r.right() - self.minimap.width() - 12, r.bottom() - self.minimap.height() - 12
        )

    def resizeEvent(self, event: object) -> None:
        super().resizeEvent(event)  # type: ignore[arg-type]
        self._layout_overlays()
        self.minimap.refit()
        self._update_minimap_visibility()

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)
        self.minimap.viewport().update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
        self.zoom_by(factor)
        event.accept()

    def zoom_by(self, factor: float) -> None:
        current = self.transform().m11()
        # a large diagram is fitted below 0.25; zooming out must never jump back in
        lowest = max(0.02, min(0.25, self._fit_scale * 0.9))
        new = max(lowest, min(3.0, current * factor))
        self.scale(new / current, new / current)
        self.minimap.viewport().update()

    def content_rect(self) -> QRectF:
        """Bounding box of units and links (not the tall lane backgrounds)."""
        rect = QRectF()
        for it in (*self.dscene.unit_items.values(), *self.dscene.link_items.values()):
            rect = rect.united(it.sceneBoundingRect())
        return rect

    def fit(self) -> None:
        self.resetTransform()
        rect = self.content_rect()
        if not rect.isNull():
            self.fitInView(rect.adjusted(-60, -60, 60, 60), Qt.AspectRatioMode.KeepAspectRatio)
            if self.transform().m11() > 1.2:
                self.resetTransform()
                self.centerOn(rect.center())
            self._fit_scale = self.transform().m11()
        self.minimap.viewport().update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        item = self.itemAt(event.position().toPoint())
        if item is None and self.ctl.tool == "select":
            self.ctl.select(None)
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.ctl.end_connect()
            event.accept()
            return
        super().keyPressEvent(event)

    def reveal(self, unit_id: str) -> None:
        """Scroll a unit into view without changing keyboard focus."""
        item = self.dscene.unit_items.get(unit_id)
        if item is not None:
            self.ensureVisible(item, 40, 40)

    def focus_unit(self, unit_id: str) -> None:
        item = self.dscene.unit_items.get(unit_id)
        if item is not None:
            self.ensureVisible(item)
            item.setFocus()
