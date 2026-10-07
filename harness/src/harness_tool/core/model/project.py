"""In-memory project: the single mutable container. Change it only through `commands`."""

from dataclasses import dataclass, field
from typing import Any

from .base import Entity, Name, Text
from .config import ConfigFile, default_configs
from .library import LibraryInfo, Part
from .logical import InterfaceInstance, InterfaceType, Unit
from .physical import Connector, Harness

SCHEMA_VERSION = 1


class ProjectMeta(Entity):
    name: Name = "Untitled project"
    description: Text = ""
    schema_version: int = SCHEMA_VERSION
    tool_version: str = ""  # version of the tool that last saved the project


@dataclass
class QuarantinedItem:
    """Data that could not be loaded. It is reported and kept, never silently dropped."""

    file: str
    kind: str
    reason: str
    raw: Any


@dataclass
class Project:
    meta: ProjectMeta = field(default_factory=ProjectMeta)
    library_info: LibraryInfo = field(default_factory=LibraryInfo)
    parts: dict[str, Part] = field(default_factory=dict)
    interface_types: dict[str, InterfaceType] = field(default_factory=dict)
    units: dict[str, Unit] = field(default_factory=dict)
    interfaces: dict[str, InterfaceInstance] = field(default_factory=dict)
    connectors: dict[str, Connector] = field(default_factory=dict)  # box connectors only
    harnesses: dict[str, Harness] = field(default_factory=dict)
    config: dict[str, ConfigFile] = field(default_factory=default_configs)
    quarantine: list[QuarantinedItem] = field(default_factory=list)
    quarantine_files: dict[str, bytes] = field(default_factory=dict)
    read_only: bool = False  # written by a newer tool version
    migrated_from: int | None = None

    @property
    def recovered(self) -> bool:
        """True if something could not be loaded; such a project cannot overwrite its folder."""
        return bool(self.quarantine or self.quarantine_files)

    def all_connectors(self) -> dict[str, Connector]:
        """Box connectors plus every harness-owned connector, keyed by ID."""
        result = dict(self.connectors)
        for harness in self.harnesses.values():
            for connector in harness.connectors:
                result.setdefault(connector.id, connector)
        return result

    def placeholder_configs(self) -> list[str]:
        return sorted(n for n, c in self.config.items() if c.placeholder)
