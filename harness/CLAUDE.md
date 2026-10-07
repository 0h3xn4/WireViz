# CLAUDE.md: spacecraft harness design tool (`harness/`)

Clean-room project inside the WireViz repo. **Never copy or import code from `../src/wireviz` (GPL-3.0).** Specification: `docs/SPEC.md`; decisions: `docs/DECISIONS.md`; architecture: `docs/ARCHITECTURE.md`; plan: `docs/PLAN.md`.

## Status
Planning stage: no code yet. Next: owner reviews ARCHITECTURE.md and PLAN.md, then implement M0.

## Commands (to be filled in during M0)
- Install: TBD
- Test: `pytest` (core coverage gate 90%)
- Lint/type: `ruff check` and `mypy --strict`
- Run CLI: `harness --help`

## Conventions
- `core` must not import `gui`, `cli` or any network module. Offline guarantee is tested.
- All model changes go through commands/transactions; GUI never mutates the model directly.
- Deterministic everywhere: sort by stable IDs, no timestamps in generated data, canonical JSON.
- Never invent standard values (derating, current ratings, mass). Use `PLACEHOLDER` config values and list them for the owner.
- No design data in logs. UI strings in one module.
- Every new dependency: record name, version, licence in `docs/DECISIONS.md`.
- Tests first; every bug fix gets a regression test.
- End each session with: done, tested, next, UX targets met/open.
