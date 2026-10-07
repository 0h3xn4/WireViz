"""Every artefact carries the generator version and the model hash it was made from."""

import csv
import io
from dataclasses import dataclass

from harness_tool import __version__
from harness_tool.core.io.layout import model_hash
from harness_tool.core.model import Project


@dataclass(frozen=True)
class Stamp:
    version: str
    model_hash: str

    @property
    def short(self) -> str:
        return self.model_hash[:12]

    @property
    def line(self) -> str:
        return f"harness-tool {self.version} model {self.short}"


def stamp_of(project: Project) -> Stamp:
    return Stamp(__version__, model_hash(project))


Table = list[list[str]]  # first row is the header


def _safe(cell: str) -> str:
    """Spreadsheet programs run cells that start with = + - @ as formulas; mark such text."""
    if cell[:1] in ("=", "+", "-", "@", "\t", "\r"):
        try:
            float(cell)
        except ValueError:
            return "'" + cell
    return cell


def _unsafe(cell: str) -> str:
    return cell[1:] if cell[:1] == "'" and cell[1:2] in ("=", "+", "-", "@", "\t", "\r") else cell


def csv_bytes(table: Table, stamp: Stamp) -> bytes:
    """CSV with LF line endings. The first line is a comment `# <stamp>`; readers skip lines
    starting with `#` (documented in docs/OUTPUTS.md)."""
    buf = io.StringIO()
    buf.write(f"# {stamp.line}\n")
    w = csv.writer(buf, lineterminator="\n")
    w.writerows([[_safe(c) for c in row] for row in table])
    return buf.getvalue().encode()


def parse_csv(data: bytes) -> Table:
    """Inverse of `csv_bytes` (used by the independent output verifier)."""
    lines = data.decode().splitlines(keepends=True)
    if lines and lines[0].startswith("# "):  # only the stamp line: a cell may hold "# ..." text
        lines = lines[1:]
    return [[_unsafe(c) for c in row] for row in csv.reader(io.StringIO("".join(lines)))]
