"""Finite stabilizer solve port; Rust owns all algebra and enumeration.

The result is the native public challenge contract, without historical aliases.
Missing explicit injection refuses instead of executing a Python reference.
AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pfp.domain.ports.stabilizer_port import StabilizerPort


def solve(case: Mapping[str, Any], *, port: StabilizerPort | None = None) -> dict[str, Any]:
    """Delegate one exact solve; an unbound port cannot issue a solved result."""
    if port is None:
        return {
            "id": str(case.get("id") or case.get("case_id") or "unnamed"),
            "status": "UNKNOWN",
            "refusal_code": "NATIVE_PORT_UNBOUND",
            "message": "An explicit Rust-backed StabilizerPort is required",
        }
    return port.solve(case)
