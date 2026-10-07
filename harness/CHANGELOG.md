# Changelog

Versions follow semantic versioning. Every project file records the tool version that saved it.

## 0.1.0rc3 (release candidate; not yet signed off by the owner)

- **Release hardening**: fuzzing of loaders, importers, generation, rules, outputs and verifiers (found and fixed five crashes: CSV with bare carriage returns or stray characters, a damaged interface-type file stopping generation, damaged output files stopping the verifier, mixed connector keying in a rule, a harness without connectors in the drawing sketch); symlinked and oversized project files; zip-bomb and huge-sheet spreadsheets; a security review (`docs/SECURITY.md`) enforced by tests.
- **Ready for the data still to come**: `harness config` (hand-over checklist, range and table validation, ampacity CSV), `config-invalid` rule, `harness import-parts` (approved parts list, you define what the approval values mean), `harness import-lengths` (millimetres, for lengths measured outside the tool); `docs/IMPORTS.md`, `docs/OPEN_DECISIONS.md` (options for D-10 and D-15).
- **KiCad import** (`harness import-netlist`, `docs/KICAD.md`): unit connector pinouts from a KiCad XML netlist as fixed pins that generation respects. Tested on a hand-written fixture only.
- Ubuntu 22.04 build image and clean-machine test scripts (`packaging/ubuntu/container/`; need Docker, not run here), `README.md`.

## 0.1.0rc2

- **Drawing preview** in the Harness plans tab: the exact sheet the export draws, with next/previous for multi-sheet harnesses.
- **Routing sketch** on the first drawing sheet: connectors and branch points as boxes, segments with lengths (schematic, not to scale).
- **Outline** tab: every unit with its interfaces as a tree that screen readers read item by item; selection follows the diagram.
- **Arrange diagram** (Edit/View menu): units stay in their lanes, ordered to shorten links, one undo step.
- Bottom panel capped at 45% of the window and wider toasts, so the diagram keeps room at large UI scales.
- Multi-drop interfaces (more than two units) are still not generated; they need an engineering rule (see `docs/DECISIONS.md` D-116).

## 0.1.0rc1

First feature-complete version for Ubuntu 22.04 and 24.04 (Windows and RHEL are not targets).

- **Model and files** (M1): human-readable, diffable project folders; atomic saves with backups; recovery mode; schema migrations; project lock; autosave journal.
- **Block diagram editor** (M2): zone lanes, guided and expert modes, connect tool with compatibility reasons, problems and to-do lists, import from CSV/XLSX, light and dark themes, UI scale 100 to 200%, first-run tour.
- **Generation** (M3): harness segmentation, pin allocation with reasons, wiring, wire sizing from configured tables, lengths and mass, stable IDs, regeneration report, independent verifier.
- **Design rule check** (M4): 20 rules with plain-language explanations, waivers with reasons, report, background run.
- **Outputs** (M5): drawings (SVG, PDF), wire lists, pinouts, BOM, mass and length, test tables, labels, system diagrams and matrices, XLSX, WireViz-style YAML, JSON; manifest, stale detection, independent output verifier.
- **Change control** (M6): review, release with gate, baselines, locks, new revisions, diff, change log, revision report.
- **Polish** (M7): accessibility audit and fixes (names for all controls, announced canvas), user guide (F1, offline), rule and configuration reference, soak test, link-label placement, hidden-panel hints, faster integrity checks, Ubuntu `.deb` and `.tar.gz` with install scripts, release checklist tool.

Known open items are listed in `docs/demos/M7.md`. Real derating and EMC values (D-11) and the harness boundary rule (D-10) still need the owner; until then results say so.
