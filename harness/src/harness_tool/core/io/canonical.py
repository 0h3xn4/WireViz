"""Canonical JSON: the same data always yields the same bytes (sorted keys, fixed layout)."""

import json
from typing import Any


def dumps(data: Any) -> bytes:
    text = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
    return (text + "\n").encode("utf-8")


class DuplicateKeyError(ValueError):
    pass


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"key '{key}' appears twice in the same object")
        result[key] = value
    return result


def _no_constants(name: str) -> Any:
    raise ValueError(f"'{name}' is not valid JSON")


def _finite_float(text: str) -> float:
    value = float(text)
    if value in (float("inf"), float("-inf")) or value != value:
        raise ValueError("a number is too large to store")  # e.g. 1e999 would read back as infinity
    return value


def loads_strict(data: bytes) -> Any:
    """Parse UTF-8 JSON, rejecting duplicate keys (silent data loss) and NaN/Infinity."""
    text = data.decode("utf-8")  # UnicodeDecodeError is a ValueError
    if text.startswith("﻿"):
        text = text[1:]
    return json.loads(
        text,
        object_pairs_hook=_no_duplicates,
        parse_constant=_no_constants,
        parse_float=_finite_float,
    )
