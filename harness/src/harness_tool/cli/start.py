"""Commands for getting started: create a project from an example, copy the import templates."""

import argparse
import sys
from pathlib import Path

from harness_tool.core import templates

COMMANDS = ("new", "templates")


def register(sub: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    n = sub.add_parser(
        "new",
        help="create a new project from an example (blank, first-steps, small-satellite)",
        description="Create a project folder from one of the bundled examples. "
        "`harness new --list` shows them. The folder must not exist yet or be empty.",
    )
    n.add_argument("folder", type=Path, nargs="?", help="the new project folder")
    n.add_argument("--template", default="blank", help="which example to start from")
    n.add_argument("--name", default=None, help="project name (default: the example's name)")
    n.add_argument("--list", action="store_true", help="list the examples and exit")
    t = sub.add_parser(
        "templates",
        help="copy the import templates (CSV files, netlist, scripts, checklist) to a folder",
        description="Copy the bundled templates for the imports, CI scripts and the review "
        "checklist. The folder must not exist yet or be empty.",
    )
    t.add_argument("folder", type=Path, help="where to put the templates")


def run(args: argparse.Namespace) -> int:
    if args.command == "templates":
        files = templates.copy_import_templates(args.folder)
        print(
            f"{len(files)} files written to {args.folder}. Start with {args.folder / 'README.md'}."
        )
        return 0
    if args.list:
        for t in templates.TEMPLATES:
            print(f"{t.name:16} {t.summary}")
        return 0
    if args.folder is None:
        print("error: give the folder for the new project (or use --list).", file=sys.stderr)
        return 2
    project = templates.create_project(args.folder, args.template, args.name)
    print(
        f"Project '{project.meta.name}' created in {args.folder} "
        f"({len(project.units)} units, {len(project.interfaces)} interfaces).\n"
        f"Next: harness validate {args.folder}   or open it in the app (File > Open project)."
    )
    return 0
