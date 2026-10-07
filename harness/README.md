# Harness tool

Offline desktop tool for designing the electrical harnesses of a spacecraft from a block diagram: units and interfaces in, harnesses, pin allocations, checks, drawings, wire lists and a change-controlled record out. Runs on Ubuntu 22.04 and 24.04. Never uses the network.

- **Use it**: install the `.deb` (`sudo apt install ./harness-tool_<version>_amd64.deb`) or unpack the `.tar.gz` and run `./install.sh`; start *Harness tool*; press **F1** for the user guide (`docs/guide/USER_GUIDE.md`).
- **Command line**: `harness --help` (validate, generate, drc, export, release, diff, config, import-parts ...).
- **Status**: release candidate. Real derating and EMC values, the approved parts list and the segment lengths still have to be supplied; until then results say what is "pending" or "not checked" (`docs/PLACEHOLDERS.md`, `docs/IMPORTS.md`).

## For developers
Clean-room project: never copy code from `../src/wireviz` (GPL-3.0). Start with `CLAUDE.md` (commands, layout, conventions), then `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/FILE_FORMAT.md`, `docs/OUTPUTS.md`, `docs/RULES.md`, `docs/CONFIG.md`, `docs/SECURITY.md`. Release procedure: `docs/RELEASE.md`.

```
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[gui,dev]"
pytest            # tests, 90% core coverage gate
ruff format . && ruff check . && mypy
python -m tools.release_check --quick
```
