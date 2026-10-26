"""Typed contracts for the cycle-balance four-object lifecycle (packets/README.md).

Objects: problem (P), candidate proposal (P'), verifier contract (V), receipt (R).
Digests are sha256 over sorted-key compact UTF-8 JSON (not a claim of RFC 8785).
Receipt digests are computed with ``receipt_digest`` set to the empty string.
A content digest binds bytes; it does not show that verification occurred.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StrictBool,
    StrictInt,
    StrictStr,
    model_validator,
)

Sha256Hex = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
NonEmptyStr = Annotated[StrictStr, Field(min_length=1)]


class QuartetBaseModel(BaseModel):
    """Strict immutable base record."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class ArithmeticDomain(str, Enum):
    EXACT_INTEGER = "EXACT_INTEGER"


class ClaimedMove(str, Enum):
    ATTACH_2CELL = "ATTACH_2CELL"


class VerificationRule(str, Enum):
    STATIC_CELL_BOUNDS_CHECK = "STATIC_CELL_BOUNDS_CHECK"
    CHAIN_COMPLEX_NILPOTENCY_CHECK = "CHAIN_COMPLEX_NILPOTENCY_CHECK"
    INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE = "INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE"


class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"


def object_digest(obj: object) -> str:
    """sha256 of sorted-key compact UTF-8 JSON."""
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class StaticCellBounds(QuartetBaseModel):
    max_vertices: Annotated[StrictInt, Field(ge=0)]
    max_edges: Annotated[StrictInt, Field(ge=0)]
    max_faces: Annotated[StrictInt, Field(ge=0)]


class Edge(QuartetBaseModel):
    id: NonEmptyStr
    source: StrictInt
    target: StrictInt


class Face(QuartetBaseModel):
    id: NonEmptyStr
    boundary_edges: list[NonEmptyStr]


class Carrier(QuartetBaseModel):
    """Carrier complex K0 = (V, E, B) with declared cell bounds."""

    name: NonEmptyStr
    vertices: list[StrictInt]
    edges: list[Edge]
    faces: list[Face]
    static_cell_bounds: StaticCellBounds

    @model_validator(mode="after")
    def _check_bounds_and_references(self) -> Carrier:
        b = self.static_cell_bounds
        if len(self.vertices) > b.max_vertices:
            raise ValueError("vertex count exceeds static_cell_bounds.max_vertices")
        if len(self.edges) > b.max_edges:
            raise ValueError("edge count exceeds static_cell_bounds.max_edges")
        if len(self.faces) > b.max_faces:
            raise ValueError("face count exceeds static_cell_bounds.max_faces")
        vertex_set = set(self.vertices)
        edge_ids = [e.id for e in self.edges]
        if len(set(edge_ids)) != len(edge_ids):
            raise ValueError("duplicate edge id")
        for e in self.edges:
            if e.source == e.target:
                raise ValueError("irreflexive carrier: edge endpoints must differ")
            if e.source not in vertex_set or e.target not in vertex_set:
                raise ValueError("edge endpoint is not a declared vertex")
        for f in self.faces:
            for ref in f.boundary_edges:
                if ref.lstrip("-") not in edge_ids:
                    raise ValueError("face boundary references an undeclared edge")
        return self


class BoundaryMatrices(QuartetBaseModel):
    """Integer boundary operators d1 (|V| x |E|) and d2 (|E| x |faces|)."""

    d1: list[list[StrictInt]]
    d2: list[list[StrictInt]]


class ActiveObstruction(QuartetBaseModel):
    cycle_z: list[StrictInt]
    cycle_edges: list[NonEmptyStr]
    d1_z: list[StrictInt]
    homology_status: VerificationStatus


class CycleBalanceProblem(QuartetBaseModel):
    """Object 1: problem / carrier contract."""

    schema_version: Literal["omega.symbol_game.cycle_balance.problem.v1"]
    problem_id: NonEmptyStr
    case_id: NonEmptyStr
    authority_effect: Literal["None"]
    arithmetic_domain: ArithmeticDomain
    carrier: Carrier
    boundary_matrices: BoundaryMatrices
    active_obstruction: ActiveObstruction

    @model_validator(mode="after")
    def _check_chain_complex(self) -> CycleBalanceProblem:
        n_v = len(self.carrier.vertices)
        n_e = len(self.carrier.edges)
        n_f = len(self.carrier.faces)
        d1, d2 = self.boundary_matrices.d1, self.boundary_matrices.d2
        if len(d1) != n_v or any(len(r) != n_e for r in d1):
            raise ValueError("d1 must be |V| x |E|")
        if len(d2) != n_e or any(len(r) != n_f for r in d2):
            raise ValueError("d2 must be |E| x |faces|")
        for i in range(n_v):
            for j in range(n_f):
                if sum(d1[i][k] * d2[k][j] for k in range(n_e)) != 0:
                    raise ValueError("chain law violated: d1 * d2 != 0")
        z = self.active_obstruction.cycle_z
        if len(z) != n_e:
            raise ValueError("cycle_z length must equal edge count")
        d1z = [sum(d1[i][k] * z[k] for k in range(n_e)) for i in range(n_v)]
        if d1z != self.active_obstruction.d1_z:
            raise ValueError("d1_z does not equal d1 * cycle_z")
        if any(d1z):
            raise ValueError("cycle_z is not in ker d1")
        edge_ids = {e.id for e in self.carrier.edges}
        if not set(self.active_obstruction.cycle_edges) <= edge_ids:
            raise ValueError("cycle_edges references an undeclared edge")
        return self

    def to_domain(self) -> Any:
        """Convert wire schema to domain ProblemEntity."""
        from ..entities.cycle_balance import ProblemEntity
        from ..value_objects.cycle_balance import (
            ActiveObstructionVO,
            BoundaryMatricesVO,
            CarrierEdgeVO,
            CarrierFaceVO,
            CarrierVO,
            StaticCellBoundsVO,
        )
        from ..value_objects.identifiers import CaseId, ProblemId
        from ..value_objects.taxonomy import ArithmeticDomainVO, VerificationStatusVO

        carrier_vo = CarrierVO(
            name=self.carrier.name,
            vertices=tuple(self.carrier.vertices),
            edges=tuple(CarrierEdgeVO(id=e.id, source=e.source, target=e.target) for e in self.carrier.edges),
            faces=tuple(CarrierFaceVO(id=f.id, boundary_edges=tuple(f.boundary_edges)) for f in self.carrier.faces),
            static_cell_bounds=StaticCellBoundsVO(
                max_vertices=self.carrier.static_cell_bounds.max_vertices,
                max_edges=self.carrier.static_cell_bounds.max_edges,
                max_faces=self.carrier.static_cell_bounds.max_faces,
            ),
        )
        return ProblemEntity(
            id=ProblemId(self.problem_id),
            case_id=CaseId(self.case_id),
            carrier=carrier_vo,
            boundary_matrices=BoundaryMatricesVO(
                d1=tuple(tuple(r) for r in self.boundary_matrices.d1),
                d2=tuple(tuple(r) for r in self.boundary_matrices.d2),
            ),
            active_obstruction=ActiveObstructionVO(
                cycle_z=tuple(self.active_obstruction.cycle_z),
                cycle_edges=tuple(self.active_obstruction.cycle_edges),
                d1_z=tuple(self.active_obstruction.d1_z),
                homology_status=VerificationStatusVO(self.active_obstruction.homology_status.value),
            ),
            arithmetic_domain=ArithmeticDomainVO(self.arithmetic_domain.value),
        )

    @classmethod
    def from_domain(cls, entity: Any) -> CycleBalanceProblem:
        """Construct wire schema model from domain ProblemEntity."""
        d = entity.to_canonical_dict()
        d["arithmetic_domain"] = ArithmeticDomain(d["arithmetic_domain"])
        d["active_obstruction"]["homology_status"] = VerificationStatus(d["active_obstruction"]["homology_status"])
        return cls.model_validate(d)




class CycleBalanceCandidate(QuartetBaseModel):
    """Object 2: untrusted candidate proposal; never self-certifying."""

    schema_version: Literal["omega.symbol_game.cycle_balance.candidate.v1"]
    candidate_id: NonEmptyStr
    problem_digest: Sha256Hex
    authority_effect: Literal["None"]
    claimed_move: ClaimedMove
    repair_face_name: NonEmptyStr
    constituent_edges: list[Annotated[StrictStr, Field(pattern=r"^[^:\s]+:-?\d+->-?\d+$")]]
    repair_boundary_column: list[StrictInt]
    preserves_chain_law: StrictBool
    claimed_integer_preimage_c: list[StrictInt]
    claimed_h1_status: NonEmptyStr

    def to_domain(self) -> Any:
        """Convert wire schema to domain CandidateEntity."""
        from ..entities.cycle_balance import CandidateEntity
        from ..value_objects.identifiers import CandidateId, Sha256Digest
        from ..value_objects.taxonomy import ClaimedMoveVO

        return CandidateEntity(
            id=CandidateId(self.candidate_id),
            problem_digest=Sha256Digest(self.problem_digest),
            claimed_move=ClaimedMoveVO(self.claimed_move.value),
            repair_face_name=self.repair_face_name,
            constituent_edges=tuple(self.constituent_edges),
            repair_boundary_column=tuple(self.repair_boundary_column),
            preserves_chain_law=self.preserves_chain_law,
            claimed_integer_preimage_c=tuple(self.claimed_integer_preimage_c),
            claimed_h1_status=self.claimed_h1_status,
        )

    @classmethod
    def from_domain(cls, entity: Any) -> CycleBalanceCandidate:
        """Construct wire schema model from domain CandidateEntity."""
        d = entity.to_canonical_dict()
        d["claimed_move"] = ClaimedMove(d["claimed_move"])
        return cls.model_validate(d)




class CycleBalanceVerifier(QuartetBaseModel):
    """Object 3: deterministic host verifier contract."""

    schema_version: Literal["omega.symbol_game.cycle_balance.verifier.v1"]
    verifier_id: NonEmptyStr
    arithmetic_domain: ArithmeticDomain
    problem_digest: Sha256Hex
    verification_rules: Annotated[list[VerificationRule], Field(min_length=1)]
    static_bounds: StaticCellBounds

    @model_validator(mode="after")
    def _rules_unique(self) -> CycleBalanceVerifier:
        if len(set(self.verification_rules)) != len(self.verification_rules):
            raise ValueError("duplicate verification rule")
        return self

    def to_domain(self) -> Any:
        """Convert wire schema to domain VerifierEntity."""
        from ..entities.cycle_balance import VerifierEntity
        from ..value_objects.cycle_balance import StaticCellBoundsVO
        from ..value_objects.identifiers import Sha256Digest, VerifierId
        from ..value_objects.taxonomy import ArithmeticDomainVO, VerificationRuleVO

        return VerifierEntity(
            id=VerifierId(self.verifier_id),
            problem_digest=Sha256Digest(self.problem_digest),
            verification_rules=tuple(VerificationRuleVO(r.value) for r in self.verification_rules),
            static_bounds=StaticCellBoundsVO(
                max_vertices=self.static_bounds.max_vertices,
                max_edges=self.static_bounds.max_edges,
                max_faces=self.static_bounds.max_faces,
            ),
            arithmetic_domain=ArithmeticDomainVO(self.arithmetic_domain.value),
        )

    @classmethod
    def from_domain(cls, entity: Any) -> CycleBalanceVerifier:
        """Construct wire schema model from domain VerifierEntity."""
        d = entity.to_canonical_dict()
        d["arithmetic_domain"] = ArithmeticDomain(d["arithmetic_domain"])
        d["verification_rules"] = [VerificationRule(r) for r in d["verification_rules"]]
        return cls.model_validate(d)




class ClaimHygiene(QuartetBaseModel):
    what_it_supports: NonEmptyStr
    what_it_does_not_support: NonEmptyStr
    next_test_needed: NonEmptyStr


class CycleBalanceReceipt(QuartetBaseModel):
    """Object 4: receipt envelope. An UNVERIFIED skeleton carries no verdict fields."""

    schema_version: Literal["omega.symbol_game.cycle_balance.receipt.v1"]
    receipt_id: NonEmptyStr
    authority_effect: Literal["None"]
    problem_digest: Sha256Hex
    candidate_digest: Sha256Hex
    verifier_digest: Sha256Hex
    verification_status: VerificationStatus
    terminal_status: StrictStr | None
    residuals: JsonValue | None
    exact_witness: JsonValue | None
    claim_hygiene: ClaimHygiene
    receipt_digest: Sha256Hex

    @model_validator(mode="after")
    def _unverified_skeleton_is_empty(self) -> CycleBalanceReceipt:
        if self.verification_status is VerificationStatus.UNVERIFIED and (
            self.terminal_status is not None
            or self.residuals is not None
            or self.exact_witness is not None
        ):
            raise ValueError("UNVERIFIED receipt must have null terminal_status, residuals, exact_witness")
        return self

    def to_domain(self) -> Any:
        """Convert wire schema to domain ReceiptEntity."""
        from ..entities.cycle_balance import ReceiptEntity
        from ..value_objects.cycle_balance import ClaimHygieneVO
        from ..value_objects.identifiers import ReceiptId, Sha256Digest
        from ..value_objects.taxonomy import VerificationStatusVO

        return ReceiptEntity(
            id=ReceiptId(self.receipt_id),
            problem_digest=Sha256Digest(self.problem_digest),
            candidate_digest=Sha256Digest(self.candidate_digest),
            verifier_digest=Sha256Digest(self.verifier_digest),
            verification_status=VerificationStatusVO(self.verification_status.value),
            terminal_status=self.terminal_status,
            residuals=self.residuals,
            exact_witness=self.exact_witness,
            claim_hygiene=ClaimHygieneVO(
                what_it_supports=self.claim_hygiene.what_it_supports,
                what_it_does_not_support=self.claim_hygiene.what_it_does_not_support,
                next_test_needed=self.claim_hygiene.next_test_needed,
            ),
            receipt_digest=Sha256Digest(self.receipt_digest) if self.receipt_digest else None,
        )

    @classmethod
    def from_domain(cls, entity: Any) -> CycleBalanceReceipt:
        """Construct wire schema model from domain ReceiptEntity."""
        d = entity.to_canonical_dict(include_receipt_digest=True)
        d["verification_status"] = VerificationStatus(d["verification_status"])
        return cls.model_validate(d)



class CycleBalanceQuartet(BaseModel):
    """The four objects with cross-object digest bindings."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    problem: CycleBalanceProblem
    candidate: CycleBalanceCandidate
    verifier: CycleBalanceVerifier
    receipt: CycleBalanceReceipt

    def to_domain(self) -> Any:
        """Convert wire schema quartet to domain CycleBalanceQuartetAggregate."""
        from ..aggregates.cycle_balance_aggregate import CycleBalanceQuartetAggregate

        return CycleBalanceQuartetAggregate(
            problem=self.problem.to_domain(),
            candidate=self.candidate.to_domain(),
            verifier=self.verifier.to_domain(),
            receipt=self.receipt.to_domain(),
        )

    @classmethod
    def from_domain(cls, agg: Any) -> CycleBalanceQuartet:
        """Construct wire schema quartet from domain CycleBalanceQuartetAggregate."""
        if agg.problem is None or agg.candidate is None or agg.verifier is None or agg.receipt is None:
            raise ValueError("All four quartet entities must be present to serialize to wire DTO")
        return cls(
            problem=CycleBalanceProblem.from_domain(agg.problem),
            candidate=CycleBalanceCandidate.from_domain(agg.candidate),
            verifier=CycleBalanceVerifier.from_domain(agg.verifier),
            receipt=CycleBalanceReceipt.from_domain(agg.receipt),
        )

    def check_digest_bindings(self, raw: dict[str, dict[str, object]]) -> bool:
        """True iff digests link problem, candidate, verifier and receipt.

        ``raw`` maps the keys problem/candidate/verifier/receipt to the original JSON objects.
        A matching digest binds bytes only; it is not verification.
        """
        pd = object_digest(raw["problem"])
        cd = object_digest(raw["candidate"])
        vd = object_digest(raw["verifier"])
        receipt_raw = dict(raw["receipt"])
        receipt_raw["receipt_digest"] = ""
        return (
            self.candidate.problem_digest == pd
            and self.verifier.problem_digest == pd
            and self.receipt.problem_digest == pd
            and self.receipt.candidate_digest == cd
            and self.receipt.verifier_digest == vd
            and self.receipt.receipt_digest == object_digest(receipt_raw)
        )

