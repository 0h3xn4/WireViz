# Architecture

> **Status.** Written as a proposal and since built as described, with these changes: the platform is Ubuntu 24.04 and newer only (D-110, D-127), so the Windows and RHEL remarks below are historical; the design rule check runs in a helper process (D-128). The layout in section 2 and the mechanisms in section 4 match the code.

## 1. Stack comparison

| | A. Python + PySide6 (chosen) | B. Rust core + Tauri (web UI) | C. Electron + TypeScript |
| --- | --- | --- | --- |
| Offline packaging | PyInstaller one-folder; ~150-250 MB; proven on locked-down hosts | Small binaries (~10 MB) but needs OS WebView2/WebKitGTK, which may be missing or outdated on RHEL 8 / locked Windows | Bundles Chromium (~150 MB); works everywhere; large npm supply chain to vendor |
| Licences | Python/Qt LGPL OK | Rust crates mostly MIT/Apache; WebKit LGPL | MIT; many transitive npm licences to audit |
| Canvas editor | QGraphicsView: mature, high-DPI, offscreen screenshots | Custom canvas/SVG in JS | Same as Tauri |
| PDF/SVG | reportlab + own SVG writer | Strong (printpdf, svg) but fewer drafting helpers | JS libs, heavier |
| Testing the GUI | pytest-qt, offscreen | Playwright-style, more infra | Same |
| Team ramp-up / Claude Code velocity | Fastest; one language for core, CLI, GUI | Two languages | Two ecosystems |
| Supply chain / SBOM | pip: small, vendorable | cargo vendor + npm | npm: very large |

**Choice: A.** It fits the air-gapped constraint (no system WebView dependency), has the best-supported desktop canvas, and keeps a single language. Cost: bigger installer and slower startup than Tauri. Performance risk (20,000 wires) is handled by keeping the core pure and algorithmically indexed, and by rendering only visible items in the canvas; if profiling in M3 shows the generator misses the 10 s target, hot spots can move to a compiled extension without changing the API.

## 2. Layering

```
harness/src/harness_design_studio/
  core/            no GUI, no network imports (enforced by test)
    model/         pydantic models: logical + physical layer, IDs, units
    io/            project folder load/save, atomic writes, schema migration, recovery mode
    library/       parts library load/validate/import
    config/        rules, derating, naming, segregation, EMC (JSON, with placeholders)
    commands/      transactions + undo/redo (command pattern over the model)
    generate/      segmentation, pin allocation, wire sizing, length/mass, naming
    drc/           rules, severities, waivers, messages, fixes
    explain/       provenance records: why a harness / pin / gauge exists
    outputs/       SVG/PDF/CSV/XLSX/WireViz/JSON generators, title blocks
    verify/        independent output verifier (separate code path from generate/ and outputs/)
    vcs/           revisions, baselines, diff, change log
    imports/       CSV/XLSX importers with preview and per-row errors
    templates.py   example projects and import templates shipped with the tool (`harness new`)
  cli/             `harness` commands: start (new, templates), check, generate, export, change control, imports
    start.py       `harness new` and `harness templates`

  gui/             PySide6: canvas, table view, panels, command palette, design-system tokens
  resources/       bundled help (offline HTML) and examples: example projects (built by tools/build_examples.py) and templates (CSV, netlist, CI scripts, checklist, demo values)
```

Rules: `gui` and `cli` depend on `core`; `core` depends on nothing in `gui`/`cli`. The GUI never mutates the model directly; every change is a `Command` run in a transaction (all-or-nothing, invariant check after each in debug builds).

## 3. Project folder format

```
myproject/
  project.json            schema_version, tool_version, name, naming scheme ref, mode defaults
  config/                 segmentation.json, segregation.json, derating.json (PLACEHOLDER), naming.json, emc.json, titleblock.json
  library/                connectors.json, contacts.json, wires.json, backshells.json, sleeving.json (versioned, with approval status)
  logical/
    units/<subsystem>.json        one file per subsystem so merges are clean
    interfaces/<subsystem>.json
    interface_types.json
  physical/
    connectors/<subsystem>.json
    harnesses/<harness-id>.json   wires, splices, shields, segments, overrides, locks
  generated/              derived data + outputs; carries model_hash + generator version; safe to delete
  baselines/<harness-id>/<rev>.json   frozen snapshots on release
  waivers.json, changelog.jsonl
```

Properties: stable key ordering, stable IDs (`<kind>-<ULID-free short id>` assigned deterministically or user-given; never renumbered once released), one object per file section so Git merges rarely conflict. The `generated/` directory is separate from user-edited data, so "data is the source of truth" holds and regeneration diffs stay small. Atomic save: write `*.tmp`, fsync, rename, keep `*.bak`.

## 4. Key mechanisms

- **Determinism:** generation is a pure function `(model, config, library) -> physical model + provenance`. Sorting by stable IDs everywhere; no reliance on dict/set order or timestamps; hash of canonical JSON is the `model_hash`. Property test: regenerate twice and compare bytes.
- **Locks and overrides:** user-edited pins/wires carry `locked: true` or `override` records. Regeneration runs in "merge" mode and returns a `RegenReport` (kept / changed / conflicts) shown before applying.
- **Explain:** every generator decision appends a provenance record `{object_id, rule_id, inputs, reason}`. The "Explain" action and the DRC fix text read these.
- **Verifier:** `verify/` reads only emitted artefacts (CSV/JSON/SVG data) and the model, and recomputes expected end-to-end connectivity with its own simple implementation (no shared code with `generate/` beyond model types). Release command refuses on any verifier error. Stale detection: each artefact stores `model_hash`; GUI/CLI compare it with the current hash.
- **DRC process:** the background check runs in a long-lived helper process (`gui/drc_process.py` starts `core/drc/worker.py`; a packaged program is started with `--drc-worker`), because a thread shared the interpreter lock with the editor and stalled edits. The project and the findings cross the pipes in small pieces. If the helper cannot start it falls back to a thread (D-128).
- **DRC:** each rule is a class with `id`, `severity`, `check(model) -> [Finding]`, message template (what / why / fix), optional `fix(model) -> Command`. Rules and thresholds come from config. Waivers are keyed by (rule id, object id, hash of finding) with mandatory justification.
- **Recovery mode:** loader validates per file; broken files are quarantined into a `RecoveryReport`, the rest loads; nothing is dropped silently and originals are never overwritten.
- **Offline guarantee:** test 1 scans all source and imported modules for `socket`, `http`, `urllib`, `requests`, `ssl`, `QtNetwork` etc.; test 2 patches `socket.socket` to raise and runs the CLI and a GUI smoke test; GUI build excludes QtNetwork/QtWebEngine.
- **Logging:** structured, local, allow-listed fields only (event name, error type, counts). Object names and values are never logged by default.
- **Performance:** model holds ID indexes; DRC is incremental (re-check only affected objects); generation parallelisable per harness group; canvas uses item culling. Stress project generated by script in `tests/fixtures`.

## 5. Testing architecture

pytest + hypothesis (property tests, fuzzing loaders/importers/generator), pytest-cov (>= 90% core gate), mypy strict, ruff, pytest-qt for journeys, golden-file tests per output type on three reference projects (`mini3`, `sat15`, `stress`), soak test (random edits/undo/redo/save/reload with invariants + verifier), offline test, migration fixtures per schema version, CI on Ubuntu 24.04 (the supported platform).

## 6. Risks

1. Pin allocation is the hardest algorithm: start with a constraint-ordered greedy allocator with explicit rule list and provenance; keep it replaceable.
2. Real derating/EMC numbers are missing (D-11); generator and DRC must run with placeholders and mark every result "uses placeholder rules" until replaced.
3. Installer size and PyInstaller: build on the supported OS (Ubuntu 24.04) in CI.
4. Locked-down hosts may block unsigned executables; code signing is configurable (D-19).
5. UX sign-off is a gate: no full editor before the prototype review (spec UX process step 2).
