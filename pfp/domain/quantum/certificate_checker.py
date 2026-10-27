"""Explicit native certificate checker port. AuthorityEffect: None.

Python neither verifies algebra nor fills missing certificate fields. The Rust
checker accepts the compact public challenge result and owns every verdict.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pfp.domain.ports.stabilizer_port import StabilizerPort


def check_certificate(
    case: Mapping[str, Any], result: Any, *, port: StabilizerPort | None = None
) -> dict[str, Any]:
    """Delegate checking, including malformed JSON-shaped model proposals."""
    if port is None:
        return {
            "verdict": "FAIL",
            "case_id": str(case.get("id") or case.get("case_id") or "unnamed"),
            "refusal_code": "NATIVE_PORT_UNBOUND",
            "error": "An explicit Rust-backed StabilizerPort is required",
        }
    return port.check(case, result)
