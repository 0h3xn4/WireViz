"""Import an approved-parts list (CSV or XLSX) into the project's parts library (D-12).

The tool does not know any program's list format, so columns are mapped by header name (with
common aliases) and the meaning of the approval column is stated by you: values you list as
approved, pending or rejected. A status that is not in any of your lists is an error for that
row; the tool never guesses whether a part is approved. Preview first, apply as one undo step.
"""

from dataclasses import dataclass, field

from harness_tool.core.commands import Op, Put
from harness_tool.core.ids import ID_RE
from harness_tool.core.model import Part, Project, evolve
from harness_tool.core.model.library import PART_CATEGORIES

Table = list[list[str]]

FIELDS: tuple[tuple[str, str], ...] = (
    ("id", "Part ID"), ("category", "Category"), ("manufacturer", "Manufacturer"),
    ("part_number", "Part number"), ("description", "Description"), ("specification", "Specification"),
    ("approval", "Approval status"), ("pin_count", "Pin count"), ("mass_g", "Mass (g)"),
    ("mass_per_m_g", "Mass per metre (g/m)"), ("mates_with", "Mating part ID"),
)  # fmt: skip
_ALIASES = {
    "id": ("id", "partid", "part", "item", "ref"),
    "category": ("category", "type", "class", "kind"),
    "manufacturer": ("manufacturer", "mfr", "vendor", "supplier", "maker"),
    "part_number": ("partnumber", "pn", "mpn", "partno", "number"),
    "description": ("description", "desc", "name", "title"),
    "specification": ("specification", "spec", "standard"),
    "approval": ("approval", "status", "approvalstatus", "eppl", "approved", "qualification"),
    "pin_count": ("pincount", "pins", "contacts", "positions"),
    "mass_g": ("massg", "mass", "weightg", "weight"),
    "mass_per_m_g": ("masspermg", "gpm", "massperm", "weightperm"),
    "mates_with": ("mateswith", "mate", "mating", "matingpart"),
}


@dataclass
class PartRow:
    row_number: int
    ok: bool
    message: str
    part_id: str = ""
    action: str = ""  # "added" | "updated"


@dataclass
class PartsPlan:
    rows: list[PartRow] = field(default_factory=list)
    ops: list[Op] = field(default_factory=list)

    @property
    def ok_count(self) -> int:
        return sum(r.ok for r in self.rows)


def guess_mapping(header: list[str]) -> dict[str, int]:
    norm = ["".join(ch for ch in h.lower() if ch.isalnum()) for h in header]
    out: dict[str, int] = {}
    used: set[int] = set()
    for key, _ in FIELDS:
        for alias in _ALIASES[key]:
            hit = next((i for i, h in enumerate(norm) if h == alias and i not in used), None)
            if hit is not None:
                out[key] = hit
                used.add(hit)
                break
    return out


def _words(values: list[str]) -> set[str]:
    return {v.strip().casefold() for v in values if v.strip()}


def _number(text: str) -> float | None:
    try:
        value = float(text.replace(",", "."))
    except ValueError:
        return None
    return value if value >= 0 and value == value and value != float("inf") else None


def plan_parts_import(
    project: Project,
    table: Table,
    mapping: dict[str, int],
    *,
    approved: list[str],
    pending: list[str] | None = None,
    rejected: list[str] | None = None,
    default_category: str | None = None,
) -> PartsPlan:
    """One result per data row. `approved`, `pending` and `rejected` say what the values of the
    approval column mean in YOUR list."""
    ok_words, pend_words, rej_words = (
        _words(approved),
        _words(pending or []),
        _words(rejected or []),
    )
    plan = PartsPlan()
    seen: dict[str, Part] = {}
    for n, row in enumerate(table[1:], start=2):

        def cell(key: str, row: list[str] = row) -> str:
            i = mapping.get(key)
            return row[i].strip() if i is not None and i < len(row) else ""

        pid = cell("id") or cell("part_number")
        if not pid:
            plan.rows.append(PartRow(n, False, "The row has no part ID or part number"))
            continue
        if not ID_RE.fullmatch(pid) or pid.endswith("."):
            plan.rows.append(
                PartRow(
                    n,
                    False,
                    f"'{pid}' cannot be used as a part ID (letters, digits, - _ . and a letter first); put a usable ID in the ID column",
                    pid,
                )
            )
            continue
        category = (cell("category") or default_category or "").lower()
        old = seen.get(pid) or project.parts.get(pid)
        if category not in PART_CATEGORIES:
            if old is None or cell("category"):
                shown = category or "(empty)"
                plan.rows.append(
                    PartRow(
                        n,
                        False,
                        f"Category '{shown}' is not one of {', '.join(PART_CATEGORIES)}",
                        pid,
                    )
                )
                continue
            category = old.category
        status = cell("approval").casefold()
        if not status:
            approval = old.approval if old is not None else "pending"
        elif status in ok_words:
            approval = "approved"
        elif status in rej_words:
            approval = "not_approved"
        elif status in pend_words:
            approval = "pending"
        else:
            plan.rows.append(
                PartRow(
                    n,
                    False,
                    f"Approval status '{cell('approval')}' is not in your approved, pending or rejected lists; say what it means",
                    pid,
                )
            )
            continue
        changes: dict[str, object] = {
            "category": category,
            "approval": approval,
            "unverified": False,
        }
        problem = ""
        for key in ("manufacturer", "part_number", "description", "specification", "mates_with"):
            if cell(key):
                changes[key] = cell(key)
        for key in ("mass_g", "mass_per_m_g"):
            if cell(key):
                value = _number(cell(key))
                if value is None:
                    problem = f"'{cell(key)}' is not a valid {key.replace('_', ' ')}"
                changes[key] = value
        if cell("pin_count"):
            pins = _number(cell("pin_count"))
            if pins is None or pins != int(pins) or pins < 1:
                problem = problem or f"'{cell('pin_count')}' is not a valid pin count"
            else:
                changes["pin_count"] = int(pins)
        if problem:
            plan.rows.append(PartRow(n, False, problem, pid))
            continue
        try:
            part = evolve(old, **changes) if old is not None else Part(id=pid, **changes)  # type: ignore[arg-type]
        except ValueError as exc:
            plan.rows.append(PartRow(n, False, str(exc).splitlines()[0][:120], pid))
            continue
        seen[pid] = part
        plan.rows.append(PartRow(n, True, "", pid, "updated" if pid in project.parts else "added"))
    plan.ops = [Put("parts", part) for part in seen.values()]
    return plan
