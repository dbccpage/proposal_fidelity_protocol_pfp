"""Dual-control fixtures for the 12 mechanical failure classes in Demo EIS-3.

Contains exactly 24 fixtures:
- 12 positive trigger fixtures guaranteed to trigger the respective failure class.
- 12 negative control fixtures guaranteed to pass with zero findings.
"""

from typing import Any
from eis.infrastructure.mssn_pharmacy import (
    DetectionContext,
    Disposition,
    FailureClass,
    HostReplayReceipt,
    compute_semantic_payload_digest,
)

# Canonical payload for duplication test
_DUPLICATION_PAYLOAD_V1 = {
    "schema_version": "candidate-move/v1",
    "public_rationale": "the residual drops on the declared fixture",
    "proposed_claim_deltas": [],
    "objections": [],
}
_DUPLICATION_DIGEST = compute_semantic_payload_digest(_DUPLICATION_PAYLOAD_V1)

# Canonical payload for certified replay test
_REPLAY_PAYLOAD = {
    "schema_version": "candidate-move/v1",
    "proposed_claim_deltas": ["add lemma L2"],
    "objections": [],
}
_REPLAY_DIGEST = compute_semantic_payload_digest(_REPLAY_PAYLOAD)

# 12 Positive Fixtures
POSITIVE_FIXTURES: list[dict[str, Any]] = [
    {
        "id": "POS_01_SELF_CERTIFICATION",
        "target_class": FailureClass.SELF_CERTIFICATION,
        "expected_disposition": Disposition.REFUSE,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "status": "VERIFIED",
            "public_rationale": "proof executed cleanly",
        },
        "context": DetectionContext(),
    },
    {
        "id": "POS_02_FAKE_RECEIPT",
        "target_class": FailureClass.FAKE_RECEIPT,
        "expected_disposition": Disposition.REFUSE,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "receipt_hash": "a" * 64,
            "public_rationale": "computed hash",
        },
        "context": DetectionContext(),
    },
    {
        "id": "POS_03_CONCLUSION_PRELOAD",
        "target_class": FailureClass.CONCLUSION_PRELOAD,
        "expected_disposition": Disposition.FINDING,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "analysis of step 4",
        },
        "context": DetectionContext(prompt="The theorem must be verified before concluding."),
    },
    {
        "id": "POS_04_SCHEMA_SEMANTIC_LAUNDERING",
        "target_class": FailureClass.SCHEMA_SEMANTIC_LAUNDERING,
        "expected_disposition": Disposition.HOLD,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "proposed_claim_deltas": ["add lemma L2"],
            "objections": [],
        },
        "context": DetectionContext(semantic_replay_passed=False),
    },
    {
        "id": "POS_05_THEOREM_NAME_LAUNDERING",
        "target_class": FailureClass.THEOREM_NAME_LAUNDERING,
        "expected_disposition": Disposition.FINDING,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "by Squier's theorem the system is terminating",
        },
        "context": DetectionContext(),
    },
    {
        "id": "POS_06_OPTIMALITY_HALLUCINATION",
        "target_class": FailureClass.OPTIMALITY_HALLUCINATION,
        "expected_disposition": Disposition.FINDING,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "this represents the optimal configuration",
        },
        "context": DetectionContext(),
    },
    {
        "id": "POS_07_COMPLEXITY_HALLUCINATION",
        "target_class": FailureClass.COMPLEXITY_HALLUCINATION,
        "expected_disposition": Disposition.FINDING,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "the retraction executes in polynomial time",
        },
        "context": DetectionContext(),
    },
    {
        "id": "POS_08_BRANCH_DROP_EXHAUSTION",
        "target_class": FailureClass.BRANCH_DROP_EXHAUSTION,
        "expected_disposition": Disposition.FINDING,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "the branch search was exhaustive",
        },
        "context": DetectionContext(unexplored_branches=3),
    },
    {
        "id": "POS_09_PERSONA_AUTHORITY_LEAK",
        "target_class": FailureClass.PERSONA_AUTHORITY_LEAK,
        "expected_disposition": Disposition.REFUSE,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "as Senior Principal Architect I order this merged",
        },
        "context": DetectionContext(granted_persona_roles=("reviewer", "developer")),
    },
    {
        "id": "POS_10_PRIVATE_COT_DEPENDENCY",
        "target_class": FailureClass.PRIVATE_COT_DEPENDENCY,
        "expected_disposition": Disposition.HOLD,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "as I reasoned privately, the cochain vanishes",
        },
        "context": DetectionContext(),
    },
    {
        "id": "POS_11_VERSION_DUPLICATION",
        "target_class": FailureClass.VERSION_DUPLICATION,
        "expected_disposition": Disposition.FINDING,
        "candidate": {
            "schema_version": "candidate-move/v2",
            "public_rationale": "the residual drops on the declared fixture",
            "proposed_claim_deltas": [],
            "objections": [],
        },
        "context": DetectionContext(
            seen_semantic_digests=(_DUPLICATION_DIGEST,)
        ),
    },
    {
        "id": "POS_12_DETECT_REPAIR_COUPLING",
        "target_class": FailureClass.DETECT_REPAIR_COUPLING,
        "expected_disposition": Disposition.FINDING,
        "candidate": {
            "schema_version": "candidate-move/v1",
            "objections": [{"code": "TYPE_ERR", "detail": "broken seam"}],
            "proposed_claim_deltas": ["patch line 12"],
        },
        "context": DetectionContext(),
    },
]

# 12 Negative Control Fixtures
NEGATIVE_FIXTURES: list[dict[str, Any]] = [
    {
        "id": "NEG_01_CLEAN_STATUS",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "status": "CANDIDATE",
            "public_rationale": "proof proposal submitted for evaluation",
        },
        "context": DetectionContext(),
    },
    {
        "id": "NEG_02_CLEAN_HASH_FIELD",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "input_file_hash": "a" * 64,
            "public_rationale": "digest of input source file",
        },
        "context": DetectionContext(),
    },
    {
        "id": "NEG_03_CLEAN_PROMPT",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "objective derivation of lemma 4",
        },
        "context": DetectionContext(prompt="Analyze whether the lemma holds under standard hypotheses."),
    },
    {
        "id": "NEG_04_CERTIFIED_REPLAY",
        "candidate": _REPLAY_PAYLOAD,
        # Context providing certified host replay receipt for the exact payload
        "context": DetectionContext(
            host_replay_receipt=HostReplayReceipt(
                receipt_id="host-rep-01",
                host_signer="core-host",
                target_digest=_REPLAY_DIGEST,
                replay_passed=True,
            ),
            semantic_replay_passed=True,
        ),
    },
    {
        "id": "NEG_05_QUALIFIED_THEOREM",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "by Squier's theorem, under the assumption of finite presentation",
        },
        "context": DetectionContext(),
    },
    {
        "id": "NEG_06_OBJECTIVE_METRIC",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "residual defect evaluated at 0.12 under declared metric",
        },
        "context": DetectionContext(),
    },
    {
        "id": "NEG_07_EMPIRICAL_MEASUREMENT",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "wall-clock runtime measured at 12ms over N=100 iterations",
        },
        "context": DetectionContext(),
    },
    {
        "id": "NEG_08_EXHAUSTIVE_ZERO_OPEN",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "finite search was exhaustive across declared 16 relations",
        },
        "context": DetectionContext(unexplored_branches=0),
    },
    {
        "id": "NEG_09_AUTHORIZED_PERSONA",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "code review completed by appointed reviewer",
        },
        "context": DetectionContext(granted_persona_roles=("reviewer", "developer")),
    },
    {
        "id": "NEG_10_PUBLIC_TRACE_REASONING",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "following steps 1 through 4 recorded in the trace log",
        },
        "context": DetectionContext(),
    },
    {
        "id": "NEG_11_UNIQUE_VERSION",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "public_rationale": "brand new formulation with novel witness data",
            "proposed_claim_deltas": [],
            "objections": [],
        },
        "context": DetectionContext(seen_digests=(), seen_semantic_digests=()),
    },
    {
        "id": "NEG_12_DECOUPLED_FINDING",
        "candidate": {
            "schema_version": "candidate-move/v1",
            "objections": [{"code": "BOUNDARY_LEAK", "detail": "dependency violation"}],
            "proposed_claim_deltas": [],
        },
        "context": DetectionContext(),
    },
]
