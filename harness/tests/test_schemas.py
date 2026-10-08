"""REQ-SCHEMA-01: JSON Schemas of the project files come from the model, work offline and match real files."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path

import pytest

from harness_design_studio.cli.main import main
from harness_design_studio.core import schemas
from harness_design_studio.core.io.layout import serialize
from harness_design_studio.core.samples import sat15


def test_every_kind_of_file_has_a_schema() -> None:
    docs = schemas.schemas()
    assert {"project", "config", "units", "interfaces", "connectors", "harness", "parts"} <= set(
        docs
    )
    assert all(d.get("type") == "object" and "properties" in d for d in docs.values())


def test_schemas_describe_the_files_the_tool_writes() -> None:
    """Every key of every saved file is a property of the matching schema (no drift)."""
    patterns = {pattern: name for name, pattern, _ in schemas._kinds()}
    docs = schemas.schemas()
    checked = 0
    for rel, data in serialize(sat15()).items():
        name = next((n for pat, n in patterns.items() if fnmatch.fnmatch(rel, pat)), None)
        if name is None:
            continue
        keys = set(json.loads(data))
        assert keys <= set(docs[name]["properties"]), (rel, keys - set(docs[name]["properties"]))
        checked += 1
    assert checked > 10


def test_the_schema_command_writes_files_and_refuses_a_used_folder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "schemas"
    assert main(["schema", str(target)]) == 0
    assert (target / "units.schema.json").is_file()
    settings = json.loads((target / "editor-settings.json").read_text(encoding="utf-8"))
    assert any(e["url"] == "./schemas/config.schema.json" for e in settings["json.schemas"])
    assert "schemas written" in capsys.readouterr().out
    assert main(["schema", str(target)]) == 2  # not empty any more


def test_schema_output_is_deterministic(tmp_path: Path) -> None:
    main(["schema", str(tmp_path / "a")])
    main(["schema", str(tmp_path / "b")])
    for f in sorted((tmp_path / "a").iterdir()):
        assert f.read_bytes() == (tmp_path / "b" / f.name).read_bytes()
