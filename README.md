# Harness Design Studio

**An offline desktop tool for designing the electrical harnesses of a spacecraft.**
You describe the units (computer, power unit, reaction wheel, ...) and the interfaces between them. The tool generates the harnesses (connectors, pins, wires, each with a reason), checks them against design rules, writes the drawings and lists, and keeps a change-controlled record of every release.

```
 you draw                      the tool makes                  the tool writes
 units + interfaces   ──►      harnesses: connectors,   ──►    drawings, wire lists, pinouts,
                               pins, wires, with a             BOM, test tables, labels,
                               reason for each choice          block diagram, change log
```

- **Offline and reproducible.** No network, and the same design always produces byte-identical files, so Git diffs show real changes only.
- **Honest about what it does not know.** Engineering values (derating, ampacity, EMC rules, approved parts) are never invented. Until you supply them, results say *pending* or *not checked*.
- **Desktop app and command line.** `harness-design-studio` is the editor, `harness` is the command line tool.
- **Runs on Ubuntu 24.04 or newer** (x86-64). Version 0.1.0. See [Status](harness/README.md#status) for what is and is not done.

## Start here

| You want to | Go to |
| --- | --- |
| **try it in five minutes** | [`harness/README.md`](harness/README.md#try-it-in-five-minutes) |
| **install it** | [`harness/docs/INSTALL.md`](harness/docs/INSTALL.md) (Ubuntu package or unpack and run) |
| **learn it, step by step** | [`harness/docs/LEARNING_PATH.md`](harness/docs/LEARNING_PATH.md), then [`harness/docs/GETTING_STARTED.md`](harness/docs/GETTING_STARTED.md) (your first harness in 45 minutes) |
| **see all the documents** | [`harness/docs/README.md`](harness/docs/README.md) |
| **get the newest release** | the [Releases page](../../releases) of this repository |

Quick taste, after installing:

```
harness new wheel-link --template first-steps
harness generate wheel-link
harness drc wheel-link
harness export wheel-link
```

Four example projects and a set of templates (CSV imports, a design worksheet, a review checklist, CI scripts) ship with the tool: `harness new --list`, `harness templates FOLDER`.

## What is in this repository

This repository holds two separate things.

| Folder | What it is |
| --- | --- |
| [`harness/`](harness/) | **Harness Design Studio**, the tool described above. Its own sources, tests, documentation and packaging. This is the project of this repository. |
| `src/`, `docs/`, `examples/`, `tutorial/`, `setup.py` | The upstream [WireViz](https://github.com/wireviz/WireViz) tool for drawing cable and wire harnesses from YAML text files, kept as it was when this repository was created. Its own documentation is [`docs/README.md`](docs/README.md). |

Harness Design Studio is a **clean-room** project: it shares no code with WireViz and never imports it. It can write a harness as WireViz-style YAML (best effort), but that is all the two have in common. WireViz is released under the GPL-3.0 (the [`LICENSE`](LICENSE) in this folder).

## For developers

Start with [`harness/CLAUDE.md`](harness/CLAUDE.md) (commands, layout, conventions), then [`harness/docs/ARCHITECTURE.md`](harness/docs/ARCHITECTURE.md) and [`harness/docs/DECISIONS.md`](harness/docs/DECISIONS.md). CI for the tool is `.github/workflows/harness-ci.yml`; the release procedure is [`harness/docs/RELEASE.md`](harness/docs/RELEASE.md).
