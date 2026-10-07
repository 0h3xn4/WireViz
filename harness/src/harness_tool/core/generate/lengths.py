"""Wire lengths from routing segments, and CSV import of segment lengths (from CAD exports)."""

from collections import deque
from dataclasses import dataclass, field

from harness_tool.core.commands import Op, Put
from harness_tool.core.imports import Table
from harness_tool.core.model import Harness, Project, Segment, evolve


def path_length(h: Harness, start: str, end: str) -> float | None:
    """Sum of segment lengths along the (unique) path in the harness tree; None if any is unknown."""
    graph: dict[str, list[tuple[str, float | None]]] = {}
    for s in h.segments:
        graph.setdefault(s.from_node, []).append((s.to_node, s.length_m))
        graph.setdefault(s.to_node, []).append((s.from_node, s.length_m))
    seen = {start}
    queue: deque[tuple[str, list[float | None]]] = deque([(start, [])])
    while queue:
        node, trail = queue.popleft()
        if node == end:
            return (
                None
                if any(x is None for x in trail)
                else float(sum(x for x in trail if x is not None))
            )
        for nxt, length in graph.get(node, []):
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, [*trail, length]))
    return None


@dataclass
class LengthRow:
    row_number: int
    ok: bool
    message: str
    values: tuple[str, ...]


@dataclass
class LengthPlan:
    rows: list[LengthRow] = field(default_factory=list)
    ops: list[Op] = field(default_factory=list)


def plan_length_import(
    project: Project, table: Table, columns: tuple[int, int, int] = (0, 1, 2)
) -> LengthPlan:
    """Rows: harness ID, segment ID, length in metres. Applies as one undo step after confirmation."""
    plan = LengthPlan()
    pending: dict[str, Harness] = {}
    for n, row in enumerate(table[1:], start=2):
        vals = tuple(row[c].strip() if c < len(row) else "" for c in columns)
        hid, sid, text = vals
        error = ""
        h = pending.get(hid) or project.harnesses.get(hid)
        if h is None:
            error = f"Harness '{hid}' does not exist"
        elif h.status == "released":
            error = f"Harness '{hid}' is released and locked"
        elif sid not in {s.id for s in h.segments}:
            error = f"Harness '{hid}' has no segment '{sid}'"
        else:
            try:
                length = float(text)
                if not length >= 0 or length == float("inf"):
                    raise ValueError
            except ValueError:
                error = f"'{text}' is not a length in metres"
        if not error and h is not None:
            segs = [evolve(s, length_m=length) if s.id == sid else s for s in h.segments]
            pending[hid] = evolve(h, segments=segs)
        plan.rows.append(LengthRow(n, not error, error, vals))
    plan.ops = [Put("harnesses", h) for h in pending.values()]
    return plan


def segment_lengths_known(h: Harness) -> bool:
    return bool(h.segments) and all(s.length_m is not None for s in h.segments)


__all__ = [
    "LengthPlan",
    "LengthRow",
    "Segment",
    "path_length",
    "plan_length_import",
    "segment_lengths_known",
]
