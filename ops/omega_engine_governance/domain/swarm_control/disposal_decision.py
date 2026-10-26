"""Disposal Decision Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DisposalDecision:
    may_dispose: bool
    residual: str | None
    used_force: bool
    proof: str | None
