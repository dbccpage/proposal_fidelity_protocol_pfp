"""Claim ledger and formal claim verification tracking.

Enforces 1:1 claim ID bijections, claim hygiene, and verification receipts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set, Tuple


class ClaimStatus(str, Enum):
    """Categorical verification status of a mathematical claim."""

    FORMAL_LEAN4 = "FORMAL_LEAN4"
    EXACT_SOLVER = "EXACT_SOLVER"
    EMPIRICAL_TEST = "EMPIRICAL_TEST"
    UNVERIFIED_CONJECTURE = "UNVERIFIED_CONJECTURE"
    REFUTED = "REFUTED"


@dataclass(frozen=True)
class ClaimVerificationReceipt:
    """Cryptographic or formal verification receipt for a claim."""

    claim_id: str
    status: ClaimStatus
    verifier_id: str
    verified_digest: str
    oracle_details: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")


@dataclass(frozen=True)
class ClaimRecord:
    """Individual mathematical claim tracked in the research paper."""

    claim_id: str
    statement: str
    status: ClaimStatus
    lean4_theorem: Optional[str] = None
    solver_witness_id: Optional[str] = None
    source_file: str = ""
    line_start: int = 0
    line_end: int = 0
    receipt: Optional[ClaimVerificationReceipt] = None

    def __post_init__(self) -> None:
        if not self.claim_id.strip():
            raise ValueError("Claim ID cannot be empty")
        if not self.statement.strip():
            raise ValueError("Claim statement cannot be empty")

    def is_mechanized(self) -> bool:
        return self.status in (ClaimStatus.FORMAL_LEAN4, ClaimStatus.EXACT_SOLVER)


@dataclass(frozen=True)
class ClaimLedger:
    """Immutable ledger of all claims declared within a paper."""

    paper_id: str
    claims: Tuple[ClaimRecord, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ids: Set[str] = set()
        for c in self.claims:
            if c.claim_id in ids:
                raise ValueError(f"Duplicate claim ID detected: '{c.claim_id}'")
            ids.add(c.claim_id)

    def get_claim(self, claim_id: str) -> Optional[ClaimRecord]:
        for c in self.claims:
            if c.claim_id == claim_id:
                return c
        return None

    def all_ids(self) -> Set[str]:
        return {c.claim_id for c in self.claims}

    def mechanized_count(self) -> int:
        return sum(1 for c in self.claims if c.is_mechanized())

    def total_count(self) -> int:
        return len(self.claims)
