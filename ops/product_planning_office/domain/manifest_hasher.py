#!/usr/bin/env python3
"""Canonical hashing and line ending inspection for epic manifest files.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping
from product_planning_office.domain.manifest_models import fail


def compute_content_set_sha256(entries: Iterable[Mapping[str, Any]]) -> str:
    """Hash canonical, path-sorted ``path\\0bytes\\0sha256\\n`` records."""
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: str(item["path"])):
        record = (
            f"{entry['path']}\0{entry['bytes']}\0{entry['sha256']}\n"
        ).encode("ascii")
        digest.update(record)
    return digest.hexdigest()


def line_profile(data: bytes) -> tuple[int, str]:
    """Inspect line count and verify uniform line endings."""
    without_crlf = data.replace(b"\r\n", b"")
    has_crlf = b"\r\n" in data
    has_lf = b"\n" in without_crlf
    has_cr = b"\r" in without_crlf
    styles = sum((has_crlf, has_lf, has_cr))
    if styles > 1:
        fail("MIXED_LINE_ENDINGS", "source snapshot contains mixed line endings")
    if has_crlf:
        ending = "CRLF"
    elif has_lf:
        ending = "LF"
    elif has_cr:
        ending = "CR"
    else:
        ending = "NONE"
    return len(data.splitlines()), ending
