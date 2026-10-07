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
| D-78 | Generation is plan-then-apply: `plan_generation` is pure and returns operations, a change report and a provenance record; the editor shows the report first and applies it as one undoable step. | Foolproof regeneration; nothing changes before the user agrees. |
| D-79 | Default segmentation (placeholder for D-10): one harness per pair of box connectors. `per_unit_pair` and `per_zone_pair` are selectable in `config/segmentation.json`. Nominal and redundant chains and pyro interfaces never share a harness. | Owner has not answered D-10; the default is the safest to review. |
| D-80 | Wiring rule: an `out` signal of one end goes to the matching `in` signal of the other end (TX+ to RX+), matched by position; passive, bidirectional and unpaired directional signals connect to the same-named signal. | Starter types list signals in matching order; analog and discrete types have one direction only. |
| D-81 | Pin allocation: locked pins never move; power first; twisted pairs on adjacent pins; the power-to-signal gap is configurable (placeholder 0); a still-valid earlier allocation is kept so regeneration produces small diffs. | SPEC pin rules; stable diffs. |
| D-82 | Stable identity: harness IDs come from a monotonic counter in the generation record and are reused by segmentation key; wire IDs by wire key. Released harnesses are frozen; locked wires and pins are kept. Manually drawn harnesses own their interfaces and pins and are never touched. | Regeneration must never destroy reviewed or released work. |
| D-83 | The generation input hash covers everything generation reads and excludes outputs (generated pins, wires), placements and waivers. The record stores it; status is none, current or stale. | Detects out-of-date harnesses without false alarms. |
| D-84 | Wire sizing uses only configured tables (ampacity by AWG, bundle and temperature derating, voltage drop, resistivity). With any value missing the gauge stays "pending" and the plan names what is missing. Mass likewise reports missing library data instead of guessing. | Never invent standards values (D-11 open). |
| D-85 | The verifier (`core/verify.py`) is an independent code path: it recomputes the expected connections from the interfaces and compares them with the wires. It shares only the hash comparison with the generator. | Independent check of the generator's output. |
| D-86 | The generation worker runs in a QThread behind a cancellable progress dialog; cancel changes nothing. The UI is blocked meanwhile, so the project cannot change under the worker. | Responsiveness without data races. |
| D-87 | The design rule check (`core/drc/`) has 20 rules plus the verifier's mismatches. Each rule states what, why and how to fix. Errors cannot be waived; warnings can, with a justification of at least 10 characters; notes cannot. | SPEC DRC requirements. |
| D-88 | A rule that needs a number nobody has entered (derating, grounding concept, EMC pairs, spare pins, category separation) checks nothing and the `unchecked-config` note says so. A clean report is never a pass for a check that could not run. | Placeholders rule; D-11 is still open. |
| D-89 | Shield-unterminated is only reported once a grounding concept exists; before that, "grounding not checked" is shown. Direction conflicts are only judged for interface types that have both outputs and inputs. | Avoids false alarms from placeholder data and one-directional types. |
| D-90 | Design rules run in a background thread on a cheap copy of the project, 1.2 s after the last edit. Edits never wait for them. Measured at stress size: running the check while editing roughly doubles edit time (GIL), so it starts only after a pause. | The 100 ms edit target; the check takes about 0.8 s at stress size. |
| D-91 | Waivers are applied when findings are displayed, so a waiver takes effect at once without waiting for a new check. The report lists waived findings with justifications and waivers whose finding no longer exists. | SPEC: waivers saved and shown in reports. |
| D-92 | `harness drc DIR` prints the Markdown report and exits 1 if any unwaived error exists. The full DRC report as a formatted deliverable (PDF and so on) belongs to M5. | CI-friendly now, formatted outputs later. |
| D-93 | `GenerationPlan.empty` is true only when the plan holds nothing but the generation record (fixes a gap where a pin-only change looked empty). | Found while testing the one-click regenerate fix. |
| D-94 | Outputs are written by the tool's own small SVG and PDF writers (`core/outputs/canvas.py`) from one drawing description; no PDF or drawing library is added. PDFs are uncompressed with no dates, so equal models give equal bytes and the verifier can read them. The architecture proposal mentioned reportlab; it is not needed. | Offline, deterministic, fewer dependencies. |
| D-95 | One monospaced font (Courier, 600/1000 em advance) for all drawing text so layout uses exact widths. Characters outside Windows-1252 print as "?" in PDF. | No font metrics to guess or bundle. |
| D-96 | Outputs live in `<project>/outputs/` with a manifest (model hash, sha256 per file). Only files listed in the previous manifest are ever deleted; foreign files are left alone. The folder is not part of the model hash. | Safe re-export; stale detection. |
| D-97 | Output verifier v2 re-reads the files and derives what they must contain from the project without the builders; XLSX is read straight from its XML. Export is refused if it fails. | SPEC verifier requirement. |
| D-98 | CSV carries its stamp as a first `# ` comment line; cells starting with `= + - @` (not numbers) get a leading `'`. | Stamp on every artefact; spreadsheet formula injection. |
| D-99 | Title block fields come from `config/titleblock.json`; date, author, checker and approver show "-" until M6. Test limits show "TBD (placeholder)" until `generation.test_*` is set. | Never invent values; D-15 open. |
| D-100 | Drawings are wire-by-wire diagrams with segments, shields and spare pins listed; a geometric branch drawing is not part of M5. | Scope; honest limits in `OUTPUTS.md`. |
| D-101 | The editor runs export in a worker thread with progress and Cancel, checks the result independently and only then writes. The quick stale check compares model hashes; file hashing is for the CLI. | Large projects take tens of seconds; the UI must not freeze. |
| D-102 | Change control is data in the project: `Harness.status/revision/author/checker/approver/released_on`, `baselines/<harness>/<revision>.json` (a frozen snapshot of the harness, the interfaces it carries, their units and the box connectors it mates with) and `changelog.json` (one line per review, release and new revision). Release, new revision and review go through `History`, so they are undoable until saved. | SPEC change-control section. Deviation: `changelog.json` instead of `changelog.jsonl`, so the existing canonical writer and loader are reused. |
| D-103 | A release needs a name, a comment of at least 10 characters, and passes this gate: no verifier or rule errors that belong to the harness, harness plans current, every wire has a gauge and a length, outputs exported from the current design. Unsized wires block a release on purpose: until the derating values (D-11) exist, nothing real can be released. | SPEC: release blocked by verifier errors, stale outputs and DRC errors. |
| D-104 | `content_hash` is the model hash without release bookkeeping (status, who, when, baselines, change log). The release gate compares it with the hash stored in the outputs manifest, so outputs reviewed before a release stay valid for it; after a release the outputs are stale by model hash (the title block must say "released") and `harness release` re-exports them. | Avoids a circle: a release changes status, which would make every release's own outputs stale. |
| D-105 | Locks live in `History.execute` (`vcs/locks.py`): a released harness, the interfaces it carries (type and ends), the box pins it uses and the box connectors it mates with cannot be changed or deleted. The only allowed change to a released harness is its next revision (same content, status draft, new revision letter). Harmless edits (names, notes) elsewhere stay possible. | "Released items cannot be edited without a new revision." |
| D-106 | A released harness that differs from its baseline (edited in a text editor, damaged by a merge) is an unwaivable rule error `released-modified`, also shown by `harness check`. | Post-merge consistency. |
| D-107 | The diff engine flattens snapshots to (kind, id) objects: units, interfaces, box connectors and pins, harnesses, cable connectors and pins, wires, shields, splices, branch points, segments (and parts, interface types, configuration for whole projects). It lists added, removed and changed objects with field changes; `harness compare OLD NEW` diffs two project folders (for example Git checkouts). | "Diff of two baselines lists added/removed/changed objects exactly." |
| D-108 | Revisions are letters (A, B ... Z, AA ...). A regenerated harness that was in review goes back to draft with a note, because its reviewed content changed. Generation's input hash no longer includes harness status (a release must not make the harness plans look outdated). | Review means "this content was checked". |
| D-109 | Who and when are typed or default to the operating-system user name and today's date at the moment of the step; the tool never invents them and generated files contain no clock times. | Deterministic outputs; honest change log. |
| D-110 | Supported platform: Ubuntu LTS (22.04 and 24.04) on x86-64, per the owner. Windows and RHEL/Rocky are no longer targets (supersedes D-14 and the Windows part of D-38). Packaging is a PyInstaller folder shipped as a `.tar.gz` and a `.deb`; release builds run on Ubuntu 22.04 (glibc 2.35) so they start on both LTS versions. Windows-specific safety code (reserved file names, long paths, case-insensitive IDs) stays because it is harmless and keeps projects portable. | Owner instruction at M7. |
| D-111 | The user guide is Markdown (`docs/guide/USER_GUIDE.md`) converted by a small in-repo tool to one offline HTML page bundled in the app; F1 opens it in the system browser (a local file, no network). A test keeps the HTML in sync and checks that every CLI command and every button it names exists. | SPEC: user guide, offline. |
| D-112 | `docs/RULES.md` is generated from the rule registry and `docs/CONFIG.md` documents every configuration key; tests fail if either is stale or incomplete. | Developer docs that cannot drift. |
| D-113 | Release candidates carry `rcN` in the version (`0.1.0rc1`, Debian `0.1.0~rc1`) until the owner signs off, with open decisions listed in the changelog. | Honest status. |
| D-114 | Integrity results are cached per connector and harness object (immutable) together with a token of everything they are checked against (unit, interface and part IDs, connector objects, duplicate wire IDs). | Keeps edits near the 100 ms target for large generated projects; a regression test proves it never hides a new problem. |
| D-115 | The accessibility audit has an automated part (names on every control, text size at every scale, keyboard reach, canvas announcement; part of the test suite) and a manual part that needs a person with a screen reader (still open). | An audit cannot be fully automated. |
| D-116 | Multi-drop interfaces (more than two units, for example a bus) are still not generated; they are skipped with a warning. Generating them needs an engineering rule I will not guess: daisy chain or star, who owns the stub lengths, which connector carries the through-wiring, and where the splices sit. Owner input needed. | Never invent engineering rules. |
| D-117 | The editor previews drawings by painting the same sheet description that the exporter writes (no second renderer), stamped "preview". The routing sketch is a schematic tree (columns by distance from the first connector), shown only for up to 14 nodes. | What you see is what is exported. |
| D-118 | The Outline tab (a plain Qt tree) is the item-by-item accessible view of the diagram; custom accessibility interfaces for graphics items were not attempted because they are fragile in PySide6 and cannot be tested without a screen reader here. | Honest scope. |
| D-119 | Arrange keeps each unit in its zone lane and orders units by the average position of their neighbours in other lanes (four sweeps, starting from the current order), then stacks them with the standard spacing. Deterministic; one undo step. | Tidy diagrams without moving units across zones. |
| D-120 | Owner answers at M9: D-11 (real derating, ampacity, EMC values) and D-12 (approved parts list) will be supplied later and the tool is prepared (`harness config`, `harness import-parts`, `config-invalid` rule); D-13: KiCad is the CAD tool, lengths come in as a table in millimetres (`harness import-lengths`) because KiCad does not route harnesses; D-20 (formal qualification) is not needed. Options for D-10 and D-15 are in `docs/OPEN_DECISIONS.md`. | Owner instruction. |
| D-121 | Hostile or damaged input never crashes the tool: strict parsing, quarantine, size and zip-bomb limits, symlinks ignored, damaged outputs and manifests are findings. Review in `docs/SECURITY.md`, enforced by `tests/test_security.py` and `tests/test_fuzz.py`. | Release hardening (M9). |
| D-122 | The Windows-only process check using ctypes was removed (D-110: Ubuntu only), so the code base imports no foreign-function module; a test scans for banned imports and calls. | Smaller attack surface. |
