#!/usr/bin/env python3
"""Domain errors for the paper_iteration Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations


class PaperIterationDomainError(ValueError):
    """Base error for paper iteration domain invariant violations."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"PAPER_ITERATION_DOMAIN_ERROR[{code}]: {detail}")


class InvalidGateReceiptError(PaperIterationDomainError):
    """Raised when a gate receipt fails validation invariants."""

    def __init__(self, detail: str) -> None:
        super().__init__("INVALID_GATE_RECEIPT", detail)


class StrictProposerEvaluatorCollisionError(PaperIterationDomainError):
    """Raised when proposer and evaluator identities collide in strict mode."""

    def __init__(self, identity: str) -> None:
        super().__init__(
            "STRICT_ID_COLLISION",
            f"strict mode requires independent proposer and evaluator IDs (got {identity!r})",
        )


class AuthorityFirewallViolationError(PaperIterationDomainError):
    """Raised when an evaluation attempts to claim non-null execution authority."""

    def __init__(self, effect: str) -> None:
        super().__init__(
            "AUTHORITY_FIREWALL_VIOLATION",
            f"research evaluations must carry AuthorityEffect::None (got {effect!r})",
        )
