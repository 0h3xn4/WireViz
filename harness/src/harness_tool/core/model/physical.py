"""Physical layer: connectors, pins, wires, shields and harnesses."""

from typing import Literal

from harness_tool.core.ids import Id, PinId

from .base import Entity, Name, Text

Gender = Literal["male", "female", "unspecified"]
Role = Literal["box", "cable", "inline", "feedthrough", "test"]
Termination = Literal["crimp", "solder", "unspecified"]
HarnessStatus = Literal["draft", "in_review", "released"]
ShieldKind = Literal["twisted_pair", "shielded_pair", "overall_shield", "quad", "coax"]
ShieldEnd = Literal["backshell_360", "pigtail", "floating"]


class Pin(Entity):
    id: PinId
    signal: Name | None = None
    contact_size: Name | None = None
    termination: Termination = "unspecified"
    locked: bool = False  # manual allocation that generation must never move


class Connector(Entity):
    id: Id
    name: Name
    role: Role
    part_id: Id
    unit_id: Id | None = None  # box connectors only
    gender: Gender = "unspecified"
    keying: Name | None = None
    pins: list[Pin] = []
    notes: Text = ""


class Wire(Entity):
    id: Id
    signal: Name | None = None
    from_connector: Id
    from_pin: PinId
    to_connector: Id
    to_pin: PinId
    gauge_awg: int | None = None
    part_id: Id | None = None
    colour: Name | None = None
    length_m: float | None = None
    interface_id: Id | None = None


class ShieldGroup(Entity):
    id: Id
    kind: ShieldKind
    wire_ids: list[Id]
    end_a: ShieldEnd = "floating"
    end_b: ShieldEnd = "floating"


class Splice(Entity):
    id: Id
    name: Name
    wire_ids: list[Id]


class BranchPoint(Entity):
    id: Id
    name: Name


class Segment(Entity):
    id: Id
    from_node: Id  # a connector or branch point of the same harness
    to_node: Id
    length_m: float | None = None


class Harness(Entity):
    id: Id
    name: Name
    revision: Name = "A"
    status: HarnessStatus = "draft"
    connectors: list[Connector] = []
    wires: list[Wire] = []
    splices: list[Splice] = []
    shields: list[ShieldGroup] = []
    branch_points: list[BranchPoint] = []
    segments: list[Segment] = []
    notes: Text = ""
