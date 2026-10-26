"""Backward-compatibility re-export module for oecicd domain models.

Domain models have been decomposed into aggregate and value-object modules:
- enums: GateDisposition, GateStatus, LocalCiVerdict
- base: _StrictFrozenModel, _AuthorityNullModel
- validators: _canonical_text, _identifier, _sha256, _git_oid, _repo_path, _argv_item, _sorted_unique
- fields: GateId, ToolId, Sha256, GitOid, RepoPath, etc.
- routes: PythonGateRouteV1, ToolGateRouteV1, QuarantinedGateRouteV1, GateRouteV1
- gate_spec: GateSpec
- manifest: CandidateManifestEntryV1, CanonicalCandidateManifestV1, CandidateManifestV1
- anchors: TrustedEvaluatorAnchorV1, EvaluatorAnchorV1, _validate_anchors
- result: ResolvedGateInvocationV1, GateResult, QuarantineResidualV1, AdvisoryFindingV1, GateEvaluationV1
- invocation: LocalCiInvocationV1
- verification_inputs: LocalCiVerificationInputsV1
- receipt: LocalCiExecutionReceiptV3
"""

from __future__ import annotations

from omega_engine_operations.domain.cicd.anchors import (
    EvaluatorAnchorV1,
    TrustedEvaluatorAnchorV1,
    _validate_anchors,
)
from omega_engine_operations.domain.cicd.base import (
    _AuthorityNullModel,
    _StrictFrozenModel,
)
from omega_engine_operations.domain.cicd.enums import (
    GateDisposition,
    GateStatus,
    LocalCiVerdict,
)
from omega_engine_operations.domain.cicd.fields import (
    AnchorName,
    AnchorPath,
    BlobOid,
    CandidatePath,
    CanonicalText,
    Detail,
    DurationMs,
    EntrypointPath,
    ExitCode,
    GateId,
    GitOid,
    OptionalBlobOid,
    OptionalSha256,
    RepoPath,
    RepoPathOrDot,
    ResidualCode,
    Sha256,
    TimeoutSeconds,
    ToolId,
    make_canonical_text,
    make_git_oid,
    make_identifier,
    make_repo_path,
    make_sha256,
)
from omega_engine_operations.domain.cicd.gate_spec import GateSpec
from omega_engine_operations.domain.cicd.invocation import (
    LocalCiInvocationV1,
)
from omega_engine_operations.domain.cicd.manifest import (
    CandidateManifestEntryV1,
    CandidateManifestV1,
    CanonicalCandidateManifestV1,
)
from omega_engine_operations.domain.cicd.receipt import (
    LocalCiExecutionReceiptV3,
)
from omega_engine_operations.domain.cicd.result import (
    AdvisoryFindingV1,
    GateEvaluationV1,
    GateResult,
    QuarantineResidualV1,
    ResolvedGateInvocationV1,
)
from omega_engine_operations.domain.cicd.routes import (
    GateRouteV1,
    PythonGateRouteV1,
    QuarantinedGateRouteV1,
    ToolGateRouteV1,
)
from omega_engine_operations.domain.cicd.validators import (
    _argv_item,
    _canonical_text,
    _git_oid,
    _identifier,
    _repo_path,
    _sha256,
    _sorted_unique,
)
from omega_engine_operations.domain.cicd.verification_inputs import (
    LocalCiVerificationInputsV1,
)

__all__ = (
    "AdvisoryFindingV1",
    "AnchorName",
    "AnchorPath",
    "BlobOid",
    "CandidateManifestEntryV1",
    "CandidateManifestV1",
    "CandidatePath",
    "CanonicalCandidateManifestV1",
    "CanonicalText",
    "Detail",
    "DurationMs",
    "EntrypointPath",
    "EvaluatorAnchorV1",
    "ExitCode",
    "GateDisposition",
    "GateEvaluationV1",
    "GateId",
    "GateResult",
    "GateRouteV1",
    "GateSpec",
    "GateStatus",
    "GitOid",
    "LocalCiExecutionReceiptV3",
    "LocalCiInvocationV1",
    "LocalCiVerdict",
    "LocalCiVerificationInputsV1",
    "OptionalBlobOid",
    "OptionalSha256",
    "PythonGateRouteV1",
    "QuarantineResidualV1",
    "QuarantinedGateRouteV1",
    "RepoPath",
    "RepoPathOrDot",
    "ResidualCode",
    "ResolvedGateInvocationV1",
    "Sha256",
    "TimeoutSeconds",
    "ToolGateRouteV1",
    "ToolId",
    "TrustedEvaluatorAnchorV1",
    "_AuthorityNullModel",
    "_StrictFrozenModel",
    "_argv_item",
    "_canonical_text",
    "_git_oid",
    "_identifier",
    "_repo_path",
    "_sha256",
    "_sorted_unique",
    "_validate_anchors",
    "make_canonical_text",
    "make_git_oid",
    "make_identifier",
    "make_repo_path",
    "make_sha256",
)
