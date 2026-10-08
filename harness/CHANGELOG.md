# Changelog

Versions follow semantic versioning. Every project file records the tool version that saved it.

## Unreleased

- **Editor speed** (stress project: 200 units, 2000 links): renaming a unit takes about 35 ms (was 170 to 230), moving one 45 to 105 ms, a change while the interface table is shown 80 ms (was 370). One edit no longer repaints every unit and link: the lane backgrounds, which are as tall as the diagram, were invalidated on every edit; links whose curve did not change are left alone; the overview map follows on a 150 ms timer; the interface table keeps its rows when only values change. Regression tests count dirty regions and card builds instead of timing.
- **Platform**: Ubuntu 24.04 and newer only (D-127); CI tests on 24.04 only, the release build image is now `Dockerfile.build-24.04`. Editor speed: the problems panel builds only the cards it shows (add/undo/redo 3 to 6 times faster with many findings).

## 0.1.0rc4 (release candidate; not yet signed off by the owner)

- **Audit fixes** (`docs/AUDIT.md`): data loss and lock holes closed (unit IDs, baselines and change log, carried interfaces, recovery journal, project lock on every writing command, linked folders), wrong generation results fixed (released interfaces wired twice, locked pins, naming templates, harness numbers, provenance), the release gate now sees every error and checks the output files, the output verifier compares values, one function gives wire lengths, command line and importers show messages instead of tracebacks and read semicolon and tab files, the editor gives the diagram more room and has safer toasts, plain wording, reasons on disabled buttons, a Delete harness button and grouped problem cards.
- **Packaging**: the uninstaller removes only what the installer put there; the launcher works with spaces in paths; development tools are kept out of the package and the licence texts (LGPL for Qt) are shipped; the local system install no longer shares a folder with the .deb; defusedxml is a runtime dependency (spreadsheet XML protection); CI runs the prototype tests, scales timing limits, has timeouts and runs the package built on 22.04 on 24.04.
- `harness import-netlist` reads KiCad's default S-expression netlist as well as XML.

## 0.1.0rc3

- **Release hardening**: fuzzing of loaders, importers, generation, rules, outputs and verifiers (found and fixed five crashes: CSV with bare carriage returns or stray characters, a damaged interface-type file stopping generation, damaged output files stopping the verifier, mixed connector keying in a rule, a harness without connectors in the drawing sketch); symlinked and oversized project files; zip-bomb and huge-sheet spreadsheets; a security review (`docs/SECURITY.md`) enforced by tests.
- **Ready for the data still to come**: `harness config` (hand-over checklist, range and table validation, ampacity CSV), `config-invalid` rule, `harness import-parts` (approved parts list, you define what the approval values mean), `harness import-lengths` (millimetres, for lengths measured outside the tool); `docs/IMPORTS.md`, `docs/OPEN_DECISIONS.md` (options for D-10 and D-15).
- **KiCad import** (`harness import-netlist`, `docs/KICAD.md`): unit connector pinouts from a KiCad netlist (S-expression or XML) as fixed pins that generation respects. Read correctly on one real KiCad 10.0.6 netlist.
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
