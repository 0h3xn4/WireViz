"""Segmentation: which interfaces share a harness. Rules come from the `segmentation` and
`segregation` configuration (DECISIONS D-10: default one harness per pair of unit connectors)."""

from dataclasses import dataclass, field

from harness_tool.core.model import Endpoint, InterfaceInstance, Project

MODES = ("per_connector_pair", "per_unit_pair", "per_zone_pair")


@dataclass(frozen=True)
class Group:
    key: str
    mode: str
    chain: str
    interface_ids: tuple[str, ...]
    label: str  # human name of the harness, e.g. "OBC to RW1"


@dataclass
class Skipped:
    interface_id: str
    reason: str
    severity: str = "warning"


@dataclass
class Segmentation:
    groups: list[Group] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)
    mode: str = "per_connector_pair"
    notes: list[str] = field(default_factory=list)


def _cfg(project: Project, name: str) -> dict[str, object]:
    c = project.config.get(name)
    return dict(c.values) if c is not None else {}


def _class_of(
    project: Project, i: InterfaceInstance, seg: dict[str, object], sep: dict[str, object]
) -> str:
    cat = project.interface_types[i.type_id].category
    if cat == "pyro" and sep.get("forbid_pyro_with_other", True):
        return "pyro"
    pairs = sep.get("category_pairs_to_separate")
    if isinstance(pairs, list):
        separated = {c for pair in pairs if isinstance(pair, list) for c in pair}
        if cat in separated:
            return f"cat-{cat}"
    return "main"


def orient(
    project: Project, i: InterfaceInstance, mode: str, zones: tuple[str, str] | None
) -> tuple[Endpoint, Endpoint]:
    """Order the two endpoints so every interface of a group agrees on which end is X."""
    a, b = i.endpoints[0], i.endpoints[1]
    if mode == "per_connector_pair":
        return (a, b) if (a.connector_id or "") <= (b.connector_id or "") else (b, a)
    if mode == "per_unit_pair" or zones is None or zones[0] == zones[1]:
        return (a, b) if a.unit_id <= b.unit_id else (b, a)
    za = project.units[a.unit_id].zone or ""
    return (a, b) if za == zones[0] else (b, a)


def segment(project: Project) -> Segmentation:
    seg_cfg = _cfg(project, "segmentation")
    sep_cfg = _cfg(project, "segregation")
    mode = str(seg_cfg.get("mode", "per_connector_pair"))
    result = Segmentation(mode=mode if mode in MODES else "per_connector_pair")
    if mode not in MODES:
        result.notes.append(f"segmentation.mode '{mode}' is not known; using per_connector_pair")
    buckets: dict[str, list[str]] = {}
    labels: dict[str, str] = {}
    chains: dict[str, str] = {}
    manual = {
        w.interface_id
        for h in project.harnesses.values()
        if not h.generated
        for w in h.wires
        if w.interface_id
    }
    for i in sorted(project.interfaces.values(), key=lambda x: x.id):
        if i.id in manual:
            result.skipped.append(Skipped(i.id, "it is already routed by a manual harness", "info"))
            continue
        if i.type_id not in project.interface_types:
            result.skipped.append(Skipped(i.id, "its interface type does not exist", "error"))
            continue
        if len(i.endpoints) != 2:
            result.skipped.append(
                Skipped(i.id, "multi-drop interfaces (more than two units) are not generated yet")
            )
            continue
        a, b = i.endpoints
        if any(e.unit_id not in project.units for e in i.endpoints):
            result.skipped.append(Skipped(i.id, "a unit of this interface does not exist"))
            continue
        if a.connector_id is None or b.connector_id is None:
            result.skipped.append(Skipped(i.id, "a connector has not been chosen on every end"))
            continue
        if a.connector_id not in project.connectors or b.connector_id not in project.connectors:
            result.skipped.append(Skipped(i.id, "a connector of this interface does not exist"))
            continue
        chain = i.redundancy
        cls = _class_of(project, i, seg_cfg, sep_cfg)
        ua, ub = sorted([a.unit_id, b.unit_id])
        za, zb = sorted([project.units[a.unit_id].zone or "", project.units[b.unit_id].zone or ""])
        if result.mode == "per_connector_pair":
            ca, cb = sorted([a.connector_id, b.connector_id])
            key, label = f"cp|{chain}|{ca}|{cb}", f"{ca} to {cb}"
        elif result.mode == "per_unit_pair":
            key, label = f"up|{chain}|{cls}|{ua}|{ub}", f"{ua} to {ub}"
        else:
            key, label = f"zp|{chain}|{cls}|{za}|{zb}", f"{za or 'no zone'} to {zb or 'no zone'}"
        if cls != "main":
            label += f" ({cls.removeprefix('cat-')})"
        if chain == "redundant":
            label += " (redundant)"
        buckets.setdefault(key, []).append(i.id)
        labels[key] = label
        chains[key] = chain
    for key in sorted(buckets):
        result.groups.append(Group(key, result.mode, chains[key], tuple(buckets[key]), labels[key]))
    return result
