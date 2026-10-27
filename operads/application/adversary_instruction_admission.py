"""Independent, signed governance decision for one exact Adversary selection.

An OEWAS source document, candidate plan, or manifest field cannot approve
itself. The trusted SSH signer list is supplied outside the manifest. This
module verifies a decision; it does not dispatch Adversary or alter OEEIS guard
admission. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .adversary_task_selection import (
    SelectedCandidatePlanV01,
    AdversaryTaskShapeV01,
    task_shape_digest,
)

SCHEMA = "oewas.adversary.instruction_admission.v0.1"
SIGNATURE_NAMESPACE = "oewas-adversary-instruction-v0.1"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._@+-]{0,127}\Z")
_MAX_MANIFEST_BYTES = 8192
_MAX_SIGNATURE_BYTES = 8192
_FIELDS = frozenset({
    "schema_version", "decision", "reviewer_identity", "authority_effect",
    "request_digest", "task_shape_digest", "workload_profile_id",
    "workload_profile_digest", "domain_id", "selection_digest", "route_id",
    "plan_digest", "source_snapshot_digest",
})


class InstructionAdmissionRefusal(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def source_snapshot_digest(selected: SelectedCandidatePlanV01) -> str:
    """Bind every selected source path and its exact raw-byte digest."""
    if type(selected) is not SelectedCandidatePlanV01:
        raise InstructionAdmissionRefusal("SELECTION_INVALID")
    return "sha256:" + hashlib.sha256(_canonical({
        "schema": "oewas.adversary.source_snapshot.v0.1",
        "sources": selected.plan.source_digests,
    })).hexdigest()


def ordered_bodies_digest(bodies: tuple[str, ...]) -> str:
    """Digest ordered UTF-8 bodies with an unambiguous length-prefixed frame."""
    if type(bodies) is not tuple or not bodies or any(type(body) is not str for body in bodies):
        raise InstructionAdmissionRefusal("INSTRUCTION_BODIES_INVALID")
    hasher = hashlib.sha256(b"oewas.adversary.ordered_bodies.v0.1\0")
    for body in bodies:
        raw = body.encode("utf-8")
        hasher.update(len(raw).to_bytes(8, "big"))
        hasher.update(raw)
    return "sha256:" + hasher.hexdigest()


@dataclass(frozen=True, slots=True)
class VerifiedInstructionAdmissionV01:
    manifest_digest: str
    reviewer_identity: str
    request_digest: str
    task_shape_digest: str
    selection_digest: str
    route_id: str
    plan_digest: str
    source_snapshot_digest: str
    ordered_operand_bodies: tuple[str, ...]
    source_digests: tuple[tuple[str, str], ...]
    operation_ids: tuple[str, ...]
    instruction_bytes: int
    ordered_bodies_digest: str
    authority_effect: str = "None"


def instruction_plan_transport(admission: VerifiedInstructionAdmissionV01) -> dict:
    """Build the bounded native custody payload; this grants no live authority."""
    if type(admission) is not VerifiedInstructionAdmissionV01:
        raise InstructionAdmissionRefusal("ADMISSION_RECORD_INVALID")
    return {
        "schema_version": "oewas.adversary.instruction_plan_transport.v0.1",
        "manifest_digest": admission.manifest_digest,
        "selection_digest": admission.selection_digest,
        "plan_digest": admission.plan_digest,
        "source_snapshot_digest": admission.source_snapshot_digest,
        "ordered_bodies_digest": admission.ordered_bodies_digest,
        "ordered_operand_bodies": list(admission.ordered_operand_bodies),
        "source_digests": [list(row) for row in admission.source_digests],
        "operation_ids": list(admission.operation_ids),
        "instruction_bytes": admission.instruction_bytes,
        "authority_effect": "None",
    }


def verify_signed_instruction_admission(
    manifest_bytes: bytes,
    *,
    signature_path: Path,
    allowed_signers_path: Path,
    selected: SelectedCandidatePlanV01,
    task: AdversaryTaskShapeV01,
    request_digest: str,
    ssh_keygen: str | None = None,
) -> VerifiedInstructionAdmissionV01:
    """Check detached human signature and exact task, plan and source custody.

    ``allowed_signers_path`` is an operator-controlled trust root, never a
    path supplied by the signed manifest. The caller must freshly compile and
    select from current source bytes before invoking this function. A verified
    decision is evidence only; Adversary must separately bind plan consumption
    and obtain OEEIS clearance before live dispatch.
    """
    if type(manifest_bytes) is not bytes or not 0 < len(manifest_bytes) <= _MAX_MANIFEST_BYTES:
        raise InstructionAdmissionRefusal("MANIFEST_SIZE_INVALID")
    if type(task) is not AdversaryTaskShapeV01 or type(selected) is not SelectedCandidatePlanV01:
        raise InstructionAdmissionRefusal("SELECTION_INVALID")
    if type(request_digest) is not str or _DIGEST.fullmatch(request_digest) is None:
        raise InstructionAdmissionRefusal("REQUEST_DIGEST_INVALID")
    try:
        value = json.loads(manifest_bytes)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise InstructionAdmissionRefusal("MANIFEST_INVALID") from exc
    if type(value) is not dict or value.keys() != _FIELDS or _canonical(value) != manifest_bytes:
        raise InstructionAdmissionRefusal("MANIFEST_NONCANONICAL")
    if (
        value["schema_version"] != SCHEMA
        or value["decision"] != "APPROVE"
        or value["authority_effect"] != "None"
        or type(value["reviewer_identity"]) is not str
        or _IDENTITY.fullmatch(value["reviewer_identity"]) is None
    ):
        raise InstructionAdmissionRefusal("MANIFEST_DECISION_INVALID")
    for name in (
        "request_digest", "task_shape_digest", "workload_profile_digest",
        "selection_digest", "plan_digest", "source_snapshot_digest",
    ):
        if type(value[name]) is not str or _DIGEST.fullmatch(value[name]) is None:
            raise InstructionAdmissionRefusal("MANIFEST_DIGEST_INVALID")
    if any(type(value[name]) is not str or not value[name] for name in (
        "workload_profile_id", "domain_id", "route_id",
    )):
        raise InstructionAdmissionRefusal("MANIFEST_SCOPE_INVALID")
    if task.request_digest != request_digest or value["request_digest"] != request_digest:
        raise InstructionAdmissionRefusal("REQUEST_MISMATCH")
    if selected.admission != "Unadmitted" or selected.plan.admission != "Unadmitted":
        raise InstructionAdmissionRefusal("SELECTION_INVALID")
    if task_shape_digest(task) != selected.task_shape_digest:
        raise InstructionAdmissionRefusal("PLAN_OR_SCOPE_MISMATCH")
    expected = {
        "task_shape_digest": selected.task_shape_digest,
        "workload_profile_id": task.workload_profile_id,
        "workload_profile_digest": task.workload_profile_digest,
        "domain_id": task.domain_id,
        "selection_digest": selected.selection_digest,
        "route_id": selected.route_id,
        "plan_digest": selected.plan.plan_digest,
        "source_snapshot_digest": source_snapshot_digest(selected),
    }
    if any(value[name] != bound for name, bound in expected.items()):
        raise InstructionAdmissionRefusal("PLAN_OR_SCOPE_MISMATCH")
    signature_path = Path(signature_path)
    allowed_signers_path = Path(allowed_signers_path)
    try:
        files_present = (
            signature_path.is_file()
            and signature_path.stat().st_size <= _MAX_SIGNATURE_BYTES
            and allowed_signers_path.is_file()
        )
    except OSError:
        files_present = False
    if not files_present:
        raise InstructionAdmissionRefusal("SIGNATURE_OR_TRUST_ROOT_MISSING")
    executable = ssh_keygen or shutil.which("ssh-keygen")
    if not executable:
        raise InstructionAdmissionRefusal("SIGNATURE_VERIFIER_UNAVAILABLE")
    try:
        result = subprocess.run(
            [executable, "-Y", "verify", "-f", str(allowed_signers_path),
             "-I", value["reviewer_identity"], "-n", SIGNATURE_NAMESPACE,
             "-s", str(signature_path)],
            input=manifest_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InstructionAdmissionRefusal("SIGNATURE_VERIFIER_FAILED") from exc
    if result.returncode != 0:
        raise InstructionAdmissionRefusal("SIGNATURE_INVALID")
    return VerifiedInstructionAdmissionV01(
        manifest_digest="sha256:" + hashlib.sha256(manifest_bytes).hexdigest(),
        reviewer_identity=value["reviewer_identity"],
        request_digest=request_digest,
        task_shape_digest=selected.task_shape_digest,
        selection_digest=selected.selection_digest,
        route_id=selected.route_id,
        plan_digest=selected.plan.plan_digest,
        source_snapshot_digest=expected["source_snapshot_digest"],
        ordered_operand_bodies=selected.plan.ordered_operand_bodies,
        source_digests=selected.plan.source_digests,
        operation_ids=selected.plan.operation_ids,
        instruction_bytes=selected.plan.instruction_bytes,
        ordered_bodies_digest=ordered_bodies_digest(selected.plan.ordered_operand_bodies),
    )


__all__ = [
    "InstructionAdmissionRefusal", "VerifiedInstructionAdmissionV01",
    "instruction_plan_transport", "ordered_bodies_digest", "source_snapshot_digest",
    "verify_signed_instruction_admission",
]
