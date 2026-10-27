"""Domain models and value objects for the Adversary Swarm.

Origin: adversary bout request, receipt, and outcome schemas.
Claim: AUTHORIZED status requires an ACCEPTED checker verdict bound by digest.
Scope fence: this file does not claim a mathematical certificate for residual mass.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, cast

from governance.domain.ingress.limits import (
    MAX_ADMITTED_TEXT_BYTES,
    REFUSAL_TEXT_TOO_LARGE,
    check_text_bytes,
)
from adversary.stage.domain.canonical import IDENTIFIER

from .circuit import validate_algorithm_metadata
from .evidence import canonical_rational, is_sha256_ref, parse_exact_rational
from .specialization import SwarmTypeV1

_LOWERCASE_SHA256 = re.compile(r"[0-9a-f]{64}\Z")

#: Terminal statuses Act VII can return. Only AUTHORIZED has is_authorized true.
BOUT_STATUSES = frozenset(
    {
        "AUTHORIZED",
        "BOUNDED_RESIDUAL",
        "NOT_MEASURED",
        "REFUSED",
        "ABLATED_WOULD_AUTHORIZE",
        "FIXTURE_ONLY",
    }
)
MEASUREMENT_STATUSES = frozenset({"MEASURED", "NOT_MEASURED"})
CHECKER_VERDICTS = frozenset({"ACCEPTED", "REJECTED", "NOT_MEASURED"})
#: The evidence path of an AUTHORIZED bout; ``None`` for every other status.
AUTHORIZATION_EVIDENCE_PATHS = frozenset(
    {
        "CHECKER_VERDICT_ONLY_NO_CARRIER_DECLARED",
        "CHECKER_VERDICT_AND_EXACT_ZERO_CARRIER",
    }
)


def _check_evidence_path(status: str, measurement_status: str, path: Any) -> None:
    if (status == "AUTHORIZED") != (path is not None):
        raise ValueError("authorization_evidence is set exactly when the status is AUTHORIZED")
    if path is None:
        return
    if path not in AUTHORIZATION_EVIDENCE_PATHS:
        raise ValueError(f"unknown authorization evidence path {path!r}")
    if (path == "CHECKER_VERDICT_AND_EXACT_ZERO_CARRIER") != (measurement_status == "MEASURED"):
        raise ValueError("the carrier evidence path requires a measured carrier, and only it")


def _check_exact_text(value: Any, name: str) -> None:
    """``None`` (not measured) or a canonical exact rational string such as ``"3/2"``."""
    if value is None:
        return
    if type(value) is not str:
        raise TypeError(f"{name} must be None or a canonical rational string")
    parsed = parse_exact_rational(value)
    if canonical_rational(parsed) != value:
        raise ValueError(f"{name} must be in canonical rational form")


def _check_optional_digest(value: Any, name: str) -> None:
    if value is not None and not is_sha256_ref(value):
        raise ValueError(f"{name} must be None or a sha256:<hex> reference")


def _admit_request_text(objective: object, task_key: object) -> None:
    for value, field_name in ((objective, "objective"), (task_key, "task_key")):
        if type(value) is not str:
            raise ValueError(f"{field_name} must be a normalized nonempty string")
        check_text_bytes(
            value,
            limit=MAX_ADMITTED_TEXT_BYTES,
            refusal_code=REFUSAL_TEXT_TOO_LARGE,
        )
        if not value or value.strip() != value:
            raise ValueError(f"{field_name} must be a normalized nonempty string")
    if IDENTIFIER.fullmatch(cast(str, task_key)) is None:
        raise ValueError(
            "task_key must be a canonical identifier: ASCII letters, digits and ._:/@-"
        )


def _admit_request_bounds(request: "AdversaryBoutRequestV1") -> None:
    if type(request.max_rounds) is not int or not 1 <= request.max_rounds <= 10:
        raise ValueError("max_rounds must be an integer from 1 through 10")
    if type(request.fixture_mode) is not bool:
        raise TypeError("fixture_mode must be an exact bool")
    if type(request.request_external_admission) is not bool:
        raise TypeError("request_external_admission must be an exact bool")
    if request.authority_effect != "None":
        raise ValueError("Adversary bout requests have AuthorityEffect None")
    if not isinstance(request.carrier_context, dict):
        raise TypeError("carrier_context must be a dict")
    if not isinstance(request.ablation_flags, dict):
        raise TypeError("ablation_flags must be a dict")
    if type(request.compute_budget) is not int or request.compute_budget <= 0:
        raise ValueError("compute_budget must be a positive integer")


def _request_same(left: "AdversaryBoutRequestV1", right: "AdversaryBoutRequestV1") -> bool:
    return (
        left.objective == right.objective
        and left.task_key == right.task_key
        and left.max_rounds == right.max_rounds
        and left.fixture_mode == right.fixture_mode
        and left.request_external_admission == right.request_external_admission
        and left.authority_effect == right.authority_effect
        and left.carrier_context == right.carrier_context
        and left.ablation_flags == right.ablation_flags
        and left.compute_budget == right.compute_budget
        and left.swarm_type == right.swarm_type
    )


def _admit_receipt_identity(receipt: "AdversaryBoutReceiptV1") -> None:
    for str_field in ("task_key", "receipt_id", "status", "selected_candidate_id"):
        val = getattr(receipt, str_field)
        if type(val) is not str:
            raise TypeError(f"{str_field} must be an exact string, got {type(val).__name__}")
    if receipt.status not in BOUT_STATUSES:
        raise ValueError(f"status {receipt.status!r} is not one of {sorted(BOUT_STATUSES)}")
    if type(receipt.letter_tape) is not str:
        raise TypeError(
            f"letter_tape must be an exact string, got {type(receipt.letter_tape).__name__}"
        )
    if receipt.authority_effect != "None":
        raise ValueError("Adversary bout receipts must have authority_effect == 'None'")


def _admit_receipt_measurement(receipt: "AdversaryBoutReceiptV1") -> None:
    _check_exact_text(receipt.phi1, "phi1")
    _check_exact_text(receipt.gamma2, "gamma2")
    if receipt.measurement_status not in MEASUREMENT_STATUSES:
        raise ValueError("measurement_status must be MEASURED or NOT_MEASURED")
    measured = receipt.measurement_status == "MEASURED"
    present = receipt.phi1 is not None and receipt.gamma2 is not None
    if measured != present:
        raise ValueError("phi1 and gamma2 are present exactly when MEASURED")
    _check_optional_digest(receipt.checker_receipt_sha256, "checker_receipt_sha256")
    if receipt.checker_verdict not in CHECKER_VERDICTS:
        raise ValueError("checker_verdict must be ACCEPTED, REJECTED or NOT_MEASURED")
    object.__setattr__(receipt, "authorization_blockers", tuple(receipt.authorization_blockers))
    if any(type(item) is not str for item in receipt.authorization_blockers):
        raise TypeError("authorization_blockers must be strings")


def _admit_receipt_authorization(receipt: "AdversaryBoutReceiptV1") -> None:
    accepted = receipt.checker_verdict == "ACCEPTED" and receipt.checker_receipt_sha256 is not None
    if receipt.status == "AUTHORIZED" and not accepted:
        raise ValueError("an AUTHORIZED receipt must bind an ACCEPTED checker verdict by digest")
    _check_evidence_path(receipt.status, receipt.measurement_status, receipt.authorization_evidence)
    validate_algorithm_metadata(
        receipt.ddc_trace_hash,
        receipt.lggr_joint_kernel_status,
        receipt.phi1,
        receipt.gamma2,
        receipt.carrier_degree,
    )
    joint_zero = receipt.phi1 == "0" and receipt.gamma2 == "0"
    if receipt.status == "AUTHORIZED" and receipt.phi1 is not None and not joint_zero:
        raise ValueError("AUTHORIZED measured carrier must have exact joint zero")


def _receipt_identity_same(left: "AdversaryBoutReceiptV1", right: "AdversaryBoutReceiptV1") -> bool:
    return (
        left.task_key == right.task_key
        and left.receipt_id == right.receipt_id
        and left.status == right.status
        and left.selected_candidate_id == right.selected_candidate_id
        and left.novella_sha256 == right.novella_sha256
        and left.ddc_sha256 == right.ddc_sha256
        and left.summary_sha256 == right.summary_sha256
        and left.lean4_proof_hash == right.lean4_proof_hash
    )


def _receipt_carrier_same(left: "AdversaryBoutReceiptV1", right: "AdversaryBoutReceiptV1") -> bool:
    return (
        left.phi1 == right.phi1
        and left.gamma2 == right.gamma2
        and left.defect_count == right.defect_count
        and left.ablation_flags == right.ablation_flags
        and left.authority_effect == right.authority_effect
        and left.letter_tape == right.letter_tape
        and left.measurement_status == right.measurement_status
    )


def _receipt_checker_same(left: "AdversaryBoutReceiptV1", right: "AdversaryBoutReceiptV1") -> bool:
    return (
        left.checker_receipt_sha256 == right.checker_receipt_sha256
        and left.checker_verdict == right.checker_verdict
        and left.authorization_blockers == right.authorization_blockers
        and left.authorization_evidence == right.authorization_evidence
        and left.ddc_trace_hash == right.ddc_trace_hash
        and left.lggr_joint_kernel_status == right.lggr_joint_kernel_status
        and left.carrier_degree == right.carrier_degree
    )


def _admit_outcome_status(outcome: "AdversaryBoutOutcomeV1") -> None:
    if type(outcome.swarm_type) is not str:
        raise TypeError("swarm_type must be a string")
    if outcome.status not in BOUT_STATUSES:
        raise ValueError(f"status {outcome.status!r} is not one of {sorted(BOUT_STATUSES)}")
    _check_exact_text(outcome.phi1, "phi1")
    _check_exact_text(outcome.gamma2, "gamma2")
    if outcome.measurement_status not in MEASUREMENT_STATUSES:
        raise ValueError("measurement_status must be MEASURED or NOT_MEASURED")
    if outcome.checker_verdict not in CHECKER_VERDICTS:
        raise ValueError("checker_verdict must be ACCEPTED, REJECTED or NOT_MEASURED")
    _check_optional_digest(outcome.checker_receipt_sha256, "checker_receipt_sha256")


def _admit_outcome_blockers(outcome: "AdversaryBoutOutcomeV1") -> None:
    object.__setattr__(outcome, "authorization_blockers", tuple(outcome.authorization_blockers))
    if any(type(item) is not str for item in outcome.authorization_blockers):
        raise TypeError("authorization_blockers must be strings")
    _check_evidence_path(outcome.status, outcome.measurement_status, outcome.authorization_evidence)


def _admit_outcome_authorization(outcome: "AdversaryBoutOutcomeV1") -> None:
    if type(outcome.is_authorized) is not bool:
        raise TypeError("is_authorized must be an exact bool")
    if outcome.is_authorized != (outcome.status == "AUTHORIZED"):
        raise ValueError("is_authorized must equal (status == 'AUTHORIZED')")
    _admit_outcome_blockers(outcome)
    accepted = outcome.checker_verdict == "ACCEPTED" and outcome.checker_receipt_sha256 is not None
    if outcome.is_authorized and not accepted:
        raise ValueError("a result is authorized only with an ACCEPTED checker verdict bound by digest")
    if outcome.is_authorized != (outcome.authorization_evidence is not None):
        raise ValueError("authorization_evidence is set exactly when the result is authorized")
    known = outcome.authorization_evidence in AUTHORIZATION_EVIDENCE_PATHS
    if outcome.authorization_evidence is not None and not known:
        raise ValueError(f"unknown authorization evidence path {outcome.authorization_evidence!r}")


def _outcome_paths_same(left: "AdversaryBoutOutcomeV1", right: "AdversaryBoutOutcomeV1") -> bool:
    return (
        left.receipt_id == right.receipt_id
        and left.selected_candidate_id == right.selected_candidate_id
        and left.disposition == right.disposition
        and left.consecration_state == right.consecration_state
        and left.terminal_verdict == right.terminal_verdict
        and left.authority_effect == right.authority_effect
        and left.task_key == right.task_key
        and left.status == right.status
        and left.receipt_path == right.receipt_path
    )


def _outcome_measure_same(left: "AdversaryBoutOutcomeV1", right: "AdversaryBoutOutcomeV1") -> bool:
    return (
        left.novella_path == right.novella_path
        and left.ddc_path == right.ddc_path
        and left.summary_path == right.summary_path
        and left.phi1 == right.phi1
        and left.gamma2 == right.gamma2
        and left.defect_count == right.defect_count
        and left.residual_declared == right.residual_declared
        and left.is_authorized == right.is_authorized
        and left.measurement_status == right.measurement_status
    )


def _outcome_report_same(left: "AdversaryBoutOutcomeV1", right: "AdversaryBoutOutcomeV1") -> bool:
    return (
        left.checker_verdict == right.checker_verdict
        and left.checker_receipt_sha256 == right.checker_receipt_sha256
        and left.authorization_blockers == right.authorization_blockers
        and left.authorization_evidence == right.authorization_evidence
        and left.swarm_type == right.swarm_type
        and left.reporting_status == right.reporting_status
        and left.reporting_failure_code == right.reporting_failure_code
        and left.working_state_path == right.working_state_path
    )


@dataclass(frozen=True)
class AdversaryBoutRequestV1:
    """Request Value Object for initiating a Adversary 7-Act dialectic bout."""

    schema_version: str = field(default="core.adversary.bout-request.v1", init=False)
    objective: str
    task_key: str
    max_rounds: int = 4
    fixture_mode: bool = True
    request_external_admission: bool = False
    authority_effect: str = "None"
    carrier_context: dict[str, Any] = field(default_factory=dict)
    ablation_flags: dict[str, bool] = field(default_factory=dict)
    compute_budget: int = 100
    swarm_type: SwarmTypeV1 = field(default=SwarmTypeV1.OPEN_TOPIC)

    def __post_init__(self) -> None:
        if isinstance(self.swarm_type, str):
            object.__setattr__(self, "swarm_type", SwarmTypeV1.from_str(self.swarm_type))
        elif type(self.swarm_type) is not SwarmTypeV1:
            raise TypeError("swarm_type must be a SwarmTypeV1 or valid string")
        # Byte ceiling before strip: strip copies the whole string.
        _admit_request_text(self.objective, self.task_key)
        _admit_request_bounds(self)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return _request_same(self, cast(AdversaryBoutRequestV1, other))

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.objective,
                self.task_key,
                self.max_rounds,
                self.fixture_mode,
                self.request_external_admission,
                self.authority_effect,
                tuple(sorted((k, str(v)) for k, v in self.carrier_context.items())),
                tuple(sorted(self.ablation_flags.items())),
                self.compute_budget,
                self.swarm_type,
            )
        )


@dataclass(frozen=True)
class AdversaryBoutReceiptV1:
    """StructureBench-compliant Value Object for Adversary bout execution receipts."""

    task_key: str
    receipt_id: str
    status: str
    selected_candidate_id: str
    novella_sha256: str = ""
    ddc_sha256: str = ""
    summary_sha256: str = ""
    lean4_proof_hash: str | None = None
    phi1: str | None = None
    gamma2: str | None = None
    defect_count: int = 0
    ablation_flags: dict[str, bool] = field(default_factory=dict)
    authority_effect: str = "None"
    final_state: Any = None
    selection_proposal: Any = None
    letter_tape: str = ""
    measurement_status: str = "NOT_MEASURED"
    checker_receipt_sha256: str | None = None
    checker_verdict: str = "NOT_MEASURED"
    authorization_blockers: tuple[str, ...] = ()
    authorization_evidence: str | None = None
    ddc_trace_hash: str | None = None
    lggr_joint_kernel_status: str = "NOT_MEASURED"
    carrier_degree: int | None = None

    def __post_init__(self) -> None:
        _admit_receipt_identity(self)
        _admit_receipt_measurement(self)
        _admit_receipt_authorization(self)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        peer = cast(AdversaryBoutReceiptV1, other)
        return (
            _receipt_identity_same(self, peer)
            and _receipt_carrier_same(self, peer)
            and _receipt_checker_same(self, peer)
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.task_key,
                self.receipt_id,
                self.status,
                self.selected_candidate_id,
                self.novella_sha256,
                self.ddc_sha256,
                self.summary_sha256,
                self.lean4_proof_hash,
                self.phi1,
                self.gamma2,
                self.defect_count,
                tuple(sorted(self.ablation_flags.items())),
                self.authority_effect,
                self.letter_tape,
                self.measurement_status,
                self.checker_receipt_sha256,
                self.checker_verdict,
                self.authorization_blockers,
                self.authorization_evidence,
                self.ddc_trace_hash,
                self.lggr_joint_kernel_status,
                self.carrier_degree,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ablation_flags": dict(self.ablation_flags),
            "authority_effect": self.authority_effect,
            "authorization_blockers": list(self.authorization_blockers),
            "authorization_evidence": self.authorization_evidence,
            "checker_receipt_sha256": self.checker_receipt_sha256,
            "checker_verdict": self.checker_verdict,
            "ddc_sha256": self.ddc_sha256,
            "ddc_trace_hash": self.ddc_trace_hash,
            "lggr_joint_kernel_status": self.lggr_joint_kernel_status,
            "carrier_degree": self.carrier_degree,
            "defect_count": self.defect_count,
            "gamma2": self.gamma2,
            "lean4_proof_hash": self.lean4_proof_hash,
            "letter_tape": self.letter_tape,
            "measurement_status": self.measurement_status,
            "novella_sha256": self.novella_sha256,
            "phi1": self.phi1,
            "receipt_id": self.receipt_id,
            "selected_candidate_id": self.selected_candidate_id,
            "status": self.status,
            "summary_sha256": self.summary_sha256,
            "task_key": self.task_key,
        }

    def is_clean(self) -> bool:
        """Return whether required identifiers and digest syntax are locally valid.

        This check does not read the four persisted artifacts. Consumers that
        need content verification must replay the StructureBench evaluator.
        """
        return (
            bool(self.task_key)
            and bool(self.receipt_id)
            and _LOWERCASE_SHA256.fullmatch(self.novella_sha256) is not None
            and _LOWERCASE_SHA256.fullmatch(self.ddc_sha256) is not None
            and _LOWERCASE_SHA256.fullmatch(self.summary_sha256) is not None
            and self.authority_effect == "None"
        )


@dataclass(frozen=True)
class AdversaryBoutOutcomeV1:
    """Result Value Object returned upon completing a Adversary 7-Act dialectic bout."""

    schema_version: str = field(default="core.adversary.bout-outcome.v1", init=False)
    receipt_id: str | None
    selected_candidate_id: str
    disposition: str
    consecration_state: str
    terminal_verdict: str
    authority_effect: str = "None"
    task_key: str = ""
    status: str = "REFUSED"
    receipt_path: str | None = ""
    novella_path: str | None = ""
    ddc_path: str | None = ""
    summary_path: str | None = ""
    phi1: str | None = None
    gamma2: str | None = None
    defect_count: int = 0
    residual_declared: bool = True
    is_authorized: bool = False
    measurement_status: str = "NOT_MEASURED"
    checker_verdict: str = "NOT_MEASURED"
    checker_receipt_sha256: str | None = None
    authorization_blockers: tuple[str, ...] = ()
    authorization_evidence: str | None = None
    swarm_type: str = "open-topic"
    reporting_status: str = "UNOBSERVED"
    reporting_failure_code: str | None = None
    working_state_path: str | None = None

    def __post_init__(self) -> None:
        _admit_outcome_status(self)
        _admit_outcome_authorization(self)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        peer = cast(AdversaryBoutOutcomeV1, other)
        return (
            _outcome_paths_same(self, peer)
            and _outcome_measure_same(self, peer)
            and _outcome_report_same(self, peer)
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.receipt_id,
                self.selected_candidate_id,
                self.disposition,
                self.consecration_state,
                self.terminal_verdict,
                self.authority_effect,
                self.task_key,
                self.status,
                self.receipt_path,
                self.novella_path,
                self.ddc_path,
                self.summary_path,
                self.phi1,
                self.gamma2,
                self.defect_count,
                self.residual_declared,
                self.is_authorized,
                self.measurement_status,
                self.checker_verdict,
                self.checker_receipt_sha256,
                self.authorization_blockers,
                self.authorization_evidence,
                self.swarm_type,
                self.reporting_status,
                self.reporting_failure_code,
                self.working_state_path,
            )
        )


@dataclass(frozen=True)
class SymbolGameRequestV1:
    """Pinned exact C011 challenge bytes for the Symbol Game certificate checker.

    The connector supports the existing exact cohomology verifier. Other
    challenge families need their own explicitly bound verifier.
    """

    case_json: str
    authority_effect: str = "None"
    schema_version: str = field(default="core.symbol-game.request.v1", init=False)
    checker_id: str = field(default="symbol_game.c011.exact.v1", init=False)

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("SymbolGameRequestV1 requires authority_effect == 'None'")
        if type(self.case_json) is not str:
            raise TypeError("case_json must be JSON text")
        check_text_bytes(
            self.case_json, limit=MAX_ADMITTED_TEXT_BYTES, refusal_code=REFUSAL_TEXT_TOO_LARGE
        )

        def reject_float(value: str) -> None:
            raise ValueError("Symbol Game exact requests must not contain float tokens")

        def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key!r}")
                result[key] = value
            return result

        case = json.loads(
            self.case_json, parse_float=reject_float, parse_constant=reject_float,
            object_pairs_hook=reject_duplicates,
        )
        if type(case) is not dict:
            raise ValueError("Symbol Game case must be an object")
        challenge = case.get("challenge") or case.get("challenge_id")
        if challenge != "c011":
            raise ValueError("this connector supports exact c011 certificates only")
        object.__setattr__(
            self,
            "case_json",
            json.dumps(case, sort_keys=True, separators=(",", ":"), allow_nan=False),
        )


__all__ = [
    "AUTHORIZATION_EVIDENCE_PATHS",
    "BOUT_STATUSES",
    "SymbolGameRequestV1",
    "AdversaryBoutReceiptV1",
    "AdversaryBoutRequestV1",
    "AdversaryBoutOutcomeV1",
]
