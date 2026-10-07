"""Harness drawing: for every pair of connectors, one row per wire (pin, signal, wire ID, gauge,
colour, length, pin), grouped under connector headings, with shields, segments and spare pins
listed beneath. A title block closes every sheet. Black and grey only, so it prints legibly on a
greyscale printer; wire colour is written as text, never used as a drawing colour.

Pagination: rows flow onto as many sheets as needed; every sheet repeats the headings.
"""

from dataclasses import dataclass

from harness_tool.core.model import Harness, Project, Wire

from .canvas import SHEETS, Line, Rect, Sheet, Text, fit
from .stamp import Stamp
from .tables import PENDING, num, wire_length

MARGIN = 8.0
TB_H = 42.0  # title block height
TB_W = 190.0
SIZE = 2.6
GREY = "#555555"


@dataclass(frozen=True)
class Row:
    kind: str  # "heading" | "wire" | "text" | "gap"
    text: str = ""
    wire: Wire | None = None
    group: tuple[str, str] | None = None


HEIGHT = {"heading": 9.0, "wire": 8.0, "text": 4.4, "gap": 3.0}


def _rows(project: Project, h: Harness) -> list[Row]:
    rows: list[Row] = []
    cables = {c.id: c for c in h.connectors}
    groups: dict[tuple[str, str], list[Wire]] = {}
    for w in sorted(h.wires, key=lambda x: x.id):
        groups.setdefault(tuple(sorted((w.from_connector, w.to_connector))), []).append(w)  # type: ignore[arg-type]
    for (a, b), wires in sorted(groups.items()):
        ca, cb = cables.get(a), cables.get(b)
        rows.append(
            Row(
                "heading",
                f"{a} ({ca.part_id if ca else '?'})  to  {b} ({cb.part_id if cb else '?'})",
                group=(a, b),
            )
        )
        rows += [Row("wire", wire=w, group=(a, b)) for w in wires]
    rows.append(Row("gap"))
    if h.shields:
        rows.append(Row("text", "Shields:"))
        for s in sorted(h.shields, key=lambda x: x.id):
            rows.append(
                Row(
                    "text",
                    f"  {s.id} ({s.kind}) wires {', '.join(sorted(s.wire_ids))}; ends {s.end_a} / {s.end_b}",
                )
            )
    if h.segments:
        rows.append(Row("text", "Routing segments:"))
        for g in sorted(h.segments, key=lambda x: x.id):
            rows.append(
                Row(
                    "text",
                    f"  {g.id}: {g.from_node} to {g.to_node}, length {num(g.length_m) + ' m' if g.length_m is not None else 'unknown'}",
                )
            )
    for c in sorted(h.connectors, key=lambda x: x.id):
        used = {(w.from_connector, w.from_pin) for w in h.wires} | {
            (w.to_connector, w.to_pin) for w in h.wires
        }
        spare = [p.id for p in c.pins if (c.id, p.id) not in used]
        if spare:
            rows.append(Row("text", f"Spare pins {c.id}: {', '.join(spare)}"))
    if h.notes:
        rows.append(Row("text", f"Notes: {h.notes}"))
    return rows


def _paginate(rows: list[Row], capacity: float) -> list[list[Row]]:
    pages: list[list[Row]] = [[]]
    used = 0.0
    current: Row | None = None
    for r in rows:
        need = HEIGHT[r.kind]
        if (
            r.kind == "wire"
            and (used == 0.0 or used + need > capacity)
            and used != 0.0
            or used + need > capacity
            and used != 0.0
        ):
            pages.append([])
            used = 0.0
        if (
            r.kind == "wire"
            and used == 0.0
            and r.group is not None
            and current is not None
            and current.group == r.group
        ):
            heading = Row("heading", current.text + "  (continued)", group=r.group)
            pages[-1].append(heading)
            used += HEIGHT["heading"]
        pages[-1].append(r)
        used += need
        if r.kind == "heading" or r.kind == "wire" and current is None:
            current = r
    return [p for p in pages if p] or [[]]


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
    pages = _paginate(_rows(project, h), capacity)
    total = len(pages)
    sheets: list[Sheet] = []
    for n, rows in enumerate(pages, start=1):
        sh = Sheet(w_mm, h_mm, title=f"{h.id} sheet {n}/{total}")
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
                MARGIN,
                MARGIN + 9.0,
                f"Revision {h.revision}  status {h.status}",
                size=2.8,
                color=GREY,
            )
        )
        y = MARGIN + head_h
        left_w = 52.0
        mid_x0 = MARGIN + left_w
        right_w = 52.0
        mid_x1 = w_mm - MARGIN - right_w
        for r in rows:
            hgt = HEIGHT[r.kind]
            if r.kind == "heading":
                sh.add(Rect(MARGIN, y, w_mm - 2 * MARGIN, hgt - 2.0, width=0.3, fill="#e6e6e6"))
                sh.add(
                    Text(
                        MARGIN + 1.5,
                        y + hgt - 4.0,
                        fit(r.text, w_mm - 2 * MARGIN - 3.0, SIZE + 0.4),
                        size=SIZE + 0.4,
                        bold=True,
                    )
                )
            elif r.kind == "wire" and r.wire is not None:
                w = r.wire
                ya = y + hgt - 3.0
                flip = r.group is not None and w.from_connector != r.group[0]
                (ca_, pa_), (cb_, pb_) = [
                    (w.from_connector, w.from_pin),
                    (w.to_connector, w.to_pin),
                ][:: -1 if flip else 1]
                pa = _pin_label(ca_, pa_, project, h)
                pb = _pin_label(cb_, pb_, project, h)
                sh.add(Text(MARGIN + 1.0, ya, fit(pa, left_w - 2.0, SIZE), size=SIZE))
                sh.add(
                    Text(
                        w_mm - MARGIN - 1.0,
                        ya,
                        fit(pb, right_w - 2.0, SIZE),
                        size=SIZE,
                        anchor="end",
                    )
                )
                sh.add(Line(mid_x0, ya - 1.0, mid_x1, ya - 1.0, width=0.5))
                gauge = PENDING if w.gauge_awg is None else f"AWG {w.gauge_awg}"
                length = wire_length(h, w)
                info = f"{gauge}  {w.colour or 'colour n/a'}  {num(length) + ' m' if length is not None else 'length n/a'}  {w.part_id or ''}"
                mid_w = mid_x1 - mid_x0
                sh.add(
                    Text(
                        (mid_x0 + mid_x1) / 2,
                        ya - 2.0,
                        fit(f"{w.id}  {w.signal or ''}", mid_w, SIZE),
                        size=SIZE,
                        bold=True,
                        anchor="middle",
                    )
                )
                sh.add(
                    Text(
                        (mid_x0 + mid_x1) / 2,
                        ya + 2.2,
                        fit(info, mid_w, SIZE - 0.3),
                        size=SIZE - 0.3,
                        anchor="middle",
                        color=GREY,
                    )
                )
            elif r.kind == "text":
                sh.add(
                    Text(
                        MARGIN + 1.0,
                        y + hgt - 1.2,
                        fit(r.text, w_mm - 2 * MARGIN - 2.0, SIZE),
                        size=SIZE,
                    )
                )
            y += hgt
        _title_block(sh, project, h, stamp, n, total, fields)
        sheets.append(sh)
    return sheets


def _pin_label(cid: str, pin: str, project: Project, h: Harness) -> str:
    conn = next((c for c in h.connectors if c.id == cid), None)
    box = project.connectors.get(conn.mates_with or "") if conn else None
    signal = None
    for c in (conn, box):
        signal = next((p.signal for p in (c.pins if c else []) if p.id == pin and p.signal), None)
        if signal:
            break
    return f"{cid}:{pin}" + (f" {signal}" if signal else "")
