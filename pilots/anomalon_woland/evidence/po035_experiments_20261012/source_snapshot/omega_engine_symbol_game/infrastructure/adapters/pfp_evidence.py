"""Immutable JSON/byte evidence shared by bounded PFP campaigns."""

import hashlib
import json
import os
from pathlib import Path


def canonical(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(raw: bytes):
    return hashlib.sha256(raw).hexdigest()


def write_once(path: Path, value):
    raw = value if isinstance(value, bytes) else canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("IMMUTABLE_EVIDENCE_CONFLICT: " + str(path))
        return
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def repository_root(path: Path):
    return next(parent for parent in path.resolve().parents if (parent / ".git").exists())
