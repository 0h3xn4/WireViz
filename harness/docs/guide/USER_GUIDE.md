# Harness tool: user guide

This guide is for systems engineers who have never used the tool. It works offline. Press **F1** in the app to open it.

## 1. What the tool does

You draw units (computer, power unit, wheels ...) and the interfaces between them. The tool turns that into harnesses: which wires, on which pins, in which connectors. It checks the result, writes the drawings and lists, and keeps a record of every release.

Your design is the source of truth. Everything else (harnesses, drawings, lists) is generated from it and can be generated again at any time.

## 2. Install and start (Ubuntu 22.04 or 24.04)

1. Install the package: `sudo apt install ./harness-tool_<version>_amd64.deb`. Or unpack the `.tar.gz` anywhere and run `./harness-tool/install.sh` (no administrator rights needed; it installs for your user).
2. Start **Harness tool** from the application menu, or run `harness-tool`.
3. The command line tool is `harness` (see section 9).

No network access is needed or used.

## 3. Your first project in ten steps

1. Start the app. The sample project opens with a short tour; skip it or follow it.
2. **File > New project**, choose an empty folder, give it a name.
3. In the palette on the left press **Add a unit** and pick *Computer*. Add a *Power unit* and an *Actuator (wheel)*.
4. Pick an interface type (for example *RS-422*), then click the first unit and the second unit. Units that cannot take this interface are greyed out, with the reason written next to them.
5. Look at **Problems** (bottom). Each card says what is wrong, why it matters and how to fix it. Many have a one-click **Fix**.
6. Open the **To-do** tab for what is left to do.
7. Press **Generate harnesses**. A preview shows what will be added; nothing changes until you press **Apply**. **Undo** takes it all back.
8. Open the **Harness plans** tab: harnesses, their wires, a preview of the drawing (**Drawing** tab; arrows page through sheets) and *Why is it like this?* for each wire (**Why** tab).
9. Save with **Ctrl+S**.
10. Press **Export outputs** to write drawings and lists into the project's `outputs` folder.

## 4. Guided and Expert mode

- **Guided** (default): you work with units and interfaces. The tool chooses connectors and pins and marks its choices as *auto-filled* until you confirm them.
- **Expert**: you also see each connector of a unit and can choose the exact connector for every end of an interface.

Switching modes never changes your data.

## 5. Problems, fixes and waivers

- **Error**: must be fixed. Errors cannot be waived.
- **Warning**: fix it, or **Waive** it with a reason of at least 10 characters. Waived warnings stay visible in the report with their reason.
- **Note**: information, for example *not checked because a value is still a placeholder*.

The design rules run in the background a moment after you stop editing; the Problems tab says when they are checking.

## 6. Generating harnesses

- By default one harness is made for each pair of unit connectors. Nominal and redundant chains, and pyro lines, never share a harness.
- Pins are chosen by rules (power first, pairs side by side, locked pins never moved). **Why is it like this?** shows the reason for each choice.
- Generating again keeps IDs, locked wires and locked pins, never touches released harnesses, and shows a report of what was added, changed and removed.
- A wire gauge stays **pending** until the derating values exist (section 10). The tool never guesses an engineering value.

## 7. Outputs

`outputs/` contains, for every harness: drawing (SVG and PDF, A3 and A4), wire list, pinouts, BOM, mass and length, continuity and isolation tests, labels, a WireViz-style YAML file and an Excel workbook. For the whole system: block diagram, harness overview, BOM, mating and traceability matrices, DRC report, change log, revision report, and one JSON file with the whole model. Every file carries the tool version and a model hash. The Harness plans tab shows whether the outputs are up to date. Details: `docs/OUTPUTS.md`.

Outputs are checked independently before they are written. If that check fails, nothing is written.

## 8. Review, release and revisions

1. Make the design pass: no errors, plans current, every wire sized and measured.
2. **Export outputs** and review them.
3. In **Harness plans** select the harness: **Submit for review** (optional), then **Release…**. Type your name and a comment (at least 10 characters). Anything that blocks the release is listed in plain words.
4. The harness is now **released (locked)**: it, the interfaces it carries and the pins it uses cannot be edited. A baseline (frozen snapshot) and a change log entry are stored.
5. To change it: **New revision…**. The old revision stays available. **Changes…** shows what differs from a baseline and can mark the changed units and interfaces on the diagram. **Change log…** shows who did what, when and why.

Export the outputs again after a release so the drawings show *released*.

## 9. Command line

All commands take the project folder. Exit code 0 means success, 1 means the project has errors or a step is blocked, 2 means usage error or unreadable project.

| Command | What it does |
| --- | --- |
| `harness validate DIR` | check a project for errors |
| `harness check DIR` | validate, plus problems left by Git merges (including released harnesses that were edited) |
| `harness migrate DIR` | upgrade an old-format project (originals are kept) |
| `harness generate DIR` | generate harnesses and save (not saved if errors) |
| `harness verify DIR [--outputs]` | independent check of the harnesses, and of `outputs/` |
| `harness drc DIR` | design rule report (Markdown); exit 1 on unwaived errors |
| `harness export DIR` | write and verify all outputs |
| `harness review DIR HARNESS --by NAME` | submit a draft for review |
| `harness release DIR HARNESS --by NAME --comment TEXT [--checker NAME]` | release (blocked while checks fail) and re-export |
| `harness revise DIR HARNESS --by NAME --comment TEXT` | start a new revision |
| `harness diff DIR HARNESS [--from REV] [--to REV]` | what changed since a baseline |
| `harness compare OLD NEW` | compare two project folders (for example two Git checkouts) |
| `harness log DIR [HARNESS]` | print the change log |
| `harness config DIR [--ampacity-csv FILE]` | list missing or invalid engineering values; load a current-by-gauge table |
| `harness import-parts DIR FILE --approved VALUE ...` | import an approved-parts list; you say what the approval values mean |
| `harness import-lengths DIR FILE [--unit mm]` | import routing segment lengths from a table |
| `harness import-netlist DIR FILE --unit U [--prefix J] [--connector J1=ID] [--part J1=PART] [--signal-map NAME=SIGNAL]` | read connector pinouts of a unit from a KiCad netlist (.net or .xml); the pins become fixed |

## 10. What an engineer must fill in

Some values must come from your program's standards. Until they are filled in, results say so and the affected checks say *not checked*. The list is in `docs/PLACEHOLDERS.md`: derating factors and ampacity table (`config/derating.json`), resistivity, service loop, pin gap, mass margin, shield grounding concept and test limits (`config/generation.json`), separation rules (`config/segregation.json`), EMC rules (`config/emc.json`), title block fields (`config/titleblock.json`), part masses and ratings in the library. 

Run `harness config DIR` to see what is missing and what depends on it, load a current-by-gauge table from a CSV with `--ampacity-csv`, edit the rest in the JSON file, and set `"placeholder": false` once reviewed. Details: `docs/IMPORTS.md`.

## 11. When something goes wrong

| You see | Meaning and what to do |
| --- | --- |
| *Read-only* banner | The project was saved by a newer version of the tool, or is open in another window. Install the newer tool, or close the other window. Nothing was changed. |
| *Project already open* | Another window or session has the project open. Close it there, or choose **Open read-only**. |
| *This project has problems* (recovery view) | Some files could not be loaded. Everything else loaded. **Save salvaged copy** writes a clean copy; the original is protected. |
| *Unsaved changes found* at start | The last session ended before saving. **Restore** brings back your last edits. |
| *Project changed on disk* | Someone (or Git) changed the files. Reload to see them. |
| *Outputs: out of date* | The design changed since the last export. Export again. |
| *Blocked because it touches released items* | The harness is released. Start a new revision. |

## 12. Keyboard

| Keys | Action |
| --- | --- |
| Ctrl+K | command palette: type a command or an ID |
| Ctrl+Z, Ctrl+Y | undo, redo |
| Ctrl+S | save |
| Ctrl+=, Ctrl+-, Ctrl+0 | zoom in, out, fit |
| Tab, Enter | move between units and links, select |
| Shift+arrows | move the selected unit |
| Delete | delete the selected item (after showing what it affects) |
| F1 | this guide |

The **Interface table** and **Outline** tabs list every interface and unit; they are the screen-reader friendly views of the diagram. **Arrange diagram** (View menu) tidies the units: they stay in their lanes and are ordered to shorten links; Undo restores the old positions.

## 13. Glossary

- **Harness**: a bundle of wires with connectors that carries signals between units.
- **Interface**: a logical connection between two units, for example RS-422 from the computer to a wheel.
- **Nominal / redundant**: the main chain and its backup. They never share a connector or harness.
- **Baseline**: a frozen snapshot made when a harness is released.
- **Waiver**: a recorded decision to accept a warning, with a reason.
- **Placeholder**: a value nobody has entered yet; the tool never invents one.
- **Model hash**: a fingerprint of the design; every output carries it.
