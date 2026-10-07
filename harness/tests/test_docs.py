"""M7: the user guide, rule reference and configuration reference stay true to the program."""

import re
from pathlib import Path

import pytest

from harness_tool.cli.main import build_parser
from harness_tool.core.model.config import default_configs
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
    from harness_tool.gui import strings

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
