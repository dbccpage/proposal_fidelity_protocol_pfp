"""End-to-end integration test fixtures for Prompt Civ.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Dict, List, Optional

from omega_engine_prompt_civilization.domain.causal_witness import SealedCausalWitness


@dataclass(frozen=True)
class StateSnapshot:
    """Snapshot of rank and immunity state digests."""
    rank_digest: str
    immunity_digest: str


@dataclass(frozen=True)
class MutationExecutionResult:
    """Result of an attempted mutation."""
    edge_created: bool
    propagation_count: int
    parent_propagation_weight: Fraction = Fraction(0, 1)


class PromptCivE2EFixtureV1:
    """E2E test fixture validating reference invariance and witnessed descent."""

    def __init__(self) -> None:
        self._reference_edges: List[tuple[str, str]] = []
        self._inheritance_edges: List[tuple[str, str]] = []
        self._immunity_records: List[Dict[str, Any]] = [
            {"prompt_id": "genome_a", "antibody_id": "ab_01"}
        ]

    def capture_rank_and_immunity_snapshot(self) -> StateSnapshot:
        # Rank depends on inheritance edges and evidence, NEVER on reference edges
        rank_raw = f"rank_state:{sorted(self._inheritance_edges)}".encode("utf-8")
        rank_digest = "sha256:" + hashlib.sha256(rank_raw).hexdigest()

        immunity_raw = f"immunity_state:{self._immunity_records}".encode("utf-8")
        immunity_digest = "sha256:" + hashlib.sha256(immunity_raw).hexdigest()

        return StateSnapshot(
            rank_digest=rank_digest,
            immunity_digest=immunity_digest,
        )

    def add_reference_edge(self, source: str, target: str) -> None:
        self._reference_edges.append((source, target))

    def attempt_mutation(
        self,
        *,
        parent: str,
        child_candidate: str,
        witness_receipt: Optional[SealedCausalWitness] = None,
    ) -> MutationExecutionResult:
        if not isinstance(witness_receipt, SealedCausalWitness):
            return MutationExecutionResult(
                edge_created=False,
                propagation_count=0,
                parent_propagation_weight=Fraction(0, 1),
            )

        self._inheritance_edges.append((parent, child_candidate))
        # At d=1, parent propagation weight is 1/2
        return MutationExecutionResult(
            edge_created=True,
            propagation_count=1,
            parent_propagation_weight=Fraction(1, 2),
        )
