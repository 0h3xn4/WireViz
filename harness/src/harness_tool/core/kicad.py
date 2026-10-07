"""Read unit connector pinouts from a KiCad XML netlist and apply them to a unit (D-123).

KiCad is where each unit's electronics, and so each connector's pinout, are designed. A netlist
(`kicad-cli sch export netlist --format kicadxml`) says which net is on which pin of which
connector. This module turns that into box connectors with `fixed` pins: generation then connects
interfaces to the pin whose signal has the interface signal's name and never moves it.

What is not known yet is how your KiCad names relate to the tool's, so nothing is assumed:
- connector IDs: the symbol field `HarnessConnector` if present, else `--connector REF=ID`, else
  `<unit>-<reference>` (for example OBC1-J1);
- library part of a new connector: the field `HarnessPart`, else `--part REF=PART`, else the part
  of the connector that already exists; otherwise the row is an error;
- signal names: the net name without its sheet path, translated by a mapping table you give;
  names that match no signal of any interface type are reported so you can build that table.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree  # noqa: S405 - DOCTYPE and entities are refused before parsing

from harness_tool.core.commands import Op, Put
from harness_tool.core.errors import HarnessError
from harness_tool.core.ids import ID_RE, PIN_RE
from harness_tool.core.model import Connector, Pin, Project, evolve

MAX_BYTES = 32 * 1024 * 1024
CONNECTOR_FIELD = "harnessconnector"
PART_FIELD = "harnesspart"


class NetlistError(HarnessError):
    """The file cannot be read as a KiCad XML netlist."""


@dataclass
class PinInfo:
    number: str
    net: str  # raw net name as KiCad wrote it
    function: str = ""  # the pin name in the symbol (pinfunction), if any
    pin_type: str = ""


@dataclass
class Component:
    ref: str
    value: str = ""
    footprint: str = ""
    fields: dict[str, str] = field(default_factory=dict)  # lower-case name -> value
    pins: dict[str, PinInfo] = field(default_factory=dict)


@dataclass
class Netlist:
    source: str = ""
    components: dict[str, Component] = field(default_factory=dict)


def parse_netlist(data: bytes) -> Netlist:
    """Parse a KiCad XML netlist. Hostile input is refused: no DOCTYPE or entities, size limit."""
    if len(data) > MAX_BYTES:
        raise NetlistError("The netlist is too large (limit 32 MB).")
    if b"<!doctype" in data[:100_000].lower() or b"<!entity" in data.lower():
        raise NetlistError(
            "The file contains a DOCTYPE or entity declaration, which a netlist never needs; it was not read."
        )
    try:
        root = ElementTree.fromstring(data)  # noqa: S314
    except ElementTree.ParseError as exc:
        raise NetlistError(f"The file is not valid XML ({exc}).") from exc
    if root.tag != "export":
        raise NetlistError(
            "The file is XML but not a KiCad netlist (no <export> element). Export it with: kicad-cli sch export netlist --format kicadxml"
        )
    result = Netlist(source=(root.findtext("design/source") or "").strip())
    for comp in root.findall("components/comp"):
        ref = (comp.get("ref") or "").strip()
        if not ref:
            continue
        c = Component(
            ref=ref,
            value=(comp.findtext("value") or "").strip(),
            footprint=(comp.findtext("footprint") or "").strip(),
        )
        for f in comp.findall("fields/field"):
            name = "".join((f.get("name") or "").lower().split()).replace("_", "")
            if name:
                c.fields[name] = (f.text or "").strip()
        result.components[ref] = c
    for net in root.findall("nets/net"):
        name = net.get("name") or ""
        for node in net.findall("node"):
            ref, pin = (node.get("ref") or "").strip(), (node.get("pin") or "").strip()
            target = result.components.get(ref)
            if target is None or not pin:
                continue
            target.pins[pin] = PinInfo(
                pin,
                name,
                (node.get("pinfunction") or "").strip(),
                (node.get("pintype") or "").strip(),
            )
    return result


def read_netlist(path: Path | str) -> Netlist:
    p = Path(path)
    try:
        if p.stat().st_size > MAX_BYTES:
            raise NetlistError("The netlist is too large (limit 32 MB).")
        return parse_netlist(p.read_bytes())
    except OSError as exc:
        raise NetlistError(f"The file could not be read ({exc.strerror}).") from exc


def clean_net(name: str) -> str | None:
    """The signal name KiCad's net name stands for, or None for nets that name nothing:
    sheet paths are dropped ("/power/28V" -> "28V"); "Net-(J1-Pad3)" and "unconnected-(...)"
    are KiCad's own names for pins nobody named or connected."""
    n = name.strip()
    if not n or n.startswith("unconnected-") or n.startswith("Net-(") or n.startswith("/Net-("):
        return None
    return n.rsplit("/", 1)[-1] or None


def natural_key(text: str) -> tuple[object, ...]:
    return tuple(int(t) if t.isdigit() else t for t in re.split(r"(\d+)", text))


@dataclass
class RowResult:
    ref: str
    ok: bool
    message: str
    connector_id: str = ""
    action: str = ""  # "added" | "updated"
    pins: int = 0


@dataclass
class NetlistPlan:
    rows: list[RowResult] = field(default_factory=list)
    ops: list[Op] = field(default_factory=list)
    unmatched_signals: dict[str, list[str]] = field(default_factory=dict)  # signal -> where seen
    warnings: list[str] = field(default_factory=list)

    @property
    def ok_count(self) -> int:
        return sum(r.ok for r in self.rows)


def known_signals(project: Project) -> set[str]:
    return {s.name for t in project.interface_types.values() for s in t.signals}


def plan_netlist_import(
    project: Project,
    netlist: Netlist,
    unit_id: str,
    *,
    refs: list[str] | None = None,
    prefix: str = "J",
    connector_ids: dict[str, str] | None = None,
    parts: dict[str, str] | None = None,
    signal_map: dict[str, str] | None = None,
    use_pin_function: bool = False,
) -> NetlistPlan:
    """One row per connector component. `refs` selects connectors by reference (default: every
    component whose reference starts with `prefix`). Nothing is applied here."""
    plan = NetlistPlan()
    if unit_id not in project.units:
        plan.rows.append(RowResult("", False, f"Unit '{unit_id}' does not exist"))
        return plan
    chosen = (
        refs
        if refs
        else sorted((r for r in netlist.components if r.startswith(prefix)), key=natural_key)
    )
    if not chosen:
        plan.rows.append(
            RowResult(
                "", False, f"No component starts with '{prefix}'. Name the connectors with --ref"
            )
        )
        return plan
    wanted = known_signals(project)
    mapping = signal_map or {}
    taken: dict[str, str] = {}
    for ref in chosen:
        comp = netlist.components.get(ref)
        if comp is None:
            plan.rows.append(RowResult(ref, False, f"'{ref}' is not in the netlist"))
            continue
        cid = (
            (connector_ids or {}).get(ref) or comp.fields.get(CONNECTOR_FIELD) or f"{unit_id}-{ref}"
        )
        if not ID_RE.fullmatch(cid) or cid.endswith("."):
            plan.rows.append(
                RowResult(
                    ref,
                    False,
                    f"'{cid}' cannot be a connector ID (letters, digits, - _ . and a letter first); set the field HarnessConnector or use --connector {ref}=ID",
                    cid,
                )
            )
            continue
        if cid in taken:
            plan.rows.append(
                RowResult(ref, False, f"'{cid}' is already used for {taken[cid]}", cid)
            )
            continue
        old = project.connectors.get(cid)
        if old is not None and old.unit_id != unit_id:
            plan.rows.append(
                RowResult(ref, False, f"'{cid}' belongs to another unit ({old.unit_id})", cid)
            )
            continue
        part_id = (
            (parts or {}).get(ref) or comp.fields.get(PART_FIELD) or (old.part_id if old else "")
        )
        part = project.parts.get(part_id)
        if part is None or part.category != "connector":
            why = (
                "has no library part: set the field HarnessPart or use --part " + ref + "=PART"
                if not part_id
                else f"'{part_id}' is not a connector part in the library"
            )
            plan.rows.append(RowResult(ref, False, f"Connector {cid} {why}", cid))
            continue
        pins: dict[str, Pin] = {}
        bad = [n for n in comp.pins if not PIN_RE.fullmatch(n)]
        if bad:
            plan.rows.append(
                RowResult(
                    ref,
                    False,
                    f"Pin number '{bad[0]}' cannot be used (letters and digits, at most 16 characters)",
                    cid,
                )
            )
            continue
        seen_names: dict[str, str] = {}
        for number in sorted(comp.pins, key=natural_key):
            info = comp.pins[number]
            raw = (info.function if use_pin_function else clean_net(info.net)) or None
            signal = mapping.get(raw, raw) if raw else None
            if signal is not None and signal not in wanted:
                plan.unmatched_signals.setdefault(signal, []).append(f"{cid} pin {number}")
            if signal is not None and signal in seen_names:
                plan.warnings.append(
                    f"{cid}: signal '{signal}' is on pins {seen_names[signal]} and {number}; interfaces use the first free one"
                )
            if signal is not None:
                seen_names.setdefault(signal, number)
            was = next((p for p in (old.pins if old else []) if p.id == number), None)
            base = was or Pin(id=number)
            pins[number] = evolve(
                base,
                signal=signal,
                fixed=signal is not None,
                interface_id=None if signal is not None else base.interface_id,
            )
        if part.pin_count and all(n.isdigit() for n in pins) and len(pins) < part.pin_count:
            for k in range(1, part.pin_count + 1):  # pins KiCad never mentions are spare
                pins.setdefault(
                    str(k),
                    next((p for p in (old.pins if old else []) if p.id == str(k)), Pin(id=str(k))),
                )
        kept = [p for p in (old.pins if old else []) if p.id not in pins]
        if kept:
            plan.warnings.append(
                f"{cid}: {len(kept)} existing pin(s) are not in the netlist and were kept as they are"
            )
        merged = sorted([*pins.values(), *kept], key=lambda p: natural_key(p.id))
        if old is not None:
            conn = evolve(old, pins=merged, part_id=part_id)
        else:
            conn = Connector(
                id=cid,
                name=ref,
                role="box",
                part_id=part_id,
                unit_id=unit_id,
                gender="unspecified",
                pins=merged,
            )
        taken[cid] = ref
        plan.ops.append(Put("connectors", conn))
        plan.rows.append(
            RowResult(
                ref, True, "", cid, "updated" if old else "added", sum(1 for p in merged if p.fixed)
            )
        )
    return plan
