"""Value Objects for the Grammar Bounded Context.

Enforces:
- Exact-Type Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Immutability and Pure Python language types
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pfp.domain.mssn_research.shared_kernel.value_objects import (
    ContentDigest,
    Rational,
)

from .exact_structures import ExactRationalMatrix


@dataclass(frozen=True)
class RewriteStep:
    """A 4-tuple (rule_name, redex_loc, source_term, result_term) witnessing a term rewrite step."""
    rule_name: str
    redex_loc: str
    source_term: str
    result_term: str

    def __post_init__(self) -> None:
        if not isinstance(self.rule_name, str) or not self.rule_name:
            raise ValueError("rule_name must be a non-empty string")
        if not isinstance(self.redex_loc, str):
            raise TypeError("redex_loc must be a string")
        if not isinstance(self.source_term, str) or not isinstance(self.result_term, str):
            raise TypeError("source_term and result_term must be strings")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, RewriteStep)
        return (
            self.rule_name == other.rule_name
            and self.redex_loc == other.redex_loc
            and self.source_term == other.source_term
            and self.result_term == other.result_term
        )

    def __hash__(self) -> int:
        return hash((type(self), self.rule_name, self.redex_loc, self.source_term, self.result_term))


@dataclass(frozen=True)
class PeakClaim:
    """Witnesses a local divergent peak u <~ s ~> v and reduction sequences to a join term w."""
    peak_apex: str
    target_left: str
    target_right: str
    left_path: tuple[RewriteStep, ...]
    right_path: tuple[RewriteStep, ...]
    join_term: str

    def __post_init__(self) -> None:
        if not isinstance(self.peak_apex, str) or not isinstance(self.target_left, str) or not isinstance(self.target_right, str):
            raise TypeError("Apex and target terms must be strings")
        if not isinstance(self.left_path, tuple):
            object.__setattr__(self, "left_path", tuple(self.left_path))
        if not isinstance(self.right_path, tuple):
            object.__setattr__(self, "right_path", tuple(self.right_path))
        if not isinstance(self.join_term, str):
            raise TypeError("join_term must be a string")

    @property
    def is_reflexive_left(self) -> bool:
        return self.target_left == self.join_term and len(self.left_path) == 0

    @property
    def is_reflexive_right(self) -> bool:
        return self.target_right == self.join_term and len(self.right_path) == 0

    @property
    def is_trivial_peak(self) -> bool:
        return self.target_left == self.target_right and self.is_reflexive_left and self.is_reflexive_right

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, PeakClaim)
        return (
            self.peak_apex == other.peak_apex
            and self.target_left == other.target_left
            and self.target_right == other.target_right
            and self.left_path == other.left_path
            and self.right_path == other.right_path
            and self.join_term == other.join_term
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.peak_apex,
            self.target_left,
            self.target_right,
            self.left_path,
            self.right_path,
            self.join_term,
        ))


@dataclass(frozen=True)
class PolygraphPacket:
    """Level 11: Polygraph packet binding presentation ID, ruleset digest, steps, and peak claim."""
    presentation_id: str
    ruleset_digest: ContentDigest
    step_list: tuple[RewriteStep, ...]
    peak_claim: PeakClaim

    def __post_init__(self) -> None:
        if not isinstance(self.presentation_id, str):
            raise TypeError("presentation_id must be a string")
        if not isinstance(self.ruleset_digest, ContentDigest):
            raise TypeError("ruleset_digest must be a ContentDigest")
        if not isinstance(self.step_list, tuple):
            object.__setattr__(self, "step_list", tuple(self.step_list))
        if not isinstance(self.peak_claim, PeakClaim):
            raise TypeError("peak_claim must be a PeakClaim")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, PolygraphPacket)
        return (
            self.presentation_id == other.presentation_id
            and self.ruleset_digest == other.ruleset_digest
            and self.step_list == other.step_list
            and self.peak_claim == other.peak_claim
        )

    def __hash__(self) -> int:
        return hash((type(self), self.presentation_id, self.ruleset_digest, self.step_list, self.peak_claim))


# ---------------------------------------------------------------------------
# Level 12: DDA Event Records, 4-Field Kernel, and Kleene Cochains
# ---------------------------------------------------------------------------

class KleeneValue(int, Enum):
    """Kleene 3-valued logic truth value."""
    FAIL = 0     # <0>: Witnessed obstruction
    PASS = 1     # <1>: Certified satisfaction
    UNKNOWN = 2  # <2>: Incomplete evaluation / budget exhausted

    def to_wire_atom(self) -> str:
        return f"<{self.value}>"


@dataclass(frozen=True)
class KleeneEntry:
    """Individual entry in a Kleene obstruction cochain."""
    query_id: str
    val: KleeneValue
    witness: str

    def __post_init__(self) -> None:
        if not isinstance(self.query_id, str):
            raise TypeError("query_id must be a string")
        if not isinstance(self.val, KleeneValue):
            raise TypeError("val must be a KleeneValue")
        if not isinstance(self.witness, str):
            raise TypeError("witness must be a string")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, KleeneEntry)
        return (
            self.query_id == other.query_id
            and self.val == other.val
            and self.witness == other.witness
        )

    def __hash__(self) -> int:
        return hash((type(self), self.query_id, self.val, self.witness))


@dataclass(frozen=True)
class KleeneCochain:
    """Kleene-valued obstruction cochain Core."""
    entries: tuple[KleeneEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple):
            object.__setattr__(self, "entries", tuple(self.entries))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, KleeneCochain)
        return self.entries == other.entries

    def __hash__(self) -> int:
        return hash((type(self), self.entries))


@dataclass(frozen=True)
class DDAEventRecord:
    """Level 12: Proof-relevant 14-tuple DDA event record."""
    budget: int
    context_in: str
    state_in: str
    operator: str
    declared_cost: Rational
    context_out: str
    state_out: str
    digest_in: ContentDigest
    digest_out: ContentDigest
    obstruct_in: KleeneCochain
    obstruct_out: KleeneCochain
    delta_c: str
    info_receipt: str
    parent_digest: ContentDigest
    has_host_proof: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.budget, int) or isinstance(self.budget, bool) or self.budget <= 0:
            raise ValueError("budget must be a positive integer")
        if not isinstance(self.declared_cost, Rational):
            raise TypeError("declared_cost must be a Rational")
        if not isinstance(self.digest_in, ContentDigest) or not isinstance(self.digest_out, ContentDigest):
            raise TypeError("digest_in and digest_out must be ContentDigest")
        if not isinstance(self.obstruct_in, KleeneCochain) or not isinstance(self.obstruct_out, KleeneCochain):
            raise TypeError("obstruct_in and obstruct_out must be KleeneCochain")
        if not isinstance(self.parent_digest, ContentDigest):
            raise TypeError("parent_digest must be ContentDigest")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DDAEventRecord)
        return (
            self.budget == other.budget
            and self.context_in == other.context_in
            and self.state_in == other.state_in
            and self.operator == other.operator
            and self.declared_cost == other.declared_cost
            and self.context_out == other.context_out
            and self.state_out == other.state_out
            and self.digest_in == other.digest_in
            and self.digest_out == other.digest_out
            and self.obstruct_in == other.obstruct_in
            and self.obstruct_out == other.obstruct_out
            and self.delta_c == other.delta_c
            and self.info_receipt == other.info_receipt
            and self.parent_digest == other.parent_digest
            and self.has_host_proof == other.has_host_proof
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.budget,
            self.context_in,
            self.state_in,
            self.operator,
            self.declared_cost,
            self.context_out,
            self.state_out,
            self.digest_in,
            self.digest_out,
            self.obstruct_in,
            self.obstruct_out,
            self.delta_c,
            self.info_receipt,
            self.parent_digest,
            self.has_host_proof,
        ))


@dataclass(frozen=True)
class RuntimeKernel:
    """Level 12: Minimal irredundant runtime configuration (B, C, x, Core)."""
    budget: int
    context: str
    state: str
    obstruction: KleeneCochain

    def __post_init__(self) -> None:
        if not isinstance(self.budget, int) or isinstance(self.budget, bool) or self.budget <= 0:
            raise ValueError("budget must be a positive integer")
        if not isinstance(self.context, str) or not self.context:
            raise ValueError("context cannot be empty")
        if not isinstance(self.state, str) or not self.state:
            raise ValueError("state cannot be empty")
        if not isinstance(self.obstruction, KleeneCochain):
            raise TypeError("obstruction must be a KleeneCochain")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, RuntimeKernel)
        return (
            self.budget == other.budget
            and self.context == other.context
            and self.state == other.state
            and self.obstruction == other.obstruction
        )

    def __hash__(self) -> int:
        return hash((type(self), self.budget, self.context, self.state, self.obstruction))


# ---------------------------------------------------------------------------
# Level 13: Higher Alternation Ladders, Expansion Cycles, and BQNF Routes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExpansionCycleToken:
    """Level 13: Replayable expansion cycle detection token."""
    status_code: int  # 0: Progress within bounds, 1: EXPANSION_CYCLE_DETECTED
    state_digest_1: ContentDigest
    state_digest_2: ContentDigest
    step_distance: int

    def __post_init__(self) -> None:
        if self.status_code not in (0, 1):
            raise ValueError(f"status_code must be 0 or 1, got {self.status_code}")
        if not isinstance(self.state_digest_1, ContentDigest) or not isinstance(self.state_digest_2, ContentDigest):
            raise TypeError("state digests must be ContentDigest")
        if not isinstance(self.step_distance, int) or isinstance(self.step_distance, bool) or self.step_distance < 0:
            raise ValueError("step_distance must be non-negative integer")

    @property
    def is_cycle_detected(self) -> bool:
        return self.status_code == 1

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ExpansionCycleToken)
        return (
            self.status_code == other.status_code
            and self.state_digest_1 == other.state_digest_1
            and self.state_digest_2 == other.state_digest_2
            and self.step_distance == other.step_distance
        )

    def __hash__(self) -> int:
        return hash((type(self), self.status_code, self.state_digest_1, self.state_digest_2, self.step_distance))


class BQNFRoute(int, Enum):
    """The 11 discrete BQNF terminal routes."""
    PRESERVE = 0      # Delta c cap supp(boundary) == empty
    REPAIR = 1        # omega in im(d_0), exists alpha: omega = d_0 alpha
    INVALIDATE = 2    # Missing dependency CDC state or cache line
    RECOMPUTE = 3     # Non-exact local change omega notin im(d_0)
    SCHEMA_EVOLVE = 4 # Injected symbol introduces new boundary relations
    REFUSE = 5        # Violation of typed boundary constraints
    COMPENSATE = 6    # Out-of-order cochain update
    HALT = 7          # Critical invariant broken; progress blocked
    ESCALATE = 8      # Non-zero harmonic residue (h != 0), Phi_1 > 0
    QUARANTINE = 9    # Unverified external proposition
    CHECKPOINT = 10   # Invariants verified; audit state committed

    def to_token_wire(self) -> str:
        return f"<{self.value}>"


@dataclass(frozen=True)
class BQNFViewCochain:
    """Level 13: BQNF cochain defect and potential record."""
    omega: tuple[Rational, ...]
    d0_potential: Optional[tuple[Rational, ...]] = None
    d0_matrix: Optional[ExactRationalMatrix] = None
    quotient_status: str = "EXACT_ZERO"

    def __post_init__(self) -> None:
        if not isinstance(self.omega, tuple):
            object.__setattr__(self, "omega", tuple(self.omega))
        if self.d0_potential is not None and not isinstance(self.d0_potential, tuple):
            object.__setattr__(self, "d0_potential", tuple(self.d0_potential))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, BQNFViewCochain)
        return (
            self.omega == other.omega
            and self.d0_potential == other.d0_potential
            and self.d0_matrix == other.d0_matrix
            and self.quotient_status == other.quotient_status
        )

    def __hash__(self) -> int:
        return hash((type(self), self.omega, self.d0_potential, self.d0_matrix, self.quotient_status))
