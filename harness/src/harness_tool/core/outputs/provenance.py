"""Provenance of a set of outputs: which tool, which design and which settings made them.

So that drawings and lists can be reproduced and audited (UX/UI guidelines "Provenance on every
output"; ECSS-E-ST-40C documentation). No dates and no paths: equal design, equal bytes.
"""

from __future__ import annotations

import hashlib
import json

from harness_tool.core.model import Project

from .stamp import Stamp

FORMAT = "harness-tool-provenance"
FORMAT_VERSION = 1


def _values_hash(values: dict[str, object]) -> str:
    text = json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def provenance_bytes(project: Project, stamp: Stamp) -> bytes:
    approvals: dict[str, int] = {}
    for part in project.parts.values():
        approvals[part.approval] = approvals.get(part.approval, 0) + 1
    doc = {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "tool": "harness-tool",
        "tool_version": stamp.version,
        "model_hash": stamp.model_hash,
        "project": project.meta.name,
        "export_notes": "The WireViz-style YAML files are an export format; WireViz is not used to make any output.",
        "library": {
            "name": project.library_info.name,
            "version": project.library_info.version,
            "parts": len(project.parts),
            "parts_by_approval": dict(sorted(approvals.items())),
            "unverified_parts": sum(p.unverified for p in project.parts.values()),
        },
        "settings": {
            name: {"placeholder": cfg.placeholder, "values_sha256_16": _values_hash(cfg.values)}
            for name, cfg in sorted(project.config.items())
        },
        "design": {
            "units": len(project.units),
            "interfaces": len(project.interfaces),
            "harnesses": len(project.harnesses),
            "wires": sum(len(h.wires) for h in project.harnesses.values()),
            "released_harnesses": sum(h.status == "released" for h in project.harnesses.values()),
        },
    }
    return (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode()
