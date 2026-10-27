"""Replay native predicates on actual invocation values. AuthorityEffect: None.

Only host-selected bindings activate this adapter. A typed refusal, regex hit,
unavailable measurement or caller-supplied reason is not a checked negative.
The existing OEWAS executor propagates checked negatives to the same root
profile before dispatching a parent. Repairs use a new attempt and fresh check.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from pydantic import TypeAdapter

from adversary.domain.contracts.gate_occurrences import (
    GateOccurrenceCapability, GateOutcomeClassification,
)

from adversary.domain.native_gate_check import (
    PRIMARY_GATE_IDS,
    NativeGateCheck,
    NativePrimaryGateReceipt,
    decode_native_json,
    native_digest,
    native_response_semantics,
    validate_typed_primary_outcome,
)
from operads.skill_operad.resolver.resolver import (
    CheckedOccurrenceRejection,
    InvocationSnapshot,
)

from .teamwork_native_gates import (
    PROMPT_TRANSPORT_POOL_PROFILE, _catalog, _host, _invoke, _safe_native_path,
    compact_prompt_transport,
)


LEGACY_PROFILE = "adversary.native-checked-occurrence.v1"
PROFILE = "adversary.native-checked-occurrence.v2"
GATE14_PROJECTION = "adversary.gate14-transport-projection.v1"
def _cap(number, *, finite=(), policy=(), profiles=("supplied-finite-witness.v1",), scope):
    return GateOccurrenceCapability(gate_id=PRIMARY_GATE_IDS[number - 1], profiles=profiles,
        finite_failure_codes=finite, policy_failure_codes=policy, scope=scope)


_CAPABILITIES = (
    _cap(1, policy=("UNADMITTED_PACKET", "POLICY_VIOLATION"), scope="Declared admission and literal filler policy; no admission authentication."),
    _cap(2, finite=("LGGR_DEFECT_DETECTED",), scope="Exact supplied finite face coboundary."),
    _cap(3, scope="Stagnation or requested lift HOLDs pending the independent licensed-lift witnesses."),
    _cap(4, policy=("COMPLEXITY_EXCEEDED", "RESOURCE_EXHAUSTED"), scope="Declared finite complexity/spend/wire envelope, not billed cost."),
    _cap(5, policy=("BACKDOOR_DETECTED",), scope="Declared exact-method and replay-seed policy; malformed numbers are invalid input."),
    _cap(6, finite=("DUAL_CERTIFICATE_INVALID", "TIER_CERTIFICATE_INVALID", "MEASUREMENT_MISMATCH"), scope="Exact supplied dual, sequential tie certificate and measurement replay."),
    _cap(7, finite=("KERNEL_AUDIT_FAILED",), policy=("KERNEL_EXECUTION_FAILED", "UNCHECKED_AXIOM"), profiles=("legacy-unmeasured", "adversary.host-lean.v1"), scope="Selected authenticated Lean certificate attempt under exact statements/axiom policy; not falsity of a theorem."),
    _cap(8, policy=("KNOWN_OBSTRUCTION", "SCAR_REPAIR_UNTARGETED"), scope="Exact declared candidate scar/repair-target policy; no external ledger authentication."),
    _cap(9, finite=("UNSUPPORTED_SCOPE_PROMOTION",), policy=("SUMMARY_PART_MISSING", "CLAIM_ARTIFACT_REQUIRED"), scope="Literal summary/required artifact policy and declared scope-set inclusion, not prose truth."),
    _cap(10, finite=("DUAL_CERTIFICATE_INVALID", "TIER_CERTIFICATE_INVALID", "MEASUREMENT_MISMATCH", "ORIENTATION_INVARIANCE_FAILED"), scope="Finite exact declared signed-permutation controls and baseline certificates."),
    _cap(11, policy=("CARRIER_REGRESS", "CIRCULAR_DEPENDENCY"), scope="Declared typed quarantine/nonprogress policy; no proof of uncomputability or infinite behavior."),
    _cap(12, policy=("COWARDICE_DETECTED",), scope="Declared mock/upstream/skipped-check/error-suppression attempt policy."),
    _cap(13, finite=("DUAL_CERTIFICATE_INVALID", "TIER_CERTIFICATE_INVALID", "MEASUREMENT_MISMATCH"), scope="Only unrefused finite certificate replay; upstream reason codes never create new failures."),
    _cap(14, finite=("CONTEXT_TRANSPORT_CORRUPTED",), profiles=("legacy-utf8", "adversary.pfp-transport-pool.v2"), scope="Exact supplied UTF-8 bytes and coordinate preservation."),
    _cap(15, policy=("PROCESS_EXECUTION_FAILED",), profiles=("legacy-unmeasured", "adversary.host-process.v1"), scope="Selected authenticated direct-child checker attempt; not semantic program correctness."),
    _cap(16, finite=("EQUILIBRIUM_COLLAPSE",), policy=("EQUILIBRIUM_COLLAPSE",), scope="Exact supplied core/fallback bytes and declared bounded recovery policy."),
    _cap(17, policy=("GAUGE_ROTATION_REQUIRED",), scope="Declared confidence/circularity gauge policy; not a detected mathematical defect."),
    _cap(18, policy=("UNRESOLVED_OBLIGATION",), scope="Declared obligation closure/dependency/receipt consistency; no theorem certification."),
    _cap(19, finite=("CHAIN_OF_CUSTODY_BROKEN",), scope="Exact retained chain/citation consistency; no signer or external tip authentication."),
    _cap(20, policy=("PROCESS_EXECUTION_FAILED",), profiles=("legacy-unmeasured", "adversary.host-process.v1"), scope="Selected authenticated direct-child exit observation; not process-tree safety."),
    _cap(21, finite=("TRUTH_REPAIR_INADMISSIBLE",), policy=("TRUTH_REPAIR_INADMISSIBLE",), scope="Exact declared sibling/fence equality; checker binding errors are invalid evidence, not theorem rejection."),
    _cap(22, policy=("RESOURCE_LIMIT_EXCEEDED",), profiles=("legacy-unmeasured", "adversary.host-job-resources.v1"), scope="Actual selected host-captured Windows job resource envelope; unsigned, not RSS or mathematical failure."),
)


def gate_capabilities() -> tuple[GateOccurrenceCapability, ...]:
    """All 22 existing primary owners, including their genuine limitations."""
    return _CAPABILITIES


def classify_gate_outcome(gate_id, payload, receipt) -> GateOutcomeClassification:
    """Pure wire classification, never evidence authentication or a rejection label.

    The caller must separately validate actual native captures, selected trust,
    candidate, task and attempt. A self-authored receipt can satisfy these syntax
    checks; this function does not execute or admit it.
    """
    def result(status, grade, reason):
        return GateOutcomeClassification(gate_id=gate_id if type(gate_id) is str and gate_id else "unknown",
            status=status, evidence_grade=grade, reason=reason)
    if gate_id not in PRIMARY_GATE_IDS:
        return result("UNSUPPORTED_OBSERVATION", "UNAVAILABLE", "Not an existing primary gate.")
    try:
        wire = (receipt.model_dump(mode="json", by_alias=True, exclude_unset=True)
            if isinstance(receipt, NativePrimaryGateReceipt) else receipt)
        checked = NativePrimaryGateReceipt.model_validate(wire)
        request = {"operation": "gate_evaluate", "gate_id": gate_id, "payload": payload, "history_edges": []}
        validate_typed_primary_outcome(request, {"success": True, "result": {"refusal": None, "outcome": wire}})
    except (ValueError, TypeError, KeyError, AttributeError):
        return result("INVALID_INPUT_OR_BINDING", "INVALID", "Malformed or contradictory gate wire, payload or input/profile binding.")
    capability = _CAPABILITIES[PRIMARY_GATE_IDS.index(gate_id)]
    if gate_id == "PFP-13-REALITY-GATE" and payload.get("is_refused") is True:
        return result("FORWARDED_REFUSAL", "FORWARDED", "Upstream refusal retained; this is not a newly checked negative.")
    if checked.status == "HOLD":
        return result("MISSING_WITNESS", "UNAVAILABLE", capability.scope)
    code = checked.refusal_code or ""
    if code.startswith("EIS_AUTH_") or any(token in code for token in ("TRUST", "SIGNATURE", "ATTESTATION", "ISSUER", "KEY_", "REVOKED", "EXPIRED")):
        return result("UNTRUSTED_OBSERVATION", "UNTRUSTED", "Configured observation trust was not established.")
    if code in {"CHECKER_RECEIPT_REQUIRED", "RECEIPT_NOT_ACCEPTED", "UNMECHANIZED_SPECULATION"}:
        return result("MISSING_WITNESS", "UNAVAILABLE", "Required independently checked evidence is absent.")
    owner_profile = {"PFP-07-MANUSCRIPT-TRUTH": ("kernel_profile", "adversary.host-lean.v1"),
        "PFP-15-BARE-METAL-ANCHOR": ("process_profile", "adversary.host-process.v1"),
        "PFP-20-COVERT-VERIFIER": ("process_profile", "adversary.host-process.v1"),
        "PFP-22-HARDWARE-CONSTRAINT": ("resource_profile", "adversary.host-job-resources.v1")}.get(gate_id)
    if owner_profile and payload.get(owner_profile[0]) != owner_profile[1]:
        if gate_id == "PFP-07-MANUSCRIPT-TRUTH" and code == "UNCHECKED_AXIOM":
            return result("ATTEMPT_POLICY_FAILURE", "BOUND_ATTEMPT_POLICY_FAILURE", "Literal forbidden proof-marker policy only; not an axiom or theorem audit.")
        return result("UNTRUSTED_OBSERVATION", "UNTRUSTED", "Legacy supplied fields do not establish an owning-host execution/resource observation.")
    if gate_id == "PFP-14-CONTEXT-TRANSPORT" and (checked.status == "PASS" or code == "CONTEXT_TRANSPORT_CORRUPTED"):
        try:
            projected = gate14_transport_projection(payload)
        except (ValueError, TypeError, UnicodeError):
            return result("INVALID_INPUT_OR_BINDING", "INVALID", "Gate14's finite byte/coordinate projection is unavailable or malformed.")
        if gate14_transport_preserved(projected) != (checked.status == "PASS"):
            return result("INVALID_INPUT_OR_BINDING", "INVALID", "Gate14's checked result contradicts the finite byte/coordinate predicate.")
    if checked.status == "PASS":
        return result("PASSED_PREDICATE", "FINITE_SUPPLIED_PREDICATE_PASS", capability.scope)
    if (gate_id == "PFP-16-RESILIENCE" and code == "EQUILIBRIUM_COLLAPSE"
            and (payload.get("core_state_intact") is False
                or (type(payload.get("recovery_attempts")) is int
                    and type(payload.get("recovery_budget")) is int
                    and payload["recovery_attempts"] > payload["recovery_budget"]))):
        return result("ATTEMPT_POLICY_FAILURE", "BOUND_ATTEMPT_POLICY_FAILURE", capability.scope)
    if gate_id == "PFP-21-TRUTH-REPAIR" and code == "TRUTH_REPAIR_INADMISSIBLE" and payload.get("invariants_preserved") is False:
        return result("ATTEMPT_POLICY_FAILURE", "BOUND_ATTEMPT_POLICY_FAILURE", "Declared invariant-preservation policy was refused; no inferred mathematical defect.")
    if code in capability.finite_failure_codes:
        return result("FINITE_PREDICATE_FAILURE", "FINITE_BOUND_PREDICATE_FAILURE", capability.scope)
    if code in capability.policy_failure_codes:
        return result("ATTEMPT_POLICY_FAILURE", "BOUND_ATTEMPT_POLICY_FAILURE", capability.scope)
    if ("INVALID" in code or "MISMATCH" in code or "MALFORMED" in code
            or code in {"MAP_UNDEFINED", "NON_RATIONAL_FIELD", "ARTIFACT_DIGEST_MISMATCH", "COMPLEXITY_EXCEEDED"}):
        return result("INVALID_INPUT_OR_BINDING", "INVALID", "Malformed witness, stale binding or invalid finite carrier; not an evaluated candidate failure.")
    return result("UNSUPPORTED_OBSERVATION", "UNAVAILABLE", "No checked-negative interpretation for this native refusal: " + code)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False)


def _sha(raw: bytes):
    return hashlib.sha256(raw).hexdigest()


def gate14_transport_projection(payload: dict) -> dict:
    """Project Context Transport's exact finite fields, without authenticating a capture.

    Matches context_transport_legacy after the existing pool.v2 expansion. Checksums,
    nonempty text/coordinate items and pool indices are validated before the
    pure predicate is used. SHA authentication/compiler fidelity are not proved
    here. The original request and raw native replay remain in the capture.
    """
    def text(value):
        if type(value) is not str or not value.strip():
            raise ValueError("GATE14_PROJECTION_TEXT_INVALID")
        value.encode("utf-8")
        return value

    if type(payload) is not dict:
        raise ValueError("GATE14_PROJECTION_PAYLOAD_INVALID")
    profile = payload.get("transport_profile", "legacy-utf8")
    if profile == PROMPT_TRANSPORT_POOL_PROFILE:
        if "origin_payload_utf8" in payload or "payload_utf8" in payload:
            raise ValueError("GATE14_PROJECTION_MIXED_PROFILE")
        pool, origin, received = (payload.get(key) for key in
            ("payload_pool_utf8", "origin_payload_index", "payload_index"))
        if (type(pool) is not list or len(pool) not in (1, 2)
                or any(type(value) is not str or not value.strip() for value in pool)
                or type(origin) is not int or origin != 0 or type(received) is not int
                or (len(pool) == 1 and received != 0)
                or (len(pool) == 2 and (received != 1 or pool[0] == pool[1]))):
            raise ValueError("GATE14_PROJECTION_POOL_INVALID")
        origin, received = text(pool[origin]), text(pool[received])
    elif "transport_profile" not in payload:
        origin, received = text(payload.get("origin_payload_utf8")), text(payload.get("payload_utf8"))
    else:
        raise ValueError("GATE14_PROJECTION_PROFILE_INVALID")
    origin_bytes, received_bytes = origin.encode("utf-8"), received.encode("utf-8")
    if (payload.get("origin_checksum") != "sha256:" + _sha(origin_bytes)
            or payload.get("payload_checksum") != "sha256:" + _sha(received_bytes)):
        raise ValueError("GATE14_PROJECTION_CHECKSUM_INVALID")
    coordinates = {}
    for key in ("origin_coordinates", "retained_coordinates", "dropped_coordinates"):
        values = payload.get(key)
        if type(values) is not list:
            raise ValueError("GATE14_PROJECTION_COORDINATES_INVALID")
        coordinates[key] = [text(value) for value in values]
    return {"schema_version": GATE14_PROJECTION, "transport_profile": profile,
        "snapshot_id": text(payload.get("snapshot_id")), "origin_bytes": list(origin_bytes),
        "received_bytes": list(received_bytes), **coordinates}


def gate14_transport_preserved(projected: dict) -> bool:
    """The finite predicate mirrored by NativeModelBridge.Gate14.preserves."""
    return (projected["origin_bytes"] == projected["received_bytes"]
        and projected["dropped_coordinates"] == []
        and set(projected["origin_coordinates"]) == set(projected["retained_coordinates"]))


def _action_bytes(action):
    # The public historical v1-v3 serializer deliberately omits new native
    # fields. An internal actual-context snapshot must retain every field, not
    # reinterpret that public compatibility projection as the complete object.
    return TypeAdapter(dict[str, object]).dump_json(
        {name: getattr(action, name) for name in type(action).model_fields})


def decode_occurrence_rejection(invocation, rejection) -> dict:
    """Read unchanged v1/v2 bytes; this authenticates neither code nor evidence.

    Historical v1 captures remain readable without substituting today's adapter
    source or scope for their recorded owner. Fresh replay is a separate v2
    operation and requires this actual checker's current bindings.
    """
    if (type(invocation) is not InvocationSnapshot
            or type(rejection) is not CheckedOccurrenceRejection
            or rejection.invocation_digest != invocation.digest()):
        raise ValueError("GATE_OCCURRENCE_REJECTION_CHANGED")
    rejection.__post_init__()
    scope = decode_native_json(rejection.scope_json)
    if (type(scope) is not dict or scope.get("profile") not in {LEGACY_PROFILE, PROFILE}
            or scope.get("checker_id") != scope["profile"]
            or type(scope.get("capture")) is not dict
            or native_digest(scope["capture"]) != rejection.evidence_digest):
        raise ValueError("GATE_OCCURRENCE_CAPTURE_CHANGED")
    return scope


@dataclass(frozen=True)
class GateCheckScope:
    task_id: str
    attempt_id: str
    task_bytes: bytes

    def __post_init__(self):
        if any(type(value) is not str or not value.strip() or len(value.encode()) > 512
               for value in (self.task_id, self.attempt_id)):
            raise ValueError("GATE_OCCURRENCE_SCOPE_INVALID")
        if type(self.task_bytes) is not bytes or not 1 <= len(self.task_bytes) <= 1048576:
            raise ValueError("GATE_OCCURRENCE_TASK_BOUND")
        self.task_bytes.decode("utf-8")


@dataclass(frozen=True)
class GateSubjectBinding:
    op_id: str
    gate_id: str
    subject_slot: int | None = None
    candidate_field: str | None = None

    def __post_init__(self):
        if (type(self.op_id) is not str or not self.op_id.strip()
                or self.gate_id not in PRIMARY_GATE_IDS
                or self.subject_slot is not None and (
                    type(self.subject_slot) is not int or self.subject_slot < 0)
                or self.candidate_field is not None and (
                    type(self.candidate_field) is not str or not self.candidate_field.strip())):
            raise ValueError("GATE_OCCURRENCE_BINDING_INVALID")


class NativeGateOccurrenceChecker:
    """Optional OEWAS post-check, supplied by Adversary's composition adapter.

    The selected entire operand/output object is the request payload. No fixture,
    arbitrary external witness or answer key can be substituted by a projector.
    Raw captures remain available as immutable JSON observations; no new store
    or receipt registry is introduced. Native syntax/resource failures stop as
    unavailable, without manufacturing an absorbing rejection occurrence.
    """

    def __init__(self, *, selection: NativeGateCheck, scope: GateCheckScope,
                 bindings: tuple[GateSubjectBinding, ...], action_context=None):
        if type(scope) is not GateCheckScope or type(bindings) is not tuple or any(
                type(binding) is not GateSubjectBinding for binding in bindings):
            raise ValueError("GATE_OCCURRENCE_BINDING_INVALID")
        if len({binding.op_id for binding in bindings}) != len(bindings):
            raise ValueError("GATE_OCCURRENCE_DUPLICATE_BINDING")
        self._selection = NativeGateCheck.model_validate_json(selection.model_dump_json())
        if self._selection.witness_path or self._selection.witness_sha256:
            raise ValueError("GATE_OCCURRENCE_EXTERNAL_OBSERVER_NOT_SUPPORTED")
        self._action = None
        self._action_json = None
        if action_context is not None:
            from ..use_cases.teamwork import TeamworkAction
            if type(action_context) is not TeamworkAction:
                raise ValueError("GATE_OCCURRENCE_ACTUAL_ACTION_REQUIRED")
            self._action_json = _action_bytes(action_context)
            self._action = TeamworkAction.model_validate_json(self._action_json)
            if (self._action.initial_task_id != scope.task_id
                    or self._action.action_id != scope.attempt_id
                    or self._action.objective.encode("utf-8") != scope.task_bytes
                    or self._action.native_gate_check != self._selection):
                raise ValueError("GATE_OCCURRENCE_ACTION_SCOPE_CHANGED")
        if (any(config is not None for config in (self._selection.process_observer,
                self._selection.kernel_check, self._selection.resource_check)) and self._action is None):
            raise ValueError("GATE_OCCURRENCE_ACTUAL_ACTION_REQUIRED")
        self._scope = scope
        self._bindings = {binding.op_id: binding for binding in bindings}
        self._bindings_sha256 = native_digest([
            {"op_id": binding.op_id, "gate_id": binding.gate_id,
             "subject_slot": binding.subject_slot,
             **({"candidate_field": binding.candidate_field} if binding.candidate_field is not None else {})}
            for binding in sorted(bindings, key=lambda binding: binding.op_id)])
        self._check_sources()
        host, self._binary, _captures = _host(self._selection)
        catalog = _catalog(_invoke(host, {"operation": "gate_schemas"}))
        self._specs = {row["gate_id"]: row["specification_sha256"]
            for row in catalog["primary_and_empirical"]["gates"]}
        if any(self._specs.get(gate_id) != digest for gate_id, digest
               in self._selection.specification_sha256.items()):
            raise ValueError("GATE_OCCURRENCE_SPECIFICATION_CHANGED")
        self._transport_profiles = tuple(catalog["primary_and_empirical"].get("transport_profiles", ()))
        self._adapter_sha256 = _sha(Path(__file__).read_bytes())
        self._observations: list[str] = []
        self._model = None
        self._model_json = None
        self._model_digest = None
        self._observation_time = int(time.time())

    def bind_native_model(self, binding):
        """Bind the root's checked native realization before external effects.

        The root owns the codec and verifies actual static syntax and executed
        prefixes. This adapter retains the exact immutable readback; no snapshot
        fields or historical snapshot.v1 digest profile are changed.
        """
        if not all(callable(getattr(binding, name, None)) for name in
                   ("to_json", "digest", "verify_invocation")):
            raise ValueError("GATE_OCCURRENCE_NATIVE_MODEL_INVALID")
        raw, digest = _json(binding.to_json()), binding.digest()
        if type(digest) is not str or len(digest) != 64:
            raise ValueError("GATE_OCCURRENCE_NATIVE_MODEL_INVALID")
        if self._model is not None:
            if (raw, digest) != (self._model_json, self._model_digest):
                raise ValueError("GATE_OCCURRENCE_NATIVE_MODEL_CHANGED")
            return
        self._model, self._model_json, self._model_digest = binding, raw, digest

    def _verify_model(self, invocation):
        if self._model is not None:
            if (_json(self._model.to_json()) != self._model_json
                    or self._model.digest() != self._model_digest):
                raise ValueError("GATE_OCCURRENCE_NATIVE_MODEL_CHANGED")
            if self._model.verify_invocation(invocation) is False:
                raise ValueError("GATE_OCCURRENCE_NATIVE_MODEL_INVOCATION_CHANGED")

    @property
    def observations(self) -> tuple[str, ...]:
        return tuple(self._observations)

    def _check_sources(self):
        from .teamwork_intelligence_host import _current_artifacts
        for path in self._selection.source_paths:
            _safe_native_path(path)
        _current_artifacts(self._selection.source_paths)

    def _scope_wire(self):
        return {"profile": PROFILE, "task_id": self._scope.task_id,
            "attempt_id": self._scope.attempt_id, "task_sha256": _sha(self._scope.task_bytes),
            "checker_id": PROFILE, "checker_source_sha256": self._adapter_sha256,
            "bindings_sha256": self._bindings_sha256,
            "selection_sha256": native_digest(self._selection.model_dump(mode="json")),
            "binary": self._binary, "authority_effect": "None",
            **({"owner_action_sha256": _sha(self._action_json)}
                if self._action is not None else {}),
            **({"native_model_binding": decode_native_json(self._model_json),
                "native_model_binding_sha256": self._model_digest} if self._model_json is not None else {})}

    def _gate14_binding(self, invocation):
        """The exact finite view named by NativeModelBridge.Gate14.Scope.

        An empty model digest records the Python-reference/unbound case; it
        cannot discharge the theorem's faithful decoded-model premise.
        """
        return {"task_id": self._scope.task_id, "attempt_id": self._scope.attempt_id,
            "task_sha256": _sha(self._scope.task_bytes), "invocation_sha256": invocation.digest(),
            "input_sha256": _sha(invocation.args_json.encode("utf-8")),
            "output_sha256": _sha(invocation.output_json.encode("utf-8")),
            "operation_id": invocation.op_id,
            "operation_sha256": _sha(invocation.operation_json.encode("utf-8")),
            "ordinal": invocation.ordinal, "source_profile": PROFILE,
            "native_model_sha256": self._model_digest or "",
            "native_binary_sha256": self._binary["sha256"],
            "checker_source_sha256": self._adapter_sha256,
            "gate_specification_sha256": self._specs["PFP-14-CONTEXT-TRANSPORT"]}

    def _subject(self, invocation: InvocationSnapshot):
        if type(invocation) is not InvocationSnapshot:
            raise ValueError("GATE_OCCURRENCE_SNAPSHOT_INVALID")
        binding = self._bindings[invocation.op_id]
        if binding.subject_slot is None:
            subject = decode_native_json(invocation.output_json)
        else:
            operands = decode_native_json(invocation.args_json)
            if binding.subject_slot >= len(operands):
                raise ValueError("GATE_OCCURRENCE_SLOT_INVALID")
            subject = operands[binding.subject_slot]
        if type(subject) is not dict:
            raise ValueError("GATE_OCCURRENCE_SUBJECT_NOT_OBJECT")
        return subject

    def _owner_payload(self, invocation, binding, subject, *, replay, now):
        action = self._action
        if action is not None and _action_bytes(action) != self._action_json:
            raise ValueError("GATE_OCCURRENCE_ACTION_CONTEXT_CHANGED")
        selected = ((binding.gate_id == "PFP-07-MANUSCRIPT-TRUTH" and self._selection.kernel_check is not None)
            or (binding.gate_id in {"PFP-15-BARE-METAL-ANCHOR", "PFP-20-COVERT-VERIFIER"} and self._selection.process_observer is not None)
            or (binding.gate_id == "PFP-22-HARDWARE-CONSTRAINT" and self._selection.resource_check is not None))
        reserved = {"kernel_profile", "kernel_expected", "kernel_observation", "kernel_trust_policy",
            "process_profile", "process_expected", "process_observation", "process_trust_policy",
            "resource_profile", "resource_expected", "resource_observation", "now"}
        if reserved.intersection(subject):
            raise ValueError("GATE_OCCURRENCE_CANDIDATE_OBSERVER_FIELDS_REFUSED")
        if not selected:
            return subject
        candidate = _json(subject) if binding.candidate_field is None else subject.get(binding.candidate_field)
        if type(candidate) is not str or candidate != action.candidate:
            raise ValueError("GATE_OCCURRENCE_OWNER_CANDIDATE_CHANGED")
        if not replay:
            from .teamwork_intelligence_host import _current_artifacts, _current_checker, _current_source
            _current_source(action)
            _current_checker(action)
            _current_artifacts(action.artifacts)
        if binding.gate_id == "PFP-07-MANUSCRIPT-TRUTH":
            from .teamwork_kernel_observation import kernel_gate_payload
            return kernel_gate_payload(action, now=now, replay=replay)
        if binding.gate_id in {"PFP-15-BARE-METAL-ANCHOR", "PFP-20-COVERT-VERIFIER"}:
            from .teamwork_process_observation import process_gate_payload, replay_process_gate_payload
            return (replay_process_gate_payload if replay else process_gate_payload)(action, binding.gate_id, now=now)
        from .teamwork_resource_observation import resource_gate_payload
        return resource_gate_payload(action, replay=replay)

    def _request(self, invocation: InvocationSnapshot, *, replay=False, now=None):
        self._verify_model(invocation)
        binding = self._bindings[invocation.op_id]
        subject = self._subject(invocation)
        subject = self._owner_payload(invocation, binding, subject, replay=replay,
            now=self._observation_time if now is None else now)
        if (binding.gate_id == "PFP-14-CONTEXT-TRANSPORT"
                and PROMPT_TRANSPORT_POOL_PROFILE in self._transport_profiles
                and "transport_profile" not in subject
                and "origin_payload_utf8" in subject and "payload_utf8" in subject):
            subject = compact_prompt_transport(subject)
        request = {"operation": "gate_evaluate", "gate_id": binding.gate_id,
            "payload": subject, "history_edges": []}
        from ..domain.contracts.gate_contracts import validate_typed_gate_request
        validate_typed_gate_request(request)
        return request

    def _evaluate(self, request):
        self._check_sources()
        if _sha(Path(__file__).read_bytes()) != self._adapter_sha256:
            raise ValueError("GATE_OCCURRENCE_CHECKER_CHANGED")
        host, binary, captures = _host(self._selection, expected_binary=self._binary)
        response = _invoke(host, request)
        first_capture = captures[-1]
        first = native_response_semantics(captures[-1], request, response, binary)
        replay = _invoke(host, request)
        second_capture = captures[-1]
        second = native_response_semantics(captures[-1], request, replay, binary)
        if native_digest(first) != native_digest(second):
            raise ValueError("GATE_OCCURRENCE_REPLAY_MISMATCH")
        _host(self._selection, expected_binary=binary)
        self._check_sources()
        capture = {"request": request, "response": response, "process": first_capture,
            "replay_response": replay, "replay_process": second_capture, "binary": binary}
        if response.get("success") is not True or response["result"].get("refusal") is not None:
            raise ValueError("GATE_OCCURRENCE_NATIVE_UNAVAILABLE")
        validate_typed_primary_outcome(request, response)
        receipt = NativePrimaryGateReceipt.model_validate(response["result"]["outcome"])
        if receipt.specification_sha256 != self._specs[request["gate_id"]]:
            raise ValueError("GATE_OCCURRENCE_SPECIFICATION_CHANGED")
        return receipt, capture

    def __call__(self, invocation: InvocationSnapshot):
        self._verify_model(invocation)
        if invocation.op_id not in self._bindings:
            return None
        request = self._request(invocation)
        receipt, capture = self._evaluate(request)
        classification = classify_gate_outcome(receipt.gate_id, request["payload"], receipt)
        self._observations.append(_json({"scope": self._scope_wire(),
            "invocation_sha256": invocation.digest(), "capture": capture,
            "classification": classification.to_json()}))
        if classification.status == "PASSED_PREDICATE":
            return None
        if classification.status not in {"FINITE_PREDICATE_FAILURE", "ATTEMPT_POLICY_FAILURE"}:
            raise ValueError("GATE_OCCURRENCE_NEGATIVE_NOT_ESTABLISHED")
        scope = {**self._scope_wire(), "capture": capture,
            "candidate_sha256": _sha(invocation.output_json.encode("utf-8")),
            "subject_sha256": native_digest(self._subject(invocation)),
            "gate_specification_sha256": receipt.specification_sha256,
            "evidence_grade": classification.evidence_grade}
        if receipt.gate_id == "PFP-14-CONTEXT-TRANSPORT":
            scope["finite_predicate_projection"] = gate14_transport_projection(request["payload"])
            scope["finite_predicate_binding"] = self._gate14_binding(invocation)
        return CheckedOccurrenceRejection(invocation.digest(), receipt.gate_id,
            receipt.refusal_code, native_digest(capture), _json(scope))

    def replay_rejection(self, invocation: InvocationSnapshot, rejection: CheckedOccurrenceRejection):
        """Verify retained labels without replacing them or starting a new run."""
        scope = decode_occurrence_rejection(invocation, rejection)
        if scope["profile"] == LEGACY_PROFILE:
            raise ValueError("GATE_OCCURRENCE_LEGACY_READBACK_ONLY")
        expected_keys = {*self._scope_wire(), "capture", "candidate_sha256", "subject_sha256",
            "gate_specification_sha256", "evidence_grade"}
        if rejection.gate_id == "PFP-14-CONTEXT-TRANSPORT":
            expected_keys.add("finite_predicate_projection")
            expected_keys.add("finite_predicate_binding")
        if type(scope) is not dict or set(scope) != expected_keys:
            raise ValueError("GATE_OCCURRENCE_SCOPE_CHANGED")
        capture = scope.get("capture")
        if type(capture) is not dict or native_digest(capture) != rejection.evidence_digest:
            raise ValueError("GATE_OCCURRENCE_CAPTURE_CHANGED")
        if any(scope.get(key) != value for key, value in self._scope_wire().items()):
            raise ValueError("GATE_OCCURRENCE_SCOPE_CHANGED")
        if capture.get("binary") != self._binary:
            raise ValueError("GATE_OCCURRENCE_BINARY_CHANGED")
        request = self._request(invocation, replay=True, now=capture["request"]["payload"].get("now", self._observation_time))
        if request != capture["request"] or rejection.gate_id != request["gate_id"]:
            raise ValueError("GATE_OCCURRENCE_SUBJECT_CHANGED")
        retained = native_response_semantics(capture["process"], request,
            capture["response"], self._binary)
        retained_replay = native_response_semantics(capture["replay_process"], request,
            capture["replay_response"], self._binary)
        receipt, current = self._evaluate(request)
        actual = native_response_semantics(current["process"], request,
            current["response"], current["binary"])
        classification = classify_gate_outcome(receipt.gate_id, request["payload"], receipt)
        if (receipt.gate_id == "PFP-14-CONTEXT-TRANSPORT"
                and (scope.get("finite_predicate_projection") != gate14_transport_projection(request["payload"])
                    or scope.get("finite_predicate_binding") != self._gate14_binding(invocation))):
            raise ValueError("GATE_OCCURRENCE_FINITE_PROJECTION_CHANGED")
        if (native_digest(retained) != native_digest(retained_replay)
                or native_digest(retained) != native_digest(actual)
                or receipt.status != "REFUSE" or receipt.refusal_code != rejection.finding_code
                or classification.status not in {"FINITE_PREDICATE_FAILURE", "ATTEMPT_POLICY_FAILURE"}
                or scope.get("candidate_sha256") != _sha(invocation.output_json.encode("utf-8"))
                or scope.get("subject_sha256") != native_digest(self._subject(invocation))
                or scope.get("gate_specification_sha256") != receipt.specification_sha256
                or scope.get("evidence_grade") != classification.evidence_grade):
            raise ValueError("GATE_OCCURRENCE_REPLAY_MISMATCH")
        return True
