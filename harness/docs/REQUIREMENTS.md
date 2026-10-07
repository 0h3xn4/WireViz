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
