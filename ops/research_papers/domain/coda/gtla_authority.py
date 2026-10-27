"""GTLA Terminal Factorization and Authority Firewall.

Enforces that zero defect mass does NOT automatically mint authority.
Authorization strictly requires an external cryptographic grant / human key.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class GTLATerminalOutcome(str, Enum):
    """The three disjoint terminal outcomes under GTLA master factorization."""

    AUTHORIZED = "AUTHORIZED"
    RESIDUAL_TRAPPED = "RESIDUAL_TRAPPED"
    REFUSED = "REFUSED"


@dataclass(frozen=True)
class GTLAResult:
    """Outcome of GTLA terminal factorization."""

    outcome: GTLATerminalOutcome
    grant_key: Optional[str] = None
    sentinel_id: Optional[str] = None
    refusal_reason: Optional[str] = None
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")
        if self.outcome == GTLATerminalOutcome.AUTHORIZED and not self.grant_key:
            raise ValueError("Outcome AUTHORIZED strictly requires an external cryptographic grant key.")
        if self.outcome == GTLATerminalOutcome.RESIDUAL_TRAPPED and not self.sentinel_id:
            raise ValueError("Outcome RESIDUAL_TRAPPED requires an SentinelRecord identifier.")
        if self.outcome == GTLATerminalOutcome.REFUSED and not self.refusal_reason:
            raise ValueError("Outcome REFUSED requires a typed refusal reason.")


class GTLAAuthorityResolver:
    """Resolves terminal authority under the GTLA refusal monad."""

    @staticmethod
    def resolve(
        all_guards_passed: bool,
        has_stable_residual: bool,
        sentinel_id: Optional[str],
        external_cryptographic_grant: Optional[str],
    ) -> GTLAResult:
        # Authority firewall: Even if all guards pass, without external key it cannot be Authorized
        if all_guards_passed and external_cryptographic_grant:
            return GTLAResult(
                outcome=GTLATerminalOutcome.AUTHORIZED,
                grant_key=external_cryptographic_grant,
                authority_effect="None",
            )
        elif has_stable_residual and sentinel_id:
            return GTLAResult(
                outcome=GTLATerminalOutcome.RESIDUAL_TRAPPED,
                sentinel_id=sentinel_id,
                authority_effect="None",
            )
        else:
            reason = "Refused by GTLA authority firewall: missing external cryptographic grant or unsatisfied guards."
            return GTLAResult(
                outcome=GTLATerminalOutcome.REFUSED,
                refusal_reason=reason,
                authority_effect="None",
            )
