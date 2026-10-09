# Harness Design Studio: user guide

This guide is for systems engineers who have never used the tool. It works offline. Press **F1** in the app to open it.

New here? Read sections 1 to 4 (about fifteen minutes). Section 3 gives you a ready-made practice project to play with.

## 1. What the tool does

You draw units (computer, power unit, wheels ...) and the interfaces between them. The tool turns that into harnesses: which wires, on which pins, in which connectors. It checks the result, writes the drawings and lists, and keeps a record of every release.

Your design is the source of truth. Everything else (harnesses, drawings, lists) is generated from it and can be generated again at any time.

Seven words carry most of the meaning:

| Word | What it is |
| --- | --- |
| **Unit** | A box with connectors on it: the computer `OBC1`, the power unit `PCDU1`, the wheel `RW1`. |
| **Interface** | One connection between two units, of a type such as RS-422 or primary power. This is what you add. |
| **Connector, pin** | A plug or socket, and one contact of it. A pin carries one signal. |
| **Harness** | A bundle of wires with connectors that carries interfaces between units. Generated, never drawn by hand. |
| **Wire** | One conductor between two pins, with a gauge, a part and a length. |
| **Zone** | A lane of the diagram (a panel or compartment) that units sit in. |
| **Placeholder** | A value nobody has entered yet. The tool never invents engineering numbers. |

The starter library follows one baseline:

| For | Baseline |
| --- | --- |
| Communication | RS-422, RS-485 and CAN |
| High data rates (for example a payload) | Ethernet, on an RJ45 connector, as the alternative |
| Power and data connectors | Micro-D 9, 15, 21, 25 and 31 pin (power: 9 pin; for data the size follows the number of interface types the connector carries) |
| RF | SMA |

Other interface types and older connector parts stay in the library for projects that need them. All parts are examples with fictional part numbers, none approved; your approved parts list replaces them.

## 2. Install and start (Ubuntu 24.04 or newer)

1. Install the package: `sudo apt install ./harness-design-studio_<version>_amd64.deb`. Or unpack the `.tar.gz` anywhere and run `./harness-design-studio/install.sh` (no administrator rights needed; it installs for your user).
2. Check it: `harness --version` prints the version. If the command is not found after `install.sh`, add `~/.local/bin` to your PATH (the installer prints how).
3. Start **Harness Design Studio** from the application menu, or run `harness-design-studio`.
4. The command line tool is `harness` (see section 9).

No network access is needed or used. On a minimal Ubuntu the app may need a few system libraries; the installer lists them.

## 3. Start from an example

The tool ships three practice projects. List them and create one in a new folder:

```
harness new --list
harness new wheel-link --template first-steps
```

Then **File > Open project…** and pick the folder. You cannot break anything: it is your own copy.

| Example | What it is |
| --- | --- |
| `blank` | An empty project with the starter parts and interface types. Use it for a real design. |
| `first-steps` | Three units, a power link and an RS-422 link. Nothing is generated yet: start here. |
| `minimal-satellite` | Seven units, nominal only: power, computer, radio, wheel and sun sensor. Adapt it. |
| `small-satellite` | 14 units with nominal and redundant chains. Generate it to see a realistic system. |
| `flatsat` | A complete bench: 23 flight and ground units, generated, with example numbers. |

`harness templates my-templates` copies templates for your own data: CSV files for interfaces, parts and lengths, a KiCad netlist, a CI script and a review checklist. The demo engineering values in it are for learning only.

## 4. Your first project in ten steps

1. Start the app. The sample project opens with a short tour; skip it or follow it.
2. **File > New project…**, choose an empty folder, give it a name. Or **File > New project from an example…** and pick `blank`, `first-steps` (three units, start here) or `small-satellite` (14 units); these are the same examples as `harness new` (section 3).
3. In the palette on the left press **Add a unit** and pick *Computer*. Add a *Power unit* and an *Actuator (wheel)*.
4. Pick an interface type (for example *RS-422*), then click the first unit and the second unit. Units that cannot take this interface are greyed out, with the reason written next to them.
5. Look at **Problems** (bottom). Each card says what is wrong, why it matters and how to fix it. Many have a one-click **Fix**.
6. Open the **To-do** tab for what is left to do.
7. Press **Generate harnesses**. A preview shows what will be added; nothing changes until you press **Apply**. **Undo** takes it all back.
8. Open the **Harness plans** tab: harnesses, their wires, a preview of the drawing (**Drawing** tab; arrows page through sheets) and *Why is it like this?* for each wire (**Why** tab).
9. Save with **Ctrl+S**.
10. Press **Export outputs** to write drawings and lists into the project's `outputs` folder.

On a power interface set **Max current (A)** in the Properties panel on the right; without it the wire gauge stays pending.

## 5. Guided and Expert mode

- **Guided** (default): you work with units and interfaces. The tool chooses connectors and pins and marks its choices as *auto-filled* until you confirm them.
- **Expert**: you also see each connector of a unit and can choose the exact connector for every end of an interface.

Switching modes never changes your data.

### Reading a dense diagram

A system with many units has many links. The editor makes them readable in these ways:

- **Pictures tell the kinds apart.** A link carries the picture of its kind: a bolt for power, a ground symbol, a bus with end stops for CAN, two arrows for a differential pair (RS-422, LVDS), a bus with drops for RS-485, a node with branches for SpaceWire, two boxes for Ethernet, a sine wave for an analog signal, a square wave for a discrete signal, a spark for a pyro line, a ring for RF coax. A link with twisted-pair signals is drawn as two lines, a redundant link is dashed. The key under the diagram shows the pictures the project uses.
- **Connectors are drawn as they look**: the tapered D of a D-sub, the small D of a Micro-D, a round shell, an RJ45 plug, a coax ring. Dots show the pins, and the gender is drawn twice: a male connector (pins) is solid and carries the male sign ♂ (circle with an arrow), a female connector (sockets) is an outline and carries the female sign ♀, and a connector whose gender is not set carries a dashed circle. The harness drawings and the mating matrix state the gender of every cable connector in words. In Expert mode a dashed line splits the unit into a left side and a darker right side (ports sit on the edge of their side), and every port reads from its edge inwards: the designator (J01), the picture of what the linked interface carries, the connector picture with its gender sign (a D-sub is a tapered D, a Micro-D has square shoulders and a double rim; both grow with the pin count), the pin count and the name; in Guided mode a unit shows its connectors and the kinds of link that end on it.
- **Numbers appear when they exist.** A power link shows e.g. `28 V · 5 A` beside its picture, but only what somebody entered; nothing is filled in. In a diagram of more than 30 links the numbers show for the selected, focused or hovered link; *View > Show all link labels* shows them everywhere. Hover a link to read its name, type, values and ends in words.
- **Click a unit or a link.** Only its links stay in full colour; everything else fades. Click the empty background or press Escape to see everything again. This is the quickest way to answer "what is connected to this?".
- **Show** (toolbar) fades everything except one signal class, one connector or one bundle. It can be combined with a selection.
- **Links run in lines.** Each link leaves on the edge that faces the unit at its other end, goes sideways into the gutter between lanes, runs up or down in its own track, and enters the other unit sideways. Links between the same two lanes run side by side, ordered so that they cross as little as possible.
- **Arrange diagram** (View menu) puts the units in order and keeps room for each one: a unit with many connectors is tall in Expert mode, and the units around it make way. One undo step restores the old positions.

Zoomed far out, the diagram shows lines only; zoom in to see pictures and numbers.

## 6. Problems, fixes and waivers

- **Error**: must be fixed. Errors cannot be waived.
- **Warning**: fix it, or **Waive** it with a reason of at least 10 characters. Waived warnings stay visible in the report with their reason.
- **Note**: information, for example *not checked because a value is still a placeholder*.

The quick checks run on every edit. The design rules (33 of them) run in the background a moment after you stop editing; the Problems tab says when they are checking.

## 7. Generating harnesses

- By default one harness is made for each pair of unit connectors. Nominal and redundant chains, and pyro lines, never share a harness.
- Pins are chosen by rules (power first, pairs side by side, locked pins never moved). **Why is it like this?** shows the reason for each choice.
- Generating again keeps IDs, locked wires and locked pins, never touches released harnesses, and shows a report of what was added, changed and removed.
- A wire gauge stays **pending** until the derating values exist and the lengths are known (section 10). The tool never guesses an engineering value.

## 8. Outputs

`outputs/` contains, for every harness: drawing (SVG and PDF, A3 and A4), wire list, pinouts, BOM, mass and length, continuity and isolation tests, labels, a WireViz-style YAML file and an Excel workbook. For the whole system: block diagram, harness overview, BOM, mating and traceability matrices, DRC report, change log, revision report, and one JSON file with the whole model. Every file carries the tool version and a model hash. The Harness plans tab shows whether the outputs are up to date. Details: `docs/OUTPUTS.md`.

Outputs are checked independently before they are written. If that check fails, nothing is written. The `outputs` folder is always safe to delete and make again.

## 9. Review, release and revisions

1. Make the design pass: no errors, plans current, every wire sized and measured.
2. **Export outputs** and review them.
3. In **Harness plans** select the harness: **Submit for review** (optional), then **Release…**. Type your name and a comment (at least 10 characters). Anything that blocks the release is listed in plain words. While a configuration file is still marked as a placeholder, the window also asks for a written reason (at least 10 characters); it is kept in the change log and the baseline. Once an engineer has reviewed the values and cleared the mark, no reason is asked. The same holds for the parts: while the harness uses parts that are not approved (or are example data), the window asks for a second written reason.
4. The harness is now **released (locked)**: it, the interfaces it carries and the pins it uses cannot be edited. A baseline (frozen snapshot) and a change log entry are stored.
5. To change it: **New revision…**. The old revision stays available. **Changes…** shows what differs from a baseline and can mark the changed units and interfaces on the diagram. **Change log…** shows who did what, when and why.

Export the outputs again after a release so the drawings show *released*. The release check looks at the harness (gauges, lengths, open errors) and at whether the configuration files are still marked as placeholders. It cannot judge whether the values are right; that stays a decision for a person.

## 10. Command line

All commands take the project folder. Exit code 0 means success, 1 means the project has errors or a step is blocked, 2 means usage error or unreadable project. Commands that import data take `--dry-run`: they show what they would do and change nothing.

| Command | What it does |
| --- | --- |
| `harness new FOLDER [--template NAME] [--name TEXT]` | create a project from an example (`harness new --list` shows them) |
| `harness templates FOLDER` | copy the import templates, CI scripts and the review checklist to a new folder |
| `harness library DIR [--library-version V] [--library-source TEXT] [--library-date YYYY-MM-DD]` | show or record where the parts library comes from |
| `harness schema FOLDER` | write JSON Schemas of the project files for editors that complete and check JSON |
| `harness validate DIR` | check a project for errors |
| `harness check DIR` | validate, plus problems left by Git merges (including released harnesses that were edited) |
| `harness migrate DIR` | upgrade an old-format project (originals are kept) |
| `harness generate DIR` | generate harnesses and save (not saved if errors) |
| `harness verify DIR [--outputs]` | independent check of the harnesses, and of `outputs/` |
| `harness drc DIR` | design rule report (Markdown); exit 1 on unwaived errors |
| `harness export DIR` | write and verify all outputs |
| `harness review DIR HARNESS --by NAME` | submit a draft for review |
| `harness release DIR HARNESS --by NAME --comment TEXT [--checker NAME] [--accept-placeholders REASON] [--accept-unapproved-parts REASON]` | release (blocked while checks fail, or while values are placeholders or parts are not approved and no reason is given) and re-export |
| `harness revise DIR HARNESS --by NAME --comment TEXT` | start a new revision |
| `harness diff DIR HARNESS [--from REV] [--to REV]` | what changed since a baseline |
| `harness compare OLD NEW` | compare two project folders (for example two Git checkouts) |
| `harness log DIR [HARNESS]` | print the change log |
| `harness config DIR [--ampacity-csv FILE] [--apply-profile NAME]` | list missing or invalid engineering values; load a current-by-gauge table; fill unset values from a standard profile |
| `harness import-parts DIR FILE --approved VALUE ...` | import an approved-parts list; you say what the approval values mean |
| `harness import-lengths DIR FILE [--unit mm]` | import routing segment lengths from a table |
| `harness import-netlist DIR FILE --unit U [--prefix J] [--connector J1=ID] [--part J1=PART] [--signal-map NAME=SIGNAL\|FILE]` | read connector pinouts of a unit from a KiCad netlist (.net or .xml); the pins become fixed |

A script that builds everything: `harness check DIR`, `harness generate DIR`, `harness verify DIR`, `harness drc DIR`, `harness export DIR`. The templates folder contains it as `ci/build.sh`.

## 11. What an engineer must fill in

Some values must come from your program's standards. Until they are filled in, results say so and the affected checks say *not checked*. The list is in `docs/PLACEHOLDERS.md`: derating factors and ampacity table (`config/derating.json`), resistivity, service loop, pin gap, mass margin, shield grounding concept and test limits (`config/generation.json`), separation rules (`config/segregation.json`), EMC rules (`config/emc.json`), title block fields (`config/titleblock.json`), part masses and ratings in the library.

Run `harness config DIR` to see what is missing and what depends on it, load a current-by-gauge table from a CSV with `--ampacity-csv`, edit the rest in the JSON file, and set `"placeholder": false` once reviewed. If you work to ECSS-Q-ST-30-11C or ECSS-E-ST-20-07C you can start from the values of those standards with `--apply-profile ecss-q-st-30-11c` or `ecss-e-st-20-07c`: only unset values are filled, each is printed with the requirement it comes from, and the files stay placeholders until you review them (`CONFIG.md` lists the keys and the part ratings the new rules need).

To see the machinery work before you have real values, copy the demo values from the templates (`config-demo-values/`) over a practice project. They are not engineering data, and the files stay marked as placeholders so every result built on them says so. Never release a real design with them.

## 12. Bring in your own data

Every import first shows what it would do, and a bad row stops the whole import so nothing is half applied.

| You have | Do |
| --- | --- |
| Interfaces as a table | **File > Import interfaces…** (CSV or XLSX with the columns id, type, from, to and optionally redundancy) |
| An approved-parts list | `harness import-parts`, saying what your approval values mean |
| Segment lengths | `harness import-lengths`, then generate again |
| A unit's connector pinout in KiCad | export a netlist, then `harness import-netlist`; the pins become fixed |
| A current-by-gauge table | `harness config DIR --ampacity-csv FILE` |

Example files for every one of these are in the templates folder (`harness templates FOLDER`).

## 13. When something goes wrong

| You see | Meaning and what to do |
| --- | --- |
| *Read-only* banner | The project was saved by a newer version of the tool, or is open in another window. Install the newer tool, or close the other window. Nothing was changed. |
| *Project already open* | Another window or session has the project open. Close it there, or choose **Open read-only**. |
| *This project has problems* (recovery view) | Some files could not be loaded. Everything else loaded. **Save salvaged copy** writes a clean copy; the original is protected. |
| *Unsaved changes found* at start | The last session ended before saving. **Restore** brings back your last edits. |
| *Project changed on disk* | Someone (or Git) changed the files. Reload to see them. |
| *Outputs: out of date* | The design changed since the last export. Export again. |
| *Blocked because it touches released items* | The harness is released. Start a new revision. |
| A wire gauge says *pending* | A value is missing: `harness config DIR` says which. A gauge also needs the interface's Max current and the segment lengths. |
| `harness` is not found | `~/.local/bin` is not on your PATH. Add it, or log out and in. |

## 14. Keyboard

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

The **Show** lists in the toolbar fade everything except one signal class (power, data, analog, RF ...), one connector or one bundle (harness), so a large diagram can be read one piece at a time; choose *All interfaces* to see everything again. It changes nothing in the project. The **Interface table** and **Outline** tabs list every interface and unit; they are the screen-reader friendly views of the diagram. **Arrange diagram** (View menu) tidies the units: they stay in their lanes and are ordered to shorten links; Undo restores the old positions.

## 15. Glossary

- **Harness**: a bundle of wires with connectors that carries signals between units.
- **Interface**: a logical connection between two units, for example RS-422 from the computer to a wheel.
- **Nominal / redundant**: the main chain and its backup. They never share a connector or harness.
- **Auto-filled**: a connector the tool chose; unconfirmed until a person looks at it.
- **Baseline**: a frozen snapshot made when a harness is released.
- **Waiver**: a recorded decision to accept a warning, with a reason.
- **Placeholder**: a value nobody has entered yet; the tool never invents one.
- **Model hash**: a fingerprint of the design; every output carries it.
- **Fixed pin**: a pin whose signal the unit itself defines (imported from KiCad); generation never moves it.
