"""Software configuration file and integrity values (ECSS-Q-ST-80C 6.2.4.10, 6.2.4.11)."""

from __future__ import annotations

from pathlib import Path

from tools import gen_scf


def make_root(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "1.0"\ndependencies = ["a==1"]\n'
        '[project.optional-dependencies]\ngui = ["b==2"]\n',
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "m.py").write_text("x = 1\n", encoding="utf-8")
    for f in ("tools", "packaging", "tests", "docs", "compliance"):
        (tmp_path / f).mkdir()
    return tmp_path


def test_integrity_value_changes_with_a_source_file(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    a = gen_scf.build_scf(root, root / "dist")
    assert a["version"] == "1.0"
    assert a["dependencies"] == ["a==1", "b==2"]
    assert gen_scf.build_scf(root, root / "dist") == a
    (root / "src" / "m.py").write_text("x = 2\n", encoding="utf-8")
    assert (
        gen_scf.build_scf(root, root / "dist")["source_integrity_sha256"]
        != a["source_integrity_sha256"]
    )


def test_deliverables_of_this_version_are_listed_with_their_hash(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    (root / "dist").mkdir()
    (root / "dist" / "x_1.0_amd64.deb").write_bytes(b"abc")
    (root / "dist" / "x_0.9_amd64.deb").write_bytes(b"old")
    got = gen_scf.build_scf(root, root / "dist")["deliverables"]
    assert got == {
        "x_1.0_amd64.deb": {
            "bytes": 3,
            "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        }
    }
