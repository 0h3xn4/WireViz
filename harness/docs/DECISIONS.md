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
