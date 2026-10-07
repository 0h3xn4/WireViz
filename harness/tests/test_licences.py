"""REQ-LIC-01: licence allow-list logic (the report itself is built by tools/licence_report.py)."""

import pytest

from tools.licence_report import classify


@pytest.mark.parametrize(
    "lic", ["MIT License", "BSD License", "Apache Software License", "ISC License (ISCL)",
            "GNU Lesser General Public License v3 (LGPLv3)", "LGPL-3.0-only", "MIT AND Python-2.0"],
)  # fmt: skip
def test_allowed(lic: str) -> None:
    assert classify(lic) == "allowed"


@pytest.mark.parametrize(
    "lic", ["GNU General Public License v3 (GPLv3)", "GPL-3.0-only", "AGPL-3.0", "UNKNOWN", ""]
)
def test_rejected(lic: str) -> None:
    assert classify(lic) == "rejected"
