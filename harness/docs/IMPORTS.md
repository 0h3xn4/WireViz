# Importing outside data

Everything is previewed row by row and applied as one undo step (CLI: nothing is written if any row has a problem).

## Interfaces (CSV or XLSX)
Editor: File > Import interfaces. Columns: id, type, from, to, redundancy (optional); headers are matched by name.

## Approved parts list (D-12)
`harness import-parts DIR FILE --approved A --approved Yes --pending Review --rejected X [--category connector] [--dry-run]`

- Columns are matched by header: part ID or part number, manufacturer, description, category, specification, approval status, pin count, mass (g), mass per metre (g/m), mating part.
- **You say what the approval values mean** with `--approved`, `--pending`, `--rejected` (repeat for several values). A value in none of the lists is an error for that row. The tool never decides that something is approved.
- New parts are added; existing parts are updated with the columns that are filled in. Imported parts are no longer marked as example data.
- Parts that are used but not approved stay design rule warnings until the list marks them approved.
- A program-specific format (for example an EPPL or DCL export) can be added as a column mapping once you can show an example file.

## Engineering values (D-11)
`harness config DIR` is the hand-over checklist: which derating, grounding, test-limit and separation values are still missing, what depends on each, and which values that are set are invalid (for example a factor above 1, or an ampacity table in which a thinner wire carries more). Invalid values are also rule errors in the editor.

`harness config DIR --ampacity-csv FILE` loads the current-by-gauge table from a two-column CSV (gauge, amperes; header optional; decimal commas accepted). It is validated before anything is written. The other values are edited in `config/*.json` (see CONFIG.md); set `"placeholder": false` in a file once it is reviewed.

Until the values exist, wire gauges stay "pending", the affected checks say "not checked", and nothing can be released.

## Segment lengths from a CAD or spreadsheet (D-13)
`harness import-lengths DIR FILE [--unit mm|cm|m] [--dry-run]` with columns harness ID, segment ID, length (default unit millimetres, decimal commas accepted). Run `harness generate DIR` afterwards so the wire lengths follow.

KiCad: it is used only for the electronics inside each unit, so the tool has no KiCad integration (D-123). Segment lengths come from wherever the mechanical or routing lengths are measured, as a plain table. If you later want unit connector pinouts taken from a KiCad schematic or netlist instead of being entered here, that needs a reader for the specific export and a sample file.
