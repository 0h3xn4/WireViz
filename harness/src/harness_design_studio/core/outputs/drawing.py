"""Harness drawing, in the manner of a wiring diagram: the connectors as tables on the left and
the right (name, part, gender, pins, and for every used pin its signal), the wires between them as
curves in their wire colour, and between the connectors a cable block that lists the wires (ID,
colour code) with gauge and length. Shields, routing segments, spare pins and a routing sketch follow.
A title block closes every sheet.

Wire colours are drawn (with a dark outline) and also written as a code beside every wire, so a
greyscale print loses nothing; a wire whose colour is not set is drawn grey. The colour names and
codes are the IEC 60757 designators; they are only used to draw, never to decide anything.

Pagination: when the connectors do not fit one sheet the wires flow onto the next; every sheet
repeats the connectors it needs and marks a continued cable block.
"""

from dataclasses import dataclass

from harness_design_studio.core.generate.lengths import wire_length
from harness_design_studio.core.model import Connector, Harness, Project, Wire

from .canvas import SHEETS, Curve, Line, Rect, Sheet, Text, fit
from .stamp import Stamp
from .tables import PENDING, num

MARGIN = 8.0
TB_H = 42.0  # title block height
TB_W = 190.0
SIZE = 2.6
GREY = "#555555"


SKETCH_MAX_NODES = 14
NODE_W, NODE_H, NODE_GAP_X, NODE_GAP_Y = 36.0, 7.0, 34.0, 4.0


def sketch_layout(h: Harness) -> dict[str, tuple[int, int]] | None:
    """Columns by distance from the first connector, rows in order; None if there is no tree or
    it is too large to sketch. A schematic of the routing, not drawn to scale."""
    nodes = sorted({c.id for c in h.connectors} | {b.id for b in h.branch_points})
    if not h.segments or not h.connectors or len(nodes) > SKETCH_MAX_NODES:
        return None
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    for g in h.segments:
        if g.from_node in adj and g.to_node in adj:
            adj[g.from_node].append(g.to_node)
            adj[g.to_node].append(g.from_node)
    start = sorted(c.id for c in h.connectors)[0]
    depth = {start: 0}
    queue = [start]
    for n in queue:
        for m in sorted(adj[n]):
            if m not in depth:
                depth[m] = depth[n] + 1
                queue.append(m)
    for n in nodes:  # nodes not reachable from the start sit in a column of their own
        depth.setdefault(n, max(depth.values()) + 1)
    per_col: dict[int, int] = {}
    layout = {}
    for n in sorted(nodes, key=lambda x: (depth[x], x)):
        layout[n] = (depth[n], per_col.get(depth[n], 0))
        per_col[depth[n]] = per_col.get(depth[n], 0) + 1
    return layout


def sketch_height(layout: dict[str, tuple[int, int]]) -> float:
    rows = max(r for _, r in layout.values()) + 1
    return 8.0 + rows * (NODE_H + NODE_GAP_Y) + 3.0


CONN_W = 58.0  # width of a connector table
BOX_W = 96.0  # width of a cable block
ROW = 4.2  # height of a pin row and of a wire row
HEAD_ROW = 3.9
HEAD_H = 3 * HEAD_ROW  # connector and cable headers: three lines
GAP = 7.0
MAX_WIRE_RUN = 45.0  # longest stretch of wire between a connector table and a cable block
WIRE_W = 0.8
PIN_SIZE = 2.5
HEAD_SIZE = 2.2

# IEC 60757 colour codes with a screen colour for drawing: display only, nothing is decided by it
_COLOURS = {
    "BK": "#1a1a1a", "BN": "#8b5a2b", "RD": "#e02020", "OG": "#ff8c00", "YE": "#ffd700",
    "GN": "#22aa22", "BU": "#1e5bd8", "VT": "#8a2be2", "GY": "#9a9a9a", "WH": "#ffffff",
    "PK": "#ff8fb0", "TQ": "#20b2aa",
}  # fmt: skip
_COLOUR_NAMES = {
    "black": "BK", "brown": "BN", "red": "RD", "orange": "OG", "yellow": "YE", "green": "GN",
    "blue": "BU", "violet": "VT", "purple": "VT", "grey": "GY", "gray": "GY", "white": "WH",
    "pink": "PK", "turquoise": "TQ",
}  # fmt: skip
UNSET_COLOUR = "#808080"


def wire_colour(name: str | None) -> tuple[str, str]:
    """(code, screen colour) of a wire colour: ("BK", "#1a1a1a"); a colour that is not set gives
    ("", grey) and one this table does not know keeps its text (shortened) and is drawn grey."""
    if not name:
        return "", UNSET_COLOUR
    key = name.strip()
    code = _COLOUR_NAMES.get(key.lower()) or (key.upper() if key.upper() in _COLOURS else None)
    if code:
        return code, _COLOURS[code]
    return key[:6], UNSET_COLOUR


def _pin_key(pin: str) -> tuple[bool, int, str]:
    return (not pin.isdigit(), int(pin) if pin.isdigit() else 0, pin)


def _gender_words(c: Connector | None) -> str:
    return {"male": "male, pins", "female": "female, sockets"}.get(
        c.gender if c else "", "gender not set"
    )


def _signal(cid: str, pin: str, project: Project, h: Harness) -> str:
    """Signal of a cable connector's pin, or of the box connector it mates with."""
    conn = next((c for c in h.connectors if c.id == cid), None)
    box = project.connectors.get(conn.mates_with or "") if conn else None
    for c in (conn, box):
        signal = next((p.signal for p in (c.pins if c else []) if p.id == pin and p.signal), None)
        if signal:
            return signal
    return ""


@dataclass
class _Page:
    wires: list[tuple[tuple[str, str], Wire]]
    continued: set[tuple[str, str]]


def _sides(groups: list[tuple[str, str]]) -> dict[str, int]:
    """Left (0) or right (1) column of every connector: connected connectors face each other."""
    side: dict[str, int] = {}
    for _ in range(len(groups) + 1):
        changed = False
        for a, b in groups:
            if a in side and b not in side:
                side[b], changed = 1 - side[a], True
            elif b in side and a not in side:
                side[a], changed = 1 - side[b], True
            elif a not in side and b not in side:
                side[a], side[b], changed = 0, 1, True
        if not changed:
            break
    return side


def _stack_height(items: list[float]) -> float:
    return sum(items) + GAP * max(0, len(items) - 1)


def _fits(wires: list[tuple[tuple[str, str], Wire]], side: dict[str, int], capacity: float) -> bool:
    pins: dict[str, set[str]] = {}
    per_group: dict[tuple[str, str], int] = {}
    for g, w in wires:
        pins.setdefault(w.from_connector, set()).add(w.from_pin)
        pins.setdefault(w.to_connector, set()).add(w.to_pin)
        per_group[g] = per_group.get(g, 0) + 1
    cols: list[list[float]] = [[], []]
    for cid, used in pins.items():
        cols[side.get(cid, 0)].append(HEAD_H + len(used) * ROW)
    cable = [HEAD_H + n * ROW for n in per_group.values()]
    return max(_stack_height(cols[0]), _stack_height(cols[1]), _stack_height(cable)) <= capacity


def _paginate(
    items: list[tuple[tuple[str, str], Wire]], side: dict[str, int], capacity: float
) -> list[_Page]:
    pages: list[_Page] = []
    cur: list[tuple[tuple[str, str], Wire]] = []
    prev_groups: set[tuple[str, str]] = set()
    cont: set[tuple[str, str]] = set()
    for item in items:
        if cur and not _fits([*cur, item], side, capacity):
            pages.append(_Page(cur, cont))
            prev_groups = {g for g, _ in cur}
            cur = []
            cont = set()
        if not cur and item[0] in prev_groups:
            cont = {item[0]}
        elif item[0] in prev_groups and item[0] not in {g for g, _ in cur}:
            cont.add(item[0])
        cur.append(item)
    if cur or not pages:
        pages.append(_Page(cur, cont))
    return pages


def _extras(h: Harness) -> list[str]:
    """The lines beneath the diagram: shields, routing segments, spare pins, notes."""
    out: list[str] = []
    if h.shields:
        out.append("Shields:")
        for s in sorted(h.shields, key=lambda x: x.id):
            out.append(
                f"  {s.id} ({s.kind}) wires {', '.join(sorted(s.wire_ids))}; ends {s.end_a} / {s.end_b}"
            )
    if h.segments:
        out.append("Routing segments:")
        for g in sorted(h.segments, key=lambda x: x.id):
            length = f"{num(g.length_m)} m" if g.length_m is not None else "unknown"
            out.append(f"  {g.id}: {g.from_node} to {g.to_node}, length {length}")
    used = {(w.from_connector, w.from_pin) for w in h.wires} | {
        (w.to_connector, w.to_pin) for w in h.wires
    }
    for c in sorted(h.connectors, key=lambda x: x.id):
        spare = [p.id for p in c.pins if (c.id, p.id) not in used]
        if spare:
            out.append(f"Spare pins {c.id}: {', '.join(spare)}")
    if h.notes:
        out.append(f"Notes: {h.notes}")
    return out


def _cable_summary(h: Harness, wires: list[Wire]) -> str:
    gauges = {w.gauge_awg for w in wires}
    gauge = (
        "AWG ?"
        if gauges == {None}
        else (f"AWG {gauges.pop()}" if len(gauges) == 1 else "AWG mixed")
    )
    if gauge == "AWG ?":
        gauge = PENDING
    lengths = {wire_length(h, w) for w in wires}
    length = (
        "length n/a"
        if lengths == {None}
        else (f"{num(next(iter(lengths)))} m" if len(lengths) == 1 else "lengths vary")
    )
    return f"{len(wires)}x  {gauge}  {length}"


def _draw_page(
    sh: Sheet, project: Project, h: Harness, page: _Page, side: dict[str, int], y0: float
) -> float:
    """Draw connectors, cable blocks and wires of one page from y0; return the bottom edge."""
    w_mm = sh.width
    conns = {c.id: c for c in h.connectors}
    pins: dict[str, set[str]] = {}
    order: list[str] = []
    groups: dict[tuple[str, str], list[Wire]] = {}
    for g, w in page.wires:
        for cid, pin in ((w.from_connector, w.from_pin), (w.to_connector, w.to_pin)):
            pins.setdefault(cid, set()).add(pin)
            if cid not in order:
                order.append(cid)
        groups.setdefault(g, []).append(w)
    gap = min(MAX_WIRE_RUN, (w_mm - 2 * MARGIN - 2 * CONN_W - BOX_W) / 2)
    left_x = (w_mm - (2 * CONN_W + BOX_W + 2 * gap)) / 2  # the diagram is centred on the sheet
    box_x = left_x + CONN_W + gap
    right_x = box_x + BOX_W + gap
    top: dict[str, float] = {}
    rows: dict[str, list[str]] = {}
    ends = [y0, y0]
    for cid in order:
        col = side.get(cid, 0)
        top[cid] = ends[col]
        rows[cid] = sorted(pins[cid], key=_pin_key)
        ends[col] += HEAD_H + len(rows[cid]) * ROW + GAP

    def pin_pos(cid: str, pin: str) -> tuple[float, float]:
        x = left_x + CONN_W if side.get(cid, 0) == 0 else right_x
        return x, top[cid] + HEAD_H + (rows[cid].index(pin) + 0.5) * ROW

    # cable blocks: as close to the middle of their wires as the other blocks allow
    want = {}
    for g, ws in groups.items():
        ys = [pin_pos(w.from_connector, w.from_pin)[1] for w in ws] + [
            pin_pos(w.to_connector, w.to_pin)[1] for w in ws
        ]
        want[g] = sum(ys) / len(ys)
    box_top: dict[tuple[str, str], float] = {}
    edge = y0
    for g in sorted(groups, key=lambda k: (want[k], k)):
        height = HEAD_H + len(groups[g]) * ROW
        box_top[g] = max(edge, want[g] - height / 2)
        edge = box_top[g] + height + GAP / 2
    # connector tables
    for cid in order:
        c = conns.get(cid)
        col = side.get(cid, 0)
        x = left_x if col == 0 else right_x
        height = HEAD_H + len(rows[cid]) * ROW
        sh.add(Rect(x, top[cid], CONN_W, height, width=0.35, fill="#ffffff"))
        sh.add(Rect(x, top[cid], CONN_W, HEAD_H, width=0.35, fill="#e6e6e6"))
        mate = f"mates {c.mates_with}" if c is not None and c.mates_with else ""
        part = f"{c.part_id}, {_gender_words(c)}, {len(c.pins)}-pin" if c is not None else ""
        for k, (text, size, bold) in enumerate(
            ((cid, 2.8, True), (part, HEAD_SIZE, False), (mate, HEAD_SIZE, False))
        ):
            sh.add(
                Text(
                    x + CONN_W / 2,
                    top[cid] + (k + 1) * HEAD_ROW - 1.1,
                    fit(text, CONN_W - 2.0, size),
                    size=size,
                    bold=bold,
                    anchor="middle",
                    color=GREY if k else "#000000",
                )
            )
        split = x + CONN_W - 12.0 if col == 0 else x + 12.0
        sh.add(Line(split, top[cid] + HEAD_H, split, top[cid] + height, width=0.25))
        for k, pin in enumerate(rows[cid]):
            yy = top[cid] + HEAD_H + (k + 1) * ROW
            if k < len(rows[cid]) - 1:
                sh.add(Line(x, yy, x + CONN_W, yy, width=0.2, color="#bbbbbb"))
            base = yy - 1.2
            signal = fit(_signal(cid, pin, project, h), CONN_W - 12.0 - 3.0, PIN_SIZE)
            if col == 0:
                sh.add(Text(x + 1.5, base, signal, size=PIN_SIZE))
                sh.add(Text(x + CONN_W - 1.5, base, pin, size=PIN_SIZE, bold=True, anchor="end"))
            else:
                sh.add(Text(x + 1.5, base, pin, size=PIN_SIZE, bold=True))
                sh.add(Text(x + 12.0 + 1.5, base, signal, size=PIN_SIZE))
    # cable blocks and wires
    for g in sorted(groups, key=lambda k: (box_top[k], k)):
        ws = groups[g]
        bt = box_top[g]
        height = HEAD_H + len(ws) * ROW
        sh.add(Rect(box_x, bt, BOX_W, height, width=0.3, dash=(1.5, 1.0), color=GREY))
        title = f"{g[0]} - {g[1]}" + ("  (continued)" if g in page.continued else "")
        sh.add(
            Text(
                box_x + BOX_W / 2,
                bt + HEAD_ROW - 1.1,
                fit(title, BOX_W - 2.0, 2.8),
                size=2.8,
                bold=True,
                anchor="middle",
            )
        )
        sh.add(
            Text(
                box_x + BOX_W / 2,
                bt + 2 * HEAD_ROW - 1.1,
                fit(_cable_summary(h, ws), BOX_W - 2.0, HEAD_SIZE),
                size=HEAD_SIZE,
                anchor="middle",
                color=GREY,
            )
        )
        mixed = len({(w.gauge_awg, wire_length(h, w)) for w in ws}) > 1
        for k, w in enumerate(ws):
            cy = bt + HEAD_H + (k + 0.5) * ROW
            code, hexcolour = wire_colour(w.colour)
            (ca, pa), (cb, pb) = (w.from_connector, w.from_pin), (w.to_connector, w.to_pin)
            if side.get(ca, 0) == 1 and side.get(cb, 0) == 0:
                (ca, pa), (cb, pb) = (cb, pb), (ca, pa)
            (x1, y1), (x2, y2) = pin_pos(ca, pa), pin_pos(cb, pb)
            for width, colour in ((WIRE_W + 0.7, "#000000"), (WIRE_W, hexcolour)):
                sh.add(
                    Curve(x1, y1, box_x, cy, width=width, color=colour),
                    Line(box_x, cy, box_x + BOX_W, cy, width=width, color=colour),
                    Curve(box_x + BOX_W, cy, x2, y2, width=width, color=colour),
                )
            label = f"{w.id}  {code}".rstrip()
            if mixed:
                length = wire_length(h, w)
                gauge = "AWG ?" if w.gauge_awg is None else f"AWG {w.gauge_awg}"
                label += f"  {gauge}  {num(length) + ' m' if length is not None else 'n/a'}"
            sh.add(
                Text(
                    box_x + BOX_W / 2,
                    cy - 1.0,
                    fit(label, BOX_W - 2.0, PIN_SIZE),
                    size=PIN_SIZE,
                    anchor="middle",
                    bold=True,
                )
            )
    return max([*ends, edge]) - GAP


def _title_block(
    sheet: Sheet, project: Project, h: Harness, stamp: Stamp, n: int, total: int, fields: list[str]
) -> None:
    x0, y0 = sheet.width - MARGIN - TB_W, sheet.height - MARGIN - TB_H
    sheet.add(Rect(x0, y0, TB_W, TB_H, width=0.5))
    values = {
        "project": project.meta.name, "harness_id": h.id, "title": h.name, "revision": h.revision,
        "status": h.status, "sheet": f"{n} / {total}", "date": h.released_on or "-", "author": h.author or "-", "checker": h.checker or "-", "approver": h.approver or "-",
    }  # fmt: skip
    cols, rows_n = 2, (len(fields) + 1) // 2
    cw, rh = TB_W / cols, (TB_H - 6.0) / max(1, rows_n)
    for k, key in enumerate(fields):
        cx, cy = x0 + (k % cols) * cw, y0 + (k // cols) * rh
        sheet.add(Line(cx, cy, cx + cw, cy, width=0.2))
        sheet.add(Text(cx + 1.0, cy + 2.2, key.replace("_", " ").upper(), size=1.8, color=GREY))
        sheet.add(
            Text(
                cx + 1.0,
                cy + rh - 1.2,
                fit(values.get(key, "-"), cw - 2.0, 3.0),
                size=3.0,
                bold=(key in ("harness_id", "status")),
            )
        )
    sheet.add(Line(x0 + cw, y0, x0 + cw, y0 + TB_H - 6.0, width=0.2))
    sheet.add(Line(x0, y0 + TB_H - 6.0, x0 + TB_W, y0 + TB_H - 6.0, width=0.2))
    sheet.add(
        Text(x0 + 1.0, y0 + TB_H - 2.0, fit(stamp.line, TB_W - 2.0, 2.4), size=2.4, color=GREY)
    )


def harness_sheets(project: Project, h: Harness, stamp: Stamp, size: str) -> list[Sheet]:
    w_mm, h_mm = SHEETS[size]
    fields = (
        [str(f) for f in (project.config["titleblock"].values.get("fields") or [])]
        if "titleblock" in project.config
        else []
    )
    fields = fields or ["project", "harness_id", "title", "revision", "status", "sheet"]
    head_h = 14.0
    capacity = h_mm - 2 * MARGIN - head_h - TB_H - 4.0
    groups: dict[tuple[str, str], list[Wire]] = {}
    for w in sorted(h.wires, key=lambda x: x.id):
        groups.setdefault(tuple(sorted((w.from_connector, w.to_connector))), []).append(w)  # type: ignore[arg-type]
    keys = sorted(groups)
    side = _sides(keys)
    items = [(g, w) for g in keys for w in groups[g]]
    layout = sketch_layout(h)
    sketch_h = sketch_height(layout) if layout is not None else 0.0
    pages = _paginate(items, side, capacity - sketch_h)
    extras = _extras(h)
    sheets: list[Sheet] = []
    bottoms: list[float] = []
    for n, pg in enumerate(pages, start=1):
        sh = _sheet_head(h, w_mm, h_mm, head_h)
        y = MARGIN + head_h
        if n == 1 and layout is not None:
            _draw_sketch(sh, h, y, w_mm)
            y += sketch_h
        bottoms.append(_draw_page(sh, project, h, pg, side, y))
        sheets.append(sh)
    # the lines beneath the diagram go below its last sheet when they fit, else on sheets of their own
    limit = h_mm - MARGIN - TB_H - 4.0
    lines_here = max(0, int((limit - bottoms[-1] - 6.0) / 4.4))
    rest = list(extras)
    y = bottoms[-1] + 6.0
    for line in rest[:lines_here]:
        y += 4.4
        sheets[-1].add(Text(MARGIN + 1.0, y, fit(line, w_mm - 2 * MARGIN - 2.0, SIZE), size=SIZE))
    rest = rest[lines_here:]
    per_sheet = int(capacity / 4.4)
    while rest:
        sh = _sheet_head(h, w_mm, h_mm, head_h)
        y = MARGIN + head_h
        for line in rest[:per_sheet]:
            y += 4.4
            sh.add(Text(MARGIN + 1.0, y, fit(line, w_mm - 2 * MARGIN - 2.0, SIZE), size=SIZE))
        sheets.append(sh)
        rest = rest[per_sheet:]
    total = len(sheets)
    for n, sh in enumerate(sheets, start=1):
        sh.title = f"{h.id} sheet {n}/{total}"
        _title_block(sh, project, h, stamp, n, total, fields)
    return sheets


def _sheet_head(h: Harness, w_mm: float, h_mm: float, head_h: float) -> Sheet:
    sh = Sheet(w_mm, h_mm)
    sh.add(Rect(MARGIN / 2, MARGIN / 2, w_mm - MARGIN, h_mm - MARGIN, width=0.6))
    sh.add(
        Text(
            MARGIN,
            MARGIN + 4.0,
            fit(f"{h.id}  {h.name}", w_mm - 2 * MARGIN, 4.2),
            size=4.2,
            bold=True,
        )
    )
    sh.add(
        Text(
            MARGIN, MARGIN + 9.0, f"Revision {h.revision}  status {h.status}", size=2.8, color=GREY
        )
    )
    return sh


def _draw_sketch(sh: Sheet, h: Harness, y: float, width: float) -> None:
    layout = sketch_layout(h)
    if layout is None:
        return
    sh.add(Text(MARGIN + 1.0, y + 4.0, "Routing (schematic, not to scale):", size=SIZE, bold=True))
    x0, y0 = MARGIN + 6.0, y + 7.0
    columns = max(col for col, _row in layout.values()) + 1
    natural = columns * NODE_W + (columns - 1) * NODE_GAP_X
    scale = min(1.0, (width - 2 * MARGIN - 6.0) / natural)  # a long chain is squeezed, not cut off
    node_w, gap_x = NODE_W * scale, NODE_GAP_X * scale
    pos = {
        n: (x0 + col * (node_w + gap_x), y0 + row * (NODE_H + NODE_GAP_Y))
        for n, (col, row) in layout.items()
    }
    for g in sorted(h.segments, key=lambda x: x.id):
        if g.from_node in pos and g.to_node in pos:
            (ax, ay), (bx, by) = pos[g.from_node], pos[g.to_node]
            if ax > bx:
                (ax, ay), (bx, by) = (bx, by), (ax, ay)
            xa, xb = ax + node_w, bx
            ya, yb = ay + NODE_H / 2, by + NODE_H / 2
            sh.add(Line(xa, ya, xb, yb, width=0.5))
            length = f"{num(g.length_m)} m" if g.length_m is not None else "? m"
            sh.add(
                Text(
                    (xa + xb) / 2,
                    (ya + yb) / 2 - 1.0,
                    fit(f"{g.id} {length}", gap_x, 2.2),
                    size=2.2,
                    anchor="middle",
                    color=GREY,
                )
            )
    connector_ids = {c.id for c in h.connectors}
    for n, (x, yy) in pos.items():
        sh.add(
            Rect(
                x,
                yy,
                node_w,
                NODE_H,
                width=0.4,
                fill="#ffffff" if n in connector_ids else "#e6e6e6",
            )
        )
        sh.add(
            Text(x + 1.0, yy + 4.6, fit(n, node_w - 2.0, SIZE), size=SIZE, bold=n in connector_ids)
        )
