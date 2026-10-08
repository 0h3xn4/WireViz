"""DRC building blocks: a rule states what is wrong, why it matters and how to fix it; its check
yields `Hit`s (one per offending object). Findings reuse `checks.Finding` so the Problems panel,
waivers and to-do list treat logical and design rule findings the same way."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from harness_tool.core.checks import Finding, finding_id
from harness_tool.core.issues import Severity
from harness_tool.core.model import Project


@dataclass(frozen=True)
class Hit:
    object_id: str
    title: str  # plain-language statement of this one problem
    fix_label: str | None = None  # set only when `drc.fix_ops` can really fix it


@dataclass(frozen=True)
class Rule:
    id: str
    severity: Severity
    topic: str  # short plain-language name, shown in the report
    why: str
    how: str  # how to fix it by hand
    check: Callable[[Project], Iterator[Hit]]
    waivable: bool | None = None  # default: warnings can be waived, errors and info cannot
    sources: tuple[str, ...] = ()  # IDs of the standard requirements this rule serves (compliance/)

    @property
    def can_waive(self) -> bool:
        return self.severity == "warning" if self.waivable is None else self.waivable

    @property
    def cite(self) -> str:
        return f" Requirement: {', '.join(self.sources)}." if self.sources else ""

    def run(self, project: Project) -> list[Finding]:
        return [
            Finding(
                finding_id(self.id, h.object_id), self.id, self.severity, h.object_id,
                h.title, f"{self.why} To fix it: {self.how}{self.cite}", h.fix_label, self.can_waive,
            )
            for h in self.check(project)
        ]  # fmt: skip


def cfg(project: Project, name: str) -> dict[str, object]:
    c = project.config.get(name)
    return dict(c.values) if c is not None else {}


def number(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def flag(values: dict[str, object], key: str) -> bool:
    """A yes/no setting that defaults to yes; an explicit null must not silently switch it off."""
    value = values.get(key)
    return True if value is None else bool(value)
