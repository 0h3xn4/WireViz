"""Parts library: real, qualified parts the plans refer to."""

from typing import Literal

from harness_tool.core.ids import Id

from .base import Entity, Name, Text

PartCategory = Literal["connector", "contact", "backshell", "wire", "sleeving", "label"]
PART_CATEGORIES: tuple[PartCategory, ...] = (
    "connector", "contact", "backshell", "wire", "sleeving", "label",
)  # fmt: skip
Approval = Literal["approved", "pending", "not_approved"]


class Part(Entity):
    id: Id
    category: PartCategory
    manufacturer: Name | None = None
    part_number: Name | None = None
    specification: Name | None = None
    description: Name | None = None
    approval: Approval = "pending"
    unverified: bool = False  # example data that no engineer has checked
    pin_count: int | None = None
    mates_with: Id | None = None  # connector parts: the mating counterpart (e.g. male for female)
    mass_g: float | None = None
    mass_per_m_g: float | None = None
    ratings: dict[Name, float] = {}
    notes: Text = ""


class LibraryInfo(Entity):
    name: Name = "Project parts library"
    version: Name = "0"
