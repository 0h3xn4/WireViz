"""Explain data: the recorded reasons behind generated objects (no guessing, only what was logged)."""

from harness_design_studio.core.model import Harness, Project, Wire


def explain_wire(project: Project, h: Harness, w: Wire) -> list[str]:
    prov = project.generation.provenance if project.generation else {}
    keys = [f"wire:{w.id}", f"gauge:{w.id}", f"harness:{h.id}"]
    cables = {c.id: c for c in h.connectors}
    for cid, pin in ((w.from_connector, w.from_pin), (w.to_connector, w.to_pin)):
        box = cables[cid].mates_with if cid in cables else None
        if box:
            keys.append(f"pin:{box}.{pin}")
    out: list[str] = []
    for k in keys:
        out.extend(prov.get(k, []))
    return out


def explain_harness(project: Project, h: Harness) -> list[str]:
    prov = project.generation.provenance if project.generation else {}
    return list(prov.get(f"harness:{h.id}", []))
