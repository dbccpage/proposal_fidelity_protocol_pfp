"""Opt-in signed OEWAS ingress; no default task authority or live dispatch.

The operator supplies the task/profile binding and trust root. Every call
re-reads selected source files, recompiles the route set, and verifies the
human signature before returning exact native transport bytes. OEEIS remains
a separate gate. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from operations.domain.rop.result import Err, Ok, Refusal, Result
from operads.application.adversary_candidate_plan import (
    PlanNodeV01,
    PlanRefusal,
    candidate_plan_material,
)
from operads.application.adversary_instruction_admission import (
    InstructionAdmissionRefusal,
    instruction_plan_transport,
    verify_signed_instruction_admission,
)
from operads.application.adversary_task_selection import (
    AdversaryCandidateRouteV01,
    AdversaryTaskShapeV01,
    select_candidate_plan,
)
from operads.infrastructure.fs.adversary_operand_source import (
    read_adversary_operand_sources,
)

from ..domain.instruction_ingress import (
    InstructionIngressReceiptV1,
    instruction_request_digest,
)
from ..domain.models import AdversaryBoutRequestV1
from ..domain.specialization import ADVERSARY_BASE_SPECIALIZATION_V1, SwarmSpecializationV1
from ..use_cases.base_swarm.specializations import SPECIALIZED_SWARMS, WORKLOAD_PROFILES_V01
from .specialization_check import check_specialization

_LOCUS = "adversary.infrastructure.oewas_instruction_ingress"
_MAX_MANIFEST_BYTES = 8192


def workload_profile_digest(profile: SwarmSpecializationV1) -> str:
    """Canonical digest of the same profile wire form checked by the native host."""
    if type(profile) is not SwarmSpecializationV1:
        raise TypeError("exact Adversary workload profile required")
    encoded = json.dumps(
        profile.to_wire(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class OeopSourceRouteV01:
    route_id: str
    workload_profile_id: str
    workload_profile_digest: str
    domain_id: str
    source_paths: tuple[str, ...]
    root: PlanNodeV01
    source_kind: str = "operands"


def read_route_documents(repo_root: Path, route: OeopSourceRouteV01):
    """Read the configured canonical source family; never upgrade legacy specimens."""
    if route.source_kind == "operands":
        return read_adversary_operand_sources(repo_root, route.source_paths)
    if route.source_kind == "projection":
        return read_candidate_route(repo_root, route).documents
    if route.source_kind != "typed_contracts":
        raise PlanRefusal("SOURCE_KIND_INVALID", route.source_kind)
    from operads.infrastructure.typed_contract_compiler import (
        compile_typed_contracts,
    )

    documents = compile_typed_contracts(repo_root).all_documents
    by_path = {item.source_relative_path: item for item in documents}
    if not route.source_paths or len(set(route.source_paths)) != len(route.source_paths):
        raise PlanRefusal("SOURCE_SELECTION_INVALID", "explicit unique typed sources required")
    if any(path not in by_path for path in route.source_paths):
        raise PlanRefusal("SOURCE_UNAVAILABLE", "unknown typed contract source")
    return tuple(by_path[path] for path in route.source_paths)


def read_candidate_route(repo_root: Path, spec: OeopSourceRouteV01):
    projection, projection_path = None, None
    if spec.source_kind == "projection":
        from operads.infrastructure.providers.projection_manifest_adapter import read_projection_documents

        if len(spec.source_paths) != 1:
            raise PlanRefusal("PROJECTION_SELECTION_INVALID", "exactly one projection required")
        ids = set()

        def visit(node):
            if node.operation_id in ids:
                return
            ids.add(node.operation_id)
            for _, child in node.children:
                visit(child)

        visit(spec.root)
        projection_path = spec.source_paths[0]
        documents, projection = read_projection_documents(repo_root, projection_path, ids)
    else:
        documents = read_route_documents(repo_root, spec)
    return AdversaryCandidateRouteV01(
        spec.route_id, spec.workload_profile_id, spec.workload_profile_digest,
        spec.domain_id, documents, spec.root, projection, projection_path,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class SignedOeopInstructionIngress:
    """Verify an operator-configured exact-task plan without self-admission.

    The operator fixes the profile, domain, and one immutable task shape here.
    Ordered ports and ceilings are supplied before source selection, never
    inferred from objective prose or a source clause. This adapter checks the
    request digest but cannot establish the independent provenance of that
    supplied contract on the caller's behalf.
    """

    repo_root: Path
    workload_profile: SwarmSpecializationV1
    domain_id: str
    route_specs: tuple[OeopSourceRouteV01, ...]
    task_shape: AdversaryTaskShapeV01
    manifest_path: Path
    signature_path: Path
    allowed_signers_path: Path
    ssh_keygen: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "repo_root", Path(self.repo_root).resolve())
        for field_name in ("manifest_path", "signature_path", "allowed_signers_path"):
            object.__setattr__(self, field_name, Path(getattr(self, field_name)))

    def pre_dispatch(
        self, request: AdversaryBoutRequestV1
    ) -> Result[InstructionIngressReceiptV1, Refusal]:
        try:
            request_digest = instruction_request_digest(request)
            if (
                type(self.task_shape) is not AdversaryTaskShapeV01
                or type(self.workload_profile) is not SwarmSpecializationV1
                or self.workload_profile
                not in (
                    ADVERSARY_BASE_SPECIALIZATION_V1,
                    *WORKLOAD_PROFILES_V01.values(),
                    *(swarm.SPECIALIZATION for swarm in SPECIALIZED_SWARMS),
                )
                or type(self.domain_id) is not str
                or not self.domain_id
                or type(self.route_specs) is not tuple
                or not 1 <= len(self.route_specs) <= 64
                or any(type(item) is not OeopSourceRouteV01 for item in self.route_specs)
                or any(
                    not path.is_absolute()
                    for path in (self.manifest_path, self.signature_path, self.allowed_signers_path)
                )
                or any(
                    (item.workload_profile_id, item.workload_profile_digest, item.domain_id)
                    != (
                        self.workload_profile.specialization_id,
                        workload_profile_digest(self.workload_profile),
                        self.domain_id,
                    )
                    for item in self.route_specs
                )
            ):
                return Err(
                    Refusal("OEWAS_CONFIG_INVALID", "operator route binding is missing", _LOCUS)
                )
            trust_root = self.allowed_signers_path.resolve()
            if trust_root.is_relative_to(self.repo_root) or self.allowed_signers_path.is_symlink():
                return Err(
                    Refusal(
                        "OEWAS_TRUST_ROOT_NOT_EXTERNAL",
                        "the signer trust root must be operator-held outside the repository",
                        _LOCUS,
                    )
                )
            task = self.task_shape
            if (
                type(task) is not AdversaryTaskShapeV01
                or task.request_digest != request_digest
                or (task.workload_profile_id, task.workload_profile_digest, task.domain_id)
                != (
                    self.workload_profile.specialization_id,
                    workload_profile_digest(self.workload_profile),
                    self.domain_id,
                )
            ):
                return Err(
                    Refusal(
                        "OEWAS_TASK_BINDING_INVALID",
                        "task shape does not bind this request",
                        _LOCUS,
                    )
                )
            native_profile = check_specialization(self.workload_profile)
            if (
                not isinstance(native_profile, Ok)
                or type(native_profile.value) is not dict
                or native_profile.value.get("specialization_id")
                != self.workload_profile.specialization_id
                or native_profile.value.get("authority_effect") != "None"
            ):
                return Err(
                    Refusal(
                        "OEWAS_PROFILE_NATIVE_REFUSED",
                        "workload profile failed native validation",
                        _LOCUS,
                    )
                )
            routes = tuple(
                read_candidate_route(self.repo_root, spec)
                for spec in self.route_specs
            )
            selected = select_candidate_plan(task, routes)
            if self.manifest_path.is_symlink():
                return Err(Refusal("OEWAS_MANIFEST_ALIAS", "manifest alias refused", _LOCUS))
            if not 0 < self.manifest_path.stat().st_size <= _MAX_MANIFEST_BYTES:
                return Err(Refusal("OEWAS_MANIFEST_SIZE_INVALID", "manifest size invalid", _LOCUS))
            with self.manifest_path.open("rb") as stream:
                manifest_bytes = stream.read(_MAX_MANIFEST_BYTES + 1)
            if not 0 < len(manifest_bytes) <= _MAX_MANIFEST_BYTES:
                return Err(Refusal("OEWAS_MANIFEST_SIZE_INVALID", "manifest size invalid", _LOCUS))
            verified = verify_signed_instruction_admission(
                manifest_bytes,
                signature_path=self.signature_path,
                allowed_signers_path=self.allowed_signers_path,
                selected=selected,
                task=task,
                request_digest=request_digest,
                ssh_keygen=self.ssh_keygen,
            )
            payload = json.dumps(
                instruction_plan_transport(verified),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
            return Ok(
                InstructionIngressReceiptV1(
                    request_digest=request_digest,
                    plan_digest=verified.plan_digest,
                    source_snapshot_digest=verified.source_snapshot_digest,
                    admission_receipt_id=verified.manifest_digest,
                    verifier_id="oewas.signed_instruction_admission.v0.1",
                    plan_payload=payload,
                )
            )
        except (PlanRefusal, InstructionAdmissionRefusal) as exc:
            return Err(Refusal("OEWAS_" + exc.code, str(exc), _LOCUS))
        except (OSError, TypeError, ValueError, RecursionError) as exc:
            return Err(
                Refusal(
                    "OEWAS_INGRESS_UNAVAILABLE",
                    f"instruction ingress failed with {type(exc).__name__}",
                    _LOCUS,
                )
            )

    def native_admission(self, request: AdversaryBoutRequestV1) -> Result[dict, Refusal]:
        """Freshly verify, then expose the same signed material to the native verifier."""
        verified = self.pre_dispatch(request)
        if isinstance(verified, Err):
            return verified
        try:
            routes = tuple(
                read_candidate_route(self.repo_root, spec)
                for spec in self.route_specs
            )
            selected = select_candidate_plan(self.task_shape, routes)
            if (
                selected.plan.plan_digest != verified.value.plan_digest
                or selected.task_shape_digest == ""
            ):
                return Err(Refusal("OEWAS_SOURCE_CHANGED", "plan changed during admission", _LOCUS))
            return Ok(
                {
                    "manifest_path": str(self.manifest_path),
                    "signature_path": str(self.signature_path),
                    "allowed_signers_path": str(self.allowed_signers_path),
                    "request_digest": instruction_request_digest(request),
                    "request_json": asdict(request),
                    "ssh_keygen": self.ssh_keygen,
                    "plan_material": candidate_plan_material(selected.plan),
                }
            )
        except (OSError, TypeError, ValueError) as exc:
            return Err(Refusal("OEWAS_NATIVE_ADMISSION_UNAVAILABLE", str(exc), _LOCUS))


__all__ = [
    "OeopSourceRouteV01",
    "SignedOeopInstructionIngress",
    "workload_profile_digest",
    "read_route_documents",
]
