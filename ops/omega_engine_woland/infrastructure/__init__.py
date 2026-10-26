"""Concrete Woland infrastructure adapters. AuthorityEffect: None."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cochain_adapter import (
        DefaultCochainScoringAdapter,
        build_face_boundary,
        build_incidence,
    )
    from .diff_oracle import DiffOracleCandidateChecker
    from .prime_continuation_adapter import PrimeContinuationAdapter

__all__ = [
    "DefaultCochainScoringAdapter",
    "DiffOracleCandidateChecker",
    "PrimeContinuationAdapter",
    "build_face_boundary",
    "build_incidence",
]


def __getattr__(name: str):
    if name in ("DefaultCochainScoringAdapter", "build_face_boundary", "build_incidence"):
        from . import cochain_adapter
        return getattr(cochain_adapter, name)
    if name == "DiffOracleCandidateChecker":
        from . import diff_oracle
        return getattr(diff_oracle, name)
    if name == "PrimeContinuationAdapter":
        from . import prime_continuation_adapter
        return getattr(prime_continuation_adapter, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

