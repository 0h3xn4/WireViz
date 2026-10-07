"""What a baseline stores: one harness and the design objects it depends on."""

from harness_tool.core.model import Harness, Project, Snapshot, evolve


def normalize(h: Harness) -> Harness:
    """Lists in a fixed order (by ID), so equal harnesses compare equal however they were built."""
    return evolve(
        h,
        connectors=sorted(h.connectors, key=lambda x: x.id),
        wires=sorted(h.wires, key=lambda x: x.id),
        splices=sorted(h.splices, key=lambda x: x.id),
        shields=sorted(h.shields, key=lambda x: x.id),
        branch_points=sorted(h.branch_points, key=lambda x: x.id),
        segments=sorted(h.segments, key=lambda x: x.id),
        interfaces=sorted(h.interfaces),
    )


def carried_interfaces(h: Harness) -> set[str]:
    return {w.interface_id for w in h.wires if w.interface_id} | set(h.interfaces)


def snapshot_for(project: Project, h: Harness) -> Snapshot:
    interfaces = [
        project.interfaces[i] for i in sorted(carried_interfaces(h)) if i in project.interfaces
    ]
    units = sorted(
        {e.unit_id for i in interfaces for e in i.endpoints if e.unit_id in project.units}
    )
    boxes = {c.mates_with for c in h.connectors if c.mates_with}
    boxes |= {e.connector_id for i in interfaces for e in i.endpoints if e.connector_id}
    return Snapshot(
        units=[project.units[u] for u in units],
        interfaces=interfaces,
        connectors=[project.connectors[c] for c in sorted(boxes) if c in project.connectors],
        harnesses=[normalize(h)],
    )


def related_ids(project: Project, h: Harness) -> set[str]:
    """Every object ID that belongs to the harness (for scoping verifier and rule findings)."""
    ids = (
        {h.id} | {c.id for c in h.connectors} | {w.id for w in h.wires} | {s.id for s in h.shields}
    )
    ids |= carried_interfaces(h)
    ids |= {c.mates_with for c in h.connectors if c.mates_with}
    ids |= {
        e.connector_id
        for i in carried_interfaces(h)
        if i in project.interfaces
        for e in project.interfaces[i].endpoints
        if e.connector_id
    }
    return ids
