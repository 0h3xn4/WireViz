# KiCad import (unit connector pinouts)

KiCad is used only for the electronics inside each unit. The pinout of a unit's external connectors (which signal sits on which pin) is defined there, so the tool reads it instead of asking you to retype it.

**Status: checked against one real file.** The S-expression netlist of a KiCad 10.0.6 project (59 components, 248 pins on nets) was read correctly: connector pins, net names and pin numbers match the schematic. Tests use small hand-made fixtures in the same style (`tests/fixtures/kicad/unit.net`, `unit.net.xml`). One real file is not proof for every project: check the printed rows on each unit.

## Input

A KiCad netlist, in either format: the S-expression `.net` that KiCad's schematic editor writes by default (File, Export, Netlist), or the XML one (`kicad-cli sch export netlist --format kicadxml`). The tool tells them apart by the first character. Reading `.kicad_sch` directly is not implemented: it would mean resolving wires, labels and sheets ourselves, where the netlist is KiCad's own computed connectivity.

## Command

    harness import-netlist DIR FILE --unit OBC [--ref J7 ...] [--prefix J]
                           [--connector J1=OBC-J01] [--part J1=PART-ID]
                           [--signal-map NET=SIGNAL | FILE] [--pin-function] [--dry-run]

- Which components are connectors: those whose reference starts with `--prefix` (default `J`), or the `--connector` list. A symbol field `HarnessConnector` sets the connector ID, `HarnessPart` the part.
- Net names are cleaned (`/io/TX+` becomes `TX+`); unnamed nets (`Net-(J1-Pad9)`) and `unconnected-...` give a pin with no signal.
- `--signal-map` (repeatable) renames net names to signal names of the interface types, either as `NET=SIGNAL` pairs (`--signal-map CAN_H=CANH --signal-map CAN_L=CANL`) or as a CSV or JSON file of pairs. The name is the cleaned net name (`/CAN_H` is `CAN_H`). Names that match no known signal are listed, never guessed.
- `--ref J7` (repeatable) names the connectors to import instead of using `--prefix`. `--pin-function` takes the pin's name in the KiCad symbol (for example `CAN_H`) as the signal instead of the net name.
- A net named `A/B` that is a global label keeps its whole name; for a net of a sheet (`/sheet/NET`) only `NET` is used, so two sheets with a net of the same name give the same signal name.
- A connector whose KiCad pin count is larger than the library part's is refused: choose the right part with `--part`. A `--connector` or `--part` key that is not one of the imported connectors is reported as ignored.
- `--dry-run` shows the rows and changes nothing.
- The result is one undoable transaction. Imported pins are marked `fixed`.

## What "fixed" does

Generation connects each interface signal to the fixed pin with the same name and never moves it. A connector with fixed pins is allocated by name only (no automatic placement). If a needed signal has no free fixed pin, generation reports an error for that interface and routes nothing for it.

## Open questions (owner)

1. How KiCad connector references map to the unit connectors in this tool (today: by prefix, `--connector`, or the symbol field).
2. The signal-name mapping (today: optional `--signal-map`).
3. Hierarchical sheets and multi-unit symbols have not been tried on a real project.
