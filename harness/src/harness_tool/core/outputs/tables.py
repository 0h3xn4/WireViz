"""Tables derived from the model: wire list, pinouts, BOM, mass and length, tests, labels,
matrices. Each function returns `Table` (header row first). No design numbers are invented:
unknown values are written as "pending", "unknown" or "TBD (placeholder)"."""

from collections import defaultdict

from harness_tool.core.generate.lengths import path_length
from harness_tool.core.generate.mass import harness_mass
from harness_tool.core.model import Connector, Harness, Project, Wire

from .stamp import Table

PENDING = "pending"
TBD = "TBD (placeholder)"


def num(v: float | None) -> str:
    return "" if v is None else f"{v:.6g}"


_PATHS: dict[tuple[int, str, str], tuple[Harness, float | None]] = {}


def clear_cache() -> None:
    _PATHS.clear()


def wire_length(h: Harness, w: Wire) -> float | None:
    """The wire's own length, else the sum of routing segments between its connectors."""
    if w.length_m is not None:
        return w.length_m
    if not h.segments:
        return None
    key = (id(h), w.from_connector, w.to_connector)
    hit = _PATHS.get(key)
    if hit is None or hit[0] is not h:  # the identity check guards against reused object ids
        hit = _PATHS[key] = (h, path_length(h, w.from_connector, w.to_connector))
    return hit[1]


def shield_of(h: Harness) -> dict[str, str]:
    return {wid: s.id for s in h.shields for wid in s.wire_ids}


def wire_list(project: Project, h: Harness) -> Table:
    shields = shield_of(h)
    rows: Table = [[
        "Wire", "Signal", "Interface", "From connector", "From pin", "To connector", "To pin",
        "AWG", "Part", "Colour", "Length (m)", "Shield group", "Locked",
    ]]  # fmt: skip
    for w in sorted(h.wires, key=lambda x: x.id):
        rows.append([
            w.id, w.signal or "", w.interface_id or "", w.from_connector, w.from_pin,
            w.to_connector, w.to_pin, PENDING if w.gauge_awg is None else str(w.gauge_awg),
            w.part_id or "", w.colour or "", num(wire_length(h, w)), shields.get(w.id, ""),
            "yes" if w.locked else "",
        ])  # fmt: skip
    return rows


def _pin_rows(project: Project, c: Connector, attached: dict[tuple[str, str], list[str]]) -> Table:
    rows: Table = []
    for p in c.pins:
        wires = attached.get((c.id, p.id), [])
        rows.append([
            c.id, c.role, c.mates_with or "", c.part_id, p.id, p.signal or "", p.interface_id or "",
            ";".join(wires), "no" if wires or p.interface_id or p.signal else "yes",
        ])  # fmt: skip
    return rows


PINOUT_HEADER = [
    "Connector",
    "Role",
    "Mates with",
    "Part",
    "Pin",
    "Signal",
    "Interface",
    "Wires",
    "Spare",
]


def pinouts(project: Project, h: Harness) -> Table:
    attached: dict[tuple[str, str], list[str]] = defaultdict(list)
    for w in h.wires:
        attached[(w.from_connector, w.from_pin)].append(w.id)
        attached[(w.to_connector, w.to_pin)].append(w.id)
    rows = [PINOUT_HEADER]
    for c in sorted(h.connectors, key=lambda x: x.id):
        rows += _pin_rows(project, c, attached)
    return rows


def box_pinouts(project: Project) -> Table:
    attached: dict[tuple[str, str], list[str]] = defaultdict(list)
    for h in project.harnesses.values():
        mates = {c.id: c.mates_with for c in h.connectors}
        for w in h.wires:
            for cid, pin in ((w.from_connector, w.from_pin), (w.to_connector, w.to_pin)):
                if mates.get(cid):
                    attached[(mates[cid] or "", pin)].append(w.id)
    rows = [PINOUT_HEADER]
    for c in sorted(project.connectors.values(), key=lambda x: x.id):
        rows += _pin_rows(project, c, attached)
    return rows


BOM_HEADER = [
    "Part", "Category", "Manufacturer", "Part number", "Description", "Approval",
    "Quantity", "Unit", "Wires without length", "Used in",
]  # fmt: skip


def bom(project: Project, harnesses: list[Harness]) -> Table:
    counts: dict[str, int] = defaultdict(int)
    metres: dict[str, float] = defaultdict(float)
    unknown: dict[str, int] = defaultdict(int)
    used: dict[str, set[str]] = defaultdict(set)
    for h in harnesses:
        for c in h.connectors:
            counts[c.part_id] += 1
            used[c.part_id].add(h.id)
        for w in h.wires:
            pid = w.part_id or "(no part)"
            used[pid].add(h.id)
            length = wire_length(h, w)
            if length is None:
                unknown[pid] += 1
            else:
                metres[pid] += length
            metres.setdefault(pid, 0.0)
    rows = [BOM_HEADER]
    for pid in sorted({*counts, *metres}):
        part = project.parts.get(pid)
        is_wire = pid in metres
        rows.append([
            pid, part.category if part else "unknown", (part.manufacturer or "") if part else "",
            (part.part_number or "") if part else "", (part.description or "") if part else "",
            ("missing from parts list" if part is None else part.approval + (" (example data)" if part.unverified else "")),
            num(round(metres[pid], 6)) if is_wire else str(counts[pid]), "m" if is_wire else "ea",
            str(unknown[pid]) if is_wire else "", ";".join(sorted(used[pid])),
        ])  # fmt: skip
    return rows


MASS_HEADER = [
    "Harness", "Wires", "Connectors", "Wire length known (m)", "Wires without length",
    "Mass of known parts (g)", "Margin (g)", "Mass with margin (g)", "Complete", "Missing data",
]  # fmt: skip


def mass_length(project: Project, harnesses: list[Harness]) -> Table:
    rows = [MASS_HEADER]
    tot_len = tot_mass = 0.0
    tot_unknown = tot_wires = tot_conn = 0
    complete = True
    margins: list[float | None] = []
    for h in harnesses:
        r = harness_mass(project, h)
        lengths = [wire_length(h, w) for w in h.wires]
        known = sum(x for x in lengths if x is not None)
        unk = sum(1 for x in lengths if x is None)
        rows.append([
            h.id, str(len(h.wires)), str(len(h.connectors)), num(round(known, 6)), str(unk),
            num(round(r.total_g, 6)), num(r.margin_g), num(r.with_margin_g),
            "yes" if r.complete and unk == 0 else "no", "; ".join(r.missing),
        ])  # fmt: skip
        tot_len += known
        tot_mass += r.total_g
        tot_unknown += unk
        tot_wires += len(h.wires)
        tot_conn += len(h.connectors)
        complete = complete and r.complete and unk == 0
        margins.append(r.margin_g)
    margin = None if any(m is None for m in margins) else sum(m for m in margins if m is not None)
    rows.append([
        "TOTAL", str(tot_wires), str(tot_conn), num(round(tot_len, 6)), str(tot_unknown),
        num(round(tot_mass, 6)), num(margin), num(None if margin is None else tot_mass + margin),
        "yes" if complete else "no", "totals count only what is known" if not complete else "",
    ])  # fmt: skip
    return rows


def _cfg(project: Project, key: str) -> object:
    c = project.config.get("generation")
    return c.values.get(key) if c else None


def _limit(project: Project, key: str, unit: str) -> str:
    v = _cfg(project, key)
    return f"{v:g} {unit}" if isinstance(v, int | float) and not isinstance(v, bool) else TBD


def tests(project: Project, h: Harness) -> Table:
    cont = _limit(project, "test_continuity_max_ohm", "ohm max")
    iso = _limit(project, "test_isolation_min_mohm", "Mohm min")
    volts = _limit(project, "test_isolation_voltage_v", "V")
    rows: Table = [["Test", "Type", "From", "To", "Expected", "Limit", "Test voltage", "Wire"]]
    n = 0
    for w in sorted(h.wires, key=lambda x: x.id):
        n += 1
        rows.append([f"T{n:03d}", "continuity", f"{w.from_connector}.{w.from_pin}", f"{w.to_connector}.{w.to_pin}", "continuous", cont, "", w.id])  # fmt: skip
    for w in sorted(h.wires, key=lambda x: x.id):
        n += 1
        rows.append([f"T{n:03d}", "isolation", f"{w.from_connector}.{w.from_pin}", "all other wires and shields", "isolated", iso, volts, w.id])  # fmt: skip
    for s in sorted(h.shields, key=lambda x: x.id):
        n += 1
        rows.append([f"T{n:03d}", "isolation", f"shield {s.id}", "all wires", "isolated", iso, volts, ";".join(sorted(s.wire_ids))])  # fmt: skip
    return rows


def labels(project: Project, h: Harness) -> Table:
    rows: Table = [["Label", "Kind", "Text", "Quantity"]]
    for c in sorted(h.connectors, key=lambda x: x.id):
        rows.append([f"{c.id}", "connector", f"{c.id} mates {c.mates_with or '-'}", "1"])
    for w in sorted(h.wires, key=lambda x: x.id):
        far = f"{w.to_connector}.{w.to_pin}"
        near = f"{w.from_connector}.{w.from_pin}"
        rows.append(
            [f"{w.id}-A", "wire", f"{w.id} {w.signal or ''} to {far}".replace("  ", " "), "1"]
        )
        rows.append(
            [f"{w.id}-B", "wire", f"{w.id} {w.signal or ''} to {near}".replace("  ", " "), "1"]
        )
    return rows


def mating_matrix(project: Project) -> Table:
    """Every box connector with the cable connector that plugs into it (if any)."""
    mated: dict[str, list[tuple[str, Connector]]] = defaultdict(list)
    for h in project.harnesses.values():
        for c in h.connectors:
            if c.mates_with:
                mated[c.mates_with].append((h.id, c))
    rows: Table = [
        ["Box connector", "Unit", "Part", "Gender", "Cable connector", "Cable part", "Harness"]
    ]
    for b in sorted(project.connectors.values(), key=lambda x: x.id):
        pairs = sorted(mated.get(b.id, []), key=lambda t: t[1].id) or [("", None)]  # type: ignore[list-item]
        for hid, c in pairs:
            rows.append(
                [
                    b.id,
                    b.unit_id or "",
                    b.part_id,
                    b.gender,
                    c.id if c else "",
                    c.part_id if c else "",
                    hid,
                ]
            )
    return rows


def traceability(project: Project) -> Table:
    carried: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for h in project.harnesses.values():
        for w in h.wires:
            if w.interface_id:
                carried[w.interface_id].append((h.id, w.id))
    rows: Table = [["Interface", "Name", "Type", "From", "To", "Harnesses", "Wires", "Routed"]]
    for i in sorted(project.interfaces.values(), key=lambda x: x.id):
        ends = [f"{e.unit_id}/{e.connector_id or '-'}" for e in i.endpoints]
        hs = sorted({h for h, _ in carried.get(i.id, [])})
        ws = sorted(w for _, w in carried.get(i.id, []))
        rows.append([i.id, i.name, i.type_id, ends[0] if ends else "", ends[1] if len(ends) > 1 else "", ";".join(hs), ";".join(ws), "yes" if ws else "no"])  # fmt: skip
    return rows
