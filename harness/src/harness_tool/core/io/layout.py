"""Mapping between the in-memory project and its folder of small JSON files.

One file per subsystem keeps Git merges clean; one file per harness likewise. File names only
*group* data: loading never depends on them, so renaming a subsystem never loses anything.
"""

import hashlib
import re
from collections.abc import Callable
from typing import Any

from harness_tool.core.model import CONFIG_NAMES, PART_CATEGORIES, Project, ProjectMeta
from harness_tool.core.model.base import Entity

from . import canonical
from .fs import slug

MANAGED_RE = re.compile(
    r"^(project\.json|config/[^/]+\.json|library/[^/]+\.json|logical/interface_types\.json"
    r"|logical/(units|interfaces)/[^/]+\.json|physical/(connectors|harnesses)/[^/]+\.json)$"
)
MANAGED_DIRS = ("config", "library", "logical", "physical")


def is_managed(rel: str) -> bool:
    return bool(MANAGED_RE.match(rel))


def _dump(items: list[Entity]) -> list[dict[str, Any]]:
    return [i.model_dump(mode="json") for i in sorted(items, key=lambda x: getattr(x, "id"))]  # noqa: B009


def _grouped[T: Entity](
    items: dict[str, T], folder: str, key: str, group_of: Callable[[T], str]
) -> dict[str, bytes]:
    groups: dict[str, list[T]] = {}
    for item in items.values():
        groups.setdefault(slug(group_of(item)), []).append(item)
    return {f"{folder}/{g}.json": canonical.dumps({key: _dump(list(v))}) for g, v in groups.items()}


def serialize(project: Project, *, tool_version: str | None = None) -> dict[str, bytes]:
    """Return every project file as canonical bytes, keyed by project-relative POSIX path."""
    meta = project.meta
    if tool_version is not None:
        meta = ProjectMeta.model_validate({**meta.model_dump(), "tool_version": tool_version})
    files: dict[str, bytes] = {"project.json": canonical.dumps(meta.model_dump(mode="json"))}
    for name in CONFIG_NAMES:
        if name in project.config:
            files[f"config/{name}.json"] = canonical.dumps(project.config[name].model_dump())
    files["library/manifest.json"] = canonical.dumps(project.library_info.model_dump(mode="json"))
    for category in PART_CATEGORIES:
        parts = [p for p in project.parts.values() if p.category == category]
        files[f"library/{category}.json"] = canonical.dumps({"parts": _dump(list(parts))})
    files["logical/interface_types.json"] = canonical.dumps(
        {"interface_types": _dump(list(project.interface_types.values()))}
    )
    files.update(_grouped(project.units, "logical/units", "units", lambda u: u.subsystem))

    def interface_group(i: Any) -> str:
        first = i.endpoints[0].unit_id if i.endpoints else ""
        unit = project.units.get(first)
        return unit.subsystem if unit else "unassigned"

    files.update(_grouped(project.interfaces, "logical/interfaces", "interfaces", interface_group))

    def connector_group(c: Any) -> str:
        unit = project.units.get(c.unit_id) if c.unit_id else None
        return unit.subsystem if unit else "unassigned"

    files.update(_grouped(project.connectors, "physical/connectors", "connectors", connector_group))
    for h in project.harnesses.values():
        data = h.model_dump(mode="json")
        for key in ("connectors", "wires", "splices", "shields", "branch_points", "segments"):
            data[key] = sorted(data[key], key=lambda x: x["id"])
        files[f"physical/harnesses/{h.id}.json"] = canonical.dumps(data)
    return files


def model_hash(project: Project) -> str:
    """Hash of the model state, independent of which tool version last saved it."""
    digest = hashlib.sha256()
    for rel, data in sorted(serialize(project, tool_version="").items()):
        digest.update(rel.encode("utf-8") + b"\0" + data + b"\0")
    return digest.hexdigest()
