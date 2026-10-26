"""Canonical bytes: sorted keys, two-space indent, LF, ASCII, final newline.

Classification: Domain Solvers Canonical Serialization.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

from .errors import ExactError


def _check(obj: object, path: str) -> None:
    if isinstance(obj, float):
        raise ExactError("RR-FLOAT", f"float at {path or '$'}")
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise ExactError("RR-KEY", f"non-string key at {path or '$'}")
            _check(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _check(v, f"{path}[{i}]")
    elif obj is None or isinstance(obj, (str, int, bool)):
        return
    else:
        raise ExactError("RR-TYPE", f"{type(obj).__name__} at {path or '$'} is not JSON")


def dumps(obj: object) -> bytes:
    _check(obj, "")
    text = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True)
    return (text + "\n").encode("ascii")


def _no_float(text: str) -> float:
    raise ExactError("RR-FLOAT", f"float literal {text!r} in input")


def _no_constant(text: str) -> float:
    raise ExactError("RR-FLOAT", f"non-finite literal {text!r} in input")


def _pairs(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for k, v in pairs:
        if k in out:
            raise ExactError("RR-DUPLICATE-KEY", f"duplicate key {k!r}")
        out[k] = v
    return out


def loads(data: bytes | str) -> object:
    text = data.decode("utf-8") if isinstance(data, bytes) else data
    return json.loads(
        text,
        parse_float=_no_float,
        parse_constant=_no_constant,
        object_pairs_hook=_pairs,
    )


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_tag(data: bytes) -> str:
    return "sha256:" + sha256_hex(data)


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


__all__ = [
    "dumps",
    "git_blob_id",
    "loads",
    "sha256_hex",
    "sha256_tag",
]
