"""Pin Check Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PinCheck:
    ok: bool
    residual: str | None
    pin_sha: str
