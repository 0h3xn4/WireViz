# Decisions

Format: ID, decision, one-line rationale. `Default` = chosen by Claude Code because the owner said "default the rest"; the owner may overturn it.

## Scope and ownership
| ID | Decision | Rationale |
| --- | --- | --- |
| D-01 | Clean-room codebase in `harness/`, separate from upstream WireViz (GPL-3.0). No WireViz source is copied or imported; WireViz is only an export target (YAML). Contributors must not paste WireViz code. | Owner decision. Keeps new code free of GPL. |
| D-02 | Default: the tool is internal and proprietary for now. Dependencies stay permissive or LGPL so open-sourcing later remains possible. Licence file for `harness/` is TBD by owner. | Open question "licence and ownership" unanswered. |
| D-03 | Default: docs live in `harness/docs/` (not repo-root `docs/`, which holds WireViz docs). | Avoids mixing GPL project docs with the clean-room project. |

## Open decisions from the spec (all defaulted)
| ID | Question | Default | Needs owner input? |
| --- | --- | --- | --- |
| D-10 | Harness boundary rule | One harness per unit-connector pair, merged when both ends share a routing zone and merge rules allow; rule set lives in project config. | Yes, before M3. |
| D-11 | Standards baseline | No standard's numbers in code. `config/derating.json`, `config/emc.json` ship with placeholder values labelled `PLACEHOLDER: engineer must fill`. | Yes: someone must supply real derating, current and EMC values. |
| D-12 | Approved parts list | Library has `approval` field per part; importer for a generic CSV. EPPL/DCL-specific format deferred. | Only if a specific format is required. |
| D-13 | Mechanical lengths | Manual entry plus generic CSV import (harness ID, segment, length mm). No CAD-specific integration. | If a CAD tool is mandated. |
| D-14 | Operating systems | Windows 10/11 and Linux (RHEL/Rocky 8+, Ubuntu LTS) are targets; macOS best-effort, not in CI. | Confirm. |
| D-15 | Title block / drafting standard | Generic configurable title block (fields in spec). Template is a config file, replaceable later. | Yes, if a company format exists. |
| D-16 | Approval workflow | Status field (draft / in review / released) plus change log and baselines. No PLM integration. | Only if PLM is required. |
| D-17 | 3D routing | Out of scope. 2D routing segments only. | Confirm. |
| D-18 | Formboard drawings | Later: not in M0 to M7; revisit after M5. | Confirm. |
| D-19 | Security accreditation | CycloneDX JSON SBOM; code signing hooks in the build script but disabled until a certificate is provided. | Yes, if IT requires something else. |
| D-20 | Formal qualification (ECSS-E-ST-40C / Q-ST-80C) | Assume not required, but requirement IDs (`REQ-xxx`) are used in `docs/REQUIREMENTS.md` and tests reference them so traceability can be added cheaply. | Yes, must be confirmed early; it changes process overhead. |

## Technology (see ARCHITECTURE.md for the comparison)
| ID | Decision | Licence | Rationale |
| --- | --- | --- | --- |
| D-30 | Python 3.12+ (3.13 is installed in dev environment) | PSF | Matches strong default in spec. |
| D-31 | PySide6 (Qt) for GUI | LGPL-3.0 | Mature canvas (QGraphicsView), offscreen rendering for UX screenshots, pytest-qt. LGPL obligations: dynamic linking, ship licence text. |
| D-32 | pydantic v2 for model validation and JSON Schema export | MIT | Strict validation and schema generation from one source. |
| D-33 | Project files: JSON, sorted keys, 2-space indent, `\n` endings, UTF-8 | stdlib | Diffable, no extra dependency. YAML only for the WireViz export (PyYAML, MIT). |
| D-34 | openpyxl for XLSX | MIT | Pure Python, no network. |
| D-35 | reportlab for PDF; core also writes SVG itself | BSD | Vector PDF with embedded bundled TTF fonts; no system font dependency. To be re-checked in M5 (fallback: Qt QPdfWriter in GUI layer only). |
| D-36 | Fonts: Inter and JetBrains Mono (SIL OFL) bundled; icon set: Lucide (ISC) bundled as SVG. Final choice made in docs/UX.md. | OFL / ISC | No CDN, permissive. |
| D-37 | Dev tools: pytest, hypothesis, pytest-qt, pytest-cov, mypy (strict), ruff, cyclonedx-bom, pip-licenses | MIT/BSD/Apache | Spec testing and SBOM needs. Dev-only, not shipped. |
| D-38 | Packaging: PyInstaller (one-folder build, plus Windows installer via Inno Setup or portable zip) | GPL w/ bootloader exception (allows closed apps) / Inno Setup licence | Standard offline packaging. Build must be run per OS in CI. |
| D-39 | CLI: stdlib `argparse` | stdlib | Fewer dependencies in the headless core. |
| D-40 | Package layout `harness/src/harness_tool/{core,cli,gui}`; core never imports gui or network modules (enforced by test). | n/a | Spec architecture rule. |

## M0 additions
| ID | Decision | Rationale |
| --- | --- | --- |
| D-41 | Build backend setuptools 84.0.0 (MIT), runtime pins: pydantic 2.13.5 (MIT), PySide6-Essentials 6.11.2 (LGPL-3.0 OR GPL), shiboken6 6.11.2 (same). | PySide6-Essentials avoids the large Addons set; needed so `license = "LicenseRef-Proprietary"` (SPDX string) works. |
| D-42 | Dev-only tools (not shipped): pytest 9.1.1, pytest-cov 7.1.0, pytest-qt 4.5.0, hypothesis 6.168.5 (MPL-2.0), mypy 2.4.0, ruff 0.16.10, cyclonedx-bom 7.5.0 (Apache-2.0), pip-licenses 5.5.5, pyinstaller 6.22.3 (GPL-2.0+ with bootloader exception, permits closed apps). Transitive `pyinstaller-hooks-contrib` is dual Apache/GPL, dev-only. | The licence report checks only the clean runtime env. |
| D-43 | Licence classifier: SPDX `OR` needs any allowed, `AND` and `;` need all allowed, GPL/AGPL without LGPL rejected, unknown rejected. | Conservative allow-list. |
| D-44 | Qt build excludes QtNetwork, WebEngine, WebChannel, WebSockets, QtQml/Quick, QtPdf, QtSvg. QtSvg may be re-enabled in M2 if the canvas needs it. | Offline guarantee and smaller package. |
| D-45 | Coverage gate disabled until M1 (empty core has 0 statements). | Avoids a meaningless failure; enable in M1. |

## M1 additions
| ID | Decision | Rationale |
| --- | --- | --- |
| D-50 | Connector IDs (box and harness) and wire IDs are unique across the whole project. Default naming `UNIT-J01`, `W001-P1`, `W001-001` supports this. | Wires and interfaces can then reference connectors by one ID. Confirm. |
| D-51 | IDs must also be unique ignoring case. | Windows and macOS file systems are case-insensitive; harness IDs are file names. |
| D-52 | Models are immutable pydantic objects with strict types (no coercion); changes use `evolve()` and `commands`. | Cheap undo (store old objects), safe sharing, no silent type conversion of flight data. |
| D-53 | Undo/redo stores operations (put/delete of whole objects), not project snapshots. | Memory stays small at stress size. |
| D-54 | A project with unloadable parts cannot be saved over its folder, only "save as", which also writes the rejected data verbatim. | Never lose data silently; salvage the rest. |
| D-55 | Saves with integrity errors are refused unless explicitly allowed (recovery copies). | Spec: validate on every save. |
| D-56 | No new third-party dependencies in M1 (pydantic only); hypothesis is dev-only. | Keeps the SBOM small. |

## M2 gate additions
| ID | Decision | Rationale |
| --- | --- | --- |
| D-60 | Dev-only dependency: playwright 1.63.0 (Apache-2.0), driving the pre-installed Chromium, to test the clickable prototype. Not shipped. Tests skip when no Chromium is present. | Verifies the prototype journeys automatically. |
| D-61 | Category colours were chosen by a small search that maximises the minimum colour difference under simulated colour blindness, subject to AA contrast on all surfaces; the test locks in dE >= 20. | A hand-picked palette had indistinguishable pairs for protanopia. |
| D-62 | Zones are vertical lanes in the prototype (zone follows where a unit is placed). Free-form zones are an open question in UX.md. | Simplest model that makes "grouped by zone" visible. |
| D-63 | The prototype's harness rule (one harness per interface) and all pin/gauge data are mock. The real rule is D-10. | Prototype only. |

## M2 additions (defaults taken because the owner approved the prototype without answering UX.md section 11)
| ID | Decision | Rationale |
| --- | --- | --- |
| D-64 | The editor starts in Guided mode and then remembers the last mode, theme and UI scale per user (local settings file, no design data). | Prototype default; mode never changes data. |
| D-65 | Zones are vertical lanes; their ordered list is stored in `logical/layout.json` and a unit's zone follows the lane it sits in. "Add zone…" appends a lane. | Simplest model that shows "grouped by zone". Free-form zones remain an option. |
| D-66 | The default one-click fix for a cross-strap is "connect to a redundant copy of the nominal end"; waiving with a justification is always offered next to it. | Prototype review: the fix must make engineering sense. |
| D-67 | Seven built-in unit templates (computer, power unit, wheel, star tracker, payload, transceiver, pyro unit). Importing your own template list is deferred. | Enough for the usability tests; needs the owner's list to go further. |
| D-68 | Diagram positions are stored in the project (`layout.json`), use one footprint independent of mode (so switching modes never causes overlap), and are auto-assigned deterministically for units without one. | Layout must be remembered and diffable. |
| D-69 | `Connector.carries` and `Endpoint.auto` are new optional fields; the schema version stays 1 because projects saved by M1 load and behave unchanged. | Additive change; tested with an M1-format fixture. |
| D-70 | Waivers live in `waivers.json` with a mandatory justification of at least 10 characters. | SPEC DRC waiver rule. M4 reuses the store. |
| D-71 | The sample project opens untitled with a banner and no autosave journal until it is saved to a folder. | Rule: no project content outside a project folder. |
| D-72 | Autosave = journal in `<project>/.harness-recovery/`, debounced 1.5 s; restore is offered at open. | Never lose more than a few seconds of work. |
| D-73 | XLSX import uses openpyxl 3.1.5 (MIT) and et_xmlfile 2.0.0 (MIT), read-only, at most 8 MB and 20,000 rows. | SPEC import requirement; permissive licences. |
| D-74 | UI scale 100 to 200% scales fonts and spacing; panels auto-collapse by effective window size; the diagram has its own zoom. | Keeps the canvas usable at 200%. |
| D-75 | "Generate harnesses" is shown but disabled with an explanation until M3. | Honest about what exists. |
| D-76 | Canvas keyboard support: Tab between units and links, Enter selects or picks, Shift+arrows nudge. The interface table is the screen-reader-friendly alternative. Full screen-reader support for the canvas is open (M7). | Qt graphics items have no accessibility tree by default. |
| D-77 | A fully zoomed-out view draws units as plain boxes and links without labels (level of detail), and panels refresh lazily when hidden. | Needed for the 200-unit / 2,000-interface target. |
