"""Re-exports the omega-canonical-v1 packet sealer.

RFC 8785 encoding is ``rfc8785.rfc8785_canonicalize``. This module does not
call it, and that encoder is not the sealer.
"""

from __future__ import annotations

from omega_engine_pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    canonical_bytes,
    canonical_json,
    canonical_unwire,
    canonical_wire,
    domain_digest,
    freeze,
    thaw,
)

__all__ = [
    "CanonicalizationError",
    "canonical_bytes",
    "canonical_json",
    "canonical_unwire",
    "canonical_wire",
    "domain_digest",
    "freeze",
    "thaw",
]
