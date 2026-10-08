"""M7: the user guide, rule reference and configuration reference stay true to the program."""

import re
from pathlib import Path

import pytest

from harness_design_studio.cli.main import build_parser
from harness_design_studio.core.model.config import default_configs
from tools.build_guide import SOURCE, TARGET, convert
from tools.gen_rule_docs import TARGET as RULES_MD
from tools.gen_rule_docs import render

ROOT = Path(__file__).resolve().parents[1]


def test_guide_html_is_up_to_date() -> None:
    assert TARGET.read_text() == convert(SOURCE.read_text()), "run: python -m tools.build_guide"


def test_guide_internal_links_resolve() -> None:
    html = TARGET.read_text()
    ids = set(re.findall(r'id="([^"]+)"', html))
    for anchor in re.findall(r'href="#([^"]+)"', html):
        assert anchor in ids, anchor


def test_guide_documents_every_cli_command() -> None:
    parser = build_parser()
    sub = next(a for a in parser._actions if a.dest == "command")
    text = SOURCE.read_text()
    for name in sub.choices:  # type: ignore[union-attr]
        assert f"`harness {name}" in text, f"the guide does not document 'harness {name}'"


def test_guide_names_buttons_that_exist() -> None:
    from harness_design_studio.gui import strings

    text = SOURCE.read_text()
    shown = " ".join(str(v) for v in vars(strings).values() if isinstance(v, str))
    for label in (
        "Generate harnesses",
        "Export outputs",
        "Submit for review",
        "Release…",
        "New revision…",
        "Changes…",
        "Change log…",
        "Add a unit",
        "Interface table",
        "Harness plans",
        "Problems",
        "To-do",
        "Waive",
        "Save salvaged copy",
    ):
        assert label in text and label.rstrip("…") in shown, label


def test_guide_has_no_wall_of_text() -> None:
    """Short paragraphs and steps: no paragraph longer than 700 characters."""
    for para in re.split(r"\n\s*\n", SOURCE.read_text()):
        if not para.lstrip().startswith(("|", "#", "-", "1.", "```")):
            assert len(para) <= 700, para[:60]


def test_rule_reference_is_up_to_date() -> None:
    assert RULES_MD.read_text() == render(), "run: python -m tools.gen_rule_docs"


def test_every_configuration_key_is_documented() -> None:
    text = (ROOT / "docs" / "CONFIG.md").read_text()
    for name, cfg in default_configs().items():
        assert f"`{name}.json`" in text, name
        if name in ("naming", "titleblock"):
            continue
        for key in cfg.values:
            assert f"`{key}`" in text, f"{name}.{key} is not documented in docs/CONFIG.md"


def test_help_menu_opens_the_guide(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    pytest.importorskip("PySide6")
    from tests.gui_helpers import make_window

    w = make_window(tmp_path)
    qtbot.addWidget(w)
    opened = []
    w.open_url = lambda url: opened.append(url.toLocalFile()) or True  # type: ignore[assignment,func-returns-value]
    assert w.act_guide.shortcut().toString() == "F1"
    w.act_guide.trigger()
    assert opened and opened[0].endswith("guide/index.html") and Path(opened[0]).is_file()


def test_cli_reference_is_up_to_date() -> None:
    from tools.gen_cli_docs import EXAMPLES, TARGET, render

    assert TARGET.read_text() == render(), "run: python -m tools.gen_cli_docs"
    parser = build_parser()
    sub = next(a for a in parser._actions if a.dest == "command")
    assert set(EXAMPLES) == set(sub.choices or ())  # type: ignore[union-attr]


def test_cli_examples_name_real_commands_and_options() -> None:
    """Every example line parses with the real parser (paths need not exist)."""
    import shlex

    from tools.gen_cli_docs import EXAMPLES

    parser = build_parser()
    for lines in EXAMPLES.values():
        for line in lines:
            argv = shlex.split(line.split(" > ")[0])[1:]
            parser.parse_args(argv)


def _commands_in(markdown: Path) -> list[str]:
    """Command lines (harness ..., cp ...) from the fenced blocks of a document, in order."""
    out: list[str] = []
    inside = False
    for line in markdown.read_text().splitlines():
        if line.startswith("```"):
            inside = not inside
        elif inside and line.startswith(("harness ", "cp ")):
            out.append(line.strip())
    return out


def _run_document(
    markdown: Path, tmp: Path, expected: dict[str, list[int]]
) -> list[tuple[str, str]]:
    """Run every command of a document in order, in a scratch folder, and check the exit codes.
    `expected` lists, per command start, the codes of its successive runs (default: 0)."""
    import os
    import subprocess
    import sys

    env = {**os.environ, "PATH": f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}"}
    seen: dict[str, int] = {}
    results: list[tuple[str, str]] = []
    for command in _commands_in(markdown):
        key = next((k for k in expected if command.startswith(k)), command)
        n = seen.get(key, 0)
        seen[key] = n + 1
        want = expected.get(key, [0])[min(n, len(expected.get(key, [0])) - 1)]
        done = subprocess.run(
            ["sh", "-c", command], cwd=tmp, env=env, capture_output=True, text=True, check=False
        )
        assert done.returncode == want, (
            f"{markdown.name}: `{command}` exited {done.returncode}, expected {want}\n"
            f"{done.stdout[-600:]}{done.stderr[-600:]}"
        )
        results.append((command, done.stdout))
    return results


def test_getting_started_commands_work_in_order(tmp_path: Path) -> None:
    """The tutorial is run word for word, so it cannot drift from the program."""
    doc = ROOT / "docs" / "GETTING_STARTED.md"
    results = _run_document(
        doc,
        tmp_path,
        {
            "harness release wheel-link": [1, 1, 0],  # blocked, blocked on placeholders, accepted
            "harness config wheel-link": [1],  # exit 1 while values are missing
            "harness drc wheel-link": [0, 1, 0],  # the library import makes the plans stale (1)
        },
    )
    # the model hash quoted in the text is the one the first export prints
    first_export = next(out for cmd, out in results if cmd == "harness export wheel-link")
    printed = re.search(r"model ([0-9a-f]{12})", first_export)
    assert printed and f"(model {printed.group(1)})" in doc.read_text(), (
        "the model hash in docs/GETTING_STARTED.md is out of date: "
        f"{printed.group(1) if printed else '?'}"
    )
    assert f"Model hash: `{printed.group(1)}`" in doc.read_text()
    assert (tmp_path / "wheel-link" / "outputs" / "manifest.json").is_file()
    assert (tmp_path / "my-first-design" / "project.json").is_file()


def test_readme_quick_start_commands_work(tmp_path: Path) -> None:
    _run_document(ROOT / "README.md", tmp_path, {})
