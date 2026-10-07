"""REQ-FUZZ-01: the loader never crashes and never loses data silently, whatever the files contain."""

import json
import shutil
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from harness_tool.core.errors import HarnessError
from harness_tool.core.io.layout import model_hash
from harness_tool.core.io.loader import load_project
from harness_tool.core.io.saver import save_project
from tests.helpers import MINI3

FILES = sorted(p.relative_to(MINI3).as_posix() for p in MINI3.rglob("*.json"))
json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(max_size=20),
    lambda c: st.lists(c, max_size=4) | st.dictionaries(st.text(max_size=8), c, max_size=4),
    max_leaves=12,
)
FUZZ = settings(
    max_examples=150, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)


def _fresh(tmp: Path) -> Path:
    dest = tmp / "p"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(MINI3, dest)
    return dest


def _assert_loader_contract(root: Path, changed: bool) -> None:
    try:
        result = load_project(root)
    except HarnessError:
        return  # a clean, explained refusal (e.g. project.json missing)
    p = result.project
    if not changed:
        assert not result.has_errors
    if result.has_errors:
        return
    # No errors: the project must be fully usable and round-trip losslessly.
    assert not p.recovered
    if p.read_only:
        return
    out = root.parent / "out"
    if out.exists():
        shutil.rmtree(out)
    save_project(p, out)
    again = load_project(out)
    assert not again.has_errors
    assert model_hash(again.project) == model_hash(p)


@FUZZ
@given(st.data())
def test_random_byte_corruption(tmp_path_factory, data) -> None:  # type: ignore[no-untyped-def]
    tmp = tmp_path_factory.mktemp("fz")
    root = _fresh(tmp)
    rel = data.draw(st.sampled_from(FILES))
    path = root / rel
    raw = bytearray(path.read_bytes())
    mutation = data.draw(st.sampled_from(["truncate", "flip", "insert", "delete_file", "empty"]))
    if mutation == "truncate":
        del raw[data.draw(st.integers(0, len(raw))) :]
    elif mutation == "flip" and raw:
        raw[data.draw(st.integers(0, len(raw) - 1))] = data.draw(st.integers(0, 255))
    elif mutation == "insert":
        raw[data.draw(st.integers(0, len(raw))) : 0] = data.draw(st.binary(max_size=8))
    elif mutation == "empty":
        raw = bytearray()
    if mutation == "delete_file":
        path.unlink()
    else:
        path.write_bytes(bytes(raw))
    _assert_loader_contract(root, changed=True)


@FUZZ
@given(st.data())
def test_random_json_documents(tmp_path_factory, data) -> None:  # type: ignore[no-untyped-def]
    tmp = tmp_path_factory.mktemp("fz")
    root = _fresh(tmp)
    rel = data.draw(st.sampled_from(FILES))
    (root / rel).write_text(json.dumps(data.draw(json_values)), encoding="utf-8")
    _assert_loader_contract(root, changed=True)


@FUZZ
@given(st.data())
def test_random_value_mutation_inside_valid_structure(tmp_path_factory, data) -> None:  # type: ignore[no-untyped-def]
    tmp = tmp_path_factory.mktemp("fz")
    root = _fresh(tmp)
    rel = data.draw(st.sampled_from(FILES))
    doc = json.loads((root / rel).read_text(encoding="utf-8"))
    paths: list[list[object]] = []

    def walk(node: object, trail: list[object]) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                paths.append([*trail, k])
                walk(v, [*trail, k])
        elif isinstance(node, list):
            for i, v in enumerate(node):
                paths.append([*trail, i])
                walk(v, [*trail, i])

    walk(doc, [])
    if paths:
        trail = data.draw(st.sampled_from(paths))
        target = doc
        for step in trail[:-1]:
            target = target[step]
        target[trail[-1]] = data.draw(json_values)
    (root / rel).write_text(json.dumps(doc), encoding="utf-8")
    _assert_loader_contract(root, changed=True)


def test_unchanged_project_satisfies_contract(tmp_path: Path) -> None:
    _assert_loader_contract(_fresh(tmp_path), changed=False)
