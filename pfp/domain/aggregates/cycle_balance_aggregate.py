"""Cycle Balance Quartet Aggregate Root.

AuthorityEffect: None.
Governing standard: Proposal Fidelity Protocol (PFP v0.2), Four-Object Lifecycle.
Clean Architecture Domain-Driven Design (DDD).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..entities.cycle_balance import (
    CandidateEntity,
    ProblemEntity,
    ReceiptEntity,
    VerifierEntity,
)
from ..kernel.result import DomainError, RefusalCode, Result
from ..value_objects.identifiers import Sha256Digest
from .base import AggregateRoot


@dataclass
class CycleBalanceQuartetAggregate(AggregateRoot):
    """Aggregate Root enforcing cryptographic link binding across the four-object lifecycle.

    Encapsulates the four domain entities:
    1. ProblemEntity (P)
    2. CandidateEntity (P')
    3. VerifierEntity (V)
    4. ReceiptEntity (R)

    Invariants:
    1. INV_CB_01: Candidate binds to problem (candidate_problem_digest == problem_digest).
    2. INV_CB_02: Receipt binds to candidate (receipt_candidate_digest == candidate_digest).
    3. INV_CB_03: Receipt binds to verifier (receipt.verifier_digest == verifier_digest).
    4. INV_CB_04: Receipt binds to problem (receipt.problem_digest == problem_digest).
    """

    problem: Optional[ProblemEntity] = None
    candidate: Optional[CandidateEntity] = None
    verifier: Optional[VerifierEntity] = None
    receipt: Optional[ReceiptEntity] = None

    problem_digest: Optional[Sha256Digest] = None
    candidate_digest: Optional[Sha256Digest] = None
    candidate_problem_digest: Optional[Sha256Digest] = None
    verifier_digest: Optional[Sha256Digest] = None
    receipt_candidate_digest: Optional[Sha256Digest] = None
    is_verified: bool = False

    def __post_init__(self) -> None:
        self._sync_entities_to_digests()
        self.validate_invariants()

    def _sync_entities_to_digests(self) -> None:
        """Synchronize digests from underlying entities when entities are provided."""
        if self.problem is not None:
            self.problem_digest = self.problem.compute_digest()

        if self.candidate is not None:
            self.candidate_digest = self.candidate.compute_digest()
            self.candidate_problem_digest = self.candidate.problem_digest

        if self.verifier is not None:
            self.verifier_digest = self.verifier.compute_digest()

        if self.receipt is not None:
            self.receipt_candidate_digest = self.receipt.candidate_digest
            self.is_verified = self.receipt.verification_status.is_verified

    def validate_invariants(self) -> None:
        """Validate aggregate consistency boundaries and cryptographic linkage."""
        # INV_CB_01: Candidate problem digest must match problem digest
        if self.candidate_problem_digest is not None and self.problem_digest is not None:
            if self.candidate_problem_digest != self.problem_digest:
                raise ValueError(
                    f"INV_CB_01 violation: Candidate problem digest ({self.candidate_problem_digest}) "
                    f"does not match problem digest ({self.problem_digest})"
                )

        # INV_CB_02: If receipt exists, it must bind to candidate digest
        if self.receipt_candidate_digest is not None and self.candidate_digest is not None:
            if self.receipt_candidate_digest != self.candidate_digest:
                raise ValueError(
                    f"INV_CB_02 violation: Receipt candidate digest ({self.receipt_candidate_digest}) "
                    f"does not match candidate digest ({self.candidate_digest})"
                )

        # INV_CB_03 & INV_CB_04: If receipt entity is present, verify full binding
        if self.receipt is not None:
            if self.verifier is not None and self.receipt.verifier_digest != self.verifier_digest:
                raise ValueError(
                    f"INV_CB_03 violation: Receipt verifier digest ({self.receipt.verifier_digest}) "
                    f"does not match verifier digest ({self.verifier_digest})"
                )
            if self.problem is not None and self.receipt.problem_digest != self.problem_digest:
                raise ValueError(
                    f"INV_CB_04 violation: Receipt problem digest ({self.receipt.problem_digest}) "
                    f"does not match problem digest ({self.problem_digest})"
                )

    def submit_candidate(self, candidate: CandidateEntity) -> Result[None, DomainError]:
        """Attach a candidate proposal to this problem aggregate, enforcing INV_CB_01."""
        if not isinstance(candidate, CandidateEntity):
            return Result.err(
                DomainError(
                    code=RefusalCode.TYPING_VIOLATION,
                    message=f"Expected CandidateEntity, got {type(candidate).__name__}",
                )
            )

        if self.problem is not None:
            if not candidate.binds_to_problem(self.problem):
                return Result.err(
                    DomainError(
                        code=RefusalCode.CRYPTOGRAPHIC_BINDING_FAILURE,
                        message=f"INV_CB_01 violation: candidate problem_digest {candidate.problem_digest} does not bind to problem {self.problem_digest}",
                    )
                )

        self.candidate = candidate
        self.candidate_digest = candidate.compute_digest()
        self.candidate_problem_digest = candidate.problem_digest
        return Result.ok(None)

    def bind_verifier(self, verifier: VerifierEntity) -> Result[None, DomainError]:
        """Attach a verifier contract to this problem aggregate."""
        if not isinstance(verifier, VerifierEntity):
            return Result.err(
                DomainError(
                    code=RefusalCode.TYPING_VIOLATION,
                    message=f"Expected VerifierEntity, got {type(verifier).__name__}",
                )
            )

        if self.problem is not None:
            if not verifier.binds_to_problem(self.problem):
                return Result.err(
                    DomainError(
                        code=RefusalCode.CRYPTOGRAPHIC_BINDING_FAILURE,
                        message=f"Verifier problem_digest {verifier.problem_digest} does not bind to problem {self.problem_digest}",
                    )
                )

        self.verifier = verifier
        self.verifier_digest = verifier.compute_digest()
        return Result.ok(None)

    def record_receipt(self, receipt: ReceiptEntity) -> Result[None, DomainError]:
        """Record an immutable verification receipt, enforcing INV_CB_02, INV_CB_03, and INV_CB_04."""
        if not isinstance(receipt, ReceiptEntity):
            return Result.err(
                DomainError(
                    code=RefusalCode.TYPING_VIOLATION,
                    message=f"Expected ReceiptEntity, got {type(receipt).__name__}",
                )
            )

        if self.candidate is not None:
            if not receipt.binds_to_candidate(self.candidate):
                return Result.err(
                    DomainError(
                        code=RefusalCode.CRYPTOGRAPHIC_BINDING_FAILURE,
                        message=f"INV_CB_02 violation: receipt candidate_digest {receipt.candidate_digest} does not match candidate {self.candidate_digest}",
                    )
                )

        if self.verifier is not None:
            if not receipt.binds_to_verifier(self.verifier):
                return Result.err(
                    DomainError(
                        code=RefusalCode.CRYPTOGRAPHIC_BINDING_FAILURE,
                        message=f"INV_CB_03 violation: receipt verifier_digest {receipt.verifier_digest} does not match verifier {self.verifier_digest}",
                    )
                )

        if self.problem is not None:
            if not receipt.binds_to_problem(self.problem):
                return Result.err(
                    DomainError(
                        code=RefusalCode.CRYPTOGRAPHIC_BINDING_FAILURE,
                        message=f"INV_CB_04 violation: receipt problem_digest {receipt.problem_digest} does not match problem {self.problem_digest}",
                    )
                )

        self.receipt = receipt
        self.receipt_candidate_digest = receipt.candidate_digest
        self.is_verified = receipt.verification_status.is_verified
        return Result.ok(None)

    def is_complete(self) -> bool:
        """Check if all four objects are attached and verification succeeded."""
        return (
            self.problem is not None
            and self.candidate is not None
            and self.verifier is not None
            and self.receipt is not None
            and self.is_verified
        )
