"""Revalidate Result Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from .candidate_binding import CandidateBinding


@dataclass(frozen=True)
class RevalidateResult:
    ok: bool
    residual: str | None
    live: CandidateBinding | None = None
