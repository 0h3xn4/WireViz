"""Reference projects. `mini3` is the minimal 3-unit example used by tests and the first-run sample."""

from .model import (
    Connector,
    Endpoint,
    Harness,
    InterfaceInstance,
    Pin,
    Placement,
    Project,
    ProjectMeta,
    Unit,
    Wire,
    evolve,
)
from .starter import starter_interface_types, starter_parts


def _pins(*signals: tuple[str, str | None]) -> list[Pin]:
    return [Pin(id=pid, signal=sig) for pid, sig in signals]


def new_project(name: str = "Untitled project") -> Project:
    """An empty project with the starter library, interface types and default lanes."""
    p = Project(meta=ProjectMeta(name=name))
    p.parts = {x.id: x for x in starter_parts()}
    p.interface_types = {x.id: x for x in starter_interface_types()}
    return p


def mini3() -> Project:
    """OBC, PCDU and a reaction wheel: one power interface, one RS-422 link, one hand-made harness."""
    p = Project(
        meta=ProjectMeta(name="mini3 (example data)", description="Minimal 3-unit example.")
    )
    p.parts = {x.id: x for x in starter_parts()}
    p.interface_types = {x.id: x for x in starter_interface_types()}
    for uid, name, sub, zone in (
        ("OBC", "On-board computer", "avionics", "panel-A"),
        ("PCDU", "Power control and distribution unit", "power", "panel-A"),
        ("RW1", "Reaction wheel 1", "aocs", "panel-B"),
    ):
        p.units[uid] = Unit(id=uid, name=name, subsystem=sub, zone=zone, side="nominal")

    def box(cid: str, unit: str, part: str, carries: list[str], pins: list[Pin]) -> Connector:
        return Connector(id=cid, name=cid.rsplit("-", 1)[1], role="box", part_id=part, unit_id=unit,
                         gender="female" if part.endswith("-F") else "male", carries=carries, pins=pins)  # fmt: skip

    data_pins = _pins(("1", "TX+"), ("2", "TX-"), ("3", "RX+"), ("4", "RX-"), ("5", None))
    pwr_pins = _pins(("1", "PWR"), ("2", "RTN"), ("3", None))
    free = _pins(("1", None), ("2", None), ("3", None))
    for conn in (
        box("OBC-J01", "OBC", "EX-DSUB-9-F", ["rs422", "can", "spacewire", "discrete"], data_pins),
        box("OBC-J02", "OBC", "EX-DSUB-9-F", ["power_primary"], free),
        box("OBC-J03", "OBC", "EX-DSUB-9-F", ["rs422", "can"], free),
        box("PCDU-J01", "PCDU", "EX-DSUB-9-F", ["power_primary"], pwr_pins),
        box("PCDU-J02", "PCDU", "EX-DSUB-9-F", ["power_primary"], free),
        box("PCDU-J03", "PCDU", "EX-DSUB-9-F", ["discrete", "rs422"], free),
        box("RW1-J01", "RW1", "EX-DSUB-9-M", ["power_primary"], pwr_pins),
        box("RW1-J02", "RW1", "EX-DSUB-9-M", ["rs422", "can"], data_pins),
    ):
        p.connectors[conn.id] = conn
    p.interfaces["IF-PWR-RW1"] = InterfaceInstance(
        id="IF-PWR-RW1", name="RW1 power", type_id="power_primary", redundancy="nominal",
        flow="a_to_b",
        endpoints=[Endpoint(unit_id="PCDU", connector_id="PCDU-J01"),
                   Endpoint(unit_id="RW1", connector_id="RW1-J01")],
    )  # fmt: skip
    p.interfaces["IF-TM-RW1"] = InterfaceInstance(
        id="IF-TM-RW1", name="RW1 command and telemetry", type_id="rs422", redundancy="nominal",
        flow="bidirectional",
        endpoints=[Endpoint(unit_id="OBC", connector_id="OBC-J01"),
                   Endpoint(unit_id="RW1", connector_id="RW1-J02")],
    )  # fmt: skip
    for uid, x, y, zone in (
        ("OBC", 30.0, 60.0, "panel-A"),
        ("PCDU", 30.0, 300.0, "panel-A"),
        ("RW1", 470.0, 170.0, "panel-B"),
    ):
        p.placements[uid] = Placement(id=uid, x=x, y=y)
        p.units[uid] = evolve(p.units[uid], zone=zone)
    p.harnesses["W001"] = Harness(
        id="W001", name="PCDU to RW1 power",
        connectors=[
            Connector(id="W001-P1", name="P1", role="cable", part_id="EX-DSUB-9-M", gender="male",
                      pins=_pins(("1", "PWR"), ("2", "RTN"))),
            Connector(id="W001-P2", name="P2", role="cable", part_id="EX-DSUB-9-F", gender="female",
                      pins=_pins(("1", "PWR"), ("2", "RTN"))),
        ],
        wires=[
            Wire(id="W001-001", signal="PWR", from_connector="W001-P1", from_pin="1",
                 to_connector="W001-P2", to_pin="1", interface_id="IF-PWR-RW1"),
            Wire(id="W001-002", signal="RTN", from_connector="W001-P1", from_pin="2",
                 to_connector="W001-P2", to_pin="2", interface_id="IF-PWR-RW1"),
        ],
    )  # fmt: skip
    return p
