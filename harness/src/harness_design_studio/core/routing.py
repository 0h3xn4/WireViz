"""Rules for drawing the links of the diagram that do not depend on Qt, so that they can be tested.

Three rules make a dense diagram readable: a link leaves a unit on the edge that faces the unit
at its other end (never through its own box), the links on one edge are ordered by the height of
their other ends (parallel links cross less), and a selection puts the links it concerns in
focus while everything else fades.
"""

from .model import Project


def side_toward(own_lane: int, other_lane: int, default: str) -> str:
    """The edge of a unit a link leaves from: the one that faces the unit at the other end. A link
    inside one lane leaves from the `default` edge (the one facing the middle of the diagram)."""
    if other_lane > own_lane:
        return "right"
    if other_lane < own_lane:
        return "left"
    return default


def order_links(links: list[tuple[str, float]]) -> list[str]:
    """Link IDs from top to bottom, ordered by the height of the unit at the other end (then by
    ID), so a link to a higher unit leaves higher up and parallel links do not cross."""
    return [iid for iid, _ in sorted(links, key=lambda t: (t[1], t[0]))]


def partner(project: Project, interface_id: str, unit_id: str) -> str | None:
    """The unit at the other end of an interface, or None for a link that ends twice on one unit."""
    i = project.interfaces.get(interface_id)
    if i is None:
        return None
    others = [e.unit_id for e in i.endpoints if e.unit_id != unit_id]
    return others[0] if others else None


def focus(project: Project, kind: str, ident: str) -> tuple[set[str], set[str]]:
    """(interface IDs, unit IDs) a selection concerns: an interface and its two units, or a unit,
    all its interfaces and the units at their other ends. Empty sets when it no longer exists."""
    if kind == "interface":
        i = project.interfaces.get(ident)
        if i is None:
            return set(), set()
        return {i.id}, {e.unit_id for e in i.endpoints}
    if kind == "unit" and ident in project.units:
        links = {
            i.id
            for i in project.interfaces.values()
            if any(e.unit_id == ident for e in i.endpoints)
        }
        units = {ident} | {e.unit_id for iid in links for e in project.interfaces[iid].endpoints}
        return links, units
    return set(), set()


def channel_share(index: int) -> float:
    """Where along its way between two lanes a link turns, as a share between 0.25 and 0.75 of the
    distance. The golden ratio spreads consecutive links evenly, so the links between two lanes do
    not all turn at the same place. Deterministic: it depends only on the link's number."""
    return 0.25 + 0.5 * ((index * 0.6180339887498949) % 1.0)


def same_lane_side(lane: int, lanes: int, default: str) -> str:
    """The edge for a link between two units of one lane: the edge away from the middle of the
    diagram when a lane on that side can hold the curve, so these links stay out of the busy
    channel between the middle lanes. Otherwise the `default` edge."""
    outer = "left" if default == "right" else "right"
    room = lane > 0 if outer == "left" else lane < lanes - 1
    return outer if room else default


def loop_reach(vertical_distance: float) -> float:
    """How far a link between two units of one lane bulges out of the lane. Links of different
    length get different curves (nested arcs), so a unit with many neighbours in its own lane shows
    a fan instead of one pile."""
    return min(150.0, 36.0 + 0.2 * abs(vertical_distance))
