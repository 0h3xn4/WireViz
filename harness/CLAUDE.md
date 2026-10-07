# CLAUDE.md: spacecraft harness design tool (`harness/`)

Clean-room project inside the WireViz repo. **Never copy or import code from `../src/wireviz` (GPL-3.0).** Specification: `docs/SPEC.md`; decisions: `docs/DECISIONS.md`; architecture: `docs/ARCHITECTURE.md`; plan: `docs/PLAN.md`.

## Status
M0 to M5 done (`docs/demos/`). Next is M6 (change control: revisions, baselines, diff, release). Generation runs on placeholders until the owner answers D-10 (harness boundary rule) and D-11 (derating numbers); results must say so.

## Commands (run from `harness/`)
- Setup: `python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[gui,dev]"` (Linux also needs libegl1 libgl1 libxkbcommon0 libfontconfig1 libdbus-1-3 for Qt)
- Test: `pytest` (Qt runs offscreen via tests/conftest.py); coverage: `pytest --cov` (90% gate on core, enforced)
- Lint/type: `ruff format . && ruff check . && mypy`
- CLI: `harness --version | validate DIR | check DIR | migrate DIR | generate DIR | verify DIR | drc DIR | export DIR | verify DIR --outputs`; GUI: `harness-gui`
- GUI tests: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_journeys.py` (conftest sets it); timings: `python -m tools.bench_gui`; screenshots of the real editor: `python -m tools.gui_screenshots` (docs/ux/qt)
- Prototype: edit `prototype/template.html` / `prototype/app.js` or `gui/tokens.py`, then `python -m tools.build_prototype` (a test fails if `index.html` is stale); screenshots: `python -m tools.ux_screenshots`; journeys: `pytest tests/test_prototype.py` (needs Chromium, skips otherwise)
- Stress benchmarks: `python -m tools.bench_stress`, `python -m tools.bench_generate`
- Output goldens: `PYTHONPATH=. python -m tools.gen_output_goldens` (on purpose; review the diff)
- Package: `python -m tools.build_installer`, then `dist/harness-tool/harness-tool --selftest`
- SBOM + licence report: `python -m tools.gen_sbom`; reproducible check: `python -m tools.check_reproducible`
- Offline wheelhouse: `python -m tools.vendor`

## Conventions
- `core` must not import `gui`, `cli` or any network module. Offline guarantee is tested.
- All model changes go through commands/transactions; GUI never mutates the model directly.
- Deterministic everywhere: sort by stable IDs, no timestamps in generated data, canonical JSON.
- Never invent standard values (derating, current ratings, mass). Use `PLACEHOLDER` config values and list them for the owner.
- No design data in logs. UI strings in one module.
- Every new dependency: record name, version, licence in `docs/DECISIONS.md`.
- Tests first; every bug fix gets a regression test.
- End each session with: done, tested, next, UX targets met/open.

## Core layout (M1)
`core/model` (immutable strict models), `core/integrity.py`, `core/commands.py` (History: transactions, undo/redo), `core/io` (layout, loader, saver, migrate, fs), `core/starter.py`, `core/samples.py` (`mini3`). Format: `docs/FILE_FORMAT.md`; placeholders: `docs/PLACEHOLDERS.md`.
- Edit model objects only with `evolve()` and `History.execute`; never mutate `Project` directly outside commands/loader.
- Regenerate the golden fixture only on purpose: `python -c "from harness_tool.core.samples import mini3; from harness_tool.core.io.saver import save_project; save_project(mini3(), 'tests/fixtures/projects/mini3')"` and review the diff.
- Tests that run as root skip the read-only folder test; run the suite as a normal user in CI.

## GUI layout (M2)
`gui/controller.py` (EditorController: the only thing that changes the project; Delta signals), `canvas.py` (scene, items, view, minimap), `panels.py`, `dialogs.py`, `tour.py`, `main_window.py`, `theme.py`, `tokens.py`, `strings.py` (all UI text). Edit logic is headless in `core/edit.py`, `core/checks.py`, `core/imports.py`, `core/recovery.py`; add new editor features there first, with tests, and keep the GUI thin.
- Never name a widget attribute `palette` (it hides `QWidget.palette()`); it is `palette_panel`.
- Panels that are not visible refresh lazily (on show). Tests that read a tab's widgets must switch to that tab first.
- Dialog hooks (`run_dialog`, `ask_folder`, `ask_text`, `ask_choice`, `ask_file`) exist so tests can drive the UI without blocking.
- Keep edits under 100 ms at stress size: use the Delta, never rebuild the whole scene for a local change.

## Generation layout (M3)
`core/generate/` (`segmentation`, `wiring`, `pins`, `sizing`, `lengths`, `mass`, `naming`, `explain`, `engine`), `core/verify.py` (independent verifier), `core/model/generation.py` (record with provenance). `plan_generation(project)` is pure and returns ops + `RegenReport` + record; the GUI previews it (`GeneratePreviewDialog`), runs it in `PlanWorker` and applies it through `History`.
- Never put timestamps or history wording into provenance: a second plan must be empty and byte-identical.
- Verifier must stay independent of the generator: do not import wiring/pin logic into `core/verify.py`.
- Goldens: `tests/fixtures/projects/mini3` (hand-made, not generated) and `sat15` (generated). Regenerate sat15 on purpose: `python -c "from harness_tool.core.samples import sat15; from harness_tool.core.generate.engine import generate_project; from harness_tool.core.io.saver import save_project; p=sat15(); generate_project(p); save_project(p,'tests/fixtures/projects/sat15')"` (delete the folder first) and review the diff.
- Text-replace patches fail silently after `ruff format`; grep to confirm they applied.

## Design rule check layout (M4)
`core/drc/` (`base` Rule/Hit, `rules` RULES registry, `report` Markdown report, `__init__` run/fix_ops/locate). Add a rule: write a check generator, register it in `RULES`, add a positive case to `POSITIVE` in `tests/test_drc.py` (a test fails if a rule has none) and make sure it stays quiet on the clean project. Rules needing numbers must stay silent while config is `null` and be listed in `_unchecked`.
- `checks.find` stays the fast synchronous logical layer; the controller merges it with background DRC results (`DrcWorker`, 1.2 s after the last edit; waivers applied at display time).
- A background Python thread slows the UI (GIL): do not shorten the DRC delay or add synchronous DRC calls to edit paths.
- Regenerate the sat15 DRC report golden on purpose: `python -m harness_tool.cli.main drc tests/fixtures/projects/sat15 > tests/fixtures/drc/sat15.md`.

## Outputs layout (M5)
`core/outputs/` (`canvas` SVG/PDF writers, `drawing`, `system` diagrams, `tables`, `exports` YAML/JSON/XLSX, `stamp`, `build` build/write/status, `verify` independent verifier). Format and limits: `docs/OUTPUTS.md`.
- `build_outputs` is pure and deterministic: no dates, sorted rows, uncompressed PDF, XLSX re-zipped with fixed timestamps. Keep it that way; goldens depend on it.
- `core` must not import modules that import network code at import time (`xml.sax.saxutils` does; use `canvas.escape`). The offline test catches this.
- `core/outputs/verify.py` must stay independent of `tables.py`/`drawing.py`: derive expectations from the project.
- Adding an output file: build it in `build_outputs`, add its check to `verify.py` with a mutation test, regenerate goldens, document it in `docs/OUTPUTS.md`.
