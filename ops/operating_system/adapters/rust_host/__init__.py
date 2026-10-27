"""OEOS adapter for the native `core_symbol_game` host process.

The whole seam is `ffi.py`. Nothing else in the repository may spawn the host
binary directly -- see `RULE_FFI_SEAM_ISOLATION_001` in
`.agents/skills/techne-code-ffi-rust-python/SKILL.md` and the Parity Seam
Isolation Invariant in `.agents/AGENTS.md`.

AuthorityEffect: None.
"""

from __future__ import annotations

from .ffi import (
    CANONICALIZATION_PROFILE,
    DESCRIPTION_SCHEMA,
    MAX_REQUEST_BYTES,
    OUTCOME_SCHEMA,
    REQUEST_SCHEMA,
    HostLocation,
    RustSymbolGameHost,
    SymgamHost,
    canonical_request_bytes,
    locate_host_binary,
    verify_outcome,
)
from .source_packet import SourcePacketHost

__all__ = [
    "CANONICALIZATION_PROFILE",
    "DESCRIPTION_SCHEMA",
    "HostLocation",
    "MAX_REQUEST_BYTES",
    "OUTCOME_SCHEMA",
    "REQUEST_SCHEMA",
    "RustSymbolGameHost",
    "SourcePacketHost",
    "SymgamHost",
    "canonical_request_bytes",
    "locate_host_binary",
    "verify_outcome",
]
