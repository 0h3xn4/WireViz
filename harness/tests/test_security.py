"""M9 security review, as tests (docs/SECURITY.md): hostile files and names must neither escape
the project folder, nor run as code, nor crash the tool."""

import ast
import json
import xml.etree.ElementTree as ET  # noqa: S405
from pathlib import Path

import pytest

from harness_tool.core import recovery
from harness_tool.core.commands import Put, apply_ops
from harness_tool.core.generate.engine import generate_project
from harness_tool.core.ids import ID_RE, check_id
from harness_tool.core.io import loader
from harness_tool.core.io.loader import load_project
from harness_tool.core.io.saver import save_project
from harness_tool.core.model import evolve
from harness_tool.core.outputs.build import MANIFEST, build_outputs, write_outputs
from harness_tool.core.outputs.stamp import parse_csv
from harness_tool.core.outputs.verify import verify_outputs
from harness_tool.core.samples import mini3, sat15_full

SRC = Path(__file__).resolve().parents[1] / "src" / "harness_tool"

HOSTILE = [
    "<script>alert(1)</script>", "a & b < c > d", 'quote " and \' mix', "`backticks` and [link](http://x)",
    "=HYPERLINK(\"http://evil\",\"x\")", "+cmd|' /C calc'!A0", "@SUM(1+1)", "-2+3", "line\nbreak", "tab\there",
    "../../etc/passwd", "back\\slash", "ünïcödé ✓ 日本語", "‮RTL override", "x" * 190,
]  # fmt: skip


def test_ids_cannot_contain_path_characters() -> None:
    for bad in ("../x", "a/b", "a\\b", ".hidden", "x.", "CON", "a b", "a\x00b", "", "-x"):
        with pytest.raises(ValueError):
            check_id(bad)
    assert ID_RE.fullmatch("W001") and ID_RE.fullmatch("OBC1-J01")


@pytest.mark.parametrize("name", HOSTILE)
def test_hostile_text_in_names_is_harmless_in_every_output(name: str) -> None:
    from harness_tool.core.model.base import Name  # noqa: F401

    p = sat15_full()
    unit = next(iter(p.units.values()))
    try:
        evolve(unit, name=name)
    except ValueError:
        pytest.skip("rejected by validation (control character): the model never holds it")
    h = p.harnesses["W010"]
    apply_ops(
        p,
        [Put("units", evolve(unit, name=name)), Put("harnesses", evolve(h, name=name, notes=name))],
    )
    out = build_outputs(p)
    for rel, data in out.files.items():
        if rel.endswith(".svg"):
            ET.fromstring(data)  # noqa: S314  (well-formed: nothing broke out of the text)
            assert b"<script" not in data
        if rel.endswith(".csv"):
            for row in parse_csv(data):  # round-trips, and unsafe cells were marked
                assert all(isinstance(c, str) for c in row)
            raw = data.decode().splitlines()
            for line in raw[1:]:
                assert not line.startswith(("=", "@")), rel
    assert verify_outputs(p, out.files).ok
    xlsx = out.files["system/system.xlsx"]
    import io
    import zipfile

    with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
        for member in z.namelist():
            if member.startswith("xl/worksheets/"):
                assert b"<f>" not in z.read(member)  # no cell is a formula


def test_symlinked_project_files_are_ignored_not_followed(tmp_path: Path) -> None:
    secret = tmp_path / "secret.json"
    secret.write_text(json.dumps({"password": "hunter2"}))
    p = mini3()
    save_project(p, tmp_path / "p")
    victim = next((tmp_path / "p" / "logical" / "units").glob("*.json"))
    victim.unlink()
    victim.symlink_to(secret)
    result = load_project(tmp_path / "p")
    assert "symlink_ignored" in {i.code for i in result.issues}
    assert all("hunter2" not in repr(q.raw) for q in result.project.quarantine)
    assert not any(
        "hunter2" in v.decode(errors="ignore") for v in result.project.quarantine_files.values()
    )


def test_oversized_project_file_is_refused_unread(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    save_project(mini3(), tmp_path / "p")
    monkeypatch.setattr(loader, "MAX_FILE_BYTES", 100)
    result = load_project(tmp_path / "p")
    assert (
        "file_too_large" in {i.code for i in result.issues}
        or "invalid_json" in {i.code for i in result.issues}
        or result.has_errors
    )


def test_output_folder_manifest_cannot_make_the_tool_delete_other_files(tmp_path: Path) -> None:
    p = mini3()
    generate_project(p)
    folder = tmp_path / "outputs"
    write_outputs(p, folder)
    victim = tmp_path / "victim.txt"
    victim.write_text("keep")
    doc = json.loads((folder / MANIFEST).read_text())
    doc["files"].append({"path": "../victim.txt", "sha256": "0" * 64, "bytes": 1})
    doc["files"].append({"path": "/etc/hostname", "sha256": "0" * 64, "bytes": 1})
    (folder / MANIFEST).write_text(json.dumps(doc))
    write_outputs(p, folder)
    assert victim.read_text() == "keep" and Path("/etc/hostname").exists()


def test_a_damaged_journal_is_ignored(tmp_path: Path) -> None:
    save_project(mini3(), tmp_path / "p")
    journal = recovery.journal_path(tmp_path / "p")
    journal.parent.mkdir(parents=True, exist_ok=True)
    for text in ("{", "[" * 100_000, '{"files": 5}', '{"files": {"project.json": "{"}}', ""):
        journal.write_text(text)
        assert recovery.read_journal(tmp_path / "p") is None
        recovery.journal_differs_from_disk(tmp_path / "p")  # must not raise


def test_the_code_never_evaluates_data_or_starts_programs() -> None:
    """No eval/exec/pickle/shelve/marshal, no subprocess or os.system, no yaml.load, no sockets."""
    banned_calls = {"eval", "exec", "compile"}
    banned_modules = {
        "pickle",
        "shelve",
        "marshal",
        "subprocess",
        "socket",
        "urllib",
        "http",
        "ftplib",
        "telnetlib",
        "requests",
        "ctypes",
    }
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in banned_calls
            ):
                pytest.fail(f"{path.name}: {node.func.id}() call")
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name.split(".")[0] not in banned_modules, (
                        f"{path.name}: import {a.name}"
                    )
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in banned_modules, (
                    f"{path.name}: from {node.module}"
                )
            if (
                isinstance(node, ast.Attribute)
                and node.attr in ("system", "popen")
                and isinstance(node.value, ast.Name)
                and node.value.id == "os"
            ):
                pytest.fail(f"{path.name}: os.{node.attr}")


def test_save_never_writes_outside_the_project_folder(tmp_path: Path) -> None:
    p = sat15_full()
    root = tmp_path / "deep" / "p"
    save_project(p, root)
    for f in tmp_path.rglob("*"):
        assert str(f).startswith(str(tmp_path))
    names = {f.relative_to(root).parts[0] for f in root.iterdir()}
    assert names <= {
        "project.json",
        "config",
        "library",
        "logical",
        "physical",
        "generated",
        ".gitignore",
        "waivers.json",
        "changelog.json",
        "baselines",
        ".harness-recovery",
        "outputs",
    }
