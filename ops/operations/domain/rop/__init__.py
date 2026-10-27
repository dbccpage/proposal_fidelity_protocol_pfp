"""Railway-Oriented Programming (ROP) domain package.

AuthorityEffect: None.
"""

from __future__ import annotations

from operations.domain.rop.result import (
    Err,
    Ok,
    Refusal,
    Result,
    sequence,
    traverse,
)

__all__ = ["Err", "Ok", "Refusal", "Result", "sequence", "traverse"]
