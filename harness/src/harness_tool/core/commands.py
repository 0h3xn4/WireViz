"""Transactions with undo/redo. All model changes are lists of operations applied atomically."""

from dataclasses import dataclass, field
from typing import Literal

from .errors import TransactionError
from .integrity import check_integrity
from .issues import errors
from .model import (
    ConfigFile,
    Connector,
    GenerationRecord,
    Harness,
    InterfaceInstance,
    InterfaceType,
    Part,
    Placement,
    Project,
    ProjectMeta,
    Unit,
    Waiver,
)
from .model.base import Entity

Collection = Literal[
    "units",
    "interface_types",
    "interfaces",
    "connectors",
    "harnesses",
    "parts",
    "placements",
    "waivers",
]
_TYPES: dict[str, type[Entity]] = {
    "units": Unit,
    "interface_types": InterfaceType,
    "interfaces": InterfaceInstance,
    "connectors": Connector,
    "harnesses": Harness,
    "parts": Part,
    "placements": Placement,
    "waivers": Waiver,
}


@dataclass(frozen=True)
class Put:
    """Add or replace one object (matched by its ID)."""

    collection: Collection
    obj: Entity


@dataclass(frozen=True)
class Delete:
    collection: Collection
    key: str


@dataclass(frozen=True)
class SetConfig:
    config: ConfigFile


@dataclass(frozen=True)
class SetMeta:
    meta: ProjectMeta


@dataclass(frozen=True)
class SetZones:
    zones: tuple[str, ...]


@dataclass(frozen=True)
class SetGeneration:
    record: GenerationRecord | None


Op = Put | Delete | SetConfig | SetMeta | SetZones | SetGeneration


def _apply(project: Project, op: Op) -> Op:
    """Apply one operation and return the operation that undoes it."""
    if isinstance(op, SetMeta):
        before_meta = project.meta
        project.meta = op.meta
        return SetMeta(before_meta)
    if isinstance(op, SetGeneration):
        before_gen = project.generation
        project.generation = op.record
        return SetGeneration(before_gen)
    if isinstance(op, SetZones):
        before_zones = tuple(project.zones)
        project.zones = list(op.zones)
        return SetZones(before_zones)
    if isinstance(op, SetConfig):
        previous = project.config.get(op.config.name)
        project.config[op.config.name] = op.config
        return SetConfig(previous) if previous is not None else SetConfig(op.config)
    if op.collection not in _TYPES:
        raise TypeError(f"unknown collection '{op.collection}'")
    store: dict[str, Entity] = getattr(project, op.collection)
    if isinstance(op, Put):
        if not isinstance(op.obj, _TYPES[op.collection]):
            raise TypeError(f"{type(op.obj).__name__} cannot be stored in '{op.collection}'")
        key: str = op.obj.id  # type: ignore[attr-defined]
        previous_obj = store.get(key)
        store[key] = op.obj
        return (
            Delete(op.collection, key) if previous_obj is None else Put(op.collection, previous_obj)
        )
    if op.key not in store:
        raise KeyError(f"'{op.key}' does not exist in '{op.collection}'")
    return Put(op.collection, store.pop(op.key))


def apply_ops(project: Project, ops: list[Op]) -> list[Op]:
    """Apply all operations or none. Returns the undo operations (already in reverse order)."""
    undo: list[Op] = []
    try:
        for op in ops:
            undo.append(_apply(project, op))
    except Exception:
        for inverse in reversed(undo):
            _apply(project, inverse)
        raise
    undo.reverse()
    return undo


@dataclass
class _Step:
    label: str
    forward: list[Op]
    backward: list[Op]


@dataclass
class History:
    """Undo/redo stack for one project. A change that would break consistency is rolled back."""

    project: Project
    _undo: list[_Step] = field(default_factory=list)
    _redo: list[_Step] = field(default_factory=list)
    revision: int = 0  # increases with every applied change, undo or redo
    last_ops: list[Op] = field(default_factory=list)  # what the latest call applied
    _baseline: set[tuple[str, str, str | None, str | None]] | None = None

    def execute(self, label: str, ops: list[Op]) -> None:
        if self.project.read_only:
            raise TransactionError("This project is read-only (saved by a newer tool version).")
        before = self._baseline
        if before is None:
            before = {i.key() for i in errors(check_integrity(self.project))}
        backward = apply_ops(self.project, ops)
        after_issues = errors(check_integrity(self.project))
        after = {i.key() for i in after_issues}
        new = after - before
        if new:
            apply_ops(self.project, backward)
            self._baseline = before
            raise TransactionError(
                f"'{label}' was cancelled because it would leave the project inconsistent.",
                [i.message for i in after_issues if i.key() in new],
            )
        self._baseline = after
        self._undo.append(_Step(label, list(ops), backward))
        self._redo.clear()
        self.revision += 1
        self.last_ops = list(ops)

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    @property
    def next_undo_label(self) -> str | None:
        return self._undo[-1].label if self._undo else None

    def undo(self) -> str:
        step = self._undo.pop()
        apply_ops(self.project, step.backward)
        self._redo.append(step)
        self.revision += 1
        self._baseline = None
        self.last_ops = list(step.backward)
        return step.label

    def redo(self) -> str:
        step = self._redo.pop()
        apply_ops(self.project, step.forward)
        self._undo.append(step)
        self.revision += 1
        self._baseline = None
        self.last_ops = list(step.forward)
        return step.label
