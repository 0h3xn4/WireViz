# Harness Design Studio

An offline desktop tool for designing the electrical harnesses of a spacecraft.

> **Created mainly by an AI.** Harness Design Studio was written mainly by Claude, Anthropic's AI assistant, used through Claude Code; the repository owner set the requirements and approved the decisions and releases. No other person has reviewed it independently (waived by the owner, `compliance/DEVIATIONS.md`), and no compliance with any standard is claimed. Check its results before relying on them.
>
> **Based in the WireViz repository.** This repository is a fork of [WireViz](https://github.com/wireviz/WireViz). Harness Design Studio is a separate, clean-room codebase inside it: no WireViz code is copied or imported (D-01 in [`docs/DECISIONS.md`](docs/DECISIONS.md)), and WireViz is an export target (WireViz-style YAML, best effort). The original WireViz documentation is at [`../docs/README.md`](../docs/README.md).

You describe the **units** (computer, power unit, reaction wheel ...) and the **interfaces** between them. The tool generates the harnesses (connectors, pins, wires), checks them, writes the drawings and lists, and keeps a change-controlled record of every release.

```
 you draw                      the tool makes                  the tool writes
 units + interfaces   ──►      harnesses: connectors,   ──►    drawings, wire lists, pinouts,
                               pins, wires, with a             BOM, test tables, labels,
                               reason for each choice          block diagram, change log
```

- **Your design is the source of truth.** Harnesses, drawings and lists are generated from it and can be regenerated at any time.
- **Offline.** It never uses the network (a test enforces this).
- **Reproducible.** The same design always produces byte-identical files, so Git diffs show real changes only.
- **Starts from the usual standards.** RS-422, RS-485 and CAN for communication, Micro-D (9 to 31 pin) for power and data, Ethernet as the alternative for high data rates, SMA for RF. Other types and connectors can be added.
- **Honest about what it does not know.** Engineering values (derating, ampacity, EMC rules, approved parts) are never invented. Until you supply them, results say *pending* or *not checked*.

Runs on **Ubuntu 24.04 or newer**. Version `0.1.0`, released by the owner with the engineering decisions still open (see [Status](#status)).

## Try it in five minutes

1. **Install** (details in [`docs/INSTALL.md`](docs/INSTALL.md)):

   ```
   sudo apt install ./harness-design-studio_<version>_amd64.deb
   harness --version
   ```

2. **Make a practice project** from the built-in example and let the tool work on it:

   ```
   harness new wheel-link --template first-steps
   harness generate wheel-link
   harness drc wheel-link
   harness export wheel-link
   ```

3. **Look at the result**: drawings and lists are in `wheel-link/outputs/`. Open the project in the app (**Harness Design Studio** in the application menu, then **File > Open project…**) to see the diagram, the *Problems* tab and the *Why is it like this?* explanation of every wire.

That is the whole idea. [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) walks through it step by step with the real output of every command.

## Documentation

| You are | Start with |
| --- | --- |
| **new to the tool** | [`docs/LEARNING_PATH.md`](docs/LEARNING_PATH.md): the route in nine steps. Or directly [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md): your first harness in 45 minutes, then [`docs/CONCEPTS.md`](docs/CONCEPTS.md): how the tool thinks, in ten minutes. |
| **installing it** | [`docs/INSTALL.md`](docs/INSTALL.md) |
| **doing a task** (import, KiCad, release, Git, CI) | [`docs/HOWTO.md`](docs/HOWTO.md), step by step |
| **looking something up** | [`docs/CLI.md`](docs/CLI.md) (every command), [`docs/guide/USER_GUIDE.md`](docs/guide/USER_GUIDE.md) (also in the app: **F1**), [`docs/FAQ.md`](docs/FAQ.md), the one-page [`docs/CHEATSHEET.md`](docs/CHEATSHEET.md) |
| **stuck** | [`docs/FAQ.md`](docs/FAQ.md) |
| **an engineer supplying values** | [`docs/CONFIG.md`](docs/CONFIG.md), [`docs/PLACEHOLDERS.md`](docs/PLACEHOLDERS.md), [`docs/IMPORTS.md`](docs/IMPORTS.md) |
| **a reviewer or releaser** | [`docs/RULES.md`](docs/RULES.md), [`docs/OUTPUTS.md`](docs/OUTPUTS.md), the review checklist in the templates |
| **a developer** | [`CLAUDE.md`](CLAUDE.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DECISIONS.md`](docs/DECISIONS.md), [`docs/SECURITY.md`](docs/SECURITY.md) |

[`docs/README.md`](docs/README.md) lists every document.

## Examples and templates

`harness new --list` shows the example projects shipped with the tool:

| Example | What it is |
| --- | --- |
| `blank` | An empty project with the starter parts and interface types. Start a real design here. |
| `first-steps` | Three units, a power link and an RS-422 link. Nothing generated yet. Start here. |
| `minimal-satellite` | Seven units, nominal only: solar array, battery, power unit, computer, radio, wheel and sun sensor. A small but realistic starting point. |
| `small-satellite` | 14 units with redundant chains. Generate it to see a realistic system. |
| `flatsat` | A complete bench: 23 flight and ground units, generated, with example numbers. Read [`docs/FLATSAT_EXAMPLE.md`](docs/FLATSAT_EXAMPLE.md) for a tour. |

`harness templates my-templates` copies templates for your own data: CSV files for interfaces, approved parts and segment lengths, a KiCad netlist, a CI script, a GitHub Actions workflow, a **design worksheet** to plan a design on paper, a design review checklist and *demo* engineering values for learning (not engineering data). What each file is for: [`src/harness_design_studio/resources/examples/templates/README.md`](src/harness_design_studio/resources/examples/templates/README.md).

## What is in a project

A project is a folder of small JSON files (`project.json`, `config/`, `library/`, `logical/`, `physical/`, ...). Put it in Git. Outputs go to `outputs/` and are always safe to delete and regenerate. Format: [`docs/FILE_FORMAT.md`](docs/FILE_FORMAT.md).

## Status

Version `0.1.0`, released by the owner on 2026-10-09 with the following still open (`compliance/SIGNOFF.md`). Not supplied: the harness boundary rule (D-10), real derating and EMC values (D-11), the approved parts list (D-12), the title block (D-15). Not done and waived by the owner: independent review, usability sessions, a screen-reader pass and a clean-machine installation test (`compliance/DEVIATIONS.md`). See [`docs/OPEN_DECISIONS.md`](docs/OPEN_DECISIONS.md) and [`docs/RELEASE.md`](docs/RELEASE.md). Until the engineering values exist, results say so.

## For developers

Clean-room project: never copy code from `../src/wireviz` (GPL-3.0). Start with [`CLAUDE.md`](CLAUDE.md) (commands, layout, conventions), then [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DECISIONS.md`](docs/DECISIONS.md) and [`docs/SECURITY.md`](docs/SECURITY.md). Release procedure: [`docs/RELEASE.md`](docs/RELEASE.md).

```
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[gui,dev]"
pytest --cov      # tests; the 90% core coverage gate applies with --cov
ruff format . && ruff check . && mypy
python -m tools.release_check --quick
```
