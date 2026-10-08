# Outputs (M5)

`harness export DIR` (or **Export outputs** in the Harness plans tab) writes everything below into `DIR/outputs/`. The files are produced from the model only: the same model gives the same bytes. Nothing in them is typed in by hand; edit the model and export again.

```
outputs/
  manifest.json                    format, generator version, model hash, placeholder config, sha256 and size of every file
  harnesses/<ID>/
    drawing_A3_s<n>.svg            harness drawing, one SVG per A3 sheet
    drawing_A3.pdf, drawing_A4.pdf vector PDF, multi-sheet, same content
    wirelist.csv  pinouts.csv  bom.csv  mass_length.csv  tests.csv  labels.csv
    wireviz.yaml                   WireViz-style input (best effort, see below)
    <ID>.xlsx                      all tables of the harness as sheets
  system/
    block_diagram.svg|pdf          units in zone lanes, interfaces coloured by category
    harness_overview.svg|pdf       harnesses between units, solid = nominal, dashed = redundant
    bom.csv  mass_length.csv  mating_matrix.csv  traceability.csv  box_pinouts.csv
    changelog.csv  revision_report.md   change log and per-harness history with differences between revisions
    drc_findings.csv  drc_report.md
    export.json                    the whole model in one documented JSON file
    system.xlsx                    BOM, mass and length, matrices, box pinouts, DRC findings
```

## Stamps
Every file carries `harness-tool <version> model <first 12 hex of the model hash>`: CSV and YAML as a first comment line (`# ...`), SVG in `<desc>`, PDF in the Subject, Markdown as the first line, XLSX on the About sheet, JSON as `model_hash`. CSV readers must skip lines that start with `# `. Cells that start with `= + - @` and are not numbers are written with a leading `'` so spreadsheet programs do not run them as formulas.

## Stale detection
`manifest.json` stores the model hash. The editor compares it with the current model (quick check) and shows "up to date", "out of date" or "not exported". `harness verify DIR --outputs` also hashes every file (detects edited or missing files) and re-checks content against the design.

## Verifier v2 (`core/outputs/verify.py`)
Re-reads the finished files and compares them with the model without using the builders: wire list against wires (missing, duplicated, extra, different ends, gauge or length), pinouts, BOM quantities and wire lengths, one continuity test per wire and one isolation test per wire and shield, label counts, WireViz connection counts, XLSX contents, drawing text and sheet numbers (SVG and PDF), system tables, JSON counts, diagram contents, DRC findings, stamps and manifest. `harness export` and the editor refuse to write outputs that fail it.

## Drawing
One row per wire grouped by connector pair: pin and signal, wire ID, gauge, colour, length, part, pin and signal. Shields, routing segments, spare pins and notes follow. A title block closes every sheet (project, harness, title, revision, status, sheet n / N, stamp). Drawings are black and grey only; wire colour is printed as text. Long harnesses continue on further sheets with repeated headings. The text font is Courier (monospaced), so text widths are exact.
The first sheet starts with a routing sketch (connectors and branch points as boxes, segments with lengths; schematic, not to scale; omitted above 14 nodes). Limits: the drawing is a wire-by-wire diagram plus this sketch, not a geometric layout of the branches. Author, checker, approver and date come from the harness (set by review and release, see change control); they show "-" until then. The title block field list comes from `config/titleblock.json` (placeholder, D-15).

## Tables
- `wirelist.csv`: Wire, Signal, Interface, From connector/pin, To connector/pin, AWG ("pending" when undecided), Part, Colour, Length (m), Shield group, Locked.
- `pinouts.csv` / `box_pinouts.csv`: every pin of every cable / box connector, wires attached, spare flag.
- `bom.csv`: connector parts by count, wire parts by metres known (plus the number of wires without length), approval status.
- `mass_length.csv`: known wire length, mass of known parts, margin, whether the data is complete, what is missing. Totals count only what is known and say so.
- `tests.csv`: continuity per wire, isolation per wire (against all others and shields) and per shield. Limits come from `generation.test_*` and read "TBD (placeholder)" until set.
- `labels.csv`: one label per connector, two per wire (one per end).
- `mating_matrix.csv`, `traceability.csv`: box connector to cable connector; interface to harness and wires.

## WireViz YAML
Each wire is written as its own one-conductor cable, with `connectors`, `cables` and `connections` in the structure WireViz reads. It is written from the model by this tool and has not been validated against the WireViz program (outside this clean-room project). Treat it as a convenience export.

## JSON export (`system/export.json`)
```
{ "format": "harness-tool-export", "format_version": 1,
  "generator": {"name", "version"}, "model_hash": "<64 hex>",
  "project": {"name", "description"}, "placeholder_config": [names],
  "units": [...], "interface_types": [...], "interfaces": [...],
  "box_connectors": [...], "harnesses": [...], "parts": [...] }
```
Each list holds the model objects exactly as in the project files (sorted by ID); fields are described in `FILE_FORMAT.md`. `format_version` changes only for incompatible changes.

## Print
Dark colours and dash patterns carry every distinction (category, nominal/redundant), so greyscale prints stay readable. Tests check contrast against white (at least 3:1) and that drawings use only grey.

## Change control in the outputs
`system/changelog.csv` lists every change log entry. `system/revision_report.md` gives, per harness, the history and the differences between consecutive baselines and between the working design and the latest baseline. The manifest also stores `content_hash` (model hash without release bookkeeping) which the release gate compares; see DECISIONS D-104.

## EMC class on wires and labels

When at least one interface type has an EMC class, the wire list gets a last column `EMC class` and the wire labels end with `[EMC <class>]`, so personnel can see the category of every wire (ECSS-E-ST-20-07C 4.2.13.1 d). Projects without EMC classes get byte-identical files. The output verifier checks the column against the design.

## Provenance

`system/provenance.json` states which tool version and which design made the outputs: the model hash, the project name, the parts library (name, version, number of parts by approval status), every configuration file with its placeholder flag and a short hash of its values, and the counts of units, interfaces, harnesses and wires. There are no dates and no paths, so equal designs give equal bytes. The output verifier checks the placeholder flags and counts against the design. The WireViz-style YAML files are an export format only; WireViz is not used to make any output.

## Requirement IDs on findings

`system/drc_findings.csv` ends with a column `Requirement`: the IDs of the standard requirements the rule serves (empty when the rule serves none). The Problems panel shows the same IDs under the explanation of a finding, and the design rule report prints them after it. The IDs are those of `compliance/requirements` in the tool's repository (`docs/RULES.md` lists them per rule).
