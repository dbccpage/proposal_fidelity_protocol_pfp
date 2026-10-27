#!/usr/bin/env python3
"""Policy and markdown metadata validation for epic documents.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from product_planning_office.domain.manifest_models import (
    OIKONOMIA_STATUSES,
    fail,
)


def extract_markdown_field(text: str, field: str, path: str) -> str:
    """Extract a required markdown bold field value (e.g. **Status:** `...`)."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    pattern = re.compile(
        rf"^\*\*{re.escape(field)}:\*\*[ \t]+"
        rf"(?:`([^`\r\n]+)`|([A-Za-z][A-Za-z0-9_]*))[ \t]*$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(normalized))
    if len(matches) != 1:
        fail(
            "MARKDOWN_FIELD_CARDINALITY",
            f"{path}: expected exactly one {field!r} field, observed={len(matches)}",
        )
    return matches[0].group(1) or matches[0].group(2)


def verify_epic_policy(path: str, data: bytes) -> None:
    """Verify that an epic markdown file satisfies UTF-8 encoding and Oikonomia policy."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        fail("EPIC_NOT_UTF8", f"{path}: {error}")
    status = extract_markdown_field(text, "Status", path)
    if status not in OIKONOMIA_STATUSES:
        fail(
            "UNKNOWN_STATUS",
            f"{path}: {status!r} is outside the oikonomia vocabulary",
        )
    authority_effect = extract_markdown_field(text, "AuthorityEffect", path)
    if authority_effect != "None":
        fail(
            "AUTHORITY_EFFECT",
            f"{path}: expected AuthorityEffect None, observed={authority_effect!r}",
        )
