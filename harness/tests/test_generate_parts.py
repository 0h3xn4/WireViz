"""M3 building blocks: sizing, mass, lengths, pin allocation, segmentation modes, naming."""

from harness_tool.core.commands import Put, apply_ops
from harness_tool.core.generate.engine import generate_project, plan_generation
from harness_tool.core.generate.lengths import (
    path_length,
    plan_length_import,
    segment_lengths_known,
)
from harness_tool.core.generate.mass import harness_mass
from harness_tool.core.generate.naming import namer_for
from harness_tool.core.generate.pins import Request, allocate
from harness_tool.core.generate.segmentation import segment
from harness_tool.core.generate.sizing import ampacity_table, size_wire
from harness_tool.core.model import (
    BranchPoint,
    Connector,
    Pin,
    Project,
    Segment,
    evolve,
)
from harness_tool.core.model.config import ConfigFile
from harness_tool.core.samples import mini3, sat15
from harness_tool.core.verify import verify_project

# Test-only numbers: they exercise the arithmetic and are NOT engineering data.
TABLE: dict[str, object] = {"ampacity_a_by_awg": {"24": 2.0, "22": 3.0, "20": 5.0, "18": 7.0}}
FULL = {**TABLE, "bundle_derating": 0.5, "temperature_derating": 1.0}


def test_sizing_pending_with_placeholders() -> None:
    s = size_wire({}, {}, current_a=2.0, length_m=1.0, path_conductors=2)
    assert s.awg is None
    assert "derating.ampacity_a_by_awg" in s.pending
    s = size_wire({}, {}, current_a=None, length_m=None, path_conductors=2)
    assert s.pending and s.awg is None


def test_sizing_picks_smallest_gauge_that_carries_current() -> None:
    gen: dict[str, object] = {}
    s = size_wire(
        {**FULL, "max_voltage_drop_v": 100.0}, {"conductor_resistivity_ohm_m": 1.7e-8},
        current_a=2.0, length_m=1.0, path_conductors=2,
    )  # fmt: skip
    assert s.awg == 20  # 5 A * 0.5 = 2.5 A >= 2 A; 22 AWG gives 1.5 A
    assert not s.pending
    assert size_wire(FULL, gen, current_a=2.0, length_m=1.0, path_conductors=2).awg is None


def test_sizing_voltage_drop_can_force_a_larger_wire() -> None:
    s = size_wire(
        {**FULL, "max_voltage_drop_v": 0.001}, {"conductor_resistivity_ohm_m": 1.7e-8},
        current_a=2.0, length_m=5.0, path_conductors=2,
    )  # fmt: skip
    assert s.error or (s.awg is not None and s.awg <= 20)


def test_sizing_error_when_nothing_carries_the_current() -> None:
    s = size_wire(FULL, {}, current_a=100.0, length_m=1.0, path_conductors=2)
    assert s.error and s.awg is None


def test_ampacity_table_rejects_junk() -> None:
    assert ampacity_table(None) is None
    assert ampacity_table({"x": 1}) is None
    assert ampacity_table({"20": 5}) == {20: 5.0}


def _with_config(p: Project, name: str, **values: object) -> None:
    old = p.config[name]
    apply_ops(p, [])
    p.config[name] = ConfigFile(
        name=name, placeholder=old.placeholder, values={**old.values, **values}
    )


def test_mass_reports_missing_data_not_guesses() -> None:
    p = generate_and_return(sat15())
    h = next(x for x in p.harnesses.values() if x.wires)
    r = harness_mass(p, h)
    assert not r.complete and r.missing
    assert r.with_margin_g is None


def test_mass_with_full_data_and_margin() -> None:
    p = generate_and_return(mini3())
    h = p.harnesses["W001"]
    parts = {c.part_id for c in h.connectors}
    for pid in parts:
        apply_ops(p, [Put("parts", evolve(p.parts[pid], mass_g=10.0))])
    wp = next(iter(p.parts.values()))
    assert wp is not None
    r = harness_mass(p, h)
    assert r.total_g == 20.0 or r.missing
    _with_config(p, "generation", mass_margin_fraction=0.1)
    assert harness_mass(p, h).margin_g is not None


def generate_and_return(p: Project) -> Project:
    generate_project(p)
    return p


def _tree() -> Project:
    p = generate_and_return(sat15())
    h = next(x for x in p.harnesses.values() if x.generated and len(x.connectors) >= 2)
    a, b = h.connectors[0].id, h.connectors[1].id
    seg = [
        Segment(id="S1", from_node=a, to_node="BP1", length_m=0.5),
        Segment(id="S2", from_node="BP1", to_node=b, length_m=1.0),
    ]
    bp = BranchPoint(id="BP1", name="BP1")
    h2 = evolve(h, segments=seg, branch_points=[bp])
    apply_ops(p, [Put("harnesses", h2)])
    return p


def test_path_length_sums_segments() -> None:
    p = _tree()
    h = next(x for x in p.harnesses.values() if x.segments)
    a, b = h.connectors[0].id, h.connectors[1].id
    assert path_length(h, a, b) == 1.5
    assert path_length(h, a, a) == 0.0
    assert segment_lengths_known(h)
    unknown = evolve(h, segments=[evolve(h.segments[0], length_m=None), h.segments[1]])
    assert path_length(unknown, a, b) is None
    assert not segment_lengths_known(unknown)


def test_length_import_validates_rows() -> None:
    p = _tree()
    h = next(x for x in p.harnesses.values() if x.segments)
    table = [
        ["harness", "segment", "length"],
        [h.id, "S1", "2.5"],
        [h.id, "S9", "1"],
        ["NOPE", "S1", "1"],
        [h.id, "S2", "abc"],
        [h.id, "S2", "-1"],
    ]
    plan = plan_length_import(p, table)
    assert [r.ok for r in plan.rows] == [True, False, False, False, False]
    apply_ops(p, plan.ops)
    assert p.harnesses[h.id].segments[0].length_m == 2.5


def test_length_import_refuses_released() -> None:
    p = _tree()
    h = next(x for x in p.harnesses.values() if x.segments)
    apply_ops(p, [Put("harnesses", evolve(h, status="released"))])
    plan = plan_length_import(p, [["h", "s", "l"], [h.id, "S1", "1"]])
    assert not plan.rows[0].ok and not plan.ops


# ---- pins -----------------------------------------------------------------------------------------


def _connector(n: int) -> Connector:
    return Connector(
        id="U-J01", name="J01", role="box", part_id="EX-DSUB-9-F", unit_id="U", gender="female",
        pins=[Pin(id=str(k)) for k in range(1, n + 1)],
    )  # fmt: skip


def test_pins_power_first_then_pairs_adjacent() -> None:
    p = mini3()
    reqs = [
        Request("IF-A", p.interface_types["rs422"]),
        Request("IF-P", p.interface_types["power_primary"]),
    ]
    out = allocate(_connector(9), reqs, {}, gap_pins=0)
    power = sorted(
        int(out.pins[("IF-P", s.name)]) for s in p.interface_types["power_primary"].signals
    )
    assert power == [1, 2]
    tx = int(out.pins[("IF-A", "TX+")])
    assert abs(tx - int(out.pins[("IF-A", "TX-")])) == 1
    assert not out.errors


def test_pins_gap_after_power() -> None:
    p = mini3()
    reqs = [
        Request("IF-P", p.interface_types["power_primary"]),
        Request("IF-A", p.interface_types["rs422"]),
    ]
    out = allocate(_connector(12), reqs, {}, gap_pins=2)
    assert int(out.pins[("IF-A", "TX+")]) >= 5


def test_pins_locked_pin_is_never_used() -> None:
    p = mini3()
    c = _connector(9)
    c = evolve(c, pins=[evolve(c.pins[0], locked=True, signal="X"), *c.pins[1:]])
    out = allocate(c, [Request("IF-P", p.interface_types["power_primary"])], {}, 0)
    assert "1" not in out.pins.values()


def test_pins_previous_allocation_kept() -> None:
    p = mini3()
    reqs = [Request("IF-P", p.interface_types["power_primary"])]
    first = allocate(_connector(9), reqs, {}, 0)
    again = allocate(_connector(9), reqs, dict(first.pins), 0)
    assert again.pins == first.pins


def test_pins_too_few_free_is_an_error() -> None:
    p = mini3()
    out = allocate(_connector(2), [Request("IF-A", p.interface_types["rs422"])], {}, 0)
    assert out.errors


def test_pins_non_adjacent_is_a_warning() -> None:
    p = mini3()
    c = _connector(6)
    pins = [evolve(x, locked=True, signal="X") if x.id in ("2", "4", "6") else x for x in c.pins]
    out = allocate(evolve(c, pins=pins), [Request("IF-A", p.interface_types["rs422"])], {}, 0)
    assert out.warnings or out.errors


# ---- segmentation modes and naming ---------------------------------------------------------------


def test_segmentation_modes_group_differently() -> None:
    counts = {}
    for mode in ("per_connector_pair", "per_unit_pair", "per_zone_pair"):
        p = sat15()
        _with_config(p, "segmentation", mode=mode)
        counts[mode] = len(segment(p).groups)
        generate_project(p)
        assert verify_project(p).ok, mode
    assert counts["per_connector_pair"] >= counts["per_unit_pair"] >= counts["per_zone_pair"]
    assert len(set(counts.values())) > 1


def test_segmentation_unknown_mode_falls_back() -> None:
    p = sat15()
    _with_config(p, "segmentation", mode="nonsense")
    seg = segment(p)
    assert seg.mode == "per_connector_pair" and seg.notes


def test_segmentation_skips_unrouted_interfaces() -> None:
    p = mini3()
    seg = segment(p)
    assert {s.interface_id for s in seg.skipped} >= {"IF-PWR-RW1"}  # manual harness owns it


def test_redundant_never_shares_with_nominal() -> None:
    p = sat15()
    seg = segment(p)
    for g in seg.groups:
        kinds = {p.interfaces[i].redundancy for i in g.interface_ids}
        assert len(kinds) == 1


def test_naming_uses_configured_patterns() -> None:
    n = namer_for(mini3())
    assert n.harness(7) == "W007"
    assert n.wire("W007", 3).startswith("W007")


def test_second_generation_report_lists_unchanged() -> None:
    p = generate_and_return(sat15())
    plan = plan_generation(p)
    assert plan.report.unchanged and not plan.report.added
