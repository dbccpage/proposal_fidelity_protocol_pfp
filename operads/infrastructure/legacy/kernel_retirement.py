"""Typed refusal for legacy entry points built on the retired higher-operad kernel.

AuthorityEffect: None.
"""

from __future__ import annotations

from operations.domain.rop.result import Err, Refusal

RUNTIME_RETIRED = "RUNTIME_RETIRED"
KERNEL_RETIRED_MESSAGE = (
    "the Python higher-operad kernel is retired; its Rust successor "
    "engine/crates_rs/core_operad_theory has no Python seam yet"
)


def kernel_retired(locus: str) -> Err[Refusal]:
    """A diagnostic refusal; it compiles, admits and authorizes nothing."""
    return Err(Refusal(code=RUNTIME_RETIRED, message=KERNEL_RETIRED_MESSAGE, locus=locus))


__all__ = ["KERNEL_RETIRED_MESSAGE", "RUNTIME_RETIRED", "kernel_retired"]
