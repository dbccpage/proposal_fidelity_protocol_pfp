"""Use Cases for gate resolution, evaluation, and receipt construction."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from omega_engine_operations.domain.cicd import (
    AdvisoryFindingV1,
    CandidateManifestEntryV1,
    CanonicalCandidateManifestV1,
    GateDisposition,
    GateEvaluationV1,
    GateResult,
    GateSpec,
    GateStatus,
    LocalCiExecutionReceiptV3,
    LocalCiInvocationV1,
    LocalCiVerdict,
    LocalCiVerificationInputsV1,
    PythonGateRouteV1,
    QuarantinedGateRouteV1,
    QuarantineResidualV1,
    ResolvedGateInvocationV1,
    ToolGateRouteV1,
    TrustedEvaluatorAnchorV1,
    _git_oid,
)
from omega_engine_operations.domain.cicd.catalog import (
    _GATE_BY_ID,
    active_gate_specs,
    quarantined_gate_specs,
)
from omega_engine_operations.domain.cicd.errors import (
    LocalCiReceiptError,
    LocalCiReceiptErrorCode,
)
from omega_engine_operations.domain.cicd.protocols import (
    LocalCiSerializerProtocol,
    get_local_ci_serializer,
)

_ModelT = TypeVar("_ModelT", bound=BaseModel)


def _strict_declared_rehydrate(
    value: Any, model_type: type[_ModelT], *, label: str
) -> _ModelT:
    """Rebuild an exact base model from its declared serializer's primitives."""
    if type(value) is not model_type:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            f"{label} must be an exact {model_type.__name__}",
        )
    try:
        primitive = model_type.__pydantic_serializer__.to_python(
            value,
            mode="python",
            by_alias=True,
            warnings="error",
        )
        rebuilt = model_type.model_validate(primitive, strict=True)
    except Exception as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            f"{label} does not satisfy its declared strict base schema",
        ) from error
    if type(rebuilt) is not model_type:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            f"{label} did not rehydrate as its declared base type",
        )
    return rebuilt


def _require_exact_tuple(
    value: Any, item_type: type[Any], *, label: str
) -> None:
    if type(value) is not tuple or any(
        type(item) is not item_type for item in value
    ):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            f"{label} must be a tuple of exact {item_type.__name__} values",
        )


def _required_model_field(value: BaseModel, field: str, *, label: str) -> Any:
    try:
        return object.__getattribute__(value, field)
    except (AttributeError, RuntimeError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            f"{label} is missing required field {field!r}",
        ) from error


def _rehydrate_manifest(value: Any) -> CanonicalCandidateManifestV1:
    if type(value) is not CanonicalCandidateManifestV1:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "candidate manifest must be an exact CanonicalCandidateManifestV1",
        )
    _require_exact_tuple(
        _required_model_field(value, "entries", label="candidate manifest"),
        CandidateManifestEntryV1,
        label="candidate manifest entries",
    )
    rebuilt = _strict_declared_rehydrate(
        value, CanonicalCandidateManifestV1, label="candidate manifest"
    )
    _require_exact_tuple(
        rebuilt.entries,
        CandidateManifestEntryV1,
        label="rehydrated candidate manifest entries",
    )
    return rebuilt


def _rehydrate_anchors(
    value: Any, *, label: str
) -> tuple[TrustedEvaluatorAnchorV1, ...]:
    _require_exact_tuple(value, TrustedEvaluatorAnchorV1, label=label)
    return tuple(
        _strict_declared_rehydrate(
            anchor, TrustedEvaluatorAnchorV1, label=f"{label} item"
        )
        for anchor in value
    )


def _bind_gate_catalog() -> None:
    from omega_engine_operations.infrastructure.cicd.gate_catalog_loader import (
        ensure_gate_catalog,
    )

    ensure_gate_catalog()


def _rehydrate_gate_spec(value: Any) -> GateSpec:
    _bind_gate_catalog()
    if type(value) is not GateSpec:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "gate must be an exact GateSpec",
        )
    route = _required_model_field(value, "route", label="gate spec")
    if type(route) not in {
        PythonGateRouteV1,
        ToolGateRouteV1,
        QuarantinedGateRouteV1,
    }:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "gate route must be an exact declared route base type",
        )
    runner_kind = _required_model_field(
        route, "runner_kind", label="gate route"
    )
    expected_route_type: type[Any]
    if runner_kind == "PYTHON":
        expected_route_type = PythonGateRouteV1
    elif runner_kind == "TOOL":
        expected_route_type = ToolGateRouteV1
    elif runner_kind == "QUARANTINED":
        expected_route_type = QuarantinedGateRouteV1
    else:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "gate route has an unknown discriminator",
        )
    if type(route) is not expected_route_type:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "gate route must be the exact declared route base type",
        )
    rebuilt = _strict_declared_rehydrate(value, GateSpec, label="gate spec")
    canonical = _GATE_BY_ID.get(rebuilt.gate_id)
    if canonical is None or rebuilt != canonical:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.RESULT_BINDING_MISMATCH,
            "gate spec is not the exact canonical catalog entry",
        )
    return canonical


def _rehydrate_result(value: Any) -> GateResult:
    return _strict_declared_rehydrate(value, GateResult, label="gate result")


def _rehydrate_results(values: Any) -> tuple[GateResult, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.MALFORMED_RESULT,
            "gate results must be an ordered sequence",
        )
    return tuple(_rehydrate_result(value) for value in values)


def _rehydrate_invocation(value: Any) -> LocalCiInvocationV1:
    if type(value) is not LocalCiInvocationV1:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "invocation must be an exact LocalCiInvocationV1",
        )
    _rehydrate_manifest(
        _required_model_field(value, "candidate_manifest", label="invocation")
    )
    _rehydrate_anchors(
        _required_model_field(value, "evaluator_anchors", label="invocation"),
        label="invocation evaluator anchors",
    )
    rebuilt = _strict_declared_rehydrate(
        value, LocalCiInvocationV1, label="local-CI invocation"
    )
    _rehydrate_manifest(rebuilt.candidate_manifest)
    _rehydrate_anchors(
        rebuilt.evaluator_anchors,
        label="rehydrated invocation evaluator anchors",
    )
    return rebuilt


def _rehydrate_verification_inputs(value: Any) -> LocalCiVerificationInputsV1:
    if type(value) is not LocalCiVerificationInputsV1:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "verification inputs must be exact LocalCiVerificationInputsV1",
        )
    _rehydrate_manifest(
        _required_model_field(
            value, "candidate_manifest", label="verification inputs"
        )
    )
    _rehydrate_anchors(
        _required_model_field(
            value, "evaluator_anchors", label="verification inputs"
        ),
        label="verification input evaluator anchors",
    )
    rebuilt = _strict_declared_rehydrate(
        value, LocalCiVerificationInputsV1, label="verification inputs"
    )
    _rehydrate_manifest(rebuilt.candidate_manifest)
    _rehydrate_anchors(
        rebuilt.evaluator_anchors,
        label="rehydrated verification input evaluator anchors",
    )
    return rebuilt


def _rehydrate_receipt(value: Any) -> LocalCiExecutionReceiptV3:
    if type(value) is not LocalCiExecutionReceiptV3:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "receipt must be an exact LocalCiExecutionReceiptV3",
        )
    _rehydrate_manifest(
        _required_model_field(value, "candidate_manifest", label="receipt")
    )
    _rehydrate_anchors(
        _required_model_field(value, "evaluator_anchors", label="receipt"),
        label="receipt evaluator anchors",
    )
    results = _required_model_field(value, "results", label="receipt")
    residuals = _required_model_field(
        value, "quarantine_residuals", label="receipt"
    )
    findings = _required_model_field(
        value, "advisory_findings", label="receipt"
    )
    _require_exact_tuple(results, GateResult, label="receipt results")
    _require_exact_tuple(
        residuals,
        QuarantineResidualV1,
        label="receipt quarantine residuals",
    )
    _require_exact_tuple(
        findings,
        AdvisoryFindingV1,
        label="receipt advisory findings",
    )
    for result in results:
        _rehydrate_result(result)
    rebuilt = _strict_declared_rehydrate(
        value, LocalCiExecutionReceiptV3, label="local-CI receipt"
    )
    _rehydrate_manifest(rebuilt.candidate_manifest)
    _rehydrate_anchors(
        rebuilt.evaluator_anchors, label="rehydrated receipt evaluator anchors"
    )
    _require_exact_tuple(
        rebuilt.results, GateResult, label="rehydrated receipt results"
    )
    _require_exact_tuple(
        rebuilt.quarantine_residuals,
        QuarantineResidualV1,
        label="rehydrated receipt quarantine residuals",
    )
    _require_exact_tuple(
        rebuilt.advisory_findings,
        AdvisoryFindingV1,
        label="rehydrated receipt advisory findings",
    )
    return rebuilt


def resolve_gate_invocation(
    gate: GateSpec,
    candidate_manifest: CanonicalCandidateManifestV1,
    *,
    serializer: LocalCiSerializerProtocol | None = None,
) -> ResolvedGateInvocationV1:
    """Resolve one active route using only catalog and exact manifest bytes."""
    gate = _rehydrate_gate_spec(gate)
    candidate_manifest = _rehydrate_manifest(candidate_manifest)
    route = gate.route
    if isinstance(route, QuarantinedGateRouteV1):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.QUARANTINED_ROUTE,
            f"quarantined gate {gate.gate_id!r} has no executable route",
        )
    if isinstance(route, PythonGateRouteV1):
        resolved_inputs: tuple[str, ...] = ()
        resolved_argv = (sys.executable, "-B", *route.argv)
    elif isinstance(route, ToolGateRouteV1):
        resolved_inputs = tuple(
            entry.path
            for entry in candidate_manifest.entries
            if entry.blob_oid is not None and entry.path.endswith(".rs")
        )
        resolved_argv = (route.tool_id, *route.argv_prefix, *resolved_inputs)
    else:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "unsupported gate route",
        )
    active_serializer = serializer or get_local_ci_serializer()
    digest = active_serializer.resolved_invocation_digest(
        gate.gate_id, resolved_argv, resolved_inputs
    )
    return ResolvedGateInvocationV1(
        gate_id=gate.gate_id,
        resolved_argv=resolved_argv,
        resolved_inputs=resolved_inputs,
        resolved_invocation_sha256=digest,
    )


def build_gate_result(
    gate: GateSpec,
    candidate_manifest: CanonicalCandidateManifestV1,
    *,
    status: GateStatus,
    exit_code: int | None,
    duration_ms: int,
    detail: str,
) -> GateResult:
    """Bind measured details to the one pure resolution for an active gate."""
    resolved = resolve_gate_invocation(gate, candidate_manifest)
    return GateResult(
        gate_id=resolved.gate_id,
        status=status,
        resolved_argv=resolved.resolved_argv,
        resolved_inputs=resolved.resolved_inputs,
        resolved_invocation_sha256=resolved.resolved_invocation_sha256,
        exit_code=exit_code,
        duration_ms=duration_ms,
        detail=detail,
    )


def _quarantine_residuals() -> tuple[QuarantineResidualV1, ...]:
    _bind_gate_catalog()
    residuals: list[QuarantineResidualV1] = []
    for gate in quarantined_gate_specs():
        route = gate.route
        if not isinstance(route, QuarantinedGateRouteV1):
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.INVALID_RECORD,
                "quarantined catalog entry has an active route",
            )
        residuals.append(
            QuarantineResidualV1(
                gate_id=gate.gate_id,
                residual_code=route.residual_code,
                legacy_route=route.legacy_route,
                reason=route.reason,
            )
        )
    return tuple(residuals)


def _validated_results(results: Sequence[GateResult]) -> tuple[GateResult, ...]:
    if not results:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.EMPTY_RESULTS,
            "active gate results must not be empty",
        )
    try:
        return _rehydrate_results(results)
    except LocalCiReceiptError as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.MALFORMED_RESULT,
            "one or more gate results violate the declared strict base schema",
        ) from error


def _validate_result_ids(
    exact_results: tuple[GateResult, ...],
    active: tuple[GateSpec, ...],
) -> None:
    _bind_gate_catalog()
    result_ids = tuple(result.gate_id for result in exact_results)
    if len(set(result_ids)) != len(result_ids):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.DUPLICATE_RESULT,
            "a gate result identifier appears more than once",
        )
    for gate_id in result_ids:
        spec = _GATE_BY_ID.get(gate_id)
        if spec is None:
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.UNKNOWN_RESULT,
                f"unknown gate result {gate_id!r}",
            )
        if spec.disposition is GateDisposition.QUARANTINED:
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.QUARANTINED_GATE_EXECUTED,
                f"quarantined gate {gate_id!r} cannot produce a result",
            )
    expected_ids = tuple(gate.gate_id for gate in active)
    if len(exact_results) != len(active):
        missing = tuple(gate_id for gate_id in expected_ids if gate_id not in result_ids)
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.MISSING_RESULT,
            f"active gate result set is incomplete; missing={missing!r}",
        )
    if result_ids != expected_ids:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.RESULT_ORDER_MISMATCH,
            "active gate results are not in canonical catalog order",
        )


def _evaluate_one_result(
    gate: GateSpec,
    result: GateResult,
    candidate_manifest: CanonicalCandidateManifestV1,
) -> AdvisoryFindingV1 | None:
    resolved = resolve_gate_invocation(gate, candidate_manifest)
    measured_binding = (
        result.resolved_argv,
        result.resolved_inputs,
        result.resolved_invocation_sha256,
    )
    expected_binding = (
        resolved.resolved_argv,
        resolved.resolved_inputs,
        resolved.resolved_invocation_sha256,
    )
    if measured_binding != expected_binding:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.RESULT_BINDING_MISMATCH,
            f"gate result {gate.gate_id!r} is not bound to exact resolution",
        )
    if result.duration_ms > gate.timeout_seconds * 1_000 + 1_000:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.DURATION_OUT_OF_BOUNDS,
            f"gate result {gate.gate_id!r} exceeds its timeout envelope",
        )
    if result.status in {GateStatus.SKIP, GateStatus.BYPASS}:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.SKIP_OR_BYPASS_REFUSED,
            f"{result.status.value} is never a local-CI result",
        )
    if gate.disposition is GateDisposition.REQUIRED:
        if result.status is not GateStatus.PASS:
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.REQUIRED_GATE_NONPASS,
                f"required gate {gate.gate_id!r} did not pass",
            )
        return None
    if result.status not in {
        GateStatus.FAIL,
        GateStatus.TIMEOUT,
        GateStatus.UNAVAILABLE,
    }:
        return None
    return AdvisoryFindingV1(
        gate_id=gate.gate_id,
        status=result.status.value,
        detail=result.detail,
    )


def evaluate_gate_results(
    results: Sequence[GateResult],
    *,
    candidate_manifest: CanonicalCandidateManifestV1,
) -> GateEvaluationV1:
    """Evaluate one strict, ordered, complete active result sequence."""
    _bind_gate_catalog()
    candidate_manifest = _rehydrate_manifest(candidate_manifest)
    exact_results = _validated_results(results)
    active = active_gate_specs()
    _validate_result_ids(exact_results, active)

    findings: list[AdvisoryFindingV1] = []
    for gate, result in zip(active, exact_results, strict=True):
        finding = _evaluate_one_result(gate, result, candidate_manifest)
        if finding is not None:
            findings.append(finding)
    verdict = (
        LocalCiVerdict.PREFLIGHT_PASS_WITH_ADVISORY_FINDINGS
        if findings
        else LocalCiVerdict.PREFLIGHT_PASS
    )
    return GateEvaluationV1(
        verdict=verdict,
        advisory_findings=tuple(findings),
        quarantine_residuals=_quarantine_residuals(),
    )


def build_local_ci_receipt(
    invocation: LocalCiInvocationV1,
    *,
    observed_head_after: str,
    observed_main_after: str,
    results: Sequence[GateResult],
    serializer: LocalCiSerializerProtocol | None = None,
) -> LocalCiExecutionReceiptV3:
    """Build a receipt only after strict evaluation and no head/main drift."""
    try:
        exact_invocation = _rehydrate_invocation(invocation)
        head_after = _git_oid(observed_head_after, field="observed_head_after")
        main_after = _git_oid(observed_main_after, field="observed_main_after")
    except (
        TypeError,
        ValueError,
        ValidationError,
        LocalCiReceiptError,
    ) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "invocation or post-run observation is malformed",
        ) from error
    if head_after != exact_invocation.expected_head:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.RECEIPT_BINDING_MISMATCH,
            "observed_head_after does not equal expected_head",
        )
    if main_after != exact_invocation.expected_main:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.RECEIPT_BINDING_MISMATCH,
            "observed_main_after does not equal expected_main",
        )
    exact_results = _validated_results(results)
    active_serializer = serializer or get_local_ci_serializer()
    results_sha256 = active_serializer.canonical_gate_results_sha256(exact_results)
    evaluation = evaluate_gate_results(
        exact_results, candidate_manifest=exact_invocation.candidate_manifest
    )
    return LocalCiExecutionReceiptV3(
        expected_head=exact_invocation.expected_head,
        observed_head_before=exact_invocation.observed_head_before,
        observed_head_after=head_after,
        expected_main=exact_invocation.expected_main,
        observed_main_before=exact_invocation.observed_main_before,
        observed_main_after=main_after,
        nonce=exact_invocation.nonce,
        gate_catalog_sha256=exact_invocation.gate_catalog_sha256,
        candidate_manifest=exact_invocation.candidate_manifest,
        evaluator_anchors=exact_invocation.evaluator_anchors,
        results=exact_results,
        results_sha256=results_sha256,
        quarantine_residuals=evaluation.quarantine_residuals,
        advisory_findings=evaluation.advisory_findings,
        verdict=evaluation.verdict,
    )
