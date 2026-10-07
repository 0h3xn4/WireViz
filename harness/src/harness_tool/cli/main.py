"""`harness` command line entry point.

Exit codes: 0 ok (warnings allowed), 1 the project has errors, 2 usage error or unreadable project.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from harness_tool import __version__
from harness_tool.cli import changes, data
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
        ("generate", "generate harnesses from the interfaces and save the project"),
        ("drc", "run the design rule check and print the report (waived findings included)"),
        (
            "export",
            "write all outputs (drawings, tables, exports) to <project>/outputs and verify them",
        ),
        ("verify", "independently verify the generated harnesses against the interfaces"),
    ):
        p = sub.add_parser(name, help=text, description=text)
        p.add_argument("project", type=Path, help="project folder")
        if name == "verify":
            p.add_argument(
                "--outputs",
                action="store_true",
                help="also check <project>/outputs against the design",
            )
    changes.register(sub)
    data.register(sub)
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
    if merge_check and not result.project.recovered:
        from harness_tool.core.vcs.consistency import release_integrity

        extra.extend(release_integrity(result.project))
    return _print_report(result, extra)


def _generate(path: Path) -> int:
    from harness_tool.core.generate.engine import generate_project
    from harness_tool.core.io.saver import save_project
    from harness_tool.core.verify import verify_project

    project = load_project(path).project
    if project.read_only:
        print("error: this project is read-only (saved by a newer tool version).", file=sys.stderr)
        return 2
    plan = generate_project(project)
    for f in plan.report.findings:
        print(f"{f.severity}: [{f.code}] {f.message}")
    print(plan.report.summary())
    report = verify_project(project)
    print(report.summary())
    if plan.report.errors or not report.ok:
        print("Not saved: fix the errors above first.", file=sys.stderr)
        return 1
    save_project(project, path)
    return 0


def _export(path: Path) -> int:
    from harness_tool.core.outputs.build import DEFAULT_FOLDER, build_outputs, write_outputs
    from harness_tool.core.outputs.verify import verify_outputs

    project = load_project(path).project
    if not project.harnesses:
        print(
            "error: there are no harnesses to export; run `harness generate` first.",
            file=sys.stderr,
        )
        return 1
    result = build_outputs(project)
    report = verify_outputs(project, result.files)
    for issue in report.issues:
        print(f"{issue.severity}: [{issue.code}] {issue.message}")
    if not report.ok:
        print("Not written: the outputs failed their independent check.", file=sys.stderr)
        return 1
    write_outputs(project, path / DEFAULT_FOLDER, result)
    target = path / DEFAULT_FOLDER
    print(f"{len(result.files)} files written to {target} (model {result.stamp.short}).")
    return 0


def _drc(path: Path) -> int:
    from harness_tool.core.checks import find
    from harness_tool.core.drc import run
    from harness_tool.core.drc.report import render_markdown

    project = load_project(path).project
    findings = sorted(
        [*find(project), *run(project)],
        key=lambda f: ({"error": 0, "warning": 1, "info": 2}[f.severity], f.id),
    )
    print(render_markdown(project, findings), end="")
    return 1 if any(f.severity == "error" and f.waiver is None for f in findings) else 0


def _verify(path: Path, outputs: bool = False) -> int:
    from harness_tool.core.verify import verify_project

    project = load_project(path).project
    report = verify_project(project)
    if outputs:
        from harness_tool.core.outputs.build import DEFAULT_FOLDER
        from harness_tool.core.outputs.verify import read_folder, verify_outputs

        folder = path / DEFAULT_FOLDER
        if not folder.is_dir():
            print("error: no outputs folder; run `harness export` first.", file=sys.stderr)
            return 1
        out = verify_outputs(project, read_folder(folder))
        report.issues += out.issues
        report.stale = report.stale or out.stale
    for issue in report.issues:
        print(f"{issue.severity}: [{issue.code}] {issue.message}")
    print(report.summary())
    return 0 if report.ok else 1


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
        if args.command == "generate":
            return _generate(args.project)
        if args.command in data.COMMANDS:
            return data.run(args)
        if args.command in changes.COMMANDS:
            return changes.run(args)
        if args.command == "export":
            return _export(args.project)
        if args.command == "drc":
            return _drc(args.project)
        if args.command == "verify":
            return _verify(args.project, args.outputs)
        return _validate(args.project, merge_check=args.command == "check")
    except HarnessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
