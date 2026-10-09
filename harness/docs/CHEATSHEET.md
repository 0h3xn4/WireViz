# Cheat sheet

One page. Every command is explained in [`CLI.md`](CLI.md); `harness COMMAND --help` prints the same in a terminal.

## The loop

```
harness new my-design --template blank    # start a project (harness new --list shows the examples)
harness generate my-design                # make harnesses, connectors, pins, wires
harness check my-design                   # fast logical check
harness drc my-design                     # the full design rule check, as a report
harness export my-design                  # drawings, wire lists, pinouts, BOM, test tables
harness verify my-design --outputs        # an independent check of the exported files
```

Run the loop again after every change. Generating twice without a change changes nothing (the second run prints "0 added").

## Bring in data

| You have | Command |
| --- | --- |
| interfaces in a table | app: **File > Import interfaces** |
| a parts list | `harness import-parts DIR parts.csv --approved Approved` |
| segment lengths | `harness import-lengths DIR lengths.csv --unit mm` |
| unit connectors in KiCad | `harness import-netlist DIR file.net --unit RW1 --prefix J --connector J1=RW1-J01 --dry-run` |
| engineering values | edit `config/*.json`, see [`CONFIG.md`](CONFIG.md); `harness config DIR` lists what is missing |

Add `--dry-run` to any import to see what it would do first.

## Release and change

```
harness review  DIR W001 --by "Name"                      # submit for review
harness release DIR W001 --by "Name" --comment "why"      # baseline, change log entry, lock
harness revise  DIR W001 --by "Name" --comment "why"      # open a new revision of a released harness
harness diff    DIR W001                                  # what changed against the baseline
harness log     DIR                                       # the change log
```

A release is blocked while checks fail, while a configuration file is a placeholder, or while the harness uses parts that are not approved. You can release anyway with `--accept-placeholders REASON` and `--accept-unapproved-parts REASON`; the reason is kept in the change log.

## Exit codes

`0` success (warnings allowed), `1` the project has errors or a step is blocked, `2` usage error or an unreadable project.

## In the app

| Keys | Action |
| --- | --- |
| Ctrl+K | command palette: type a command or an ID |
| Ctrl+Z, Ctrl+Y | undo, redo |
| Ctrl+S | save |
| Ctrl+=, Ctrl+-, Ctrl+0 | zoom in, out, fit |
| Tab, Enter | move between units and links, select |
| Shift+arrows | move the selected unit |
| Delete | delete the selected item (after showing what it affects) |
| F1 | the user guide |

## What is where

```
my-design/
  project.json        name and description
  config/             engineering values (rules you or your programme supply)
  library/            parts and interface types
  logical/            units and interfaces (what you draw)
  physical/           connectors and harnesses (what the tool generates)
  generated/          how the last generation was made (for explanations)
  outputs/            drawings and lists (safe to delete and regenerate)
  changelog.json      release history, with baselines
```

Put the folder in Git. Everything except `outputs/` is meant to be reviewed as text.

## Words you will meet

| Word | Meaning |
| --- | --- |
| unit | a box: computer, power unit, wheel, sensor |
| interface | a connection need between two units: power, RS-422, CAN, ... |
| harness | a bundle of wires with connectors that carries interfaces |
| *pending* | a value is missing; nothing was invented |
| *not checked* | a rule could not run because its numbers are not supplied |
| placeholder | a configuration file nobody has reviewed yet |
| baseline | the frozen copy stored at release |

More: [`CONCEPTS.md`](CONCEPTS.md) and the glossary in the user guide.
