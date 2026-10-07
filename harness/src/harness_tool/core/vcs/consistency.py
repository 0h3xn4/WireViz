"""Consistency of released harnesses with their baselines (used by the rules and `harness check`)."""

from harness_tool.core.issues import Issue
from harness_tool.core.model import Project

from .snapshot import normalize


def release_integrity(project: Project) -> list[Issue]:
    """Errors for released harnesses that no longer match their baseline (edited after release,
    or damaged by a merge) or have none."""
    out: list[Issue] = []
    for h in sorted(project.harnesses.values(), key=lambda x: x.id):
        if h.status != "released":
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
            out.append(
                Issue(
                    "error",
                    "released_modified",
                    f"{h.id} was changed after its release (revision {h.revision}); it no longer matches its baseline.",
                    None,
                    h.id,
                )
            )
    return out
