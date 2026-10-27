"""Authority Fence helpers (0 classes).

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .authority_fence_error import AuthorityFenceError
from .window_declaration import WindowDeclaration


def audit_public_type(raw: Mapping[str, Any]) -> str:
    """Return residual if unfenced; PASS if fenced or out of scope."""
    if "authority_effect" not in raw:
        return "OUT_OF_SCOPE"
    try:
        WindowDeclaration.create(str(raw.get("name", "x")), raw.get("authority_effect"))
        return "PASS"
    except AuthorityFenceError as exc:
        return exc.residual
