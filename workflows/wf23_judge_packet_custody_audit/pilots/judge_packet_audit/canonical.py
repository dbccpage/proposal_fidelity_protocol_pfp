"""Canonical JSON output for audit records.

Records are written with sorted keys, UTF-8 without BOM and LF line endings.
Floats are refused: every ratio in an audit record is an exact ``"p/q"``
string, so a record never depends on binary floating-point formatting.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from fractions import Fraction
from pathlib import Path
from typing import Any


class FloatInRecordError(TypeError):
    """Raised when an audit record contains a float."""


def _check(value: Any, path: str = "$") -> None:
    if type(value) is float:
        raise FloatInRecordError(f"float at {path}; use an exact fraction string")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"non-string key at {path}")
            _check(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _check(item, f"{path}[{index}]")


def dumps(value: Any, *, indent: int | None = None) -> str:
    """Serializes ``value`` canonically (sorted keys, no floats)."""
    _check(value)
    if indent is None:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(value, sort_keys=True, ensure_ascii=False, indent=indent)


def ratio(numerator: int, denominator: int) -> str:
    """Exact ratio as a reduced ``"p/q"`` string; ``"0/0"`` marks an empty denominator."""
    if type(numerator) is not int or type(denominator) is not int:
        raise TypeError("ratio requires int arguments")
    if denominator == 0:
        return "0/0"
    value = Fraction(numerator, denominator)
    return f"{value.numerator}/{value.denominator}"


def write_json(path: Path, value: Any) -> str:
    """Writes one pretty-printed canonical JSON document; returns its SHA-256."""
    text = dumps(value, indent=2) + "\n"
    data = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def write_jsonl(path: Path, rows: list[Any]) -> str:
    """Writes one canonical JSON document per line; returns the file SHA-256."""
    text = "".join(dumps(row) + "\n" for row in rows)
    data = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def write_jsonl_gz(path: Path, rows: list[Any]) -> str:
    """Like ``write_jsonl`` but gzip-compressed with a zero timestamp and no file name,
    so the bytes depend only on the rows; returns the SHA-256 of the compressed file."""
    text = "".join(dumps(row) + "\n" for row in rows)
    data = _gzip(text.encode("utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def write_json_gz(path: Path, value: Any) -> str:
    """One compact canonical JSON document, gzip-compressed deterministically."""
    data = _gzip((dumps(value) + "\n").encode("utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def read_json_gz(path: Path) -> Any:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _gzip(raw: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, compresslevel=9, mtime=0) as handle:
        handle.write(raw)
    return buffer.getvalue()


def read_jsonl_gz(path: Path) -> list[Any]:
    with gzip.open(path, "rt", encoding="utf-8", newline="\n") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
