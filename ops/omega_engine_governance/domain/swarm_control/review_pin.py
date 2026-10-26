"""Review Pin Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewPin:
    pr_number: int
    pin_sha: str
