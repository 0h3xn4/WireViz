"""Output verifier v2: re-reads the finished artefacts (CSV, SVG, PDF, YAML, JSON, XLSX, manifest)
and compares them with the model. It does not import the table or drawing builders; it parses
the bytes and derives what they must contain straight from the project, so a bug in a builder
cannot hide itself."""

import csv
import hashlib
import html
import io
import json
import re
import zipfile
import zlib
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path

from harness_tool.core import checks, drc
from harness_tool.core.io.layout import model_hash
from harness_tool.core.model import Harness, Project
from harness_tool.core.verify import VerifyReport

from .stamp import parse_csv

MANIFEST = "manifest.json"
HARNESS_FILES = (
    "wirelist.csv",
    "pinouts.csv",
    "bom.csv",
    "mass_length.csv",
    "tests.csv",
    "labels.csv",
    "wireviz.yaml",
)
SYSTEM_FILES = (
    "bom.csv", "mass_length.csv", "mating_matrix.csv", "traceability.csv", "box_pinouts.csv",
    "drc_findings.csv", "drc_report.md", "changelog.csv", "revision_report.md", "export.json", "system.xlsx", "block_diagram.svg",
    "block_diagram.pdf", "harness_overview.svg", "harness_overview.pdf",
)  # fmt: skip


def read_folder(folder: Path | str) -> dict[str, bytes]:
    root = Path(folder)
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.name.endswith(".tmp")
    }


def _table(files: dict[str, bytes], rel: str) -> list[list[str]] | None:
    return parse_csv(files[rel]) if rel in files else None


def _svg_text(data: bytes) -> str:
    return " ".join(re.findall(r"<text[^>]*>([^<]*)</text>", data.decode()))


def _pdf_pages(data: bytes) -> int:
    return len(re.findall(rb"/Type /Page /", data))


def _unescape(s: str) -> str:
    return s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


DAMAGE = (
    ValueError,
    KeyError,
    IndexError,
    TypeError,
    AttributeError,
    RecursionError,
    EOFError,
    OSError,
    zipfile.BadZipFile,
    zlib.error,
    csv.Error,
)


def _guard(r: VerifyReport, what: str, fn: Callable[[], None]) -> None:
    """Damaged or unexpected file content is a finding, never a crash."""
    try:
        fn()
    except DAMAGE as exc:
        r.error(
            "out_unreadable",
            f"{what} could not be read ({type(exc).__name__}): it is damaged or not what the tool wrote.",
            what,
        )


def verify_outputs(project: Project, files: dict[str, bytes]) -> VerifyReport:
    r = VerifyReport()
    current = model_hash(project)
    short = current[:12]
    _guard(r, MANIFEST, lambda: _manifest(r, files, current))
    for rel in sorted(files):
        if rel != MANIFEST:
            _guard(r, rel, lambda rel=rel: _stamp(r, rel, files[rel], short))  # type: ignore[misc]
    for h in sorted(project.harnesses.values(), key=lambda x: x.id):
        _guard(r, f"harnesses/{h.id}", lambda h=h: _harness(r, project, h, files))  # type: ignore[misc]
    _guard(r, "system", lambda: _system(r, project, files))
    return r


def _manifest(r: VerifyReport, files: dict[str, bytes], current: str) -> None:
    raw = files.get(MANIFEST)
    if raw is None:
        return  # an in-memory set has no manifest; a folder always does
    try:
        doc = json.loads(raw)
        listed = {f["path"]: (f["sha256"], f["bytes"]) for f in doc["files"]}
    except (ValueError, KeyError, TypeError):
        r.error("out_manifest", "The manifest cannot be read.", MANIFEST)
        return
    if doc.get("model_hash") != current:
        r.error("out_stale", "The outputs were made from an older version of the design.", MANIFEST)
        r.stale = True
    for rel, (digest, size) in sorted(listed.items()):
        data = files.get(rel)
        if data is None:
            r.error("out_missing", f"{rel} is listed in the manifest but missing.", rel)
        elif hashlib.sha256(data).hexdigest() != digest or len(data) != size:
            r.error("out_modified", f"{rel} was changed after it was exported.", rel)
    for rel in sorted(set(files) - set(listed) - {MANIFEST}):
        r.warning("out_unlisted", f"{rel} is not listed in the manifest.", rel)


def _stamp(r: VerifyReport, rel: str, data: bytes, short: str) -> None:
    if rel.endswith((".csv", ".yaml")):
        first = data.split(b"\n", 1)[0].decode()
        ok = first.startswith("# harness-tool ") and first.endswith(f"model {short}")
    elif rel.endswith(".md"):
        ok = (
            data.startswith(b"<!-- harness-tool ")
            and f"model {short}".encode() in data.split(b"\n", 1)[0]
        )
    elif rel.endswith(".svg"):
        ok = (
            re.search(rb"<desc>harness-tool [^<]* model " + short.encode() + rb"</desc>", data)
            is not None
        )
    elif rel.endswith(".pdf"):
        ok = f"model {short}".encode() in data
    elif rel.endswith(".json"):
        ok = f'"model_hash": "{short}'.encode() in data
    elif rel.endswith(".xlsx"):
        ok = _xlsx_hash(data) == short
    else:
        return
    if not ok:
        r.error("out_stamp", f"{rel} does not carry the current generator and model stamp.", rel)


def _xlsx_sheets(data: bytes) -> dict[str, list[list[str]]]:
    """Read the inline-string cells of a workbook straight from its XML (fast, no spreadsheet
    library): sheet name -> rows."""
    out: dict[str, list[list[str]]] = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = re.findall(r'<sheet [^>]*name="([^"]*)"', z.read("xl/workbook.xml").decode())
        for n, name in enumerate(names, start=1):
            xml = z.read(f"xl/worksheets/sheet{n}.xml").decode()
            rows = []
            for row in re.findall(r"<row [^>]*>(.*?)</row>", xml, flags=re.S):
                rows.append(
                    [
                        html.unescape("".join(re.findall(r"<t[^>]*>([^<]*)</t>", c)))
                        for c in re.findall(r"<c [^>]*?(?:/>|>.*?</c>)", row, flags=re.S)
                    ]
                )
            out[html.unescape(name)] = rows
    return out


def _xlsx_hash(data: bytes) -> str:
    rows = _xlsx_sheets(data).get("About", [])
    return rows[1][1][:12] if len(rows) > 1 and len(rows[1]) > 1 else ""


def _xlsx_rows(data: bytes, sheet: str) -> list[list[str]]:
    return _xlsx_sheets(data).get(sheet, [])


def _harness(r: VerifyReport, project: Project, h: Harness, files: dict[str, bytes]) -> None:
    base = f"harnesses/{h.id}"
    for name in HARNESS_FILES:
        if f"{base}/{name}" not in files:
            r.error("out_missing", f"{base}/{name} was not generated.", h.id)
    wl = _table(files, f"{base}/wirelist.csv")
    if wl:
        expected = {w.id: w for w in h.wires}
        rows = wl[1:]
        got = Counter(row[0] for row in rows)
        for wid in sorted(expected):
            if got[wid] == 0:
                r.error("out_wire_missing", f"Wire {wid} is not in the wire list of {h.id}.", wid)
            elif got[wid] > 1:
                r.error(
                    "out_wire_duplicated",
                    f"Wire {wid} appears {got[wid]} times in the wire list of {h.id}.",
                    wid,
                )
        for wid in sorted(set(got) - set(expected)):
            r.error(
                "out_wire_extra",
                f"The wire list of {h.id} has {wid}, which is not in the design.",
                wid,
            )
        for row in rows:
            w = expected.get(row[0])
            if w is None:
                continue
            want = [
                w.from_connector,
                w.from_pin,
                w.to_connector,
                w.to_pin,
                "pending" if w.gauge_awg is None else str(w.gauge_awg),
            ]
            if row[3:8] != want:
                r.error(
                    "out_wire_differs",
                    f"Wire {w.id} in the wire list does not match the design (ends or gauge).",
                    w.id,
                )
            if w.length_m is not None and (not row[10] or abs(float(row[10]) - w.length_m) > 1e-9):
                r.error(
                    "out_wire_differs",
                    f"Wire {w.id} has a different length in the wire list.",
                    w.id,
                )
        r.wires_checked += len(h.wires)
    po = _table(files, f"{base}/pinouts.csv")
    if po:
        pins = {(row[0], row[4]) for row in po[1:]}
        want_pins = {(c.id, p.id) for c in h.connectors for p in c.pins}
        if pins != want_pins:
            r.error(
                "out_pinout",
                f"The pinout table of {h.id} lists different pins than the design.",
                h.id,
            )
        used: dict[tuple[str, str], set[str]] = defaultdict(set)
        for w in h.wires:
            used[(w.from_connector, w.from_pin)].add(w.id)
            used[(w.to_connector, w.to_pin)].add(w.id)
        for row in po[1:]:
            if set(filter(None, row[7].split(";"))) != used.get((row[0], row[4]), set()):
                r.error(
                    "out_pinout",
                    f"Pin {row[0]}.{row[4]} lists the wrong wires in the pinout table.",
                    h.id,
                )
                break
    bm = _table(files, f"{base}/bom.csv")
    if bm:
        conns = Counter(c.part_id for c in h.connectors)
        bom_rows = {row[0]: row for row in bm[1:]}
        for pid, n in sorted(conns.items()):
            if pid not in bom_rows or bom_rows[pid][6] != str(n):
                r.error("out_bom", f"The BOM of {h.id} has the wrong quantity for {pid}.", h.id)
        metres: dict[str, float] = defaultdict(float)
        for w in h.wires:
            if w.part_id and w.length_m is not None:
                metres[w.part_id] += w.length_m
        for pid, total in sorted(metres.items()):
            if pid not in bom_rows or abs(float(bom_rows[pid][6] or 0) - total) > 1e-5 * max(
                1.0, total
            ):
                r.error("out_bom", f"The BOM of {h.id} has the wrong wire length for {pid}.", h.id)
    ts = _table(files, f"{base}/tests.csv")
    if ts:
        cont = [row for row in ts[1:] if row[1] == "continuity"]
        iso = [row for row in ts[1:] if row[1] == "isolation"]
        if sorted(row[7] for row in cont) != sorted(w.id for w in h.wires):
            r.error(
                "out_tests", f"{h.id} does not have exactly one continuity test per wire.", h.id
            )
        if len(iso) != len(h.wires) + len(h.shields):
            r.error(
                "out_tests", f"{h.id} does not have one isolation test per wire and shield.", h.id
            )
    lb = _table(files, f"{base}/labels.csv")
    if lb and len(lb) - 1 != len(h.connectors) + 2 * len(h.wires):
        r.error("out_labels", f"{h.id} has the wrong number of labels.", h.id)
    yml = files.get(f"{base}/wireviz.yaml")
    if yml is not None:
        text = yml.decode()
        if len(re.findall(r"^  - - ", text, flags=re.M)) != len(h.wires):
            r.error(
                "out_yaml", f"The WireViz file of {h.id} has the wrong number of connections.", h.id
            )
    x = files.get(f"{base}/{h.id}.xlsx")
    if x is not None:
        ids = [row[0] for row in _xlsx_rows(x, "Wire list")[1:]]
        if sorted(ids) != sorted(w.id for w in h.wires):
            r.error(
                "out_xlsx", f"The workbook of {h.id} lists different wires than the design.", h.id
            )
    _drawings(r, h, files)


def _drawings(r: VerifyReport, h: Harness, files: dict[str, bytes]) -> None:
    base = f"harnesses/{h.id}"
    svgs = sorted(k for k in files if re.fullmatch(re.escape(base) + r"/drawing_A3_s\d+\.svg", k))
    if not svgs:
        r.error("out_missing", f"{h.id} has no drawing.", h.id)
        return
    nums = sorted(int(re.search(r"_s(\d+)\.svg", k).group(1)) for k in svgs)  # type: ignore[union-attr]
    if nums != list(range(1, len(nums) + 1)):
        r.error(
            "out_drawing", f"The drawing sheets of {h.id} are not numbered 1 to {len(nums)}.", h.id
        )
    text = " ".join(_svg_text(files[k]) for k in svgs)
    words = set(text.split())
    for wid in sorted(w.id for w in h.wires):
        if _unescape(wid) not in words:
            r.error("out_drawing", f"Wire {wid} is missing from the drawing of {h.id}.", wid)
    for c in h.connectors:
        if c.id not in words and c.id not in text:
            r.error("out_drawing", f"Connector {c.id} is missing from the drawing of {h.id}.", c.id)
    for k in svgs:
        sheet = re.search(r"_s(\d+)\.svg", k).group(1)  # type: ignore[union-attr]
        if f"{sheet} / {len(svgs)}" not in _svg_text(files[k]):
            r.error("out_drawing", f"The title block of {k} shows the wrong sheet number.", h.id)
    a3 = files.get(f"{base}/drawing_A3.pdf")
    if a3 is not None and _pdf_pages(a3) != len(svgs):
        r.error(
            "out_drawing",
            f"The A3 PDF of {h.id} has a different number of sheets than the SVG files.",
            h.id,
        )
    for size in ("A3", "A4"):
        pdf = files.get(f"{base}/drawing_{size}.pdf")
        if pdf is not None:
            for w in h.wires:
                if w.id.encode() not in pdf:
                    r.error(
                        "out_drawing",
                        f"Wire {w.id} is missing from the {size} PDF of {h.id}.",
                        w.id,
                    )
                    break


def _system(r: VerifyReport, project: Project, files: dict[str, bytes]) -> None:
    for name in SYSTEM_FILES:
        if f"system/{name}" not in files:
            r.error("out_missing", f"system/{name} was not generated.", name)
    wires = [w for h in project.harnesses.values() for w in h.wires]
    ml = _table(files, "system/mass_length.csv")
    if ml and (ml[-1][0] != "TOTAL" or ml[-1][1] != str(len(wires))):
        r.error(
            "out_mass", "The system mass and length table does not count every wire.", "mass_length"
        )
    bm = _table(files, "system/bom.csv")
    if bm:
        want = Counter(c.part_id for h in project.harnesses.values() for c in h.connectors)
        sys_rows = {row[0]: row for row in bm[1:]}
        for pid, n in sorted(want.items()):
            if pid not in sys_rows or sys_rows[pid][6] != str(n):
                r.error("out_bom", f"The system BOM has the wrong quantity for {pid}.", pid)
    mm = _table(files, "system/mating_matrix.csv")
    if mm:
        boxes = {row[0] for row in mm[1:]}
        if boxes != set(project.connectors):
            r.error(
                "out_matrix",
                "The mating matrix does not list exactly the box connectors.",
                "mating_matrix",
            )
        pairs = {(row[0], row[4]) for row in mm[1:] if row[4]}
        for h in project.harnesses.values():
            for c in h.connectors:
                if c.mates_with and (c.mates_with, c.id) not in pairs:
                    r.error("out_matrix", f"{c.id} is missing from the mating matrix.", c.id)
    tr = _table(files, "system/traceability.csv")
    if tr:
        routed = {w.interface_id for w in wires if w.interface_id}
        if {row[0] for row in tr[1:]} != set(project.interfaces):
            r.error(
                "out_trace",
                "The traceability matrix does not list exactly the interfaces.",
                "traceability",
            )
        for row in tr[1:]:
            if (row[7] == "yes") != (row[0] in routed):
                r.error("out_trace", f"{row[0]} is marked wrongly as routed or not routed.", row[0])
    ex = files.get("system/export.json")
    if ex is not None:
        try:
            doc = json.loads(ex)
            same = (
                doc["model_hash"] == model_hash(project)
                and len(doc["units"]) == len(project.units)
                and len(doc["interfaces"]) == len(project.interfaces)
                and sum(len(h["wires"]) for h in doc["harnesses"]) == len(wires)
            )
        except (ValueError, KeyError, TypeError):
            same = False
        if not same:
            r.error("out_json", "The JSON export does not match the design.", "export.json")
    for name, ids, what in (
        ("block_diagram", sorted(project.units), "unit"),
        ("harness_overview", sorted(project.harnesses), "harness"),
    ):
        svg = files.get(f"system/{name}.svg")
        if svg is not None:
            text = _svg_text(svg)
            words = set(text.split())
            missing = [i for i in ids if i not in words and name == "block_diagram"]
            if missing:
                r.error(
                    "out_diagram",
                    f"The {name.replace('_', ' ')} is missing {what} {missing[0]}.",
                    name,
                )
    fd = _table(files, "system/drc_findings.csv")
    if fd:
        n = len(checks.find(project)) + len(drc.run(project))
        if len(fd) - 1 != n:
            r.error(
                "out_drc", "The DRC findings table does not list every finding.", "drc_findings"
            )
    cl = _table(files, "system/changelog.csv")
    if cl and sorted(row[0] for row in cl[1:]) != sorted(project.changelog):
        r.error(
            "out_changelog",
            "The change log table does not list exactly the change log entries.",
            "changelog",
        )
    rr = files.get("system/revision_report.md")
    if rr is not None:
        words = set(rr.decode().replace("`", " ").replace("(", " ").split())
        for hid in sorted({b.harness_id for b in project.baselines.values()}):
            if hid not in words:
                r.error("out_changelog", f"The revision report does not mention {hid}.", hid)
    md = files.get("system/drc_report.md")
    if md is not None and "Waived:" not in md.decode():
        r.error("out_drc", "The DRC report is incomplete.", "drc_report")
