# CLAUDE.md: spacecraft harness design tool (`harness/`)

Clean-room project inside the WireViz repo. **Never copy or import code from `../src/wireviz` (GPL-3.0).** Specification: `docs/SPEC.md`; decisions: `docs/DECISIONS.md`; architecture: `docs/ARCHITECTURE.md`; plan: `docs/PLAN.md`.

## Status
M0 done (see `docs/demos/M0.md`). Next: M1 (model and files).

## Commands (run from `harness/`)
- Setup: `python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[gui,dev]"` (Linux also needs libegl1 libgl1 libxkbcommon0 libfontconfig1 libdbus-1-3 for Qt)
- Test: `pytest` (Qt runs offscreen via tests/conftest.py); coverage: `pytest --cov` (90% gate on core from M1)
- Lint/type: `ruff format . && ruff check . && mypy`
- CLI: `harness --version`; GUI: `harness-gui`
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
