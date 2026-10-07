"""Review, release and new-revision workflow.

A release needs a comment, a name, and a design that passes the gate: no verifier or rule
errors for the harness, harness plans current, every wire sized and measured, and outputs that
were exported from the current design. It writes a baseline (a frozen snapshot) and a change log
entry, and locks the harness (see `locks`). The only way to change it afterwards is a new
revision, which keeps the old baseline.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from harness_tool.core import drc
from harness_tool.core.commands import Op, Put
from harness_tool.core.errors import HarnessError
from harness_tool.core.generate.engine import generation_status
from harness_tool.core.generate.lengths import wire_length
from harness_tool.core.model import Baseline, ChangeEntry, Harness, Project, evolve
from harness_tool.core.model.review import ChangeKind
from harness_tool.core.verify import verify_project

from .consistency import release_integrity
from .hashing import content_hash
from .snapshot import carried_interfaces, normalize, related_ids, snapshot_for

MIN_COMMENT = 10
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")  # ASCII digits only


def valid_date(text: str) -> bool:
    """A real calendar date written 2026-03-31 (not 2026-02-30, not full-width digits)."""
    if not DATE_RE.fullmatch(text):
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


class ReleaseError(HarnessError):
    """The requested change-control step is not possible."""


@dataclass(frozen=True)
class Blocker:
    code: str
    message: str
    object_id: str | None = None


@dataclass
class ReleasePlan:
    ops: list[Op] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    label: str = ""

    @property
    def ok(self) -> bool:
        return not self.blockers


def next_revision(rev: str) -> str:
    """A -> B ... Z -> AA -> AB (spreadsheet-style letters)."""
    if not re.fullmatch(r"[A-Z]+", rev):
        raise ReleaseError(
            f"Revision '{rev}' is not letters; rename it before starting a new revision."
        )
    chars = list(rev)
    k = len(chars) - 1
    while k >= 0:
        if chars[k] != "Z":
            chars[k] = chr(ord(chars[k]) + 1)
            return "".join(chars)
        chars[k] = "A"
        k -= 1
    return "A" + "".join(chars)


def _next_entry_id(project: Project) -> str:
    n = max((int(k[1:]) for k in project.changelog if re.fullmatch(r"C\d{4,}", k)), default=0)
    return f"C{n + 1:04d}"


def _entry(
    project: Project, h: Harness, kind: ChangeKind, by: str, when: str, comment: str
) -> ChangeEntry:
    return ChangeEntry(
        id=_next_entry_id(project),
        harness_id=h.id,
        revision=h.revision,
        kind=kind,
        by=by,
        when=when,
        comment=comment,
    )


def _common(project: Project, hid: str, by: str, comment: str | None, when: str) -> list[Blocker]:
    out: list[Blocker] = []
    if hid not in project.harnesses:
        return [Blocker("no_harness", f"Harness {hid} does not exist.", hid)]
    if not by.strip():
        out.append(Blocker("no_name", "Enter your name; it is recorded in the change log."))
    if comment is not None and len(comment.strip()) < MIN_COMMENT:
        out.append(
            Blocker(
                "comment_short",
                f"The comment needs at least {MIN_COMMENT} characters: say what changed or why.",
            )
        )
    if not valid_date(when):
        out.append(Blocker("bad_date", "The date must look like 2026-03-31."))
    return out


def release_blockers(
    project: Project, hid: str, *, by: str, comment: str, when: str, outputs_folder: Path | None
) -> list[Blocker]:
    out = _common(project, hid, by, comment, when)
    h = project.harnesses.get(hid)
    if h is None:
        return out
    if h.status == "released":
        out.append(
            Blocker(
                "already_released",
                f"{hid} is already released (revision {h.revision}). Start a new revision to change it.",
                hid,
            )
        )
    if not h.wires:
        out.append(Blocker("no_wires", f"{hid} has no wires.", hid))
    if h.generated and generation_status(project) == "stale":
        out.append(
            Blocker(
                "generation_stale",
                "The harness plans are out of date. Generate harnesses again first.",
                hid,
            )
        )
    related = related_ids(project, h)
    for issue in verify_project(project).errors:
        if issue.object_id is None or issue.object_id in related:
            out.append(Blocker("verify_error", f"Verifier: {issue.message}", issue.object_id))
    carried = carried_interfaces(h)
    for f in drc.run(project):
        if f.severity != "error" or f.waiver is not None:
            continue
        where = drc.locate(project, f.object_id)
        mine = (
            f.object_id in related
            or where == ("harness", hid)
            or (where is not None and where[0] == "interface" and where[1] in carried)
            or f.rule == "config-invalid"  # a wrong engineering value affects every harness
        )
        if mine:
            out.append(Blocker("rule_error", f.title, f.object_id))
    undecided = [w.id for w in h.wires if w.gauge_awg is None]
    if undecided:
        out.append(
            Blocker(
                "gauge_pending",
                f"{len(undecided)} wire(s) have no gauge decided (first: {undecided[0]}). Fill in the derating values (the file config/derating.json; `harness config DIR` lists what is missing) or set the gauge by hand.",
                undecided[0],
            )
        )
    no_length = [w.id for w in h.wires if wire_length(h, w) is None]
    if no_length:
        out.append(
            Blocker(
                "length_unknown",
                f"{len(no_length)} wire(s) have no length (first: {no_length[0]}). Enter the routing segment lengths (`harness import-lengths DIR FILE` loads them from a table).",
                no_length[0],
            )
        )
    out.extend(outputs_blockers(project, outputs_folder, hid))
    existing = f"{hid}.{h.revision}"
    if existing in project.baselines:
        out.append(
            Blocker(
                "baseline_exists",
                f"Revision {h.revision} of {hid} already has a baseline; start a new revision.",
                hid,
            )
        )
    return out


def outputs_blockers(
    project: Project, folder: Path | None, hid: str | None = None
) -> list[Blocker]:
    from harness_tool.core.outputs.build import (
        damaged_files,
        exported_harnesses,
        outputs_content_state,
    )

    if folder is None:
        return [
            Blocker(
                "outputs_unsaved",
                "Save the project to a folder and export the outputs before releasing.",
            )
        ]
    state = outputs_content_state(project, folder)
    if state == "none":
        return [
            Blocker(
                "outputs_missing",
                "Outputs have not been exported yet. Export them, review them, then release.",
            )
        ]
    if state != "current":
        return [
            Blocker(
                "outputs_stale",
                "The outputs are out of date (the design changed after the export). Export again.",
            )
        ]
    # the manifest alone proves nothing: the files it lists must still be there and unchanged
    damaged = damaged_files(folder)
    if damaged:
        return [
            Blocker(
                "outputs_modified",
                f"{len(damaged)} output file(s) were changed or removed after the export (first: {damaged[0]}). Export again.",
            )
        ]
    if hid is not None and hid not in (exported_harnesses(folder) or set()):
        return [
            Blocker(
                "outputs_missing",
                f"The exported outputs do not include {hid}. Export all outputs, then release.",
                hid,
            )
        ]
    return []


def plan_release(
    project: Project,
    hid: str,
    *,
    by: str,
    checker: str | None,
    comment: str,
    when: str,
    outputs_folder: Path | None,
) -> ReleasePlan:
    blockers = release_blockers(
        project, hid, by=by, comment=comment, when=when, outputs_folder=outputs_folder
    )
    plan = ReleasePlan(blockers=blockers, label=f"Release {hid}")
    if blockers:
        return plan
    h = project.harnesses[hid]
    released = normalize(
        evolve(
            h,
            status="released",
            author=h.author or by.strip(),
            checker=(checker or "").strip() or None,
            approver=by.strip(),
            released_on=when,
        )
    )
    snapshot = snapshot_for(project, released)
    entry = _entry(project, released, "release", by.strip(), when, comment.strip())
    baseline = Baseline(
        id=f"{hid}.{h.revision}", harness_id=hid, revision=h.revision, released_on=when, by=by.strip(),
        comment=comment.strip(), content_hash=content_hash(project), snapshot=snapshot,
    )  # fmt: skip
    plan.ops = [Put("harnesses", released), Put("baselines", baseline), Put("changelog", entry)]
    plan.label = f"Release {hid} revision {h.revision}"
    return plan


def plan_new_revision(
    project: Project, hid: str, *, by: str, comment: str, when: str
) -> ReleasePlan:
    blockers = _common(project, hid, by, comment, when)
    h = project.harnesses.get(hid)
    if h is not None and h.status != "released":
        blockers.append(
            Blocker("not_released", f"{hid} is not released, so it can be edited directly.", hid)
        )
    plan = ReleasePlan(blockers=blockers, label=f"New revision of {hid}")
    if blockers or h is None:
        return plan
    new = evolve(
        h,
        revision=next_revision(h.revision),
        status="draft",
        checker=None,
        approver=None,
        released_on=None,
    )
    entry = _entry(project, new, "new_revision", by.strip(), when, comment.strip())
    plan.ops = [Put("harnesses", new), Put("changelog", entry)]
    plan.label = f"New revision {new.revision} of {hid}"
    return plan


def plan_submit_review(project: Project, hid: str, *, by: str, when: str) -> ReleasePlan:
    blockers = _common(project, hid, by, None, when)
    h = project.harnesses.get(hid)
    if h is not None and h.status != "draft":
        blockers.append(
            Blocker(
                "not_draft",
                f"{hid} is {h.status.replace('_', ' ')}; only drafts can be submitted for review.",
                hid,
            )
        )
    if h is not None and not h.wires:
        blockers.append(Blocker("no_wires", f"{hid} has no wires.", hid))
    plan = ReleasePlan(blockers=blockers, label=f"Submit {hid} for review")
    if blockers or h is None:
        return plan
    new = evolve(h, status="in_review", author=by.strip())
    plan.ops = [
        Put("harnesses", new),
        Put("changelog", _entry(project, new, "review", by.strip(), when, "")),
    ]
    return plan


__all__ = [
    "Blocker",
    "ReleaseError",
    "ReleasePlan",
    "next_revision",
    "plan_new_revision",
    "plan_release",
    "plan_submit_review",
    "release_blockers",
    "release_integrity",
]
