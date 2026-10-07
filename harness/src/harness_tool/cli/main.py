"""`harness` command line entry point."""

import argparse
import sys
from collections.abc import Sequence

from harness_tool import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness", description="Spacecraft harness design tool")
    parser.add_argument("--version", action="store_true", help="print the tool version and exit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits on bad input; report it as a return code
        return 0 if exc.code in (0, None) else 2
    if args.version:
        print(f"harness {__version__}")
        return 0
    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
