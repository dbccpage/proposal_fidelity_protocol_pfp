"""Domain layer for operations (Clean Architecture & Bounded Contexts).

Contains pure entities, value objects, domain protocols, and bounded contexts.
AuthorityEffect: None.
"""

from operations.domain.cicd import (
    GATE_CATALOG_V3,
    AdvisoryFindingV1,
    CandidateManifestEntryV1,
    CandidateManifestV1,
    CanonicalCandidateManifestV1,
    EvaluatorAnchorV1,
    GateDisposition,
    GateEvaluationV1,
    GateId,
    GateResult,
    GateRouteV1,
    GateSpec,
    GateStatus,
    LocalCiExecutionReceiptV3,
    LocalCiInvocationV1,
    LocalCiReceiptError,
    LocalCiReceiptErrorCode,
    LocalCiVerdict,
    LocalCiVerificationInputsV1,
    active_gate_specs,
    load_gate_catalog_yaml,
)

__all__ = (
    "AdvisoryFindingV1",
    "CandidateManifestEntryV1",
    "CandidateManifestV1",
    "CanonicalCandidateManifestV1",
    "EvaluatorAnchorV1",
    "GATE_CATALOG_V3",
    "GateDisposition",
    "GateEvaluationV1",
    "GateId",
    "GateResult",
    "GateRouteV1",
    "GateSpec",
    "GateStatus",
    "LocalCiExecutionReceiptV3",
    "LocalCiInvocationV1",
    "LocalCiReceiptError",
    "LocalCiReceiptErrorCode",
    "LocalCiVerdict",
    "LocalCiVerificationInputsV1",
    "active_gate_specs",
    "load_gate_catalog_yaml",
)

