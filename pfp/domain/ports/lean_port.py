"""Canonical port for Lean 4 formal verification engine (U17).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Protocol

from pfp.domain.lean_bridge.models import (
    LeanVerificationReceipt,
    LeanVerificationRequest,
)
from pfp.domain.shared_kernel.result import Result


class LeanVerifierPort(Protocol):
    """Protocol for sandboxed Lean 4 package verification and axiom audit."""

    def verify(
        self,
        request: LeanVerificationRequest,
        package_path: str,
    ) -> Result[LeanVerificationReceipt, Any]:
        """Verify a Lean 4 submission package against required declarations and axiom policy."""
        ...

