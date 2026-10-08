"""REQ-STD-02: standard value profiles are opt-in, cite their source and never overwrite a person's value."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from harness_tool.cli.main import main
from harness_tool.core import configcheck, standard_profiles
from harness_tool.core.io.loader import load_project
from harness_tool.core.samples import mini3

ROOT = Path(__file__).resolve().parent.parent


def test_every_setting_cites_a_real_requirement() -> None:
    known: set[str] = set()
    for f in (ROOT / "compliance" / "requirements").glob("*.csv"):
        if f.name != "overrides.csv":
            with f.open(newline="", encoding="utf-8") as fh:
                known |= {r["ID"] for r in csv.DictReader(fh)}
    for settings in standard_profiles.PROFILES.values():
        for s in settings:
            assert s.source in known, s


def test_table_6_41_values_match_the_standard() -> None:
    k = standard_profiles.BUNDLE_K
    assert [k[str(n)] for n in (1, 2, 3, 10, 300)] == [1, 0.9, 0.81, 0.57, 0.12]
    assert standard_profiles.PARTIAL_L == {
        "below_25_percent": 1.2, "25_to_50_percent": 1.1, "above_50_percent": 1
    }  # fmt: skip


def test_a_profile_fills_only_unset_values_and_keeps_the_placeholder_flag() -> None:
    p = mini3()
    plan = standard_profiles.plan_profile(p, "ecss-q-st-30-11c")
    names = {(s.file, s.key) for s in plan.applied}
    assert ("derating", "wire_voltage_factor") in names
    assert all(c.placeholder for c in plan.configs if c.name in ("derating", "generation"))
    assert not plan.kept


def test_a_value_set_by_a_person_is_kept() -> None:
    p = mini3()
    d = p.config["derating"]
    p.config["derating"] = type(d)(
        name="derating", placeholder=d.placeholder, values={**d.values, "wire_voltage_factor": 0.4}
    )
    plan = standard_profiles.plan_profile(p, "ecss-q-st-30-11c")
    assert ("derating", "wire_voltage_factor") not in {(s.file, s.key) for s in plan.applied}
    assert any(s.key == "wire_voltage_factor" and v == 0.4 for s, v in plan.kept)


def test_unknown_profile_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown profile"):
        standard_profiles.plan_profile(mini3(), "nope")


def test_bad_values_are_reported(tmp_path: Path) -> None:
    p = mini3()
    d = p.config["derating"]
    p.config["derating"] = type(d)(
        name="derating",
        placeholder=True,
        values={
            **d.values,
            "wire_voltage_factor": 1.5,
            "bundle_factor_by_count": {"1": 0.5, "2": 0.9},
        },
    )
    msgs = [i.message for i in configcheck.validate(p)]
    assert any("wire_voltage_factor" in m for m in msgs)
    assert any("bundle_factor_by_count" in m and "rise" in m for m in msgs)


def test_cli_applies_a_profile_and_a_second_run_changes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    proj = tmp_path / "p"
    assert main(["new", str(proj), "--template", "first-steps"]) == 0
    main(["config", str(proj), "--apply-profile", "ecss-q-st-30-11c"])
    out = capsys.readouterr().out
    assert "ECSS-Q-ST-30-11_0140213" in out and "still need an engineer's review" in out
    loaded = load_project(proj).project
    assert loaded.config["derating"].values["wire_voltage_factor"] == 0.5
    assert loaded.config["derating"].placeholder is True
    main(["config", str(proj), "--apply-profile", "ecss-q-st-30-11c"])
    assert "0 value(s) set" in capsys.readouterr().out
    assert main(["config", str(proj), "--apply-profile", "nope"]) == 2
