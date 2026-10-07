"""Naming schemes from the `naming` configuration. Invalid templates fall back to the defaults."""

from dataclasses import dataclass, field

from harness_tool.core.ids import ID_RE
from harness_tool.core.model import Project

DEFAULTS = {
    "harness": "W{n:03d}",
    "cable_connector": "{harness}-P{n}",
    "wire": "{harness}-{n:03d}",
    "shield": "{harness}-S{n}",
    "branch": "{harness}-B{n}",
    "segment": "{harness}-L{n}",
}


@dataclass
class Namer:
    templates: dict[str, str]
    warnings: list[str] = field(default_factory=list)

    def _fmt(self, kind: str, **kw: object) -> str:
        template = self.templates.get(kind, DEFAULTS[kind])
        try:
            name = template.format(**kw)
        except (KeyError, IndexError, ValueError):
            name = ""
        if not ID_RE.fullmatch(name) or name.endswith("."):
            if kind in self.templates and f"naming.{kind}" not in self.warnings:
                self.warnings.append(f"naming.{kind}")
            name = DEFAULTS[kind].format(**kw)
        return name

    def harness(self, n: int) -> str:
        return self._fmt("harness", n=n)

    def cable_connector(self, harness: str, n: int) -> str:
        return self._fmt("cable_connector", harness=harness, n=n)

    def wire(self, harness: str, n: int) -> str:
        return self._fmt("wire", harness=harness, n=n)

    def shield(self, harness: str, n: int) -> str:
        return self._fmt("shield", harness=harness, n=n)

    def branch(self, harness: str, n: int) -> str:
        return self._fmt("branch", harness=harness, n=n)

    def segment(self, harness: str, n: int) -> str:
        return self._fmt("segment", harness=harness, n=n)


def namer_for(project: Project) -> Namer:
    cfg = project.config.get("naming")
    values = cfg.values if cfg is not None else {}
    return Namer({k: v for k, v in values.items() if isinstance(v, str)})
