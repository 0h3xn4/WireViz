"""Load a project folder. Never raises on bad content: problems become issues and quarantine."""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from harness_tool.core.errors import LoadError
from harness_tool.core.integrity import check_integrity
from harness_tool.core.issues import Issue, errors
from harness_tool.core.model import (
    CONFIG_NAMES,
    SCHEMA_VERSION,
    ConfigFile,
    Connector,
    Harness,
    InterfaceInstance,
    InterfaceType,
    LibraryInfo,
    Part,
    Placement,
    Project,
    ProjectMeta,
    QuarantinedItem,
    Unit,
    Waiver,
    default_configs,
)
from harness_tool.core.model.base import Entity

from . import canonical
from .fs import long_path
from .layout import MANAGED_DIRS, is_managed, serialize
from .migrate import migrate_raw, schema_version_of


@dataclass
class LoadResult:
    project: Project
    issues: list[Issue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(errors(self.issues))


def _describe(exc: ValidationError) -> str:
    """Field paths and messages only: never the offending values (they may be export-controlled)."""
    parts = [f"{'.'.join(str(p) for p in e['loc']) or 'value'}: {e['msg']}" for e in exc.errors()]
    more = f" (+{len(parts) - 3} more)" if len(parts) > 3 else ""
    return "; ".join(parts[:3]) + more


def read_tree(root: Path) -> tuple[dict[str, Any], dict[str, bytes], list[Issue]]:
    """Read project.json and every managed JSON file. Unreadable files are reported, not fatal."""
    parsed: dict[str, Any] = {}
    broken: dict[str, bytes] = {}
    issues: list[Issue] = []
    base = long_path(root)
    candidates = [Path("project.json")]
    if (base / "waivers.json").is_file():
        candidates.append(Path("waivers.json"))
    for top in MANAGED_DIRS:
        folder = base / top
        if folder.is_dir():
            candidates += sorted(p.relative_to(base) for p in folder.rglob("*.json") if p.is_file())
    for rel_path in candidates:
        rel = rel_path.as_posix()
        if not is_managed(rel):
            issues.append(Issue("info", "unrecognized_file", "File is not part of the project format and was ignored.", rel))  # fmt: skip
            continue
        try:
            data = (base / rel_path).read_bytes()
        except OSError as exc:
            issues.append(Issue("error", "file_unreadable", f"The file could not be read ({exc.strerror}).", rel))  # fmt: skip
            continue
        try:
            parsed[rel] = canonical.loads_strict(data)
        except RecursionError:
            broken[rel] = data
            issues.append(Issue("error", "invalid_json", "The file is nested too deeply to read.", rel))  # fmt: skip
        except ValueError as exc:
            broken[rel] = data
            if b"<<<<<<<" in data or b">>>>>>>" in data:
                issues.append(Issue("error", "merge_conflict", "The file contains unresolved Git merge conflict markers. Resolve the conflict first.", rel))  # fmt: skip
            else:
                issues.append(Issue("error", "invalid_json", f"The file is not valid JSON or UTF-8 ({type(exc).__name__}: {str(exc)[:120]}).", rel))  # fmt: skip
    return parsed, broken, issues


class _Builder:
    def __init__(self, project: Project, issues: list[Issue]) -> None:
        self.p = project
        self.issues = issues

    def quarantine(self, rel: str, kind: str, reason: str, raw: Any) -> None:
        self.p.quarantine.append(QuarantinedItem(rel, kind, reason, raw))
        self.issues.append(Issue("error", "quarantined", f"A {kind} could not be loaded and was set aside: {reason}", rel))  # fmt: skip

    def one[T: Entity](self, rel: str, kind: str, model: type[T], raw: Any) -> T | None:
        try:
            return model.model_validate(raw)
        except ValidationError as exc:
            self.quarantine(rel, kind, _describe(exc), raw)
            return None

    def items[T: Entity](
        self, rel: str, data: Any, key: str, kind: str, model: type[T], target: dict[str, T]
    ) -> None:
        if not isinstance(data, dict) or set(data) != {key} or not isinstance(data[key], list):
            self.quarantine(rel, "file", f"expected an object with a single '{key}' list", data)
            return
        for raw in data[key]:
            obj = self.one(rel, kind, model, raw)
            if obj is None:
                continue
            oid: str = obj.id  # type: ignore[attr-defined]
            if oid in target:
                self.quarantine(rel, kind, f"duplicate ID '{oid}' (already defined elsewhere)", raw)
            else:
                target[oid] = obj


def _layout(b: "_Builder", rel: str, data: Any) -> None:
    ok = isinstance(data, dict) and set(data) == {"zones", "placements"}
    if not ok or not isinstance(data["zones"], list) or not isinstance(data["placements"], list):
        b.quarantine(rel, "file", "expected an object with 'zones' and 'placements' lists", data)
        return
    zones = [z for z in data["zones"] if isinstance(z, str) and z.strip()]
    if len(zones) != len(data["zones"]) or len(set(zones)) != len(zones):
        b.quarantine(rel, "zone list", "zone names must be unique, non-empty text", data["zones"])
    else:
        b.p.zones = zones
    b.items(
        rel,
        {"placements": data["placements"]},
        "placements",
        "placement",
        Placement,
        b.p.placements,
    )


def _build(files: dict[str, Any], project: Project, issues: list[Issue]) -> None:
    b = _Builder(project, issues)
    if "project.json" in files:
        meta = b.one("project.json", "project settings", ProjectMeta, files["project.json"])
        if meta is not None:
            project.meta = meta
    project.config = {}
    for rel in sorted(files):
        data = files[rel]
        if rel == "project.json":
            continue
        if rel.startswith("config/"):
            cfg = b.one(rel, "configuration", ConfigFile, data)
            stem = rel.removeprefix("config/").removesuffix(".json")
            if cfg is None:
                continue
            if cfg.name != stem or stem not in CONFIG_NAMES:
                b.quarantine(
                    rel, "configuration", f"'{stem}' is not a known configuration name", data
                )
            else:
                project.config[stem] = cfg
        elif rel == "library/manifest.json":
            info = b.one(rel, "library info", LibraryInfo, data)
            if info is not None:
                project.library_info = info
        elif rel.startswith("library/"):
            b.items(rel, data, "parts", "library part", Part, project.parts)
        elif rel == "logical/interface_types.json":
            b.items(
                rel,
                data,
                "interface_types",
                "interface type",
                InterfaceType,
                project.interface_types,
            )
        elif rel == "waivers.json":
            b.items(rel, data, "waivers", "waiver", Waiver, project.waivers)
        elif rel == "logical/layout.json":
            _layout(b, rel, data)
        elif rel.startswith("logical/units/"):
            b.items(rel, data, "units", "unit", Unit, project.units)
        elif rel.startswith("logical/interfaces/"):
            b.items(rel, data, "interfaces", "interface", InterfaceInstance, project.interfaces)
        elif rel.startswith("physical/connectors/"):
            b.items(rel, data, "connectors", "connector", Connector, project.connectors)
        elif rel.startswith("physical/harnesses/"):
            h = b.one(rel, "harness", Harness, data)
            if h is None:
                continue
            if h.id in project.harnesses:
                b.quarantine(
                    rel, "harness", f"duplicate ID '{h.id}' (already defined elsewhere)", data
                )
                continue
            project.harnesses[h.id] = h
            if rel != f"physical/harnesses/{h.id}.json":
                issues.append(Issue("warning", "file_name_mismatch", f"Harness '{h.id}' is stored in a file with a different name; it will be renamed on the next save.", rel, h.id))  # fmt: skip


def load_project(root: Path | str) -> LoadResult:
    """Open a project folder, migrating old formats in memory and recovering what it can."""
    root = Path(root)
    base = long_path(root)
    if not base.is_dir():
        raise LoadError(f"'{root}' is not a folder.")
    if not (base / "project.json").is_file():
        raise LoadError(f"'{root}' is not a harness project folder (no project.json).")
    files, broken, issues = read_tree(root)
    return load_from_files(files, broken, issues)


def load_from_files(
    files: dict[str, Any],
    broken: dict[str, bytes] | None = None,
    issues: list[Issue] | None = None,
) -> LoadResult:
    """Build a project from already-parsed files (also used to restore an autosave journal)."""
    issues = list(issues or [])
    project = Project()
    for rel, data in (broken or {}).items():
        project.quarantine_files[rel] = data
    version = schema_version_of(files)
    if version > SCHEMA_VERSION:
        project.read_only = True
        issues.append(Issue("warning", "newer_version", f"This project was saved by a newer version of the tool (format {version}; this tool understands up to {SCHEMA_VERSION}). It is opened read-only.", "project.json"))  # fmt: skip
        files_for_build = files
    elif version < SCHEMA_VERSION:
        files_for_build = migrate_raw(files, version)
        project.migrated_from = version
        issues.append(Issue("info", "migrated", f"The project was in format {version} and was upgraded in memory to {SCHEMA_VERSION}. Nothing is changed on disk until you save.", "project.json"))  # fmt: skip
    else:
        files_for_build = files
    _build(files_for_build, project, issues)
    for name, cfg in default_configs().items():
        if name not in project.config:
            project.config[name] = cfg
            issues.append(Issue("info", "config_defaulted", f"Configuration '{name}' is missing or unreadable; the built-in placeholder is used.", f"config/{name}.json"))  # fmt: skip
    issues.extend(check_integrity(project))
    placeholders = project.placeholder_configs()
    if placeholders:
        issues.append(Issue("info", "placeholder_config", f"Placeholder rule configuration still in use: {', '.join(placeholders)}. An engineer must review these before results are trusted."))  # fmt: skip
    return LoadResult(project, sorted(issues))


def disk_fingerprint(root: Path | str) -> str:
    """Hash of the managed files on disk; compare before saving to detect changes by others."""
    digest = hashlib.sha256()
    base = long_path(Path(root))
    for path in sorted(
        p for p in base.rglob("*.json") if is_managed(p.relative_to(base).as_posix())
    ):
        digest.update(path.relative_to(base).as_posix().encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def non_canonical_files(root: Path | str, project: Project) -> list[str]:
    """Managed files whose bytes differ from what a save would write (hand-edited or merged)."""
    base = long_path(Path(root))
    expected = serialize(project, tool_version=project.meta.tool_version)
    out = []
    for rel, data in expected.items():
        path = base / rel
        if path.is_file() and path.read_bytes() != data:
            out.append(rel)
    return sorted(out)
