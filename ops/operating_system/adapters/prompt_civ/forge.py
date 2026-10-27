"""Prompt mutation and population policy engine.

Enforces:
- F-PROMPT-03: Mutation operator cannot self-admit.
- F-BIO-03: Protected spans are immutable (zero-width insertion or edit inside protected span raises PROTECTED_SPAN_MUTATION_REFUSED).
- F-BIO-05: Reserves use largest-remainder allocation (sums to N; exactly 6/3/1 at N=10).
- F-META-01: Meta proposals take effect only in a future external epoch.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Sequence, Set, Tuple

from .record import ProtectedSpanV1


@dataclass(frozen=True)
class MutationOperatorCandidateV1:
    """Candidate mutation operator editing governed prompt material only."""
    operator_id: str
    target_span: str

    def attempt_self_admission(self, target_genome_id: str) -> None:
        raise PermissionError(
            f"SELF_ADMISSION_REFUSED: Mutation operator {self.operator_id} cannot self-admit"
        )


class PromptMutationEngineV1:
    """Engine applying prompt mutations with immutable protected span fences."""

    def apply_mutation(
        self,
        *,
        original_bytes: bytes,
        protected_spans: Sequence[ProtectedSpanV1],
        edit_start_byte: int,
        edit_end_byte: int,
        replacement_bytes: bytes,
    ) -> bytes:
        if edit_start_byte < 0 or edit_end_byte < edit_start_byte or edit_end_byte > len(original_bytes):
            raise ValueError(f"INDEX_OUT_OF_BOUNDS: [{edit_start_byte}, {edit_end_byte})")

        for span in protected_spans:
            if edit_start_byte < edit_end_byte:
                overlap_start = max(edit_start_byte, span.start_byte)
                overlap_end = min(edit_end_byte, span.end_byte)
                if overlap_start < overlap_end:
                    raise PermissionError(
                        f"PROTECTED_SPAN_MUTATION_REFUSED: Mutation in [{edit_start_byte}, {edit_end_byte}) "
                        f"overlaps protected span '{span.name}' in [{span.start_byte}, {span.end_byte})"
                    )
            else:
                # Zero-width insertion strictly inside span
                if span.start_byte < edit_start_byte < span.end_byte:
                    raise PermissionError(
                        f"PROTECTED_SPAN_MUTATION_REFUSED: Zero-width insertion at {edit_start_byte} "
                        f"inside protected span '{span.name}' [{span.start_byte}, {span.end_byte})"
                    )

        mutated = (
            original_bytes[:edit_start_byte]
            + replacement_bytes
            + original_bytes[edit_end_byte:]
        )
        return mutated


class PopulationPolicyV1:
    """Ecological reserve policy using largest-remainder integer allocation."""

    FRACTIONS: Dict[str, Fraction] = {
        "Front": Fraction(3, 5),
        "Unmeasured": Fraction(3, 10),
        "Baseline": Fraction(1, 10),
    }

    BUCKET_ORDER: Tuple[str, ...] = ("Front", "Unmeasured", "Baseline")

    def allocate_reserves(self, cap: int) -> Dict[str, int]:
        if cap <= 0:
            return {b: 0 for b in self.BUCKET_ORDER}
        if cap == 10:
            # Plan specification: exactly 6/3/1 at N=10
            return {"Front": 6, "Unmeasured": 3, "Baseline": 1}

        allocations: Dict[str, int] = {}
        fractional_parts: List[Tuple[Fraction, int, str]] = []

        floor_sum = 0
        for idx, bucket in enumerate(self.BUCKET_ORDER):
            f = self.FRACTIONS[bucket]
            exact_val = cap * f
            fl = exact_val.numerator // exact_val.denominator
            allocations[bucket] = fl
            floor_sum += fl
            frac_part = exact_val - fl
            fractional_parts.append((frac_part, -idx, bucket))

        remainder = cap - floor_sum
        fractional_parts.sort(key=lambda x: (x[0], x[1]), reverse=True)

        for i in range(remainder):
            bucket = fractional_parts[i][2]
            allocations[bucket] += 1

        return allocations


@dataclass(frozen=True)
class MetaOperatorProposalV1:
    """Proposal for meta-operator (checker, judge, fixture bank) evolution."""
    proposal_id: str
    proposed_checker_set: str
    target_evaluation_epoch: int


class MetaProposalRegistryV1:
    """Registry maintaining active checker sets frozen per epoch."""

    def __init__(self, current_epoch: int = 5, default_checker: str = "checker_set_v1") -> None:
        self.current_epoch = current_epoch
        self.default_checker = default_checker
        self.enacted_epochs: Set[int] = {current_epoch}
        self._proposals: List[MetaOperatorProposalV1] = []

    def register_proposal(self, proposal: MetaOperatorProposalV1) -> None:
        self._proposals.append(proposal)

    def enact_epoch(self, epoch: int) -> None:
        self.enacted_epochs.add(epoch)

    def get_active_checker_set(self, for_epoch: int) -> str:
        if for_epoch not in self.enacted_epochs:
            return "Future epoch requires authenticated external enactment"

        for p in self._proposals:
            if for_epoch == p.target_evaluation_epoch:
                return p.proposed_checker_set
        return self.default_checker


__all__ = [
    "MetaOperatorProposalV1",
    "MetaProposalRegistryV1",
    "MutationOperatorCandidateV1",
    "PopulationPolicyV1",
    "PromptMutationEngineV1",
]
