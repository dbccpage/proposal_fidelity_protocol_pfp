"""Use Cases for receipt verification against external inputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from omega_engine_operations.domain.cicd import (
    LocalCiExecutionReceiptV3,
    LocalCiVerificationInputsV1,
    _git_oid,
    _sha256,
)
from omega_engine_operations.domain.cicd.errors import (
    LocalCiReceiptError,
    LocalCiReceiptErrorCode,
)
from omega_engine_operations.domain.cicd.protocols import (
    LocalCiSerializerProtocol,
    get_local_ci_serializer,
)
from omega_engine_operations.use_cases.cicd.gate_resolution import (
    _rehydrate_receipt,
    _rehydrate_verification_inputs,
    evaluate_gate_results,
)


def verify_local_ci_receipt(
    receipt: LocalCiExecutionReceiptV3,
    *,
    expected_head: str,
    expected_main: str,
    nonce: str,
    verification_inputs: LocalCiVerificationInputsV1,
    serializer: LocalCiSerializerProtocol | None = None,
) -> LocalCiExecutionReceiptV3:
    """Verify a receipt against every independently supplied exact binding."""
    active_serializer = serializer or get_local_ci_serializer()
    try:
        exact_receipt = _rehydrate_receipt(receipt)
        exact_inputs = _rehydrate_verification_inputs(verification_inputs)
        external_head = _git_oid(expected_head, field="expected_head")
        external_main = _git_oid(expected_main, field="expected_main")
        external_nonce = _sha256(nonce, field="nonce")
    except (
        TypeError,
        ValueError,
        ValidationError,
        LocalCiReceiptError,
    ) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "receipt or verification input violates the strict schema",
        ) from error

    expected_bindings: Mapping[str, Any] = {
        "expected_head": external_head,
        "expected_main": external_main,
        "nonce": external_nonce,
        "observed_head_before": exact_inputs.observed_head_before,
        "observed_head_after": exact_inputs.observed_head_after,
        "observed_main_before": exact_inputs.observed_main_before,
        "observed_main_after": exact_inputs.observed_main_after,
        "candidate_manifest": exact_inputs.candidate_manifest,
        "evaluator_anchors": exact_inputs.evaluator_anchors,
        "gate_catalog_sha256": active_serializer.canonical_gate_catalog_sha256(),
        "results_sha256": exact_inputs.expected_results_sha256,
    }
    for field, expected_value in expected_bindings.items():
        if getattr(exact_receipt, field) != expected_value:
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.RECEIPT_BINDING_MISMATCH,
                f"receipt field {field!r} does not match external input",
            )

    evaluation = evaluate_gate_results(
        exact_receipt.results,
        candidate_manifest=exact_receipt.candidate_manifest,
    )
    if exact_receipt.results_sha256 != active_serializer.canonical_gate_results_sha256(
        exact_receipt.results
    ):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.RECEIPT_DERIVATION_MISMATCH,
            "receipt result digest does not match ordered strict results",
        )
    if (
        exact_receipt.quarantine_residuals != evaluation.quarantine_residuals
        or exact_receipt.advisory_findings != evaluation.advisory_findings
        or exact_receipt.verdict is not evaluation.verdict
    ):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.RECEIPT_DERIVATION_MISMATCH,
            "receipt projections do not match canonical result evaluation",
        )
    return exact_receipt
