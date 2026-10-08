# Harness tool

An offline desktop tool for designing the electrical harnesses of a spacecraft. You describe **units** (computer, power unit, wheels, ...) and the **interfaces** between them; the tool generates the harnesses (wires, connectors, pin allocation), checks them, writes drawings and lists, and keeps a change-controlled record of every release.

- **Your design is the source of truth.** Harnesses, drawings and lists are generated from it and can be regenerated at any time.
- **Offline.** It never uses the network (a test enforces this). Ubuntu 24.04 and newer only.
- **Reproducible.** The same design always produces byte-identical files, so Git diffs show real changes only.
- **Honest about what it does not know.** Engineering values (derating, ampacity, EMC rules, approved parts) are never invented. Until you supply them, results say *pending* or *not checked*.

## Status

Release candidate `0.1.0rc4`, not yet signed off by the owner. Still needed from people: the harness boundary rule (D-10), real derating and EMC values (D-11), the approved parts list (D-12), the title block (D-15), usability sessions and a screen-reader pass. See `docs/OPEN_DECISIONS.md` and `docs/RELEASE.md`.

## Documents

| You want to | Read |
| --- | --- |
| Do a task step by step (new project, import, release, KiCad, ...) | [`docs/HOWTO.md`](docs/HOWTO.md) |
| Learn the app (also in the app: F1) | [`docs/guide/USER_GUIDE.md`](docs/guide/USER_GUIDE.md) |
| Import parts, lengths, interfaces, engineering values | [`docs/IMPORTS.md`](docs/IMPORTS.md), [`docs/CONFIG.md`](docs/CONFIG.md) |
| Take unit connector pinouts from KiCad | [`docs/KICAD.md`](docs/KICAD.md) |
| Know what is still a placeholder | [`docs/PLACEHOLDERS.md`](docs/PLACEHOLDERS.md) |
| See which checks exist | [`docs/RULES.md`](docs/RULES.md) |
| Know what files the tool writes | [`docs/OUTPUTS.md`](docs/OUTPUTS.md), [`docs/FILE_FORMAT.md`](docs/FILE_FORMAT.md) |

## Install

- Debian package: `sudo apt install ./harness-tool_<version>_amd64.deb`
- Or unpack `harness-tool-<version>-linux-<arch>.tar.gz` and run `./harness-tool/install.sh` (no administrator rights; installs for your user).

Start **Harness tool** from the application menu (or `harness-tool`). The command line tool is `harness` (`harness --help`).

## A first look

1. Open the app. The sample project opens with a short tour.
2. File > New project, then add units and connect them with interfaces.
3. Press **Generate harnesses**, look at the preview, press **Apply**.
4. Read the **Problems** tab, press **Export outputs**.

The same from the command line:

```
harness validate my-project
harness generate my-project
harness drc my-project
harness export my-project
```

## What is in a project

A project is a folder of small JSON files (`project.json`, `config/`, `library/`, `logical/`, `physical/`, ...). Put it in Git. Outputs go to `outputs/` and are always safe to delete and regenerate. Format: `docs/FILE_FORMAT.md`.

## For developers

Clean-room project: never copy code from `../src/wireviz` (GPL-3.0). Start with `CLAUDE.md` (commands, layout, conventions), then `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/SECURITY.md`. Release procedure: `docs/RELEASE.md`.

```
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[gui,dev]"
pytest --cov      # tests; the 90% core coverage gate applies with --cov
ruff format . && ruff check . && mypy
python -m tools.release_check --quick
```
