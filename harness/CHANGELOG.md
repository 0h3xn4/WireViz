# Changelog

Versions follow semantic versioning. Every project file records the tool version that saved it.

## 0.1.0rc1 (release candidate; not yet signed off by the owner)

First feature-complete version for Ubuntu 22.04 and 24.04 (Windows and RHEL are not targets).

- **Model and files** (M1): human-readable, diffable project folders; atomic saves with backups; recovery mode; schema migrations; project lock; autosave journal.
- **Block diagram editor** (M2): zone lanes, guided and expert modes, connect tool with compatibility reasons, problems and to-do lists, import from CSV/XLSX, light and dark themes, UI scale 100 to 200%, first-run tour.
- **Generation** (M3): harness segmentation, pin allocation with reasons, wiring, wire sizing from configured tables, lengths and mass, stable IDs, regeneration report, independent verifier.
- **Design rule check** (M4): 20 rules with plain-language explanations, waivers with reasons, report, background run.
- **Outputs** (M5): drawings (SVG, PDF), wire lists, pinouts, BOM, mass and length, test tables, labels, system diagrams and matrices, XLSX, WireViz-style YAML, JSON; manifest, stale detection, independent output verifier.
- **Change control** (M6): review, release with gate, baselines, locks, new revisions, diff, change log, revision report.
- **Polish** (M7): accessibility audit and fixes (names for all controls, announced canvas), user guide (F1, offline), rule and configuration reference, soak test, link-label placement, hidden-panel hints, faster integrity checks, Ubuntu `.deb` and `.tar.gz` with install scripts, release checklist tool.

Known open items are listed in `docs/demos/M7.md`. Real derating and EMC values (D-11) and the harness boundary rule (D-10) still need the owner; until then results say so.
