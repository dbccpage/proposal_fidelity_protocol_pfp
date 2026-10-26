"""Domain Entities for Cycle Balance Four-Object Lifecycle.

AuthorityEffect: None.
Governing standards: Clean Architecture DDD, RULE_VO_EXACT_TYPE_EQUALITY_001.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Optional, Tuple

from ..value_objects.cycle_balance import (
    ActiveObstructionVO,
    BoundaryMatricesVO,
    CarrierVO,
    ClaimHygieneVO,
    StaticCellBoundsVO,
)
from ..value_objects.identifiers import (
    CandidateId,
    CaseId,
    ProblemId,
    ReceiptId,
    Sha256Digest,
    VerifierId,
)
from ..value_objects.taxonomy import (
    ArithmeticDomainVO,
    ClaimedMoveVO,
    VerificationRuleVO,
    VerificationStatusVO,
)
from .base import Entity


def _canonical_json_digest(obj: Any) -> Sha256Digest:
    """sha256 of sorted-key compact UTF-8 JSON."""
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return Sha256Digest(hashlib.sha256(raw.encode("utf-8")).hexdigest())


@dataclass
class ProblemEntity(Entity):
    """Object 1: Topological Problem & Carrier Contract Entity.

    Encapsulates carrier complex K0 = (V, E, B), boundary matrices d1, d2,
    and active non-exact 1-cycle obstruction z.
    """

    id: ProblemId
    case_id: CaseId
    carrier: CarrierVO
    boundary_matrices: BoundaryMatricesVO
    active_obstruction: ActiveObstructionVO
    arithmetic_domain: ArithmeticDomainVO = ArithmeticDomainVO("EXACT_INTEGER")

    def __post_init__(self) -> None:
        if isinstance(self.id, str):
            self.id = ProblemId(self.id)
        elif not isinstance(self.id, ProblemId):
            raise TypeError(f"ProblemEntity.id must be ProblemId, got {type(self.id).__name__}")

        if isinstance(self.case_id, str):
            self.case_id = CaseId(self.case_id)
        elif not isinstance(self.case_id, CaseId):
            raise TypeError(f"ProblemEntity.case_id must be CaseId, got {type(self.case_id).__name__}")

        if not isinstance(self.carrier, CarrierVO):
            raise TypeError(f"carrier must be CarrierVO, got {type(self.carrier).__name__}")

        if not isinstance(self.boundary_matrices, BoundaryMatricesVO):
            raise TypeError(f"boundary_matrices must be BoundaryMatricesVO, got {type(self.boundary_matrices).__name__}")

        if not isinstance(self.active_obstruction, ActiveObstructionVO):
            raise TypeError(f"active_obstruction must be ActiveObstructionVO, got {type(self.active_obstruction).__name__}")

        self.validate_invariants()

    def validate_invariants(self) -> None:
        """Enforce chain complex nilpotency and cycle membership in ker d1."""
        n_v = len(self.carrier.vertices)
        n_e = len(self.carrier.edges)
        n_f = len(self.carrier.faces)
        d1 = self.boundary_matrices.d1
        d2 = self.boundary_matrices.d2

        if len(d1) != n_v or any(len(r) != n_e for r in d1):
            raise ValueError(f"d1 must have shape {n_v} x {n_e}")
        if len(d2) != n_e or any(len(r) != n_f for r in d2):
            raise ValueError(f"d2 must have shape {n_e} x {n_f}")

        # Chain complex nilpotency: d1 * d2 == 0
        for i in range(n_v):
            for j in range(n_f):
                entry = sum(d1[i][k] * d2[k][j] for k in range(n_e))
                if entry != 0:
                    raise ValueError(f"chain law violated: (d1 * d2)[{i}, {j}] = {entry} != 0")

        # Obstruction check: d1 * z == 0
        z = self.active_obstruction.cycle_z
        if len(z) != n_e:
            raise ValueError(f"cycle_z length ({len(z)}) must equal edge count ({n_e})")

        d1z = tuple(sum(d1[i][k] * z[k] for k in range(n_e)) for i in range(n_v))
        if d1z != self.active_obstruction.d1_z:
            raise ValueError("active_obstruction.d1_z does not match d1 * cycle_z")
        if any(d1z):
            raise ValueError(f"cycle_z is not in ker d1: d1 * z = {d1z}")

        edge_ids = {e.id for e in self.carrier.edges}
        if not set(self.active_obstruction.cycle_edges).issubset(edge_ids):
            raise ValueError("active_obstruction references undeclared edge")

    def to_canonical_dict(self) -> dict[str, Any]:
        """Convert to RFC 8785 / canonical serialization dictionary."""
        return {
            "schema_version": "omega.symbol_game.cycle_balance.problem.v1",
            "problem_id": self.id.value,
            "case_id": self.case_id.value,
            "authority_effect": "None",
            "arithmetic_domain": self.arithmetic_domain.value,
            "carrier": {
                "name": self.carrier.name,
                "vertices": list(self.carrier.vertices),
                "edges": [{"id": e.id, "source": e.source, "target": e.target} for e in self.carrier.edges],
                "faces": [{"id": f.id, "boundary_edges": list(f.boundary_edges)} for f in self.carrier.faces],
                "static_cell_bounds": {
                    "max_vertices": self.carrier.static_cell_bounds.max_vertices,
                    "max_edges": self.carrier.static_cell_bounds.max_edges,
                    "max_faces": self.carrier.static_cell_bounds.max_faces,
                },
            },
            "boundary_matrices": {
                "d1": [list(r) for r in self.boundary_matrices.d1],
                "d2": [list(r) for r in self.boundary_matrices.d2],
            },
            "active_obstruction": {
                "cycle_z": list(self.active_obstruction.cycle_z),
                "cycle_edges": list(self.active_obstruction.cycle_edges),
                "d1_z": list(self.active_obstruction.d1_z),
                "homology_status": self.active_obstruction.homology_status.value,
            },
        }

    def compute_digest(self) -> Sha256Digest:
        """Compute authoritative content digest for this problem."""
        return _canonical_json_digest(self.to_canonical_dict())


@dataclass
class CandidateEntity(Entity):
    """Object 2: Untrusted Candidate Proposal Entity.

    Proposes a repair face / 2-cell attachment to resolve active obstruction cycle z.
    Never self-certifying.
    """

    id: CandidateId
    problem_digest: Sha256Digest
    claimed_move: ClaimedMoveVO
    repair_face_name: str
    constituent_edges: Tuple[str, ...]
    repair_boundary_column: Tuple[int, ...]
    preserves_chain_law: bool
    claimed_integer_preimage_c: Tuple[int, ...]
    claimed_h1_status: str

    def __post_init__(self) -> None:
        if isinstance(self.id, str):
            self.id = CandidateId(self.id)
        elif not isinstance(self.id, CandidateId):
            raise TypeError(f"CandidateEntity.id must be CandidateId, got {type(self.id).__name__}")

        if isinstance(self.problem_digest, str):
            self.problem_digest = Sha256Digest(self.problem_digest)
        elif not isinstance(self.problem_digest, Sha256Digest):
            raise TypeError(f"problem_digest must be Sha256Digest, got {type(self.problem_digest).__name__}")

        if isinstance(self.claimed_move, str):
            self.claimed_move = ClaimedMoveVO(self.claimed_move)
        elif not isinstance(self.claimed_move, ClaimedMoveVO):
            raise TypeError(f"claimed_move must be ClaimedMoveVO, got {type(self.claimed_move).__name__}")

        if isinstance(self.constituent_edges, list):
            self.constituent_edges = tuple(self.constituent_edges)
        if isinstance(self.repair_boundary_column, list):
            self.repair_boundary_column = tuple(self.repair_boundary_column)
        if isinstance(self.claimed_integer_preimage_c, list):
            self.claimed_integer_preimage_c = tuple(self.claimed_integer_preimage_c)

    def binds_to_problem(self, problem: ProblemEntity) -> bool:
        """Verify that candidate binds cryptographically to the problem."""
        return self.problem_digest == problem.compute_digest()

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "omega.symbol_game.cycle_balance.candidate.v1",
            "candidate_id": self.id.value,
            "problem_digest": self.problem_digest.value,
            "authority_effect": "None",
            "claimed_move": self.claimed_move.value,
            "repair_face_name": self.repair_face_name,
            "constituent_edges": list(self.constituent_edges),
            "repair_boundary_column": list(self.repair_boundary_column),
            "preserves_chain_law": bool(self.preserves_chain_law),
            "claimed_integer_preimage_c": list(self.claimed_integer_preimage_c),
            "claimed_h1_status": self.claimed_h1_status,
        }

    def compute_digest(self) -> Sha256Digest:
        """Compute authoritative content digest for this candidate proposal."""
        return _canonical_json_digest(self.to_canonical_dict())


@dataclass
class VerifierEntity(Entity):
    """Object 3: Deterministic Host Verifier Contract Entity."""

    id: VerifierId
    problem_digest: Sha256Digest
    verification_rules: Tuple[VerificationRuleVO, ...]
    static_bounds: StaticCellBoundsVO
    arithmetic_domain: ArithmeticDomainVO = ArithmeticDomainVO("EXACT_INTEGER")

    def __post_init__(self) -> None:
        if isinstance(self.id, str):
            self.id = VerifierId(self.id)
        elif not isinstance(self.id, VerifierId):
            raise TypeError(f"VerifierEntity.id must be VerifierId, got {type(self.id).__name__}")

        if isinstance(self.problem_digest, str):
            self.problem_digest = Sha256Digest(self.problem_digest)
        elif not isinstance(self.problem_digest, Sha256Digest):
            raise TypeError(f"problem_digest must be Sha256Digest, got {type(self.problem_digest).__name__}")

        if isinstance(self.verification_rules, list):
            self.verification_rules = tuple(
                VerificationRuleVO(r) if isinstance(r, str) else r for r in self.verification_rules
            )
        if len(self.verification_rules) == 0:
            raise ValueError("VerifierEntity must declare at least one verification rule")
        if len(set(self.verification_rules)) != len(self.verification_rules):
            raise ValueError("duplicate verification rule in verifier")

        if not isinstance(self.static_bounds, StaticCellBoundsVO):
            raise TypeError(f"static_bounds must be StaticCellBoundsVO, got {type(self.static_bounds).__name__}")

    def binds_to_problem(self, problem: ProblemEntity) -> bool:
        """Verify that verifier binds cryptographically to the problem."""
        return self.problem_digest == problem.compute_digest()

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "omega.symbol_game.cycle_balance.verifier.v1",
            "verifier_id": self.id.value,
            "arithmetic_domain": self.arithmetic_domain.value,
            "problem_digest": self.problem_digest.value,
            "verification_rules": [r.value for r in self.verification_rules],
            "static_bounds": {
                "max_vertices": self.static_bounds.max_vertices,
                "max_edges": self.static_bounds.max_edges,
                "max_faces": self.static_bounds.max_faces,
            },
        }

    def compute_digest(self) -> Sha256Digest:
        """Compute authoritative content digest for this verifier contract."""
        return _canonical_json_digest(self.to_canonical_dict())


@dataclass
class ReceiptEntity(Entity):
    """Object 4: Deterministic Host Receipt Entity."""

    id: ReceiptId
    problem_digest: Sha256Digest
    candidate_digest: Sha256Digest
    verifier_digest: Sha256Digest
    verification_status: VerificationStatusVO
    claim_hygiene: ClaimHygieneVO
    terminal_status: Optional[str] = None
    residuals: Optional[Any] = None
    exact_witness: Optional[Any] = None
    receipt_digest: Optional[Sha256Digest] = None

    def __post_init__(self) -> None:
        if isinstance(self.id, str):
            self.id = ReceiptId(self.id)
        elif not isinstance(self.id, ReceiptId):
            raise TypeError(f"ReceiptEntity.id must be ReceiptId, got {type(self.id).__name__}")

        for attr in ("problem_digest", "candidate_digest", "verifier_digest"):
            val = getattr(self, attr)
            if isinstance(val, str):
                setattr(self, attr, Sha256Digest(val))
            elif not isinstance(val, Sha256Digest):
                raise TypeError(f"{attr} must be Sha256Digest, got {type(val).__name__}")

        if isinstance(self.verification_status, str):
            self.verification_status = VerificationStatusVO(self.verification_status)
        elif not isinstance(self.verification_status, VerificationStatusVO):
            raise TypeError(f"verification_status must be VerificationStatusVO, got {type(self.verification_status).__name__}")

        if not isinstance(self.claim_hygiene, ClaimHygieneVO):
            raise TypeError(f"claim_hygiene must be ClaimHygieneVO, got {type(self.claim_hygiene).__name__}")

        if not self.verification_status.is_verified:
            if self.terminal_status is not None or self.residuals is not None or self.exact_witness is not None:
                raise ValueError("UNVERIFIED receipt must have None terminal_status, residuals, exact_witness")

        if self.receipt_digest is None:
            self.receipt_digest = self.compute_digest()
        elif isinstance(self.receipt_digest, str):
            self.receipt_digest = Sha256Digest(self.receipt_digest)

    def binds_to_problem(self, problem: ProblemEntity) -> bool:
        return self.problem_digest == problem.compute_digest()

    def binds_to_candidate(self, candidate: CandidateEntity) -> bool:
        return self.candidate_digest == candidate.compute_digest()

    def binds_to_verifier(self, verifier: VerifierEntity) -> bool:
        return self.verifier_digest == verifier.compute_digest()

    def to_canonical_dict(self, include_receipt_digest: bool = True) -> dict[str, Any]:
        return {
            "schema_version": "omega.symbol_game.cycle_balance.receipt.v1",
            "receipt_id": self.id.value,
            "authority_effect": "None",
            "problem_digest": self.problem_digest.value,
            "candidate_digest": self.candidate_digest.value,
            "verifier_digest": self.verifier_digest.value,
            "verification_status": self.verification_status.value,
            "terminal_status": self.terminal_status,
            "residuals": self.residuals,
            "exact_witness": self.exact_witness,
            "claim_hygiene": {
                "what_it_supports": self.claim_hygiene.what_it_supports,
                "what_it_does_not_support": self.claim_hygiene.what_it_does_not_support,
                "next_test_needed": self.claim_hygiene.next_test_needed,
            },
            "receipt_digest": self.receipt_digest.value if (include_receipt_digest and self.receipt_digest) else "",
        }

    def compute_digest(self) -> Sha256Digest:
        """Compute digest over receipt dictionary with receipt_digest set to empty string."""
        d = self.to_canonical_dict(include_receipt_digest=False)
        return _canonical_json_digest(d)
