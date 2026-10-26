"""Mode Verdict Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModeVerdict:
    ok: bool
    residual: str | None
