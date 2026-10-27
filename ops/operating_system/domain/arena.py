"""Solver arena policy domain models for OEOS governed tasks.

CompetitorSpecV1, CorpusManifestV1, TrialReceiptV1, ScorecardV1,
RoutingPolicyProposalV1, and AdmittedPolicyV1 implement the data model for the
Solver Arena Policy Bridge (solver_arena_policy_bridge.contract.yaml).

Invariants:
- Every competitor and corpus case binds exact implementation, lineage,
  route, budget, memory, and anti-skill digests (SAP-INV-001).
- Holdout scoring uses independent deterministic tests rather than an LLM judge (SAP-INV-002).
- Arena output remains a proposal until a human admits one exact scoped and
  expiring policy digest (SAP-INV-003).
- Self-admission is strictly forbidden: a Pareto scorecard does NOT admit a
  runtime policy, and RoutingPolicyProposalV1.is_admitted cannot be True.
- Only a human approver URN can instantiate AdmittedPolicyV1.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from .task import (
    TaskInvariantError,
    _ExactTypeValue,
    _require_digest,
    _require_exact_int,
    _require_exact_str,
    _require_timestamp,
    _IDENTIFIER,
    _SCOPED_IDENTIFIER,
    digest_payload,
)

SCHEMA_COMPETITOR_SPEC = "core.oeos.competitor-spec.v1"
SCHEMA_CORPUS_MANIFEST = "core.oeos.corpus-manifest.v1"
SCHEMA_TRIAL_RECEIPT = "core.oeos.trial-receipt.v1"
SCHEMA_SCORECARD = "core.oeos.scorecard.v1"
SCHEMA_ROUTING_POLICY_PROPOSAL = "core.oeos.routing-policy-proposal.v1"
SCHEMA_ADMITTED_POLICY = "core.oeos.admitted-policy.v1"

_HUMAN_URN = re.compile(r"urn:(?:core:)?human:[A-Za-z0-9._:-]{1,128}\Z")


@dataclass(frozen=True, slots=True, eq=False)
class CompetitorSpecV1(_ExactTypeValue):
    """Specification of an isolated arena solver competitor."""

    competitor_id: str
    implementation_digest: str
    lineage_digest: str
    route_digest: str
    budget_microunits: int
    anti_skill_digests: tuple[str, ...]
    created_at_utc: str
    schema: str = SCHEMA_COMPETITOR_SPEC
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_COMPETITOR_SPEC:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "competitor spec schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "competitor specs grant no authority",
            )
        _require_exact_str(self.competitor_id, "competitor_id", _IDENTIFIER)
        _require_digest(self.implementation_digest, "implementation_digest")
        _require_digest(self.lineage_digest, "lineage_digest")
        _require_digest(self.route_digest, "route_digest")
        _require_exact_int(
            self.budget_microunits, "budget_microunits", 1, 1_000_000_000_000
        )
        _require_timestamp(self.created_at_utc, "created_at_utc")

        if type(self.anti_skill_digests) is not tuple or any(
            type(d) is not str for d in self.anti_skill_digests
        ):
            raise TaskInvariantError(
                "INVALID_ANTI_SKILLS",
                "anti_skill_digests must be a tuple of digest strings",
            )
        for d in self.anti_skill_digests:
            _require_digest(d, "anti_skill_digest")
        if (
            tuple(sorted(set(self.anti_skill_digests)))
            != self.anti_skill_digests
        ):
            raise TaskInvariantError(
                "INVALID_ANTI_SKILLS",
                "anti_skill_digests must be sorted and unique",
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "anti_skill_digests": list(self.anti_skill_digests),
            "authority_effect": self.authority_effect,
            "budget_microunits": self.budget_microunits,
            "competitor_id": self.competitor_id,
            "created_at_utc": self.created_at_utc,
            "implementation_digest": self.implementation_digest,
            "lineage_digest": self.lineage_digest,
            "route_digest": self.route_digest,
            "schema": self.schema,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        competitor_id: str,
        implementation_digest: str,
        lineage_digest: str,
        route_digest: str,
        budget_microunits: int,
        anti_skill_digests: tuple[str, ...],
        created_at_utc: str,
    ) -> CompetitorSpecV1:
        return cls(
            competitor_id=competitor_id,
            implementation_digest=implementation_digest,
            lineage_digest=lineage_digest,
            route_digest=route_digest,
            budget_microunits=budget_microunits,
            anti_skill_digests=anti_skill_digests,
            created_at_utc=created_at_utc,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> CompetitorSpecV1:
        expected = {
            "anti_skill_digests",
            "authority_effect",
            "budget_microunits",
            "competitor_id",
            "created_at_utc",
            "implementation_digest",
            "lineage_digest",
            "route_digest",
            "schema",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_COMPETITOR_SPEC",
                "competitor spec fields differ",
            )
        raw_anti = value["anti_skill_digests"]
        if type(raw_anti) is not list:
            raise TaskInvariantError(
                "INVALID_ANTI_SKILLS",
                "anti_skill_digests must be a list in canonical form",
            )
        return cls(
            competitor_id=value["competitor_id"],  # type: ignore[arg-type]
            implementation_digest=value["implementation_digest"],  # type: ignore[arg-type]
            lineage_digest=value["lineage_digest"],  # type: ignore[arg-type]
            route_digest=value["route_digest"],  # type: ignore[arg-type]
            budget_microunits=value["budget_microunits"],  # type: ignore[arg-type]
            anti_skill_digests=tuple(raw_anti),
            created_at_utc=value["created_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class CorpusManifestV1(_ExactTypeValue):
    """Manifest of test or holdout evaluation cases."""

    manifest_id: str
    corpus_name: str
    case_count: int
    cases_digest: str
    is_holdout: bool
    created_at_utc: str
    schema: str = SCHEMA_CORPUS_MANIFEST
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_CORPUS_MANIFEST:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "corpus manifest schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "corpus manifests grant no authority",
            )
        _require_exact_str(self.manifest_id, "manifest_id", _IDENTIFIER)
        _require_exact_str(self.corpus_name, "corpus_name", _SCOPED_IDENTIFIER)
        _require_exact_int(self.case_count, "case_count", 1, 1_000_000)
        _require_digest(self.cases_digest, "cases_digest")
        if type(self.is_holdout) is not bool:
            raise TaskInvariantError(
                "INVALID_HOLDOUT_FLAG", "is_holdout must be an exact bool"
            )
        _require_timestamp(self.created_at_utc, "created_at_utc")

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "case_count": self.case_count,
            "cases_digest": self.cases_digest,
            "corpus_name": self.corpus_name,
            "created_at_utc": self.created_at_utc,
            "is_holdout": self.is_holdout,
            "manifest_id": self.manifest_id,
            "schema": self.schema,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        manifest_id: str,
        corpus_name: str,
        case_count: int,
        cases_digest: str,
        is_holdout: bool,
        created_at_utc: str,
    ) -> CorpusManifestV1:
        return cls(
            manifest_id=manifest_id,
            corpus_name=corpus_name,
            case_count=case_count,
            cases_digest=cases_digest,
            is_holdout=is_holdout,
            created_at_utc=created_at_utc,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> CorpusManifestV1:
        expected = {
            "authority_effect",
            "case_count",
            "cases_digest",
            "corpus_name",
            "created_at_utc",
            "is_holdout",
            "manifest_id",
            "schema",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_CORPUS_MANIFEST",
                "corpus manifest fields differ",
            )
        return cls(
            manifest_id=value["manifest_id"],  # type: ignore[arg-type]
            corpus_name=value["corpus_name"],  # type: ignore[arg-type]
            case_count=value["case_count"],  # type: ignore[arg-type]
            cases_digest=value["cases_digest"],  # type: ignore[arg-type]
            is_holdout=value["is_holdout"],  # type: ignore[arg-type]
            created_at_utc=value["created_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class TrialReceiptV1(_ExactTypeValue):
    """Receipt of an independent deterministic trial run on a corpus."""

    trial_id: str
    competitor_id: str
    corpus_manifest_digest: str
    passed_case_count: int
    total_case_count: int
    trial_evidence_digest: str
    completed_at_utc: str
    schema: str = SCHEMA_TRIAL_RECEIPT
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_TRIAL_RECEIPT:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "trial receipt schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "trial receipts grant no authority",
            )
        _require_exact_str(self.trial_id, "trial_id", _IDENTIFIER)
        _require_exact_str(self.competitor_id, "competitor_id", _IDENTIFIER)
        _require_digest(
            self.corpus_manifest_digest, "corpus_manifest_digest"
        )
        _require_exact_int(
            self.passed_case_count, "passed_case_count", 0, 1_000_000
        )
        _require_exact_int(
            self.total_case_count, "total_case_count", 1, 1_000_000
        )
        if self.passed_case_count > self.total_case_count:
            raise TaskInvariantError(
                "INVALID_CASE_COUNTS",
                f"passed_case_count {self.passed_case_count} exceeds total_case_count {self.total_case_count}",
            )
        _require_digest(
            self.trial_evidence_digest, "trial_evidence_digest"
        )
        _require_timestamp(self.completed_at_utc, "completed_at_utc")

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "competitor_id": self.competitor_id,
            "completed_at_utc": self.completed_at_utc,
            "corpus_manifest_digest": self.corpus_manifest_digest,
            "passed_case_count": self.passed_case_count,
            "schema": self.schema,
            "total_case_count": self.total_case_count,
            "trial_evidence_digest": self.trial_evidence_digest,
            "trial_id": self.trial_id,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        trial_id: str,
        competitor_id: str,
        corpus_manifest_digest: str,
        passed_case_count: int,
        total_case_count: int,
        trial_evidence_digest: str,
        completed_at_utc: str,
    ) -> TrialReceiptV1:
        return cls(
            trial_id=trial_id,
            competitor_id=competitor_id,
            corpus_manifest_digest=corpus_manifest_digest,
            passed_case_count=passed_case_count,
            total_case_count=total_case_count,
            trial_evidence_digest=trial_evidence_digest,
            completed_at_utc=completed_at_utc,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> TrialReceiptV1:
        expected = {
            "authority_effect",
            "competitor_id",
            "completed_at_utc",
            "corpus_manifest_digest",
            "passed_case_count",
            "schema",
            "total_case_count",
            "trial_evidence_digest",
            "trial_id",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_TRIAL_RECEIPT",
                "trial receipt fields differ",
            )
        return cls(
            trial_id=value["trial_id"],  # type: ignore[arg-type]
            competitor_id=value["competitor_id"],  # type: ignore[arg-type]
            corpus_manifest_digest=value["corpus_manifest_digest"],  # type: ignore[arg-type]
            passed_case_count=value["passed_case_count"],  # type: ignore[arg-type]
            total_case_count=value["total_case_count"],  # type: ignore[arg-type]
            trial_evidence_digest=value["trial_evidence_digest"],  # type: ignore[arg-type]
            completed_at_utc=value["completed_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class ScorecardV1(_ExactTypeValue):
    """Pareto scorecard summarizing trials without admitting policy authority."""

    scorecard_id: str
    trial_receipt_digests: tuple[str, ...]
    pareto_rank: int
    evaluated_at_utc: str
    schema: str = SCHEMA_SCORECARD
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_SCORECARD:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "scorecard schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "a pareto scorecard does not admit a runtime policy",
            )
        _require_exact_str(self.scorecard_id, "scorecard_id", _IDENTIFIER)
        _require_exact_int(self.pareto_rank, "pareto_rank", 1, 100_000)
        _require_timestamp(self.evaluated_at_utc, "evaluated_at_utc")

        if type(self.trial_receipt_digests) is not tuple or not self.trial_receipt_digests:
            raise TaskInvariantError(
                "INVALID_TRIAL_RECEIPTS",
                "trial_receipt_digests must be a non-empty tuple of digest strings",
            )
        for d in self.trial_receipt_digests:
            _require_digest(d, "trial_receipt_digest")
        if (
            tuple(sorted(set(self.trial_receipt_digests)))
            != self.trial_receipt_digests
        ):
            raise TaskInvariantError(
                "INVALID_TRIAL_RECEIPTS",
                "trial_receipt_digests must be sorted and unique",
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "evaluated_at_utc": self.evaluated_at_utc,
            "pareto_rank": self.pareto_rank,
            "schema": self.schema,
            "scorecard_id": self.scorecard_id,
            "trial_receipt_digests": list(self.trial_receipt_digests),
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        scorecard_id: str,
        trial_receipt_digests: tuple[str, ...],
        pareto_rank: int,
        evaluated_at_utc: str,
    ) -> ScorecardV1:
        return cls(
            scorecard_id=scorecard_id,
            trial_receipt_digests=trial_receipt_digests,
            pareto_rank=pareto_rank,
            evaluated_at_utc=evaluated_at_utc,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> ScorecardV1:
        expected = {
            "authority_effect",
            "evaluated_at_utc",
            "pareto_rank",
            "schema",
            "scorecard_id",
            "trial_receipt_digests",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_SCORECARD",
                "scorecard fields differ",
            )
        raw_receipts = value["trial_receipt_digests"]
        if type(raw_receipts) is not list:
            raise TaskInvariantError(
                "INVALID_TRIAL_RECEIPTS",
                "trial_receipt_digests must be a list in canonical form",
            )
        return cls(
            scorecard_id=value["scorecard_id"],  # type: ignore[arg-type]
            trial_receipt_digests=tuple(raw_receipts),
            pareto_rank=value["pareto_rank"],  # type: ignore[arg-type]
            evaluated_at_utc=value["evaluated_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class RoutingPolicyProposalV1(_ExactTypeValue):
    """Proposal for a routing policy; strictly non-admitted and non-authoritative."""

    proposal_id: str
    scorecard_digest: str
    candidate_policy_digest: str
    proposed_at_utc: str
    expires_at_utc: str
    is_admitted: bool = False
    schema: str = SCHEMA_ROUTING_POLICY_PROPOSAL
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_ROUTING_POLICY_PROPOSAL:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "routing policy proposal schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "policy proposals grant no authority",
            )
        if self.is_admitted is not False:
            raise TaskInvariantError(
                "ARENA_POLICY_REFUSED",
                "proposals cannot self-admit; is_admitted must be False",
            )
        _require_exact_str(self.proposal_id, "proposal_id", _IDENTIFIER)
        _require_digest(self.scorecard_digest, "scorecard_digest")
        _require_digest(
            self.candidate_policy_digest, "candidate_policy_digest"
        )
        _require_timestamp(self.proposed_at_utc, "proposed_at_utc")
        _require_timestamp(self.expires_at_utc, "expires_at_utc")
        if self.proposed_at_utc > self.expires_at_utc:
            raise TaskInvariantError(
                "INVALID_EXPIRY",
                "proposed_at_utc cannot be after expires_at_utc",
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "candidate_policy_digest": self.candidate_policy_digest,
            "expires_at_utc": self.expires_at_utc,
            "is_admitted": self.is_admitted,
            "proposal_id": self.proposal_id,
            "proposed_at_utc": self.proposed_at_utc,
            "schema": self.schema,
            "scorecard_digest": self.scorecard_digest,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        proposal_id: str,
        scorecard_digest: str,
        candidate_policy_digest: str,
        proposed_at_utc: str,
        expires_at_utc: str,
    ) -> RoutingPolicyProposalV1:
        return cls(
            proposal_id=proposal_id,
            scorecard_digest=scorecard_digest,
            candidate_policy_digest=candidate_policy_digest,
            proposed_at_utc=proposed_at_utc,
            expires_at_utc=expires_at_utc,
            is_admitted=False,
        )

    @classmethod
    def from_canonical(
        cls, value: Mapping[str, object]
    ) -> RoutingPolicyProposalV1:
        expected = {
            "authority_effect",
            "candidate_policy_digest",
            "expires_at_utc",
            "is_admitted",
            "proposal_id",
            "proposed_at_utc",
            "schema",
            "scorecard_digest",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_ROUTING_POLICY_PROPOSAL",
                "routing policy proposal fields differ",
            )
        if value["is_admitted"] is not False:
            raise TaskInvariantError(
                "ARENA_POLICY_REFUSED",
                "proposals cannot self-admit; is_admitted must be False",
            )
        return cls(
            proposal_id=value["proposal_id"],  # type: ignore[arg-type]
            scorecard_digest=value["scorecard_digest"],  # type: ignore[arg-type]
            candidate_policy_digest=value["candidate_policy_digest"],  # type: ignore[arg-type]
            proposed_at_utc=value["proposed_at_utc"],  # type: ignore[arg-type]
            expires_at_utc=value["expires_at_utc"],  # type: ignore[arg-type]
            is_admitted=False,
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class AdmittedPolicyV1(_ExactTypeValue):
    """Runtime routing policy admitted by an authorized human approver."""

    policy_id: str
    proposal_digest: str
    admitted_policy_digest: str
    human_approver_urn: str
    admitted_at_utc: str
    expires_at_utc: str
    schema: str = SCHEMA_ADMITTED_POLICY
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_ADMITTED_POLICY:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "admitted policy schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "admitted policy grants no authority",
            )
        _require_exact_str(self.policy_id, "policy_id", _IDENTIFIER)
        _require_digest(self.proposal_digest, "proposal_digest")
        _require_digest(
            self.admitted_policy_digest, "admitted_policy_digest"
        )
        if (
            type(self.human_approver_urn) is not str
            or _HUMAN_URN.fullmatch(self.human_approver_urn) is None
        ):
            raise TaskInvariantError(
                "ARENA_POLICY_REFUSED",
                "admitted policy requires a valid human approver URN (e.g. urn:human:<id>)",
            )
        _require_timestamp(self.admitted_at_utc, "admitted_at_utc")
        _require_timestamp(self.expires_at_utc, "expires_at_utc")
        if self.admitted_at_utc > self.expires_at_utc:
            raise TaskInvariantError(
                "INVALID_EXPIRY",
                "admitted_at_utc cannot be after expires_at_utc",
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "admitted_at_utc": self.admitted_at_utc,
            "admitted_policy_digest": self.admitted_policy_digest,
            "authority_effect": self.authority_effect,
            "expires_at_utc": self.expires_at_utc,
            "human_approver_urn": self.human_approver_urn,
            "policy_id": self.policy_id,
            "proposal_digest": self.proposal_digest,
            "schema": self.schema,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        policy_id: str,
        proposal_digest: str,
        admitted_policy_digest: str,
        human_approver_urn: str,
        admitted_at_utc: str,
        expires_at_utc: str,
    ) -> AdmittedPolicyV1:
        return cls(
            policy_id=policy_id,
            proposal_digest=proposal_digest,
            admitted_policy_digest=admitted_policy_digest,
            human_approver_urn=human_approver_urn,
            admitted_at_utc=admitted_at_utc,
            expires_at_utc=expires_at_utc,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> AdmittedPolicyV1:
        expected = {
            "admitted_at_utc",
            "admitted_policy_digest",
            "authority_effect",
            "expires_at_utc",
            "human_approver_urn",
            "policy_id",
            "proposal_digest",
            "schema",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_ADMITTED_POLICY",
                "admitted policy fields differ",
            )
        return cls(
            policy_id=value["policy_id"],  # type: ignore[arg-type]
            proposal_digest=value["proposal_digest"],  # type: ignore[arg-type]
            admitted_policy_digest=value["admitted_policy_digest"],  # type: ignore[arg-type]
            human_approver_urn=value["human_approver_urn"],  # type: ignore[arg-type]
            admitted_at_utc=value["admitted_at_utc"],  # type: ignore[arg-type]
            expires_at_utc=value["expires_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


__all__ = [
    "AdmittedPolicyV1",
    "CompetitorSpecV1",
    "CorpusManifestV1",
    "RoutingPolicyProposalV1",
    "SCHEMA_ADMITTED_POLICY",
    "SCHEMA_COMPETITOR_SPEC",
    "SCHEMA_CORPUS_MANIFEST",
    "SCHEMA_ROUTING_POLICY_PROPOSAL",
    "SCHEMA_SCORECARD",
    "SCHEMA_TRIAL_RECEIPT",
    "ScorecardV1",
    "TrialReceiptV1",
]
