"""Licence report for installed runtime dependencies, failing on anything outside the allow-list.

Usage: python -m tools.licence_report OUT.md [PYTHON]  (PYTHON = interpreter of the shipped env)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ALLOWED_WORDS = ("mit", "bsd", "apache", "isc", "python software foundation", "psf", "python-2.0",
                 "lgpl", "lesser general public", "mpl", "unlicense", "zlib", "0bsd")  # fmt: skip
REJECTED_RE = re.compile(r"(?<![a-z])(a?gpl)|general public license", re.IGNORECASE)
OWN = {"harness-tool"}
DEV_ONLY = OWN | {
    "pip-licenses", "pyinstaller", "cyclonedx-bom", "pytest", "pytest-cov", "pytest-qt",
    "hypothesis", "mypy", "ruff",
}  # fmt: skip


def classify(licence: str) -> str:
    """Return 'allowed' or 'rejected'. SPDX `AND` needs all parts allowed, `OR` any part."""
    text = licence.strip().lower()
    if not text or "unknown" in text:
        return "rejected"
    if ";" in text:  # pip-licenses joins multiple classifiers; be conservative: all must pass
        return "allowed" if all(classify(p) == "allowed" for p in text.split(";")) else "rejected"
    if " or " in text:
        return (
            "allowed" if any(classify(p) == "allowed" for p in text.split(" or ")) else "rejected"
        )
    if " and " in text:
        return (
            "allowed" if all(classify(p) == "allowed" for p in text.split(" and ")) else "rejected"
        )
    if "lgpl" in text or "lesser general public" in text:
        return "allowed"
    if REJECTED_RE.search(text):
        return "rejected"
    return "allowed" if any(w in text for w in ALLOWED_WORDS) else "rejected"


def main(out: str, python: str = sys.executable) -> int:
    raw = subprocess.run(
        [sys.executable, "-m", "piplicenses", "--python", python, "--format=json", "--with-system"],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    rows = [r for r in json.loads(raw) if r["Name"].lower() not in DEV_ONLY]
    lines = [
        "# Licence report",
        "",
        "| Package | Version | Licence | Status |",
        "| --- | --- | --- | --- |",
    ]
    bad = 0
    for r in sorted(rows, key=lambda r: r["Name"].lower()):
        status = classify(r["License"])
        bad += status == "rejected"
        lines.append(f"| {r['Name']} | {r['Version']} | {r['License']} | {status} |")
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} packages, {bad} rejected")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:3]))
