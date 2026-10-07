# How to: the whole app, task by task

Short recipes. Each says what you do, what you should see, and what to do if you do not. Background is in the user guide (`docs/guide/USER_GUIDE.md`, F1 in the app). Commands take the project folder as `DIR`.

## Contents

1. [Install](#1-install)
2. [Start a project](#2-start-a-project)
3. [Add units and interfaces](#3-add-units-and-interfaces)
4. [Import interfaces from a spreadsheet](#4-import-interfaces-from-a-spreadsheet)
5. [Take connector pinouts from KiCad](#5-take-connector-pinouts-from-kicad)
6. [Read and fix problems](#6-read-and-fix-problems)
7. [Generate harnesses](#7-generate-harnesses)
8. [Understand why a wire is the way it is](#8-understand-why-a-wire-is-the-way-it-is)
9. [Fill in the engineering values](#9-fill-in-the-engineering-values)
10. [Import the approved parts list](#10-import-the-approved-parts-list)
11. [Import segment lengths](#11-import-segment-lengths)
12. [Export outputs](#12-export-outputs)
13. [Review and release a harness](#13-review-and-release-a-harness)
14. [Change a released harness](#14-change-a-released-harness)
15. [Use Git with a project](#15-use-git-with-a-project)
16. [Run in a script or CI](#16-run-in-a-script-or-ci)
17. [When something goes wrong](#17-when-something-goes-wrong)

## 1. Install

- `sudo apt install ./harness-tool_<version>_amd64.deb`, or unpack the `.tar.gz` and run `./harness-tool/install.sh`.
- Check: `harness --version` prints the version.
- No network is used, so this works on an air-gapped machine once you have the package.

## 2. Start a project

- GUI: **File > New project**, pick an **empty** folder, name it.
- The folder is the project. Everything in it is plain JSON; **Ctrl+S** saves.
- Check it any time: `harness validate DIR` (exit code 0 means no errors).

## 3. Add units and interfaces

1. In the palette press **Add a unit** and pick a kind (computer, power unit, actuator, ...). Give it a short ID and a name.
2. Pick an interface type (for example RS-422, CAN, primary power), then click the first unit and the second. Units that cannot take that interface are greyed out, with the reason next to them.
3. **Guided mode** (default): the tool chooses connectors and marks them *auto-filled* until you confirm them. **Expert mode** also shows each connector so you can choose it yourself. Switching modes never changes data.
4. Set the current (A) on power interfaces, otherwise the wire gauge stays *pending*.
5. **Ctrl+K** opens a command palette: type a command or an ID. **Arrange diagram** (View) tidies the layout; Undo restores it.

A link between more than two units (a bus) is not generated yet (D-116); it is skipped with a warning.

## 4. Import interfaces from a spreadsheet

- GUI: **File > Import interfaces** (CSV or XLSX).
- Columns: `id`, `type`, `from`, `to`, and optionally `redundancy`. Headers are matched by name.
- You get a row-by-row preview. Nothing changes until you accept, and it is one undo step.

## 5. Take connector pinouts from KiCad

KiCad is used for the electronics inside each unit, so it knows which signal is on which pin of the unit's connectors. The tool reads that so you do not retype it. Full details: `docs/KICAD.md`.

1. In KiCad's schematic editor export a netlist (File > Export > Netlist), or run `kicad-cli sch export netlist --format kicadxml -o unit.net.xml unit.kicad_sch` (the input file goes last). Either the default S-expression `.net` or the XML file works.
2. Try it without changing anything:

   ```
   harness import-netlist DIR unit.net --unit OBC --ref J7 --ref J10 \
       --part J7=<part-id> --part J10=<part-id> \
       --signal-map CAN_H=CANH --signal-map CAN_L=CANL --dry-run
   ```

   - `--unit` is the unit the connectors belong to. `--ref` picks KiCad connector references (or use `--prefix J` for all starting with J).
   - `--part` is the library part of each new connector (or put a `HarnessPart` field on the KiCad symbol; `HarnessConnector` sets the connector ID).
   - `--signal-map NET=SIGNAL` renames a KiCad net to the interface signal name (a file of pairs also works). Names that match nothing are listed, never guessed.
3. Read the rows and warnings. Run again without `--dry-run` to apply. It is one undo step.

Imported pins are **fixed**: generation connects an interface signal to the pin of the same name and never moves it. If a needed signal has no free pin, generation reports an error for that interface instead of choosing another pin.

Not done yet: reading `.kicad_sch` directly, and hierarchical sheets on a real project.

## 6. Read and fix problems

- **Problems** tab (bottom). Each card says what is wrong, why it matters, how to fix it; many have a one-click **Fix**. **To-do** lists what is left.
- **Error**: must be fixed, cannot be waived. **Warning**: fix it or **Waive** it with a reason of at least 10 characters (waived warnings stay in the report). **Note**: information, for example *not checked because a value is a placeholder*.
- The design rules run in the background shortly after you stop editing.
- Command line: `harness drc DIR` prints the report and exits 1 on unwaived errors. Rule list: `docs/RULES.md`.

## 7. Generate harnesses

1. Press **Generate harnesses**. A **preview** shows what would be added, changed and removed. Nothing changes until you press **Apply**; **Undo** reverts it.
2. Generating again keeps IDs, locked wires and pins, never touches released harnesses, and reports what changed.
3. To keep a choice, **lock** the wire or pin.
4. Command line: `harness generate DIR` (not saved if there are errors), then `harness verify DIR`, an independent check of the result.

Today one harness is made per pair of unit connectors (placeholder until D-10 is decided). Nominal and redundant chains never share a harness.

## 8. Understand why a wire is the way it is

In **Harness plans** select a harness, then the **Why** tab: every wire, pin, gauge and length has the rule that decided it. The **Drawing** tab previews the exact sheet that export writes; arrows page through sheets.

## 9. Fill in the engineering values

The tool never invents derating factors, ampacity, EMC rules or masses. Until they exist, wire gauges are *pending*, affected checks say *not checked*, and nothing can be released.

1. `harness config DIR` lists what is missing, what depends on it, and which set values are invalid.
2. Load the current-by-gauge table: `harness config DIR --ampacity-csv table.csv` (two columns: gauge, amperes; validated before anything is written).
3. Edit the rest in `DIR/config/*.json` (`docs/CONFIG.md`). When reviewed, set `"placeholder": false` in that file.
4. `harness generate DIR` again so gauges are chosen.

## 10. Import the approved parts list

```
harness import-parts DIR parts.xlsx --approved Yes --approved Approved --pending Review --rejected No --dry-run
```

You say what the approval values in your list mean; a value in none of the lists is an error for that row, and the tool never decides on its own that something is approved. Columns are matched by header (part number, manufacturer, category, pin count, mass, approval status, ...). Details: `docs/IMPORTS.md`.

## 11. Import segment lengths

Lengths measured outside the tool (CAD or a spreadsheet; KiCad has none):

```
harness import-lengths DIR lengths.csv --unit mm --dry-run
harness import-lengths DIR lengths.csv --unit mm
harness generate DIR
```

Columns: harness ID, segment ID, length (decimal commas accepted).

## 12. Export outputs

- GUI: **Export outputs**. Command line: `harness export DIR` writes `DIR/outputs/` and verifies it. Nothing is written if the independent check fails.
- Per harness: drawing (SVG and PDF, A3 and A4), wire list, pinouts, BOM, mass and length, continuity and isolation tests, labels, WireViz-style YAML, Excel workbook. Per system: block diagram, harness overview, BOM, mating and traceability matrices, DRC report, change log, revision report, one JSON of the whole model.
- Every file carries the tool version and a model hash. The Harness plans tab shows whether outputs are up to date; `harness verify DIR --outputs` checks them.
- `outputs/` is safe to delete and regenerate. Details: `docs/OUTPUTS.md`.

## 13. Review and release a harness

1. Design passes: no errors, plans current, every wire sized and measured.
2. Export and read the outputs.
3. Optional: **Submit for review** (`harness review DIR W001 --by NAME`).
4. **Release…** (`harness release DIR W001 --by NAME --comment "text, at least 10 characters" [--checker NAME]`). Anything that blocks the release is listed in words.
5. The harness is now **released (locked)**: it, its interfaces and the pins it uses cannot be edited. A baseline and a change log entry are stored. Export again so drawings show *released*.

## 14. Change a released harness

- **New revision…** (`harness revise DIR W001 --by NAME --comment "..."`). The old revision stays.
- **Changes…** (`harness diff DIR W001 [--from REV] [--to REV]`) shows what differs from a baseline and can mark changed units on the diagram. `harness log DIR [W001]` prints the change log.
- Editing a locked item is refused with the reason.

## 15. Use Git with a project

- Commit the project folder. Files are canonical, so diffs show only real changes. `.gitignore` is written for you.
- After a merge: `harness check DIR` finds leftover conflict markers and released harnesses that were edited.
- Compare two checkouts: `harness compare OLD NEW`.

## 16. Run in a script or CI

Exit codes: 0 success, 1 the project has errors or a step is blocked, 2 usage error or unreadable project.

```
harness validate DIR && harness generate DIR && harness drc DIR && harness export DIR
```

`harness migrate DIR` upgrades a project saved by an older version (originals are kept).

## 17. When something goes wrong

| You see | Do |
| --- | --- |
| *Read-only* banner | The project is from a newer tool version, or open elsewhere. Install the newer tool, or close the other window. Nothing was changed. |
| *Project already open* | Close it in the other window, or **Open read-only**. |
| *This project has problems* (recovery view) | Some files could not be loaded; the rest did. **Save salvaged copy** writes a clean copy; the original is protected. |
| *Unsaved changes found* at start | **Restore** brings back your last edits. |
| *Outputs: out of date* | Export again. |
| *Blocked because it touches released items* | Start a new revision. |
| `kicad-cli` fails to load a library | A KiCad install problem. Export the netlist from the schematic editor instead. |
| `import-netlist` says a file is not a netlist | It must be KiCad's `.net` (S-expression) or XML export, not a `.kicad_sch`. |

Keyboard: Ctrl+K command palette, Ctrl+Z/Y undo/redo, Ctrl+S save, Ctrl+=/-/0 zoom, F1 guide. Full list in the user guide.
