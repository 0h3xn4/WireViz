"""Commands that bring outside data into a project: config, import-parts, import-lengths."""

import argparse
import sys
from pathlib import Path

from harness_tool.core import configcheck
from harness_tool.core.commands import History, SetConfig
from harness_tool.core.errors import HarnessError
from harness_tool.core.generate.lengths import plan_length_import
from harness_tool.core.imports import ImportError_, read_table
from harness_tool.core.io.loader import load_project
from harness_tool.core.io.saver import save_project
from harness_tool.core.library_import import guess_mapping, plan_parts_import

COMMANDS = ("config", "import-parts", "import-lengths", "import-netlist")
UNITS = {"mm": 0.001, "m": 1.0, "cm": 0.01}


def register(sub: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    c = sub.add_parser(
        "config",
        help="list missing or invalid engineering values; optionally load an ampacity table",
        description="Hand-over checklist for the engineering values (derating, grounding, test limits ...). Exit 1 while something is missing or invalid.",
    )
    c.add_argument("project", type=Path)
    c.add_argument(
        "--ampacity-csv",
        type=Path,
        default=None,
        help="CSV with a gauge column and an amperes column; sets derating.ampacity_a_by_awg",
    )
    pp = sub.add_parser(
        "import-parts",
        help="import an approved-parts list (CSV or XLSX)",
        description="Import parts with their approval status. Say what the approval values in your list mean; unknown values are rejected, never guessed.",
    )
    pp.add_argument("project", type=Path)
    pp.add_argument("file", type=Path)
    pp.add_argument(
        "--approved",
        action="append",
        default=[],
        help="a value of the approval column that means approved (repeat)",
    )
    pp.add_argument(
        "--pending", action="append", default=[], help="a value that means not decided yet (repeat)"
    )
    pp.add_argument(
        "--rejected", action="append", default=[], help="a value that means not approved (repeat)"
    )
    pp.add_argument(
        "--category",
        default=None,
        help="category for rows that have none (connector, contact, backshell, wire, sleeving, label)",
    )
    pp.add_argument("--dry-run", action="store_true", help="show the preview only")
    nn = sub.add_parser(
        "import-netlist",
        help="read unit connector pinouts from a KiCad netlist",
        description="Create or update the box connectors of one unit from a KiCad netlist (the .net file the schematic editor exports, or kicad-cli sch export netlist; S-expression and XML both work). Pins get fixed signals; generation connects interfaces to the pin of the same name. See docs/KICAD.md.",
    )
    nn.add_argument("project", type=Path)
    nn.add_argument("netlist", type=Path)
    nn.add_argument(
        "--unit", required=True, help="the unit these connectors belong to, for example OBC1"
    )
    nn.add_argument(
        "--ref",
        action="append",
        default=[],
        help="reference of a connector in the netlist, for example J1 (repeat; default: every component starting with --prefix)",
    )
    nn.add_argument(
        "--prefix", default="J", help="reference prefix that marks connectors (default J)"
    )
    nn.add_argument(
        "--connector",
        action="append",
        default=[],
        metavar="REF=ID",
        help="connector ID for a reference, for example J1=OBC1-J01 (default: the symbol field HarnessConnector, else <unit>-<ref>)",
    )
    nn.add_argument(
        "--part",
        action="append",
        default=[],
        metavar="REF=PART",
        help="library part for a new connector (default: the symbol field HarnessPart, or the existing connector's part)",
    )
    nn.add_argument(
        "--signal-map",
        type=Path,
        default=None,
        help="CSV (net name, signal) or JSON object that translates KiCad names to interface signal names",
    )
    nn.add_argument(
        "--pin-function",
        action="store_true",
        help="use the pin names of the symbol instead of the net names as signals",
    )
    nn.add_argument("--dry-run", action="store_true")
    ll = sub.add_parser(
        "import-lengths",
        help="import routing segment lengths (CSV or XLSX: harness, segment, length)",
        description="Import segment lengths, for example exported from the mechanical CAD (KiCad users: see docs/IMPORTS.md).",
    )
    ll.add_argument("project", type=Path)
    ll.add_argument("file", type=Path)
    ll.add_argument(
        "--unit", choices=sorted(UNITS), default="mm", help="unit of the length column (default mm)"
    )
    ll.add_argument("--dry-run", action="store_true")


def run(args: argparse.Namespace) -> int:
    try:
        project = load_project(args.project).project
        if args.command == "config":
            return _config(project, args)
        if project.read_only:
            print(
                "error: this project is read-only (saved by a newer tool version).", file=sys.stderr
            )
            return 2
        if args.command == "import-netlist":
            return _netlist(project, args)
        table = read_table(args.file)
        if args.command == "import-parts":
            return _parts(project, table, args)
        return _lengths(project, table, args)
    except (HarnessError, ImportError_) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _config(project, args: argparse.Namespace) -> int:  # type: ignore[no-untyped-def]
    if args.ampacity_csv is not None:
        table, problems = configcheck.plan_ampacity_import(read_table_raw(args.ampacity_csv))
        if problems:
            for p in problems:
                print(f"error: {p}", file=sys.stderr)
            print("Nothing was changed.", file=sys.stderr)
            return 1
        cfg = configcheck.with_value(project.config["derating"], "ampacity_a_by_awg", table)
        History(project).execute("Load ampacity table", [SetConfig(cfg)])
        invalid = [
            i for i in configcheck.validate(project) if i.object_id == "derating.ampacity_a_by_awg"
        ]
        if invalid:
            print(f"error: {invalid[0].message}", file=sys.stderr)
            print("Nothing was changed.", file=sys.stderr)
            return 1
        save_project(project, args.project)
        print(
            f'Loaded {len(table)} gauges into config/derating.json. Review it, then set "placeholder": false when the file is complete.'
        )
    text, ok = configcheck.report(project)
    print(text)
    return 0 if ok else 1


def read_table_raw(path: Path) -> list[list[str]]:
    from harness_tool.core.imports import parse_csv

    return (
        parse_csv(path.read_text(encoding="utf-8-sig"))
        if path.suffix.lower() == ".csv"
        else read_table(path)
    )


def _parts(project, table: list[list[str]], args: argparse.Namespace) -> int:  # type: ignore[no-untyped-def]
    if not table:
        print("error: the file is empty.", file=sys.stderr)
        return 2
    mapping = guess_mapping(table[0])
    if "id" not in mapping and "part_number" not in mapping:
        print("error: no column looks like a part ID or part number.", file=sys.stderr)
        return 2
    plan = plan_parts_import(
        project,
        table,
        mapping,
        approved=args.approved,
        pending=args.pending,
        rejected=args.rejected,
        default_category=args.category,
    )
    for r in plan.rows:
        print(
            f"row {r.row_number}: {'OK ' + r.action + ' ' + r.part_id if r.ok else 'ERROR ' + r.message}"
        )
    bad = [r for r in plan.rows if not r.ok]
    print(f"{plan.ok_count} part(s) ready, {len(bad)} row(s) with problems.")
    if args.dry_run or bad:
        print("Nothing was changed." if bad else "Dry run: nothing was changed.")
        return 1 if bad else 0
    History(project).execute("Import parts", plan.ops)
    save_project(project, args.project)
    print(f"Imported {plan.ok_count} part(s).")
    return 0


def _lengths(project, table: list[list[str]], args: argparse.Namespace) -> int:  # type: ignore[no-untyped-def]
    plan = plan_length_import(project, table, scale=UNITS[args.unit])
    for r in plan.rows:
        print(f"row {r.row_number}: {'OK' if r.ok else 'ERROR ' + r.message}")
    bad = [r for r in plan.rows if not r.ok]
    print(f"{len(plan.rows) - len(bad)} length(s) ready, {len(bad)} row(s) with problems.")
    if args.dry_run or bad:
        print("Nothing was changed." if bad else "Dry run: nothing was changed.")
        return 1 if bad else 0
    History(project).execute("Import segment lengths", plan.ops)
    save_project(project, args.project)
    print("Lengths imported. Generate harnesses again to update the wire lengths.")
    return 0


def _pairs(items: list[str], what: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        key, sep, value = item.partition("=")
        if not sep or not key.strip() or not value.strip():
            raise ImportError_(f"{what} '{item}' must look like REF=VALUE")
        out[key.strip()] = value.strip()
    return out


def _signal_map(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    import json

    try:
        if path.suffix.lower() == ".json":
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in raw.items()
            ):
                raise ImportError_("The signal map must be a JSON object of text to text.")
            return dict(raw)
        rows = read_table_raw(path)
    except (OSError, ValueError, RecursionError) as exc:
        raise ImportError_(f"The signal map could not be read ({exc}).") from exc
    if rows and rows[0][0].strip().lower() in ("net", "name", "kicad", "from", "net name"):
        rows = rows[1:]
    return {
        r[0].strip(): r[1].strip() for r in rows if len(r) >= 2 and r[0].strip() and r[1].strip()
    }


def _netlist(project, args: argparse.Namespace) -> int:  # type: ignore[no-untyped-def]
    from harness_tool.core.kicad import plan_netlist_import, read_netlist

    plan = plan_netlist_import(
        project, read_netlist(args.netlist), args.unit, refs=args.ref or None, prefix=args.prefix,
        connector_ids=_pairs(args.connector, "--connector"), parts=_pairs(args.part, "--part"),
        signal_map=_signal_map(args.signal_map), use_pin_function=args.pin_function,
    )  # fmt: skip
    for r in plan.rows:
        print(
            f"{r.ref or '-'}: "
            + (
                f"OK {r.action} {r.connector_id} ({r.pins} signal pin(s))"
                if r.ok
                else f"ERROR {r.message}"
            )
        )
    for w in plan.warnings:
        print(f"warning: {w}")
    if plan.unmatched_signals:
        print(
            "Signals that match no interface type (map them with --signal-map, or ignore if they are not interfaces):"
        )
        for name in sorted(plan.unmatched_signals):
            print(f"  {name}: {', '.join(plan.unmatched_signals[name][:4])}")
    bad = [r for r in plan.rows if not r.ok]
    if args.dry_run or bad or not plan.ops:
        print(
            "Nothing was changed."
            if bad
            else "Dry run: nothing was changed."
            if args.dry_run
            else "Nothing to import."
        )
        return 1 if bad or not plan.ops else 0
    History(project).execute("Import connector pinouts from KiCad", plan.ops)
    save_project(project, args.project)
    print(
        f"Imported {plan.ok_count} connector(s). Generate harnesses again to connect interfaces to the fixed pins."
    )
    return 0
