"""Requirement traceability (ECSS-E-ST-40C 5.8.3; ECSS-Q-ST-80C 6.2.6.12)."""

from __future__ import annotations

import csv
from pathlib import Path

from tools import trace

ROOT = Path(__file__).resolve().parent.parent


def test_every_requirement_is_traced_to_something() -> None:
    rows = trace.build()
    assert len(rows) >= 50
    bad = [r[0] for r in rows if r[5] not in ("traced", "verified-by-file-only", "review-only")]
    assert not bad, bad


def test_traceability_file_is_current() -> None:
    with (ROOT / "compliance" / "traceability.csv").open(newline="", encoding="utf-8") as f:
        assert list(csv.reader(f)) == [trace.HEADER, *trace.build()]
