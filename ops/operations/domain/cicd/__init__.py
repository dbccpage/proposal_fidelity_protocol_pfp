"""Domain layer exports for local_ci Bounded Context."""

from __future__ import annotations

from typing import Any

from operations.domain.cicd.anchors import (
    EvaluatorAnchorV1,
    TrustedEvaluatorAnchorV1,
    _validate_anchors,
)
from operations.domain.cicd.base import (
    _AuthorityNullModel,
    _StrictFrozenModel,
)
from operations.domain.cicd.constants import (
    _CANONICAL_MODULE_NAME,
    _CATALOG_DOMAIN,
    _CONCRETE_PATH_TYPE,
    _IDENTIFIER_RE,
    _INVOCATION_SCHEMA,
    _LOWER_GIT_OID_RE,
    _LOWER_SHA256_RE,
    _MANIFEST_DOMAIN,
    _MANIFEST_SCHEMA,
    _MAX_CANONICAL_BYTES,
    _MAX_DETAIL_CHARACTERS,
    _MAX_INTEGER_LEXEME_DIGITS,
    _MAX_JSON_DEPTH,
    _MAX_JSON_NODES,
    _RECEIPT_DIGEST_PREFIX,
    _RECEIPT_SCHEMA,
    _RESOLUTION_DOMAIN,
    _RESULTS_DOMAIN,
    _SAFE_INTEGER_LIMIT,
    MAX_RECEIPT_BYTES,
)
from operations.domain.cicd.enums import (
    GateDisposition,
    GateStatus,
    LocalCiVerdict,
)
from operations.domain.cicd.errors import (
    LocalCiReceiptError,
    LocalCiReceiptErrorCode,
)
from operations.domain.cicd.fields import (
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
from operations.domain.cicd.gate_spec import (
    GateSpec,
    load_gate_catalog_yaml,
    load_gate_spec_from_dict,
)
from operations.domain.cicd.invocation import (
    LocalCiInvocationV1,
)
from operations.domain.cicd.manifest import (
    CandidateManifestEntryV1,
    CandidateManifestV1,
    CanonicalCandidateManifestV1,
)
from operations.domain.cicd.protocols import (
    GateExecutorProtocol,
    GitReaderProtocol,
    LocalCiRunnerProtocol,
    LocalCiSerializerProtocol,
    ReceiptSinkProtocol,
    get_local_ci_serializer,
    register_local_ci_serializer,
    register_local_ci_serializer_factory,
)
from operations.domain.cicd.receipt import (
    LocalCiExecutionReceiptV3,
)
from operations.domain.cicd.result import (
    AdvisoryFindingV1,
    GateEvaluationV1,
    GateResult,
    QuarantineResidualV1,
    ResolvedGateInvocationV1,
)
from operations.domain.cicd.routes import (
    GateRouteV1,
    PythonGateRouteV1,
    QuarantinedGateRouteV1,
    ToolGateRouteV1,
)
from operations.domain.cicd.validators import (
    _argv_item,
    _canonical_text,
    _git_oid,
    _identifier,
    _repo_path,
    _sha256,
    _sorted_unique,
)
from operations.domain.cicd.verification_inputs import (
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
    "GATE_CATALOG_V3",
    "GateDisposition",
    "GateEvaluationV1",
    "GateExecutorProtocol",
    "GateId",
    "GateResult",
    "GateRouteV1",
    "GateSpec",
    "GateStatus",
    "GitOid",
    "GitReaderProtocol",
    "LocalCiExecutionReceiptV3",
    "LocalCiInvocationV1",
    "LocalCiReceiptError",
    "LocalCiReceiptErrorCode",
    "LocalCiRunnerProtocol",
    "LocalCiSerializerProtocol",
    "LocalCiVerdict",
    "LocalCiVerificationInputsV1",
    "MAX_RECEIPT_BYTES",
    "OptionalBlobOid",
    "OptionalSha256",
    "PythonGateRouteV1",
    "QuarantineResidualV1",
    "QuarantinedGateRouteV1",
    "ReceiptSinkProtocol",
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
    "_CANONICAL_MODULE_NAME",
    "_CATALOG_DOMAIN",
    "_CONCRETE_PATH_TYPE",
    "_GATE_BY_ID",
    "_IDENTIFIER_RE",
    "_INVOCATION_SCHEMA",
    "_LOWER_GIT_OID_RE",
    "_LOWER_SHA256_RE",
    "_MANIFEST_DOMAIN",
    "_MANIFEST_SCHEMA",
    "_MAX_CANONICAL_BYTES",
    "_MAX_DETAIL_CHARACTERS",
    "_MAX_INTEGER_LEXEME_DIGITS",
    "_MAX_JSON_DEPTH",
    "_MAX_JSON_NODES",
    "_RECEIPT_DIGEST_PREFIX",
    "_RECEIPT_SCHEMA",
    "_RESOLUTION_DOMAIN",
    "_RESULTS_DOMAIN",
    "_SAFE_INTEGER_LIMIT",
    "_StrictFrozenModel",
    "_argv_item",
    "_canonical_text",
    "_git_oid",
    "_identifier",
    "_repo_path",
    "_sha256",
    "_sorted_unique",
    "_validate_anchors",
    "active_gate_specs",
    "get_local_ci_serializer",
    "load_gate_catalog_yaml",
    "load_gate_spec_from_dict",
    "make_canonical_text",
    "make_git_oid",
    "make_identifier",
    "make_repo_path",
    "make_sha256",
    "quarantined_gate_specs",
    "register_local_ci_serializer",
    "register_local_ci_serializer_factory",
)

_CATALOG_NAMES = frozenset(
    {
        "GATE_CATALOG_V3",
        "_GATE_BY_ID",
        "active_gate_specs",
        "quarantined_gate_specs",
    }
)


def __getattr__(name: str) -> Any:
    """Load the protocol projection after this package has finished importing."""
    if name not in _CATALOG_NAMES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    catalog_module = importlib.import_module(
        "operations.domain.cicd.catalog"
    )
    value = getattr(catalog_module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
