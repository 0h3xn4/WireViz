# Requirements (seed, traceable to SPEC.md)

Tests reference these IDs in their docstrings. Extended each milestone.

| ID | Requirement | Source | Verified by |
| --- | --- | --- | --- |
| REQ-OFFLINE-01 | The application makes no network calls and imports no networking modules. | SPEC Part 1, hard constraint 1 | `tests/test_offline.py`, frozen self-test under `unshare -n` |
| REQ-ARCH-01 | The core has no GUI, CLI or network imports. | SPEC Part 4, Architecture | `tests/test_architecture.py` |
| REQ-LIC-01 | Shipped dependencies are permissive or LGPL only; SBOM and licence report are produced per release. | SPEC Part 1, hard constraint 3 | `tests/test_licences.py`, `tools/gen_sbom.py` |
| REQ-PKG-01 | A self-contained package runs without admin rights and without internet. | SPEC Part 1, hard constraint 2 | `tools/build_installer.py`, `--selftest` in CI |
| REQ-BUILD-01 | Builds are reproducible from pinned versions. | SPEC Part 1, hard constraint 3 | `tools/check_reproducible.py` |
| REQ-I18N-01 | All UI strings live in one module. | SPEC Part 1, hard constraint 8 | `gui/strings.py` (review) |
| REQ-MODEL-01 | IDs are safe as file names and on drawings; SI/AWG helpers. | SPEC Part 1 (7), Part 2 | `tests/test_units_ids.py` |
| REQ-MODEL-02 | Strict, immutable model; no coercion or unknown fields. | SPEC Part 4 (engineering practice) | `tests/test_model.py` |
| REQ-INTEGRITY-01 | Referential integrity and duplicate IDs are checked on load, save and every transaction. | SPEC Part 4 (data integrity) | `tests/test_integrity.py` |
| REQ-IO-01 | Human-readable, diffable, deterministic files; byte-identical round trip. | SPEC Part 1 (6) | `tests/test_io.py` |
| REQ-RECOVERY-01 | Corrupt files open in recovery mode; nothing is dropped silently. | SPEC Part 4 (data integrity) | `tests/test_recovery.py`, `tests/test_fuzz.py` |
| REQ-ATOMIC-01 | Atomic saves, backups, plain-language disk errors. | SPEC Part 4 (data integrity, robustness) | `tests/test_atomic_lock.py` |
| REQ-LOCK-01 | Same project open twice is detected; on-disk change is detected. | SPEC Part 4 (data integrity) | `tests/test_atomic_lock.py`, `tests/test_io.py` |
| REQ-MIGRATE-01 | Lossless migrations that keep the original files. | SPEC Part 4 (data integrity) | `tests/test_migrate.py` |
| REQ-TX-01 | Model changes are transactions with consistent undo/redo. | SPEC Part 4 (robustness) | `tests/test_commands.py`, `tests/test_soak.py` |
| REQ-SOAK-01 | Random edit/undo/save/reload sequences keep the model consistent. | SPEC Part 4 (testing) | `tests/test_soak.py` |
| REQ-FUZZ-01 | The loader survives random and malformed input. | SPEC Part 4 (testing) | `tests/test_fuzz.py` |
| REQ-LIB-01 | Starter library is clearly unverified example data with no invented numbers. | SPEC Part 2 (parts library), Part 4 (rules) | `tests/test_library_config.py` |
| REQ-CFG-01 | Rule configuration lives in files; standards numbers are placeholders. | SPEC Part 4 (architecture, rules) | `tests/test_library_config.py` |
| REQ-CLI-01 | `harness validate` / `check` / `migrate` with meaningful exit codes. | SPEC Part 4 (architecture) | `tests/test_cli_project.py` |
| REQ-UX-01 | Design tokens meet WCAG 2.2 AA and category colours stay distinguishable under simulated colour blindness (dE >= 20). | SPEC Part 3 (accessibility, visual design) | `tests/test_tokens.py` |
| REQ-UX-02 | The prototype supports the ten journeys, works offline and logs no console errors. | SPEC Part 3 (UX process 1 and 2) | `tests/test_prototype.py` |
| REQ-UX-03 | The committed prototype matches the generator and is self-contained. | SPEC Part 1 (offline) | `tests/test_prototype_build.py` |
| REQ-GUI-01 | The Qt editor supports the UX journeys (add units, connect safely, table and import, redundancy and findings, delete and undo, modes, search, files, recovery, read-only). | UX.md section 3 | `tests/test_gui_journeys.py` |
| REQ-EDIT-01 | Diagram edits are validated operations that compose into transactions. | SPEC Part 3 (foolproof) | `tests/test_edit.py` |
| REQ-EDIT-02 | Units saved without positions get deterministic, non-overlapping ones. | UX.md section 6 | `tests/test_autoplace.py` |
| REQ-CHECK-01 | Logical findings state what, why and how to fix; fixes are safe; waivers need a justification. | SPEC Part 3 (DRC) | `tests/test_checks.py` |
| REQ-IMPORT-01 | Imports show a per-row preview and apply as one undo step. | SPEC Part 4 (imports) | `tests/test_imports.py`, GUI import tests |
| REQ-JOURNAL-01 | Autosave journal inside the project folder; restore after a crash. | SPEC Part 4 (data integrity) | `tests/test_recovery_journal.py`, GUI recovery tests |
| REQ-PERF-01 | The editor stays responsive at 200 units, 2,000 interfaces, 20,000 wires. | SPEC Part 3 (performance) | `tests/test_gui_perf.py`, `tools/bench_gui.py` |
| REQ-GEN-01 | Regeneration of an unchanged project is byte-identical and produces an empty plan. | SPEC Part 2 (deterministic generation) | `tests/test_generate.py` |
| REQ-GEN-02 | Generated harnesses keep stable IDs; released harnesses, locked wires and locked pins are never changed. | SPEC Part 2 (regeneration merge) | `tests/test_generate.py`, `tests/test_generate_parts.py` |
| REQ-GEN-03 | Sizing, mass and lengths never guess: missing inputs are listed. | SPEC placeholders rule | `tests/test_generate_parts.py` |
| REQ-VER-01 | An independent verifier detects missing, swapped, duplicated and outdated wiring. | SPEC Part 2 (verification) | `tests/test_generate.py` |
| REQ-PERF-02 | Generating 2,000 interfaces and 20,000 wires takes under 10 s. | SPEC Part 3 (performance) | `tests/test_generate.py`, `tools/bench_generate.py` |
| REQ-GUI-02 | Generate shows a preview, applies as one undo step, shows status, the independent check and Explain. | UX.md | `tests/test_gui_generate.py` |
| REQ-DRC-01 | Every design rule has a positive test (fires on a violation) and a negative test (quiet on a clean project). | SPEC Part 3 (DRC), Part 5 (tests) | `tests/test_drc.py` |
| REQ-DRC-02 | Findings state what, why and how to fix; warnings are waivable with justification, errors are not; waivers persist and appear in the report. | SPEC Part 3 (DRC) | `tests/test_drc.py` |
| REQ-DRC-03 | A check that cannot run because of placeholders says so. | SPEC placeholders rule | `tests/test_drc.py` |
| REQ-DRC-04 | Design rules run in the background and never block edits; Show, Fix and Waive work from the Problems panel. | SPEC Part 3 (DRC, performance) | `tests/test_gui_drc.py` |
| REQ-OUT-01 | Every output type is produced from the model, deterministically (equal model, equal bytes), and carries the generator version and model hash. | SPEC Part 3 (outputs) | `tests/test_outputs.py` |
| REQ-OUT-02 | Golden-file tests for every output type on three reference projects. | PLAN M5 | `tests/test_outputs.py`, `tests/fixtures/outputs/` |
| REQ-OUT-03 | Drawings print in greyscale; system diagrams use dark colours plus dash patterns. | SPEC Part 3 (accessibility, print) | `tests/test_outputs.py` |
| REQ-OUT-04 | Stale and modified outputs are detected in the CLI and the editor. | PLAN M5 | `tests/test_outputs.py`, `tests/test_gui_outputs.py` |
| REQ-VER-02 | Verifier v2 checks every artefact against the design; each check has a mutation test. | PLAN M5 | `tests/test_outputs.py` |
| REQ-OUT-05 | Outputs never invent numbers: undecided gauges, unknown lengths, masses and test limits are written as such. | SPEC placeholders rule | `tests/test_outputs.py` |
