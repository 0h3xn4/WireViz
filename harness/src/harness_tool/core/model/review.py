"""Layout (where things sit in the diagram) and review records (waivers)."""

from typing import Annotated

from pydantic import StringConstraints

from harness_tool.core.ids import Id

from .base import Entity, Name, Text

Justification = Annotated[str, StringConstraints(min_length=10, max_length=2000)]


class Placement(Entity):
    """Diagram position of one unit, in scene units. `id` is the unit's ID."""

    id: Id
    x: float
    y: float


class Waiver(Entity):
    """A recorded decision to accept a finding. The justification is mandatory."""

    id: Id  # "<rule>.<object>" so it is stable across sessions
    rule: Name
    object_id: Id
    justification: Justification
    notes: Text = ""


__all__ = ["Justification", "Placement", "Waiver"]
