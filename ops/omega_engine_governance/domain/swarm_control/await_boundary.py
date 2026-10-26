"""Await Boundary Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from .candidate_binding import CandidateBinding


@dataclass(frozen=True)
class AwaitBoundary:
    pre_await: CandidateBinding
