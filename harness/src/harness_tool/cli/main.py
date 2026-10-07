"""`harness` command line entry point.

Exit codes: 0 ok (warnings allowed), 1 the project has errors, 2 usage error or unreadable project.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from harness_tool import __version__
from harness_tool.core.errors import HarnessError
from harness_tool.core.io.loader import LoadResult, load_project, non_canonical_files
from harness_tool.core.io.saver import migrate_project
from harness_tool.core.issues import Issue

NOT_CANONICAL = (
    "File differs from the tool's own formatting (hand-edited or merged). "
    "It will be rewritten on the next save."
)
MIGRATED = "Migrated; the original files are kept in a .migration-backup-* folder."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness", description="Spacecraft harness design tool")
    parser.add_argument("--version", action="store_true", help="print the tool version and exit")
    sub = parser.add_subparsers(dest="command")
    for name, text in (
        ("validate", "check a project folder for errors and inconsistencies"),
        ("check", "validate, plus detect problems left behind by Git merges"),
        ("migrate", "upgrade an old-format project in place (originals are kept)"),
    ):
        p = sub.add_parser(name, help=text, description=text)
        p.add_argument("project", type=Path, help="project folder")
    return parser


def _print_report(result: LoadResult, extra: list[Issue]) -> int:
    issues = sorted([*result.issues, *extra])
    for issue in issues:
        print(issue.render())
    n_err = sum(i.severity == "error" for i in issues)
    n_warn = sum(i.severity == "warning" for i in issues)
    p = result.project
    print(
        f"{len(p.units)} units, {len(p.interfaces)} interfaces, "
        f"{len(p.all_connectors())} connectors, {len(p.harnesses)} harnesses: "
        f"{n_err} error(s), {n_warn} warning(s)."
    )
    return 1 if n_err else 0


def _validate(path: Path, *, merge_check: bool) -> int:
    result = load_project(path)
    extra: list[Issue] = []
    if merge_check:
        if result.project.read_only:
            extra.append(
                Issue(
                    "info", "skipped_canonical_check", "Format check skipped (read-only project)."
                )
            )
        elif not result.project.recovered:
            extra.extend(
                Issue(
                    "warning",
                    "not_canonical",
                    NOT_CANONICAL,
                    rel,
                )
                for rel in non_canonical_files(path, result.project)
            )
    return _print_report(result, extra)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits on bad input; report it as a return code
        return 0 if exc.code in (0, None) else 2
    if args.version:
        print(f"harness {__version__}")
        return 0
    if args.command is None:
        parser.print_usage(sys.stderr)
        return 2
    try:
        if args.command == "migrate":
            migrated = migrate_project(args.project)
            print("Already up to date." if migrated is None else MIGRATED)
            return 0
        return _validate(args.project, merge_check=args.command == "check")
    except HarnessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
