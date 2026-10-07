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

COMMANDS = ("config", "import-parts", "import-lengths")
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
