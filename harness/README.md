# Harness tool

An offline desktop tool for designing the electrical harnesses of a spacecraft.

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
- **Honest about what it does not know.** Engineering values (derating, ampacity, EMC rules, approved parts) are never invented. Until you supply them, results say *pending* or *not checked*.

Runs on **Ubuntu 24.04 or newer**. Release candidate `0.1.0rc4`, not yet signed off by the owner (see [Status](#status)).

## Try it in five minutes

1. **Install** (details in [`docs/INSTALL.md`](docs/INSTALL.md)):

   ```
   sudo apt install ./harness-tool_<version>_amd64.deb
   harness --version
   ```

2. **Make a practice project** from the built-in example and let the tool work on it:

   ```
   harness new wheel-link --template first-steps
   harness generate wheel-link
   harness drc wheel-link
   harness export wheel-link
   ```

3. **Look at the result**: drawings and lists are in `wheel-link/outputs/`. Open the project in the app (**Harness tool** in the application menu, then **File > Open project…**) to see the diagram, the *Problems* tab and the *Why is it like this?* explanation of every wire.

That is the whole idea. [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) walks through it step by step with the real output of every command.

## Documentation

| You are | Start with |
| --- | --- |
| **new to the tool** | [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md): your first harness in 45 minutes. Then [`docs/CONCEPTS.md`](docs/CONCEPTS.md): how the tool thinks, in ten minutes. |
| **installing it** | [`docs/INSTALL.md`](docs/INSTALL.md) |
| **doing a task** (import, KiCad, release, Git, CI) | [`docs/HOWTO.md`](docs/HOWTO.md), step by step |
| **looking something up** | [`docs/CLI.md`](docs/CLI.md) (every command), [`docs/guide/USER_GUIDE.md`](docs/guide/USER_GUIDE.md) (also in the app: **F1**), [`docs/FAQ.md`](docs/FAQ.md) |
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
| `small-satellite` | 14 units with redundant chains. Generate it to see a realistic system. |

`harness templates my-templates` copies templates for your own data: CSV files for interfaces, approved parts and segment lengths, a KiCad netlist, a CI script, a GitHub Actions workflow, a design review checklist and *demo* engineering values for learning (not engineering data). What each file is for: [`src/harness_tool/resources/examples/templates/README.md`](src/harness_tool/resources/examples/templates/README.md).

## What is in a project

A project is a folder of small JSON files (`project.json`, `config/`, `library/`, `logical/`, `physical/`, ...). Put it in Git. Outputs go to `outputs/` and are always safe to delete and regenerate. Format: [`docs/FILE_FORMAT.md`](docs/FILE_FORMAT.md).

## Status

Release candidate `0.1.0rc4`. Still needed from people: the harness boundary rule (D-10), real derating and EMC values (D-11), the approved parts list (D-12), the title block (D-15), usability sessions and a screen-reader pass. See [`docs/OPEN_DECISIONS.md`](docs/OPEN_DECISIONS.md) and [`docs/RELEASE.md`](docs/RELEASE.md). Until the engineering values exist, results say so.

## For developers

Clean-room project: never copy code from `../src/wireviz` (GPL-3.0). Start with [`CLAUDE.md`](CLAUDE.md) (commands, layout, conventions), then [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DECISIONS.md`](docs/DECISIONS.md) and [`docs/SECURITY.md`](docs/SECURITY.md). Release procedure: [`docs/RELEASE.md`](docs/RELEASE.md).

```
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[gui,dev]"
pytest --cov      # tests; the 90% core coverage gate applies with --cov
ruff format . && ruff check . && mypy
python -m tools.release_check --quick
```
