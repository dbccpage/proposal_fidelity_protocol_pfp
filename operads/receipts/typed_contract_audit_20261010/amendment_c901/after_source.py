"""Finite, freshly replayed typed-contract evidence; live activation stays held.

The compiler is injected by the composition root. Neither a catalog declaration
nor this receipt grants anti-skill admission or production activation.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

from ..domain.anti_skills import (
    AntiSkillEvaluationReceiptV2,
    AntiSkillFixtureBankV1,
    AntiSkillHitV1,
    AntiSkillSpecV2,
    AntiSkillSubjectV1,
    canonical_id,
    canonical_json_bytes,
)
from ..domain.capability_catalog_v1 import (
    CapabilityCatalogV1,
    decode_capability_catalog,
    encode_capability_catalog,
)
from ..domain.entities.typed_contract_package import CompiledTypedPackageV1
from .anti_skill.anti_skill_v2 import evaluate_antiskill_fixture_bank
from .woland_candidate_plan import PlanNodeV01, PlanRefusal
from .woland_instruction_admission import (
    InstructionAdmissionRefusal,
    VerifiedInstructionAdmissionV01,
    verify_signed_instruction_admission,
)
from .woland_task_selection import (
    WolandCandidateRouteV01,
    WolandTaskShapeV01,
    select_candidate_plan,
)

_LOCUS = "oewas.typed_contract_audit"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_CATALOG_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class TypedContractAuditReceiptV1:
    contracts_digest: str
    catalog_digest: str
    subject_id: str
    spec_digest: str
    fixture_bank_id: str
    implementation_digest: str
    evaluation_receipt: AntiSkillEvaluationReceiptV2
    hits: tuple[()] | tuple[AntiSkillHitV1]
    disposition: Literal["CLEAN", "FINDING"]
    admission: Literal["Unadmitted"] = "Unadmitted"
    runtime_activation: Literal["HOLD"] = "HOLD"
    authority_effect: Literal["None"] = "None"
    receipt_id: str = ""

    def __post_init__(self) -> None:
        for value in (
            self.contracts_digest,
            self.subject_id,
            self.spec_digest,
            self.fixture_bank_id,
            self.implementation_digest,
        ):
            if type(value) is not str or _DIGEST.fullmatch(value) is None:
                raise ValueError("audit evidence requires canonical SHA-256 identifiers")
        if (
            type(self.catalog_digest) is not str
            or _CATALOG_DIGEST.fullmatch(self.catalog_digest) is None
        ):
            raise ValueError("audit catalog digest is invalid")
        self._validate_evidence_bindings()
        if (self.admission, self.runtime_activation, self.authority_effect) != (
            "Unadmitted",
            "HOLD",
            "None",
        ):
            raise ValueError("finite evidence cannot promote admission or activation")
        payload = asdict(self)
        payload.pop("receipt_id")
        expected = canonical_id("oewas.typed_contract.audit_receipt.v1", payload)
        if self.receipt_id and self.receipt_id != expected:
            raise ValueError("audit receipt identifier does not bind its content")
        object.__setattr__(self, "receipt_id", expected)

    def _validate_evidence_bindings(self) -> None:
        if type(self.evaluation_receipt) is not AntiSkillEvaluationReceiptV2:
            raise TypeError("audit requires an exact evaluation receipt")
        evaluation = self.evaluation_receipt
        if (
            evaluation.outcome != "COMPUTED_PASS"
            or evaluation.spec_digest != self.spec_digest
            or evaluation.fixture_bank_id != self.fixture_bank_id
            or evaluation.implementation_digest != self.implementation_digest
        ):
            raise ValueError("audit evaluation evidence is not a passing exact binding")
        if type(self.hits) is not tuple or any(
            type(hit) is not AntiSkillHitV1 for hit in self.hits
        ):
            raise TypeError("audit hits must be an exact typed tuple")
        if len(self.hits) > 1:
            raise ValueError("a single-detector receipt has at most one hit")
        if any(hit.subject_id != self.subject_id for hit in self.hits):
            raise ValueError("audit hit belongs to a different subject")
        if self.disposition != ("FINDING" if self.hits else "CLEAN"):
            raise ValueError("audit disposition must follow actual hits")

    def to_dict(self) -> dict:
        """Emit exactly the dataclass fields, including typed evaluation and hits."""
        return json.loads(canonical_json_bytes(asdict(self)))


def _refused(code: str, message: str) -> Err[Refusal]:
    return Err(Refusal(code, message, _LOCUS))


def _fresh_package(
    compile_current: Callable[[], CompiledTypedPackageV1],
) -> Result[CompiledTypedPackageV1, Refusal]:
    if not callable(compile_current):
        return _refused("TYPED_CONTRACT_SOURCE_REFUSED", "fresh compiler callback is required")
    try:
        package = compile_current()
        if (
            type(package) is not CompiledTypedPackageV1
            or type(package.catalog) is not CapabilityCatalogV1
            or type(package.anti_spec) is not AntiSkillSpecV2
            or type(package.fixture_bank) is not AntiSkillFixtureBankV1
            or type(package.contracts_digest) is not str
            or _DIGEST.fullmatch(package.contracts_digest) is None
        ):
            return _refused(
                "TYPED_CONTRACT_PACKAGE_REFUSED", "compiler returned an invalid typed package"
            )
        decode_capability_catalog(encode_capability_catalog(package.catalog))
        return Ok(package)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        return _refused(
            "TYPED_CONTRACT_SOURCE_REFUSED",
            f"fresh compilation failed ({type(exc).__name__})",
        )


def _audit_package(
    subject: AntiSkillSubjectV1,
    package: CompiledTypedPackageV1,
    expected_contracts_digest: str | None,
) -> Result[TypedContractAuditReceiptV1, Refusal]:
    if expected_contracts_digest is not None and (
        type(expected_contracts_digest) is not str
        or _DIGEST.fullmatch(expected_contracts_digest) is None
        or expected_contracts_digest != package.contracts_digest
    ):
        return _refused(
            "TYPED_CONTRACT_BINDING_MISMATCH",
            "current contracts differ from the external digest binding",
        )
    replayed = evaluate_antiskill_fixture_bank((package.anti_spec,), package.fixture_bank)
    if isinstance(replayed, Err):
        return replayed
    (evaluation,) = replayed.value
    if evaluation.outcome != "COMPUTED_PASS":
        return _refused("TYPED_CONTRACT_CONTROLS_FAILED", "fresh fixture evidence did not pass")
    spec = package.anti_spec
    hits = (
        (
            AntiSkillHitV1(
                spec_id=spec.spec_id,
                failure_code=spec.failure_code,
                disposition=spec.disposition,
                subject_id=subject.subject_id,
                protected_fields=spec.protected_fields,
            ),
        )
        if spec.predicate.matches(subject)
        else ()
    )
    return Ok(
        TypedContractAuditReceiptV1(
            contracts_digest=package.contracts_digest,
            catalog_digest=package.catalog.catalog_digest,
            subject_id=subject.subject_id,
            spec_digest=spec.spec_digest,
            fixture_bank_id=package.fixture_bank.bank_id,
            implementation_digest=evaluation.implementation_digest,
            evaluation_receipt=evaluation,
            hits=hits,
            disposition="FINDING" if hits else "CLEAN",
        )
    )


def _fresh_audit(
    subject: AntiSkillSubjectV1,
    compile_current: Callable[[], CompiledTypedPackageV1],
    expected_contracts_digest: str | None,
) -> Result[tuple[CompiledTypedPackageV1, TypedContractAuditReceiptV1], Refusal]:
    if type(subject) is not AntiSkillSubjectV1:
        return _refused(
            "TYPED_CONTRACT_SUBJECT_REFUSED", "an exact typed anti-skill subject is required"
        )
    try:
        AntiSkillSubjectV1.from_dict(subject.to_dict())
    except (TypeError, ValueError):
        return _refused(
            "TYPED_CONTRACT_SUBJECT_REFUSED", "subject content does not bind its identifier"
        )
    package = _fresh_package(compile_current)
    if isinstance(package, Err):
        return package
    audited = _audit_package(subject, package.value, expected_contracts_digest)
    if isinstance(audited, Err):
        return audited
    return Ok((package.value, audited.value))


def audit_typed_contracts(
    subject: AntiSkillSubjectV1,
    *,
    compile_current: Callable[[], CompiledTypedPackageV1],
    expected_contracts_digest: str | None = None,
) -> Result[TypedContractAuditReceiptV1, Refusal]:
    """Compile current bytes and replay finite controls before checking a subject.

    An expected digest is supplied by the caller when replay custody matters.
    No previous audit receipt or self-declared PASS is accepted as evidence.
    """
    fresh = _fresh_audit(subject, compile_current, expected_contracts_digest)
    if isinstance(fresh, Err):
        return fresh
    return Ok(fresh.value[1])


@dataclass(frozen=True, slots=True)
class TypedContractInstructionAdmissionV1:
    """External signed instruction evidence; the detector remains unadmitted."""

    audit: TypedContractAuditReceiptV1
    instruction_admission: VerifiedInstructionAdmissionV01
    admission_scope: Literal["SIGNED_INSTRUCTION_ONLY"] = "SIGNED_INSTRUCTION_ONLY"

    def __post_init__(self) -> None:
        if (
            type(self.audit) is not TypedContractAuditReceiptV1
            or type(self.instruction_admission) is not VerifiedInstructionAdmissionV01
            or self.admission_scope != "SIGNED_INSTRUCTION_ONLY"
            or self.audit.hits
            or self.instruction_admission.request_digest != self.audit.subject_id
            or self.instruction_admission.authority_effect != "None"
        ):
            raise ValueError("instruction evidence requires the exact clean audit binding")

    def to_dict(self) -> dict:
        return json.loads(canonical_json_bytes(asdict(self)))


def verify_typed_contract_admission(
    subject: AntiSkillSubjectV1,
    *,
    compile_current: Callable[[], CompiledTypedPackageV1],
    task: WolandTaskShapeV01,
    manifest_bytes: bytes,
    signature_path: Path,
    allowed_signers_path: Path,
    ssh_keygen: str | None = None,
    expected_contracts_digest: str | None = None,
) -> Result[TypedContractInstructionAdmissionV1, Refusal]:
    """Replay and select current typed instructions before verifying a signature.

    The caller supplies an operator-controlled external signer trust root.
    The signed request must be the exact audited subject identifier. This
    verifies instruction custody only: no detector registry, live admission,
    guard-trio replacement or Woland dispatch is performed.
    """
    fresh = _fresh_audit(subject, compile_current, expected_contracts_digest)
    if isinstance(fresh, Err):
        return fresh
    package, audit = fresh.value
    if audit.hits:
        return _refused(
            "TYPED_CONTRACT_SUBJECT_FALSIFIED", "actual predicate found a scope overclaim"
        )
    if type(task) is not WolandTaskShapeV01 or task.request_digest != subject.subject_id:
        return _refused(
            "TYPED_CONTRACT_TASK_BINDING_MISMATCH",
            "task request must bind the exact audited subject",
        )
    try:
        root = PlanNodeV01("woland-claim-audit", ((0, PlanNodeV01("woland-scope-falsifier")),))
        route = WolandCandidateRouteV01(
            "route.typed-contract-audit",
            task.workload_profile_id,
            task.workload_profile_digest,
            task.domain_id,
            package.documents,
            root,
        )
        selected = select_candidate_plan(task, (route,))
        instruction = verify_signed_instruction_admission(
            manifest_bytes,
            signature_path=signature_path,
            allowed_signers_path=allowed_signers_path,
            selected=selected,
            task=task,
            request_digest=subject.subject_id,
            ssh_keygen=ssh_keygen,
        )
        return Ok(TypedContractInstructionAdmissionV1(audit, instruction))
    except (InstructionAdmissionRefusal, PlanRefusal) as exc:
        return _refused(exc.code, str(exc))
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        return _refused(
            "TYPED_CONTRACT_ADMISSION_REFUSED",
            f"instruction verification failed ({type(exc).__name__})",
        )
