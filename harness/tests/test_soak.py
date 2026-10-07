"""REQ-SOAK-01: thousands of random edits, undo/redo, saves and reloads keep the project consistent."""

import random
from pathlib import Path

import pytest

from harness_tool.core.commands import Delete, History, Op, Put
from harness_tool.core.errors import TransactionError
from harness_tool.core.integrity import check_integrity
from harness_tool.core.io.layout import model_hash
from harness_tool.core.io.loader import load_project
from harness_tool.core.io.saver import save_project
from harness_tool.core.issues import errors
from harness_tool.core.model import (
    Connector,
    Endpoint,
    Harness,
    InterfaceInstance,
    Pin,
    Unit,
    Wire,
    evolve,
)
from harness_tool.core.samples import mini3

SUBSYSTEMS = ["avionics", "power", "aocs", "payload", "thermal", "Антенна"]


def random_op(rng: random.Random, h: History, n: int) -> tuple[str, list[Op]]:
    p = h.project
    units = sorted(p.units)
    kind = rng.choice(
        [
            "add_unit",
            "rename",
            "delete_unit",
            "add_if",
            "del_if",
            "add_conn",
            "add_harness",
            "del_harness",
            "bad_ref",
        ]
    )
    if kind == "add_unit":
        return kind, [Put("units", Unit(id=f"U{n}", name=f"unit {n}", subsystem=rng.choice(SUBSYSTEMS), side=rng.choice(["nominal", "redundant", "none"])))]  # fmt: skip
    if kind == "rename" and units:
        u = p.units[rng.choice(units)]
        return kind, [
            Put("units", evolve(u, name=f"renamed {n}", subsystem=rng.choice(SUBSYSTEMS)))
        ]
    if kind == "delete_unit" and units:
        return kind, [Delete("units", rng.choice(units))]  # often rejected: dependants exist
    if kind == "add_if" and len(units) >= 2:
        a, b = rng.sample(units, 2)
        return kind, [Put("interfaces", InterfaceInstance(id=f"IF{n}", name="i", type_id=rng.choice(sorted(p.interface_types)), endpoints=[Endpoint(unit_id=a), Endpoint(unit_id=b)]))]  # fmt: skip
    if kind == "del_if" and p.interfaces:
        return kind, [Delete("interfaces", rng.choice(sorted(p.interfaces)))]
    if kind == "add_conn" and units:
        owner = rng.choice(units)
        pins = [Pin(id=str(i)) for i in range(1, rng.randint(1, 9) + 1)]
        return kind, [Put("connectors", Connector(id=f"C{n}", name="c", role="box", part_id="EX-DSUB-9-F", unit_id=owner, pins=pins))]  # fmt: skip
    if kind == "add_harness":
        boxes = sorted(p.connectors)
        if len(boxes) >= 2:
            a, b = rng.sample(boxes, 2)
            wires = []
            for k, (pa, pb) in enumerate(
                zip(p.connectors[a].pins, p.connectors[b].pins, strict=False)
            ):
                wires.append(Wire(id=f"H{n}-{k}", from_connector=a, from_pin=pa.id, to_connector=b, to_pin=pb.id))  # fmt: skip
            return kind, [Put("harnesses", Harness(id=f"H{n}", name="h", wires=wires))]
    if kind == "del_harness" and p.harnesses:
        return kind, [Delete("harnesses", rng.choice(sorted(p.harnesses)))]
    if kind == "bad_ref":
        ifs = sorted(p.interfaces)
        if ifs:
            return kind, [Put("interfaces", evolve(p.interfaces[rng.choice(ifs)], type_id="ghost"))]
    return "noop", []


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_soak(seed: int, tmp_path: Path) -> None:
    rng = random.Random(seed)
    p = mini3()
    h = History(p)
    accepted = rejected = 0
    root = tmp_path / "p"
    for n in range(1500):
        action = rng.random()
        before = model_hash(p)
        if action < 0.7:
            label, ops = random_op(rng, h, n)
            try:
                h.execute(label, ops)
                accepted += 1
            except TransactionError:
                rejected += 1
                assert model_hash(p) == before, "rejected change must leave the model untouched"
        elif action < 0.85 and h.can_undo:
            h.undo()
        elif action < 0.95 and h.can_redo:
            h.redo()
        else:
            save_project(p, root)
            reloaded = load_project(root)
            assert not reloaded.has_errors and not reloaded.project.recovered
            assert model_hash(reloaded.project) == model_hash(p)
        assert errors(check_integrity(p)) == [], f"inconsistent after step {n}"
    assert accepted > 200 and rejected > 20  # the run really exercised both paths
    while h.can_undo:  # undo everything: must land exactly on the starting model
        h.undo()
    assert model_hash(p) == model_hash(mini3())
