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
