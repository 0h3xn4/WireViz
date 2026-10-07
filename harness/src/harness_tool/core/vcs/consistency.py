"""Consistency of released harnesses with their baselines (used by the rules and `harness check`)."""

from harness_tool.core.issues import Issue
from harness_tool.core.model import Harness, Project

from .locks import interface_design
from .snapshot import normalize


def release_integrity(project: Project) -> list[Issue]:
    """Errors for released harnesses that no longer match their baseline (edited after release,
    or damaged by a merge) or have none."""
    out: list[Issue] = []
    for h in sorted(project.harnesses.values(), key=lambda x: x.id):
        if h.status != "released":
            stale = project.baselines.get(f"{h.id}.{h.revision}")
            if stale is not None:
                out.append(
                    Issue(
                        "error",
                        "released_modified",
                        f"{h.id} has a baseline for revision {h.revision} but is no longer released; it was set back to {h.status} by hand. Start a new revision instead.",
                        None,
                        h.id,
                    )
                )
            continue
        b = project.baselines.get(f"{h.id}.{h.revision}")
        if b is None:
            out.append(
                Issue(
                    "error",
                    "released_without_baseline",
                    f"{h.id} is released (revision {h.revision}) but has no baseline.",
                    None,
                    h.id,
                )
            )
        elif not b.snapshot.harnesses or normalize(b.snapshot.harnesses[0]) != normalize(h):
            out.append(_modified(h))
        elif any(
            (now := project.interfaces.get(i.id)) is None
            or interface_design(now) != interface_design(i)
            for i in b.snapshot.interfaces
        ):
            out.append(_modified(h, "an interface it carries was changed"))
    return out


def _modified(h: Harness, what: str = "") -> Issue:
    detail = f" ({what})" if what else ""
    return Issue(
        "error",
        "released_modified",
        f"{h.id} was changed after its release (revision {h.revision}){detail}; it no longer matches its baseline.",
        None,
        h.id,
    )
