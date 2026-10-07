"""Rule configuration. Standards numbers are never hard-coded; defaults are placeholders."""

from typing import Any

from .base import Entity, Name

CONFIG_NAMES: tuple[str, ...] = (
    "segmentation", "segregation", "derating", "naming", "emc", "titleblock",
)  # fmt: skip


class ConfigFile(Entity):
    name: Name
    placeholder: bool  # True until an engineer has reviewed and filled in the values
    values: dict[str, Any]


def default_configs() -> dict[str, ConfigFile]:
    """Starter configuration. Every `placeholder: True` file needs an engineer's review."""
    return {
        "segmentation": ConfigFile(
            name="segmentation",
            placeholder=True,  # DECISIONS D-10: defaulted, owner must confirm
            values={"mode": "per_connector_pair", "merge_when_same_zone": True},
        ),
        "segregation": ConfigFile(
            name="segregation",
            placeholder=True,
            values={
                "forbid_nominal_with_redundant": True,
                "forbid_pyro_with_other": True,
                "category_pairs_to_separate": None,
            },
        ),
        "derating": ConfigFile(
            name="derating",
            placeholder=True,  # DECISIONS D-11: real values must come from the program's standard
            values={
                "contact_current_factor": None,
                "bundle_derating": None,
                "max_ambient_temperature_c": None,
                "max_voltage_drop_v": None,
                "spare_pin_fraction": None,
            },
        ),
        "naming": ConfigFile(
            name="naming",
            placeholder=False,
            values={
                "harness": "W{n:03d}",
                "box_connector": "{unit}-J{n:02d}",
                "cable_connector": "{harness}-P{n}",
                "wire": "{harness}-{n:03d}",
            },
        ),
        "emc": ConfigFile(name="emc", placeholder=True, values={"classes": None}),
        "titleblock": ConfigFile(
            name="titleblock",
            placeholder=True,  # DECISIONS D-15
            values={
                "fields": [
                    "project",
                    "harness_id",
                    "title",
                    "revision",
                    "date",
                    "author",
                    "checker",
                    "approver",
                    "sheet",
                    "status",
                ]
            },
        ),
    }
