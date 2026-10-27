"""External Human Decision Aggregate (Pass 5 / Stage E / P3-07).

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .decision_outcome import DecisionOutcome
from .decision_validation_error import DecisionValidationError
from .principal_evidence_v1 import PrincipalEvidenceV1
from .value_objects import (
    CandidateId,
    DecisionId,
    DigestKind,
    DomainInvariantError,
    EvidenceId,
    GitCommitOid,
    GitTreeOid,
    IdKind,
    MutationManifestV1,
    Nonce,
    OneUseToken,
    PolicyDigest,
    ProblemId,
    ProposalId,
    UtcTimestamp,
)

# Constants & Error Codes
HUMAN_DECISION_SCHEMA_V1 = "core.human_decision.v1"
ALLOWED_EFFECT_TEMPORARY_GIT_APPLY_ONCE = "TEMPORARY_GIT_APPLY_ONCE"

ERR_DECISION_SCHEMA_VERSION_MISMATCH = "DECISION_SCHEMA_VERSION_MISMATCH"
ERR_INVALID_FIELD = "INVALID_FIELD"
ERR_INVALID_DECISION_ID = "INVALID_DECISION_ID"
ERR_MISSING_IDENTITY_LINKS = "MISSING_IDENTITY_LINKS"
ERR_INVALID_BASE_COMMIT_OID = "INVALID_BASE_COMMIT_OID"
ERR_INVALID_EXPECTED_TREE_OID = "INVALID_EXPECTED_TREE_OID"
ERR_INVALID_POLICY_DIGEST = "INVALID_POLICY_DIGEST"
ERR_INVALID_NONCE_ENTROPY = "INVALID_NONCE_ENTROPY"
ERR_INVALID_ONE_USE_TOKEN = "INVALID_ONE_USE_TOKEN"
ERR_HOLD_DECISION_CANNOT_APPLY = "HOLD_DECISION_CANNOT_APPLY"
ERR_REJECT_DECISION_CANNOT_APPLY = "REJECT_DECISION_CANNOT_APPLY"
ERR_UNRECOGNIZED_DECISION_OUTCOME = "UNRECOGNIZED_DECISION_OUTCOME"
ERR_SELF_ISSUED_PRINCIPAL_ASSERTION_REFUSED = "SELF_ISSUED_PRINCIPAL_ASSERTION_REFUSED"
ERR_UNAUTHORIZED_EFFECT = "UNAUTHORIZED_EFFECT"
ERR_DECISION_EXPIRED = "DECISION_EXPIRED"
ERR_ISSUED_AFTER_EXPIRY = "ISSUED_AFTER_EXPIRY"


@dataclass(frozen=True, slots=True, eq=False)
class HumanDecisionV1:
    """Strongly-typed external human decision Aggregate."""

    decision_id: DecisionId
    outcome: DecisionOutcome
    principal_evidence: PrincipalEvidenceV1
    problem_id: ProblemId
    proposal_id: ProposalId
    candidate_id: CandidateId
    evidence_id: EvidenceId
    mutation_manifest: MutationManifestV1
    allowed_effect: str
    repository_target: str
    base_commit_oid: GitCommitOid
    expected_tree_oid: GitTreeOid
    policy_digest: PolicyDigest
    nonce: Nonce
    issued_timestamp_utc: UtcTimestamp
    expiry_timestamp_utc: UtcTimestamp
    one_use_token: OneUseToken
    authority_effect: str = "None"
    schema_version: str = HUMAN_DECISION_SCHEMA_V1

    def __init__(
        self,
        *,
        decision_id: DecisionId | str,
        outcome: DecisionOutcome | str,
        principal_evidence: PrincipalEvidenceV1,
        problem_id: ProblemId | str,
        proposal_id: ProposalId | str,
        candidate_id: CandidateId | str,
        evidence_id: EvidenceId | str,
        mutation_manifest: MutationManifestV1,
        allowed_effect: str,
        repository_target: str,
        base_commit_oid: GitCommitOid | str,
        expected_tree_oid: GitTreeOid | str,
        policy_digest: PolicyDigest | str,
        nonce: Nonce | str,
        issued_timestamp_utc: UtcTimestamp | str | datetime,
        expiry_timestamp_utc: UtcTimestamp | str | datetime,
        one_use_token: OneUseToken | str,
        authority_effect: str = "None",
        schema_version: str = HUMAN_DECISION_SCHEMA_V1,
    ) -> None:
        try:
            d_id = DecisionId.from_str(decision_id, kind=IdKind.DECISION)
        except DomainInvariantError as exc:
            raise DecisionValidationError(ERR_INVALID_DECISION_ID, str(exc)) from exc

        out = DecisionOutcome(outcome) if isinstance(outcome, str) else outcome

        try:
            prob_id = ProblemId.from_str(problem_id, kind=IdKind.PROBLEM)
            prop_id = ProposalId.from_str(proposal_id, kind=IdKind.PROPOSAL)
            cand_id = CandidateId.from_str(candidate_id, kind=IdKind.CANDIDATE)
            evid_id = EvidenceId.from_str(evidence_id, kind=IdKind.EVIDENCE)
        except DomainInvariantError as exc:
            raise DecisionValidationError(ERR_MISSING_IDENTITY_LINKS, str(exc)) from exc

        try:
            base_c = GitCommitOid.from_str(base_commit_oid, kind=DigestKind.GIT_COMMIT)
        except DomainInvariantError as exc:
            raise DecisionValidationError(ERR_INVALID_BASE_COMMIT_OID, str(exc)) from exc

        try:
            tree_oid = GitTreeOid.from_str(expected_tree_oid, kind=DigestKind.GIT_TREE)
        except DomainInvariantError as exc:
            raise DecisionValidationError(ERR_INVALID_EXPECTED_TREE_OID, str(exc)) from exc

        try:
            p_dig = PolicyDigest.from_str(policy_digest, kind=DigestKind.POLICY)
        except DomainInvariantError as exc:
            raise DecisionValidationError(ERR_INVALID_POLICY_DIGEST, str(exc)) from exc

        try:
            n_val = Nonce.from_str(nonce, kind=IdKind.NONCE)
        except DomainInvariantError as exc:
            raise DecisionValidationError(ERR_INVALID_NONCE_ENTROPY, str(exc)) from exc

        try:
            tok_val = OneUseToken.from_str(one_use_token, kind=IdKind.ONE_USE_TOKEN)
        except DomainInvariantError as exc:
            raise DecisionValidationError(ERR_INVALID_ONE_USE_TOKEN, str(exc)) from exc

        i_ts = UtcTimestamp.from_iso(issued_timestamp_utc)
        e_ts = UtcTimestamp.from_iso(expiry_timestamp_utc)

        object.__setattr__(self, "decision_id", d_id)
        object.__setattr__(self, "outcome", out)
        object.__setattr__(self, "principal_evidence", principal_evidence)
        object.__setattr__(self, "problem_id", prob_id)
        object.__setattr__(self, "proposal_id", prop_id)
        object.__setattr__(self, "candidate_id", cand_id)
        object.__setattr__(self, "evidence_id", evid_id)
        object.__setattr__(self, "mutation_manifest", mutation_manifest)
        object.__setattr__(self, "allowed_effect", allowed_effect)
        object.__setattr__(self, "repository_target", repository_target)
        object.__setattr__(self, "base_commit_oid", base_c)
        object.__setattr__(self, "expected_tree_oid", tree_oid)
        object.__setattr__(self, "policy_digest", p_dig)
        object.__setattr__(self, "nonce", n_val)
        object.__setattr__(self, "issued_timestamp_utc", i_ts)
        object.__setattr__(self, "expiry_timestamp_utc", e_ts)
        object.__setattr__(self, "one_use_token", tok_val)
        object.__setattr__(self, "authority_effect", authority_effect)
        object.__setattr__(self, "schema_version", schema_version)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.decision_id == other.decision_id

    def __hash__(self) -> int:
        return hash((type(self), self.decision_id))


def validate_human_decision(
    decision: HumanDecisionV1,
    *,
    current_time_utc: str | datetime | UtcTimestamp | None = None,
    now_utc: datetime | str | None = None,
    allowed_effect_expected: str = ALLOWED_EFFECT_TEMPORARY_GIT_APPLY_ONCE,
    banned_principal_ids: tuple[str, ...] = ("agent", "model", "swarm", "system", "self"),
) -> None:
    """Rigorous invariant validation for HumanDecisionV1."""
    if decision.schema_version != HUMAN_DECISION_SCHEMA_V1:
        raise DecisionValidationError(
            ERR_DECISION_SCHEMA_VERSION_MISMATCH,
            f"expected {HUMAN_DECISION_SCHEMA_V1} got {decision.schema_version}",
        )

    if decision.outcome is DecisionOutcome.HOLD:
        raise DecisionValidationError(ERR_HOLD_DECISION_CANNOT_APPLY)
    if decision.outcome is DecisionOutcome.REJECT:
        raise DecisionValidationError(ERR_REJECT_DECISION_CANNOT_APPLY)
    if decision.outcome is not DecisionOutcome.ACCEPT:
        raise DecisionValidationError(ERR_UNRECOGNIZED_DECISION_OUTCOME, str(decision.outcome))

    p_id_str = str(decision.principal_evidence.principal_id).lower()
    if p_id_str in banned_principal_ids:
        raise DecisionValidationError(
            ERR_SELF_ISSUED_PRINCIPAL_ASSERTION_REFUSED,
            f"principal {decision.principal_evidence.principal_id!r} is not an authorized human principal",
        )

    if decision.allowed_effect != allowed_effect_expected:
        raise DecisionValidationError(
            ERR_UNAUTHORIZED_EFFECT,
            f"allowed_effect {decision.allowed_effect!r} is unauthorized; must be {allowed_effect_expected!r}",
        )

    ref_now = UtcTimestamp.from_iso(current_time_utc or now_utc) if (current_time_utc is not None or now_utc is not None) else UtcTimestamp.now()
    if not decision.expiry_timestamp_utc.is_after(ref_now):
        raise DecisionValidationError(
            ERR_DECISION_EXPIRED,
            f"decision expired at {decision.expiry_timestamp_utc}, now is {ref_now}",
        )

    if not decision.expiry_timestamp_utc.is_after(decision.issued_timestamp_utc):
        raise DecisionValidationError(
            ERR_ISSUED_AFTER_EXPIRY,
            f"issued at {decision.issued_timestamp_utc} is after expiry {decision.expiry_timestamp_utc}",
        )
