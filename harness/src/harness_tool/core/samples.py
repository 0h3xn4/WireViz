"""Reference projects. `mini3` is the minimal 3-unit example used by tests and the first-run sample."""

from .model import (
    Connector,
    Endpoint,
    Harness,
    InterfaceInstance,
    Pin,
    Project,
    ProjectMeta,
    Unit,
    Wire,
)
from .starter import starter_interface_types, starter_parts


def _pins(*signals: tuple[str, str | None]) -> list[Pin]:
    return [Pin(id=pid, signal=sig) for pid, sig in signals]


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
    for conn in (
        Connector(id="OBC-J01", name="J01 data", role="box", part_id="EX-DSUB-9-F", unit_id="OBC",
                  gender="female", pins=_pins(("1", "TX+"), ("2", "TX-"), ("3", "RX+"), ("4", "RX-"), ("5", None))),
        Connector(id="PCDU-J01", name="J01 power out", role="box", part_id="EX-DSUB-9-F", unit_id="PCDU",
                  gender="female", pins=_pins(("1", "PWR"), ("2", "RTN"), ("3", None))),
        Connector(id="RW1-J01", name="J01 power in", role="box", part_id="EX-DSUB-9-M", unit_id="RW1",
                  gender="male", pins=_pins(("1", "PWR"), ("2", "RTN"), ("3", None))),
        Connector(id="RW1-J02", name="J02 data", role="box", part_id="EX-DSUB-9-M", unit_id="RW1",
                  gender="male", pins=_pins(("1", "TX+"), ("2", "TX-"), ("3", "RX+"), ("4", "RX-"), ("5", None))),
    ):  # fmt: skip
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
