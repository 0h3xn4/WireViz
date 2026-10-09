"""Rebuild the example projects shipped with the tool (`harness new --list`).

The projects are made with the tool's own editing functions, so they are valid by construction and
always in the current file format. Run `python -m tools.build_examples` after changing a sample or
the file format; a test fails while the shipped folders differ from what this script writes.
The hand-written templates next to them (`templates/`) are not touched.
"""

import shutil
import sys
from pathlib import Path

from harness_design_studio.core import edit
from harness_design_studio.core.commands import History
from harness_design_studio.core.io.saver import save_project
from harness_design_studio.core.model import Project, evolve
from harness_design_studio.core.samples import new_project, sat15

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "harness_design_studio" / "resources" / "examples" / "projects"

# name -> (title, one line shown by `harness new --list`)
PROJECTS = {
    "blank": ("My project", "An empty project: the starter parts and interface types, no units."),
    "first-steps": (
        "First steps: reaction wheel link",
        "Three units, a power link and an RS-422 link. Nothing is generated yet: start here.",
    ),
    "minimal-satellite": (
        "Minimal satellite",
        "Seven units, nominal only: power, computer, radio, wheel and sun sensor. Adapt it.",
    ),
    "small-satellite": (
        "Small satellite (reference)",
        "14 units with nominal and redundant chains. Generate it to see a realistic system.",
    ),
}


def _blank() -> Project:
    return new_project(PROJECTS["blank"][0])


def _first_steps() -> Project:
    p = new_project(PROJECTS["first-steps"][0])
    p.meta = evolve(
        p.meta,
        description="Power control unit, on-board computer and a reaction wheel. "
        "Generate the harnesses to see what the tool makes of two interfaces.",
    )
    history = History(p)
    for template, lane, y in (("power", 0, 40.0), ("computer", 0, 280.0), ("actuator", 1, 150.0)):
        ops, _ = edit.ops_add_unit(p, template, edit.lane_x(lane), y)
        history.execute("add unit", ops)
    for type_id, a, b in (("power_primary", "PCDU1", "RW1"), ("rs422", "OBC1", "RW1")):
        ops, iid = edit.ops_add_interface(p, type_id, a, b)
        history.execute("add interface", ops)
        if type_id == "power_primary":
            history.execute("set current", edit.ops_update_interface(p, iid, max_current_a=2.0))
    return p


def _minimal_satellite() -> Project:
    p = new_project(PROJECTS["minimal-satellite"][0])
    p.meta = evolve(
        p.meta,
        description="A small spacecraft without redundancy: solar array, battery, power control unit, "
        "on-board computer, transceiver, one reaction wheel and a sun sensor. "
        "Copy it, then rename, add and remove units to describe your own spacecraft.",
    )
    history = History(p)
    units = (
        ("solar_array", 0, 40.0), ("battery", 0, 200.0), ("pdu", 0, 360.0), ("computer_xl", 0, 520.0),
        ("transceiver", 1, 40.0), ("actuator", 1, 200.0), ("sun_sensor", 1, 360.0),
    )  # fmt: skip
    for template, lane, y in units:
        ops, _ = edit.ops_add_unit(p, template, edit.lane_x(lane), y)
        history.execute("add unit", ops)
    sa, bat, pcdu, obc, trx, rw, ss = (
        sorted(u for u in p.units if u.startswith(prefix))[0]
        for prefix in ("SA", "BAT", "PCDU", "OBC", "TRX", "RW", "SS")
    )
    wiring = (
        ("power_primary", sa, pcdu, 3.0), ("power_primary", bat, pcdu, 5.0),
        ("power_primary", pcdu, obc, 1.0), ("power_primary", pcdu, trx, 2.0),
        ("power_primary", pcdu, rw, 2.0), ("power_primary", pcdu, ss, 0.2),
        ("can", obc, pcdu, None), ("can", obc, rw, None), ("rs422", obc, trx, None),
        ("analog", obc, ss, None), ("can", obc, bat, None),
    )  # fmt: skip
    for type_id, a, b, current in wiring:
        ops, iid = edit.ops_add_interface(p, type_id, a, b)
        history.execute("add interface", ops)
        if current is not None:
            history.execute("set current", edit.ops_update_interface(p, iid, max_current_a=current))
    return p


def _small_satellite() -> Project:
    p = sat15()
    p.meta = evolve(
        p.meta,
        name=PROJECTS["small-satellite"][0],
        description="Redundant computer and power unit, battery, solar array, transceiver, payload, "
        "star tracker, two wheels, sun sensor, magnetorquer and a heater panel.",
    )
    return p


BUILDERS = {
    "blank": _blank,
    "first-steps": _first_steps,
    "minimal-satellite": _minimal_satellite,
    "small-satellite": _small_satellite,
}


def build(target: Path = TARGET) -> None:
    for name, make in BUILDERS.items():
        folder = target / name
        if folder.exists():
            shutil.rmtree(folder)
        save_project(make(), folder)
        for stray in folder.rglob("*.bak"):
            stray.unlink()


def main() -> int:
    build()
    print(f"example projects written to {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
