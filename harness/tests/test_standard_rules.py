"""REQ-STD-03, REQ-STD-04, REQ-STD-05: REQ-STD-03: rules from the supplied standards. Boundaries, quiet cases and "not checked" messages.

Numbers are test inputs, not engineering data.
"""

from __future__ import annotations

from typing import Any

from harness_tool.core import drc
from harness_tool.core.commands import Put, apply_ops
from harness_tool.core.drc import standard_rules as sr
from harness_tool.core.model import Project, evolve
from tests import test_drc as t


def hits(rule: str, p: Project) -> list[str]:
    return [f.object_id for f in t.fire(rule, p)]


def test_connector_voltage_uses_the_lower_of_the_two_limits() -> None:
    p = t.base()
    t.set_cfg(
        p, "derating", connector_voltage_factor_withstand=0.25, connector_voltage_factor_rated=0.75
    )
    t.set_part(p, "EX-MICROD-9-F", rated_voltage_v=100.0, dielectric_withstand_v=200.0)
    assert sr.connector_voltage_limit(p, "EX-MICROD-9-F") == 50.0  # min(0.25 x 200, 0.75 x 100)
    t.set_part(p, "EX-MICROD-9-F", rated_voltage_v=60.0)
    assert sr.connector_voltage_limit(p, "EX-MICROD-9-F") == 45.0


def test_voltage_exactly_at_the_limit_passes() -> None:
    p = t.pos_wire_voltage()
    h, w = t.wire_of(p, "power")
    i = p.interfaces[w.interface_id or ""]
    apply_ops(p, [Put("interfaces", evolve(i, voltage_v=25.0))])  # 0.5 x 50 V
    assert hits("wire-voltage", p) == []


def test_temperature_exactly_at_the_limit_passes() -> None:
    p = t.pos_temperature_margin()
    t.set_cfg(p, "derating", max_ambient_temperature_c=90.0)  # 120 - 30
    assert hits("temperature-margin", p) == []


def test_mating_cycles_at_the_limit_pass() -> None:
    p = t.pos_mating_cycles()
    h, w = t.wire_of(p, "power")
    i = p.interfaces[w.interface_id or ""]
    t.set_part(p, p.connectors[i.endpoints[0].connector_id or ""].part_id, mating_cycles=50.0)
    assert hits("mating-cycles", p) == []


def test_same_manufacturer_passes() -> None:
    p = t.pos_connector_manufacturer()
    for part in list(p.parts.values()):
        if part.manufacturer == "Maker B":
            apply_ops(p, [Put("parts", evolve(part, manufacturer="Maker A"))])
    assert hits("connector-manufacturer", p) == []


def test_specification_present_passes() -> None:
    p = t.pos_wire_specification()
    h, w = t.wire_of(p, "power")
    part = p.parts[w.part_id or ""]
    apply_ops(p, [Put("parts", evolve(part, specification="detail specification"))])
    assert hits("wire-specification", p) == []


def test_power_return_with_a_gap_passes_when_the_gap_is_zero() -> None:
    p = t.pos_power_return_adjacent()
    t.set_cfg(p, "generation", power_return_gap_pins=0)
    assert hits("power-return-adjacent", p) == []


def test_bundle_factor_takes_the_next_listed_count() -> None:
    p = t.base()
    t.set_cfg(p, "derating", bundle_factor_by_count={"1": 1.0, "10": 0.57, "300": 0.12})
    assert sr.bundle_factor(p, 1) == 1.0
    assert sr.bundle_factor(p, 2) == 0.57  # never a better factor than the standard gives
    assert sr.bundle_factor(p, 10) == 0.57
    assert sr.bundle_factor(p, 11) == 0.12
    assert sr.bundle_factor(p, 301) is None


def test_bundle_current_at_the_limit_passes() -> None:
    p = t.pos_bundle_current()
    h, w = t.wire_of(p, "power")
    i = p.interfaces[w.interface_id or ""]
    n = len(h.wires)
    k = sr.bundle_factor(p, n)
    assert k is not None
    apply_ops(p, [Put("interfaces", evolve(i, max_current_a=5.0 * k))])
    assert hits("bundle-current", p) == []


def test_rules_are_silent_without_their_numbers() -> None:
    p = t.base()
    for rule in (
        "connector-voltage", "wire-voltage", "temperature-margin", "mating-cycles",
        "power-return-adjacent", "bundle-current",
    ):  # fmt: skip
        assert hits(rule, p) == [], rule


def test_missing_ratings_are_reported_as_not_checked() -> None:
    p = t.base()
    t.set_cfg(
        p,
        "derating",
        connector_voltage_factor_rated=0.75,
        wire_voltage_factor=0.5,
        max_mating_cycles=50,
        bundle_factor_by_count={"1": 1.0, "300": 0.12},
    )
    h, w = t.wire_of(p, "power")
    i = p.interfaces[w.interface_id or ""]
    apply_ops(p, [Put("interfaces", evolve(i, voltage_v=28.0))])
    text = " ".join(f.title for f in drc.run(p) if f.rule == "unchecked-config")
    assert "Connector working voltage was not checked" in text
    assert "Wire voltage was not checked" in text
    assert "Mating cycles were not checked" in text
    assert "Table 6-42" in text  # L is not applied, and the report says so


def test_every_finding_names_its_requirement() -> None:
    for pos in (t.pos_bundle_current, t.pos_wire_voltage):
        for f in (x for x in drc.run(pos()) if x.rule in ("bundle-current", "wire-voltage")):
            assert "ECSS-Q-ST-30-11_" in f.why


def test_sizing_uses_the_bundle_table_instead_of_the_single_factor() -> None:
    from harness_tool.core.generate.sizing import size_wire

    der = {
        "ampacity_a_by_awg": {"24": 2.0, "20": 5.0, "18": 7.0},
        "temperature_derating": 1.0,
        "max_voltage_drop_v": 1000.0,
        "bundle_factor_by_count": {"1": 1.0, "10": 0.5, "300": 0.12},
    }
    gen: dict[str, object] = {"conductor_resistivity_ohm_m": 1.7e-8}
    kw: dict[str, Any] = {"current_a": 3.0, "length_m": 1.0, "path_conductors": 1}
    one = size_wire(der, gen, **kw, bundle_wires=1)
    ten = size_wire(der, gen, **kw, bundle_wires=10)
    assert one.awg == 20  # 5 A x 1.0 carries 3 A
    assert ten.awg == 18  # 5 A x 0.5 = 2.5 A is not enough, 7 A x 0.5 = 3.5 A is
    assert any("bundle factor K 0.5 for 10 wires" in n for n in ten.notes)
    big = size_wire(der, gen, **kw, bundle_wires=301)
    assert big.awg is None and any("no entry for 301 wires" in x for x in big.pending)
    # no table: the single factor still decides, exactly as before
    single = size_wire(
        {
            "ampacity_a_by_awg": {"20": 5.0},
            "bundle_derating": 0.6,
            "temperature_derating": 1.0,
            "max_voltage_drop_v": 1000.0,
        },
        gen,
        current_a=2.9,
        length_m=1.0,
        path_conductors=1,
        bundle_wires=10,
    )
    assert single.awg == 20 and not any("Table 6-41" in n for n in single.notes)


def test_generation_leaves_an_unassigned_contact_between_power_and_return() -> None:
    from harness_tool.core.generate.engine import generate_project, plan_generation
    from harness_tool.core.samples import sat15
    from harness_tool.core.verify import verify_project

    p = sat15()
    t.set_cfg(p, "generation", power_return_gap_pins=1)
    generate_project(p)
    assert [f for f in drc.run(p) if f.rule == "power-return-adjacent"] == []
    assert verify_project(p).ok
    box = p.connectors["OBC1-J01"]
    used = [x.signal for x in box.pins]
    assert used[:3] == ["PWR", None, "RTN"]  # pin 2 stays unassigned
    assert plan_generation(p).empty  # a second run changes nothing (REQ-GEN-01)


def test_without_the_setting_power_and_return_stay_adjacent_as_before() -> None:
    from harness_tool.core.generate.engine import generate_project
    from harness_tool.core.samples import sat15

    p = sat15()
    generate_project(p)
    used = [x.signal for x in p.connectors["OBC1-J01"].pins]
    assert used[:2] == ["PWR", "RTN"]


def test_shield_bonded_at_both_ends_passes() -> None:
    from harness_tool.core.model import ShieldGroup  # noqa: F401

    p = t.pos_shield_bonding()
    for h in list(p.harnesses.values()):
        t.put_harness(
            p,
            h,
            shields=[evolve(s, end_a="backshell_360", end_b="backshell_360") for s in h.shields],
        )
    assert hits("shield-bonding", p) == []


def test_emc_class_split_passes_when_classes_differ() -> None:
    p = t.pos_emc_class_split()
    a, b = sorted(
        {
            i.type_id
            for i in p.interfaces.values()
            if {e.unit_id for e in i.endpoints} == {"OBC1", "PCDU1"}
        }
    )[:2]
    apply_ops(p, [Put("interface_types", evolve(p.interface_types[b], emc_class="B"))])
    assert hits("emc-class-split", p) == []


def test_emc_class_is_in_the_wire_list_and_the_labels_only_when_classes_exist() -> None:
    from harness_tool.core.outputs.build import build_outputs

    p = t.base()
    plain = build_outputs(p).files
    head = next(v for k, v in plain.items() if k.endswith("/wirelist.csv")).decode().splitlines()
    assert "EMC class" not in head[1]  # byte-identical wire lists for projects without classes
    for tid in list(p.interface_types):
        apply_ops(p, [Put("interface_types", evolve(p.interface_types[tid], emc_class="A"))])
    files = build_outputs(p).files
    wl = next(v for k, v in files.items() if k.endswith("/wirelist.csv")).decode().splitlines()
    assert wl[1].endswith("EMC class") and wl[2].endswith(",A")
    labels = next(v for k, v in files.items() if k.endswith("/labels.csv")).decode()
    assert "[EMC A]" in labels


def test_the_output_verifier_catches_a_wrong_emc_class() -> None:
    from harness_tool.core.outputs.build import build_outputs
    from harness_tool.core.outputs.verify import verify_outputs

    p = t.base()
    for tid in list(p.interface_types):
        apply_ops(p, [Put("interface_types", evolve(p.interface_types[tid], emc_class="A"))])
    files = dict(build_outputs(p).files)
    assert verify_outputs(p, files).ok
    key = next(k for k in files if k.endswith("/wirelist.csv"))
    lines = files[key].decode().splitlines()
    lines[2] = lines[2][:-1] + "B"
    files[key] = ("\n".join(lines) + "\n").encode()
    codes = [i.code for i in verify_outputs(p, files).issues]
    assert "out_wire_differs" in codes
