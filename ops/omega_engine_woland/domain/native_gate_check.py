"""Host-selected native diagnostic scope; it never supplies task acceptance.

Origin: omega_engine_woland/domain/native_gate_check.py
The retained receipt is a diagnostic claim: it does not accept the task.
AuthorityEffect: None.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_serializer, model_validator

PRIMARY_GATE_IDS = (
    "PFP-01-HELLA", "PFP-02-KOROVIEV", "PFP-03-BEGEMOT", "PFP-04-AZAZELLO",
    "PFP-05-ABADONNA", "PFP-06-MARGARITA", "PFP-07-THE-MASTER", "PFP-08-BEZDOMNY",
    "PFP-09-BENGALSKY", "PFP-10-ANNUSHKA", "PFP-11-STRAVINSKY", "PFP-12-PILATE",
    "PFP-13-WOLAND", "PFP-14-NATASHA", "PFP-15-JEREMY", "PFP-16-LIUDMILA",
    "PFP-17-POLINA", "PFP-18-YAROSLAVA", "PFP-19-LEVY-MATVEI", "PFP-20-APHRANIUS",
    "PFP-21-YESHUA", "PFP-22-RATSLAYER",
)
INTERGATE_IDS = (
    "PFP-IG-01-FLOW-BAND", "PFP-IG-02-EPISTEMIC-SURPRISE", "PFP-IG-03-COWARDICE-EVASION",
    "PFP-IG-04-PLAYFUL-REVERSIBILITY", "PFP-IG-05-FALSE-URGENCY-DESENSITIZATION",
    "PFP-IG-06-AFFECTIVE-DEESCALATION", "PFP-IG-07-MANUFACTURED-CONSENSUS",
    "PFP-IG-08-QUARANTINE-RECOVERY", "PFP-IG-09-DECEPTION-COUNTERMEASURE",
    "PFP-IG-10-TERMINAL-REALITY-TETHER",
)
EMPIRICAL_GATE_IDS = ("PFP-EMP-GATE-001", "PFP-EMP-GATE-002", "PFP-EMP-GATE-003")
NATIVE_GATE_IDS = (*PRIMARY_GATE_IDS, *INTERGATE_IDS, *EMPIRICAL_GATE_IDS)
NATIVE_GATE_PHASES = ("native_intake", "native_pre", "native_post", "native_learn_pre",
                      "native_learn_post", "native_finish")
INTERGATE_ENDPOINTS = (
    ("PFP-01-HELLA", "PFP-02-KOROVIEV"), ("PFP-02-KOROVIEV", "PFP-03-BEGEMOT"),
    ("PFP-04-AZAZELLO", "PFP-12-PILATE"), ("PFP-03-BEGEMOT", "PFP-06-MARGARITA"),
    ("PFP-09-BENGALSKY", "PFP-10-ANNUSHKA"), ("PFP-02-KOROVIEV", "PFP-08-BEZDOMNY"),
    ("PFP-06-MARGARITA", "PFP-07-MASTER"), ("PFP-11-STRAVINSKY", "PFP-07-MASTER"),
    ("PFP-04-AZAZELLO", "PFP-09-BENGALSKY"), ("PFP-08-BEZDOMNY", "PFP-13-WOLAND"),
)


class NativePrimaryGateReceipt(BaseModel):
    """The existing Rust wire, not a proof or an authentication mechanism.

    Witness semantics remain with the native predicate and its replay. Invalid
    profile values are retained verbatim in native refusals, rather than erased
    by a reader that accepts only successful configuration values.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)
    wire_schema: Literal["woland.pfp.gate-receipt.v1"] = Field(alias="schema")
    gate_id: Literal[(*PRIMARY_GATE_IDS, *EMPIRICAL_GATE_IDS)]
    status: Literal["PASS", "HOLD", "REFUSE"]
    refusal_code: str | None = Field(min_length=1)
    diagnostics: str = Field(min_length=1)
    witness: dict[str, JsonValue] | None
    input_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    input_digest_profile: Literal["python-sorted-spaced-ascii-json-v1"]
    specification_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    authority_effect: Literal["None"]
    can_authorize: bool = Field(json_schema_extra={"const": False})
    observation_authentication: Literal[
        "owning_host_ports", "configured_owning_host_signature", "not_admitted", "unsigned_host_capture"
    ]
    general_theorem_verified: bool = Field(json_schema_extra={"const": False})
    diagnostic_only: bool = Field(json_schema_extra={"const": True})
    scope: str = Field(min_length=1)
    process_profile: JsonValue = None
    kernel_profile: JsonValue = None
    resource_profile: JsonValue = None

    @model_validator(mode="after")
    def consistent_outcome(self):
        if self.can_authorize or self.general_theorem_verified or not self.diagnostic_only:
            raise ValueError("NATIVE_GATE_AUTHORITY_REFUSED")
        if self.status == "PASS":
            consistent = self.refusal_code is None and self.witness is not None
        elif self.status == "HOLD":
            consistent = self.refusal_code == "GATE_WITNESS_UNMEASURED" and self.witness is None
        else:
            consistent = self.refusal_code not in (None, "GATE_WITNESS_UNMEASURED") and self.witness is None
        if not consistent:
            raise ValueError("NATIVE_GATE_OUTCOME_CONTRADICTORY")
        return self


_PROFILE_GATES = {
    "process_profile": ("PFP-15-JEREMY", "PFP-20-APHRANIUS"),
    "kernel_profile": ("PFP-07-THE-MASTER",),
    "resource_profile": ("PFP-22-RATSLAYER",),
}


def _primary_outcome_skipped(request, response):
    if request.get("operation") != "gate_evaluate":
        return True
    return response.get("success") is not True or response["result"].get("refusal") is not None


def _typed_primary_outcome(request, response):
    wire = response["result"]["outcome"]
    if request.get("gate_id") not in (*PRIMARY_GATE_IDS, *EMPIRICAL_GATE_IDS):
        if wire.get("schema") == "woland.pfp.gate-receipt.v1":
            raise ValueError("NATIVE_GATE_OUTCOME_BINDING_MISMATCH")
        return None
    try:
        return NativePrimaryGateReceipt.model_validate(wire)
    except ValueError as exc:
        raise ValueError("NATIVE_GATE_OUTCOME_INVALID") from exc


def _bind_primary_digest(outcome, request):
    payload = request["payload"]
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, allow_nan=False).encode("utf-8")
    if (outcome.gate_id != request["gate_id"]
            or outcome.input_sha256 != "sha256:" + hashlib.sha256(raw).hexdigest()):
        raise ValueError("NATIVE_GATE_OUTCOME_BINDING_MISMATCH")
    return payload


def _profile_authentication(name, status):
    if name == "resource_profile":
        return "unsigned_host_capture"
    if status == "PASS":
        return "configured_owning_host_signature"
    return "not_admitted"


def _check_profile_binding(outcome, payload, wire):
    authentication = "owning_host_ports"
    for name, gates in _PROFILE_GATES.items():
        expected = outcome.gate_id in gates and name in payload
        present = name in outcome.model_fields_set
        if expected != present or (
                expected and native_digest(wire[name]) != native_digest(payload[name])):
            raise ValueError("NATIVE_GATE_OUTCOME_BINDING_MISMATCH")
        if expected:
            authentication = _profile_authentication(name, outcome.status)
    return authentication


def validate_native_primary_outcome(request: dict, response: dict) -> None:
    """Check the typed wire against its request after checking captured bytes."""
    if _primary_outcome_skipped(request, response):
        return
    outcome = _typed_primary_outcome(request, response)
    if outcome is None:
        return
    payload = _bind_primary_digest(outcome, request)
    authentication = _check_profile_binding(outcome, payload, response["result"]["outcome"])
    if outcome.observation_authentication != authentication:
        raise ValueError("NATIVE_GATE_OUTCOME_BINDING_MISMATCH")


def native_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def validate_typed_primary_outcome(request: dict, response: dict) -> None:
    """Opt-in current contract; historical/raw refusal decoding is unchanged.

    Callers validate the request before dispatch as well. This checks the supplied
    response shape and existing digest/profile binding, not host authenticity.
    """
    from omega_engine_woland.domain.contracts.gate_contracts import (
        validate_typed_gate_receipt, validate_typed_gate_request,
    )
    validate_typed_gate_request(request)
    if response.get("success") is True and response["result"].get("refusal") is None:
        outcome = validate_typed_gate_receipt(response["result"]["outcome"])
        if outcome.gate_id == "PFP-14-NATASHA" and outcome.status == "PASS":
            if request["payload"].get("transport_profile") != getattr(outcome.witness, "transport_profile", None):
                raise ValueError("NATIVE_GATE_WITNESS_PROFILE_MISMATCH")
    validate_native_primary_outcome(request, response)


def _response_status(response: dict) -> str:
    if response.get("success") is not True:
        return "UNAVAILABLE"
    if response["result"]["refusal"] is not None:
        return "REFUSE"
    status = response["result"]["outcome"]["status"]
    if status not in {"PASS", "HOLD", "REFUSE", "BLOCKED", "DIVERTED"}:
        raise ValueError("NATIVE_GATE_STATUS_INVALID")
    return status


def decode_native_json(raw):
    """Reject ambiguous or nonfinite retained native/witness JSON."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("NATIVE_GATE_RAW_DUPLICATE_KEY")
            result[key] = value
        return result

    def finite(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("NATIVE_GATE_RAW_NONFINITE")
        if Decimal(value) != Decimal(str(parsed)):
            raise ValueError("NATIVE_GATE_JSON_DECIMAL_PRECISION_LOSS")
        return parsed

    return json.loads(raw, object_pairs_hook=unique, parse_float=finite,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))


def _decoded_streams(process):
    streams = {}
    for name in ("stdin", "stdout", "stderr"):
        streams[name] = base64.b64decode(process[name + "_base64"], validate=True)
        if hashlib.sha256(streams[name]).hexdigest() != process[name + "_sha256"]:
            raise ValueError("NATIVE_GATE_RAW_CAPTURE_CHANGED")
    return streams


def _process_exit_matches(process, response, binary, stdout):
    if process["exit_code"] != 0 or type(process["exit_code"]) is not int:
        return False
    if process["args"] != [binary["path"], "invoke"]:
        return False
    return native_digest(decode_native_json(stdout)) == native_digest(response)


def _framed_input_digest(payload):
    domain = b"omega.native.port-input.v1"
    framed = len(domain).to_bytes(4, "big") + domain + len(payload).to_bytes(8, "big") + payload
    return hashlib.sha256(framed).hexdigest()


def _support_file_matches(payload, request):
    normalized = json.loads(json.dumps(request, sort_keys=True))
    raw = json.dumps(normalized, allow_nan=False, ensure_ascii=False, separators=(",", ":")).encode()
    if set(payload) != {"request_file", "size", "sha256"}:
        return False
    if type(payload.get("size")) is not int or type(payload.get("request_file")) is not str:
        return False
    if not payload["request_file"]:
        return False
    if payload.get("size") != len(raw):
        return False
    return payload.get("sha256") == "sha256:" + hashlib.sha256(raw).hexdigest()


def _support_payload_matches(actual, request):
    if actual.get("action") == "woland_support":
        return native_digest(actual.get("payload")) == native_digest(request)
    if actual.get("action") != "woland_support_file":
        return False
    return _support_file_matches(actual["payload"], request)


def _validate_process(process, request, response, binary):
    streams = _decoded_streams(process)
    if not _process_exit_matches(process, response, binary, streams["stdout"]):
        raise ValueError("NATIVE_GATE_RAW_CAPTURE_CHANGED")
    actual = decode_native_json(streams["stdin"])
    if actual.get("schema_version") != "omega.symbol-game.runtime-request.v1":
        raise ValueError("NATIVE_GATE_RAW_CAPTURE_CHANGED")
    if (set(actual) != {"schema_version", "action", "payload"}
            or response.get("action") != actual.get("action")):
        raise ValueError("NATIVE_GATE_RAW_CAPTURE_CHANGED")
    payload = json.dumps(actual["payload"], sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode()
    if response["result"].get("input_digest") != _framed_input_digest(payload):
        raise ValueError("NATIVE_GATE_NATIVE_INPUT_DIGEST_CHANGED")
    if not _support_payload_matches(actual, request):
        raise ValueError("NATIVE_GATE_RAW_CAPTURE_CHANGED")
    validate_native_primary_outcome(request, response)


class ProcessObserverConfig(BaseModel):
    """Explicit operator-selected signing configuration; it grants no authority."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal["woland.process-observer-config.v1"] = "woland.process-observer-config.v1"
    policy_path: str = Field(min_length=1)
    policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    issuer: str = Field(min_length=1, max_length=512)
    key_id: str = Field(min_length=1, max_length=512)
    private_key_path: str = Field(min_length=1)
    private_key_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    lifetime_seconds: int = Field(ge=1, le=300)
    observer_source_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class KernelCheckConfig(BaseModel):
    """Operator-selected proof bytes and obligations, separate from model prose."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal["woland.kernel-check-config.v1"] = "woland.kernel-check-config.v1"
    proof_artifact_path: str = Field(min_length=1)
    lake_binary_path: str = Field(min_length=1)
    lake_binary_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    toolchain_pin: str = Field(min_length=1)
    required_declarations: list[list[str]] = Field(min_length=1)
    axiom_policy: list[str]
    observer: ProcessObserverConfig

    @model_validator(mode="after")
    def obligations(self):
        if (any(len(pair) != 2 or any(not value.strip() for value in pair)
                for pair in self.required_declarations)
                or len({pair[0] for pair in self.required_declarations}) != len(self.required_declarations)
                or any(not value.strip() for value in self.axiom_policy)
                or len(set(self.axiom_policy)) != len(self.axiom_policy)):
            raise ValueError("KERNEL_OBLIGATIONS_INVALID")
        return self


class ResourceCheckConfig(BaseModel):
    """Opt-in original checker sandbox; committed job memory is not RSS."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: Literal["woland.resource-check-config.v1"] = "woland.resource-check-config.v1"
    sandbox_binary_path: str = Field(min_length=1)
    sandbox_binary_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    timeout_ms: int = Field(gt=0, le=300_000)
    memory_limit_bytes: int = Field(gt=0)
    max_output_bytes: int = Field(gt=0, le=1_048_576)


def _scope_phase_invalid(gates):
    if not gates or len(set(gates)) != len(gates):
        return True
    for gate in gates:
        if gate not in NATIVE_GATE_IDS:
            return True
    ordered = tuple(gate for gate in NATIVE_GATE_IDS if gate in gates)
    return ordered != gates


def _configured_observer_ids(check):
    configured = set()
    if check.process_observer:
        configured.update(("PFP-15-JEREMY", "PFP-20-APHRANIUS"))
    if check.kernel_check:
        configured.add("PFP-07-THE-MASTER")
    if check.resource_check:
        configured.add("PFP-22-RATSLAYER")
    return configured


def _scope_excludes_configured(check):
    configured = _configured_observer_ids(check)
    for phase in ("native_post", "native_learn_post", "native_finish"):
        if not configured <= set(check.gate_scope[phase]):
            return True
    return False


class NativeGateCheck(BaseModel):
    """Immutable intake selection; missing witnesses are measured as residuals."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["woland.native-gate-check.v1"] = "woland.native-gate-check.v1"
    policy: Literal["diagnostic", "require_pass"] = "diagnostic"
    binary_path: str = ""
    binary_sha256: str = ""
    witness_path: str = ""
    witness_sha256: str = ""
    source_paths: dict[str, str] = Field(default_factory=dict)
    specification_sha256: dict[str, str] = Field(default_factory=dict)
    unavailable_reason: str = ""
    receipt_directory: str = ""
    process_observer: ProcessObserverConfig | None = None
    kernel_check: KernelCheckConfig | None = None
    resource_check: ResourceCheckConfig | None = None
    gate_scope: dict[str, tuple[str, ...]] | None = None

    @model_validator(mode="after")
    def declared_scope(self):
        if self.gate_scope is None:
            return self
        if (set(self.gate_scope) != set(NATIVE_GATE_PHASES)
                or any(_scope_phase_invalid(gates) for gates in self.gate_scope.values())):
            raise ValueError("NATIVE_GATE_SCOPE_INVALID: declare nonempty catalog-ordered IDs for every checkpoint")
        # Successful runs do not visit native_finish. Configured observers must
        # be checked after each original-task episode, including learned changes;
        # the stopped route must also retain their explicit evidence requirement.
        if _scope_excludes_configured(self):
            raise ValueError("NATIVE_GATE_SCOPE_EXCLUDES_CONFIGURED_OBSERVER")
        return self

    @model_serializer(mode="wrap")
    def versioned_wire(self, handler):
        result = handler(self)
        if self.process_observer is None:
            result.pop("process_observer", None)
        if self.kernel_check is None:
            result.pop("kernel_check", None)
        if self.resource_check is None:
            result.pop("resource_check", None)
        if self.gate_scope is None:
            result.pop("gate_scope", None)
        return result


def native_required_gate_ids(action) -> tuple[str, ...]:
    """Use the host's intake selection; absence retains the historical scan."""
    selection = action.native_gate_check
    if selection is None or selection.gate_scope is None:
        return NATIVE_GATE_IDS
    if action.phase not in NATIVE_GATE_PHASES:
        raise ValueError("NATIVE_GATE_SCOPE_PHASE_INVALID")
    return selection.gate_scope[action.phase]


def native_gate_applicability(action) -> dict[str, list[str]]:
    required = native_required_gate_ids(action)
    scope = action.native_gate_check.gate_scope
    selected = {gate for gates in scope.values() for gate in gates} if scope is not None else set(NATIVE_GATE_IDS)
    return {"required": list(required),
            "deferred": [gate for gate in NATIVE_GATE_IDS if gate in selected and gate not in required],
            "not_applicable": [gate for gate in NATIVE_GATE_IDS if gate not in selected]}


def native_required_edges(required) -> tuple[str, ...]:
    """Only a selected predicate and both selected endpoints form a path check."""
    return tuple(gate for gate, (source, target) in zip(INTERGATE_IDS, INTERGATE_ENDPOINTS, strict=True)
                 if gate in required and source in required
                 and ("PFP-07-THE-MASTER" if target == "PFP-07-MASTER" else target) in required)


def native_action_scope(action) -> dict:
    return {"run_id": action.run_id, "initial_task_id": action.initial_task_id,
        "action_id": action.action_id, "workflow_version": action.workflow_version,
        "stage": action.phase, "candidate_sha256": hashlib.sha256(action.candidate.encode()).hexdigest(),
        "objective_sha256": hashlib.sha256(action.objective.encode()).hexdigest(),
        "artifacts_sha256": native_digest(action.artifacts), "plan_sha256": action.plan_sha256,
        "check_source_id": action.check_source_id, "check_source_paths_sha256": native_digest(action.check_source_paths),
        "source_reads_sha256": native_digest([source.model_dump(mode="json") for source in action.source_reads]),
        "native_gate_check_sha256": native_digest(action.native_gate_check.model_dump(mode="json")),
        "host_observations_sha256": native_digest(action.native_host_observations),
        "prior_native_receipts_sha256": native_digest([{key: batch[key] for key in
            ("path", "sha256", "receipt_sha256")} for batch in action.native_gate_batches])}


def native_response_semantics(process, request, response, binary):
    """Verify actual transport digest before removing its ephemeral file path bind."""
    _validate_process(process, request, response, binary)
    normalized = json.loads(json.dumps(response))
    normalized["result"].pop("input_digest")
    return normalized


def validate_native_artifact_snapshots(action, snapshots):
    if type(snapshots) is not dict or set(snapshots) != set(action.artifacts):
        raise ValueError("NATIVE_GATE_ARTIFACT_SNAPSHOT_REQUIRED")
    for path, encoded in snapshots.items():
        raw = base64.b64decode(encoded, validate=True)
        if hashlib.sha256(raw).hexdigest() != action.artifacts[path].removeprefix("sha256:"):
            raise ValueError("NATIVE_GATE_ARTIFACT_SNAPSHOT_CHANGED")


_TRANSITION_KEYS = (
    "intergate_id", "source_gate", "target_gate", "source_status", "edge_status",
    "target_status", "attempted", "admitted", "diagnostic_path_passed",
)


def _row_status(response):
    if response.get("success") is not True:
        return "UNAVAILABLE", str(response.get("error"))
    if response["result"].get("refusal") is not None:
        return "REFUSE", response["result"]["refusal"]["code"]
    value = response["result"]["outcome"]
    return value["status"], value.get("refusal_code")


def _row_outcomes(rows):
    outcomes, residuals = {}, []
    for row in rows:
        status, code = _row_status(row["response"])
        outcomes[row["gate_id"]] = status
        if status != "PASS":
            residuals.append({"gate_id": row["gate_id"], "status": status, "code": code})
    return outcomes, residuals


def _transition_view(edge):
    return {key: edge[key] for key in _TRANSITION_KEYS}


def _all_pass(receipt, required, complete, residuals):
    if not required:
        return False
    if not complete:
        return complete
    if residuals:
        return False
    transitions = (receipt or {}).get("transitions", [])
    if len(transitions) != len(native_required_edges(required)):
        return False
    return all(edge["diagnostic_path_passed"] for edge in transitions)


def native_gate_summary(receipt: dict | None) -> dict:
    """Derive coverage from actual envelopes, never a saved PASS assertion."""
    body = receipt or {}
    if body.get("schema_version") == "woland.native-gate-reference.v1":
        return receipt["summary"]
    outcomes, residuals = _row_outcomes(body.get("results", []))
    scoped = body.get("schema_version") == "woland.native-gate-batch.v2"
    applicability = receipt["applicability"] if scoped else {"required": list(NATIVE_GATE_IDS)}
    required = applicability["required"]
    missing = [gate for gate in required if gate not in outcomes]
    complete = not missing and body.get("execution_complete", True)
    summary = {"required": required, "observed": list(outcomes), "missing": missing,
        "outcomes": outcomes, "residuals": residuals, "coverage_complete": complete,
        "all_pass": _all_pass(receipt, required, complete, residuals),
        "transitions": [_transition_view(edge) for edge in body.get("transitions", [])],
        "authority_effect": "None"}
    if scoped:
        summary["not_applicable"] = applicability["not_applicable"]
        summary["deferred"] = applicability["deferred"]
    return summary


def _reference_hash_invalid(receipt):
    for key in ("sha256", "receipt_sha256"):
        value = receipt.get(key)
        if type(value) is not str or len(value) != 64:
            return True
    return False


def _reference_summary_mismatch(action, receipt, required, scoped):
    summary = receipt.get("summary", {})
    if summary.get("required") != list(required):
        return True
    if not scoped:
        return False
    applicability = native_gate_applicability(action)
    for key, value in applicability.items():
        if key != "required" and summary.get(key) != value:
            return True
    return False


def _reference_receipt_mismatch(action, receipt, required, scoped):
    if receipt.get("scope") != native_action_scope(action):
        return True
    if receipt.get("authority_effect") != "None" or not receipt.get("path"):
        return True
    if _reference_hash_invalid(receipt):
        return True
    return _reference_summary_mismatch(action, receipt, required, scoped)


def _batch_binding_mismatch(action, receipt, scoped):
    expected = "woland.native-gate-batch.v2" if scoped else "woland.native-gate-batch.v1"
    if type(receipt) is not dict or receipt.get("schema_version") != expected:
        return True
    if receipt.get("scope") != native_action_scope(action):
        return True
    if receipt.get("authority_effect") != "None":
        return True
    return receipt.get("digest_profile") != "woland.native-parsed-envelope.v1"


def _scope_applicability_mismatch(action, receipt, scoped):
    if not scoped:
        return False
    return receipt.get("applicability") != native_gate_applicability(action)


def _receipt_digest_changed(receipt):
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    return receipt.get("receipt_sha256") != native_digest(body)


def _observation_time_invalid(receipt):
    observed = receipt.get("observation_time_utc")
    return type(observed) is not int or observed < 0


def _observation_required_missing(action, receipt):
    if action.feedback_policy != "semantic_digestion_v2":
        return False
    return _observation_time_invalid(receipt)


def _coverage_ids(required, receipt):
    rows = receipt.get("results")
    if receipt.get("execution_complete", True):
        return rows, required
    return rows, required[:len(rows)]


def _rows_cover(rows, expected_ids):
    if type(rows) is not list:
        return False
    return tuple(row.get("gate_id") for row in rows) == expected_ids


def _catalog_profiles(receipt):
    response = receipt.get("catalog_response") or {}
    result = response.get("result") or {}
    outcome = result.get("outcome") or {}
    return outcome.get("intergate_profiles", [])


def _contract_profile_mismatch(facts, measured, catalog_profiles):
    if not measured:
        return False
    if facts.get("source_contract_profile") != "pfp-intergates-source-v2":
        return True
    return "pfp-intergates-source-v2" not in catalog_profiles


def _source_profiles(measured):
    if measured:
        return ("pfp-intergates-source-v1", "pfp-intergates-source-v2")
    return ("pfp-intergates-source-v1",)


def _row_binding_changed(row, request, response):
    if type(request) is not dict or type(response) is not dict:
        return True
    if request.get("operation") != "gate_evaluate":
        return True
    if request.get("gate_id") != row["gate_id"]:
        return True
    if row.get("request_sha256") != native_digest(request):
        return True
    return row.get("response_sha256") != native_digest(response)


def _row_contract_mismatch(action, row, request, receipt, source_profiles):
    if action.feedback_policy != "semantic_digestion_v2" or row["gate_id"] not in INTERGATE_IDS:
        return False
    payload = request["payload"]
    if payload.get("contract_profile") not in source_profiles:
        return True
    return payload.get("now") != receipt["observation_time_utc"]


def _validate_row(action, row, receipt, source_profiles):
    request, response = row.get("request"), row.get("response")
    if _row_binding_changed(row, request, response):
        raise ValueError("NATIVE_GATE_RECEIPT_CHANGED")
    if _row_contract_mismatch(action, row, request, receipt, source_profiles):
        raise ValueError("NATIVE_GATE_CONTRACT_PROFILE_MISMATCH")
    if response.get("authority_effect") != "None":
        raise ValueError("NATIVE_GATE_AUTHORITY_REFUSED")
    _validate_process(row["process"], request, response, receipt["binary"])


def _validate_rows(action, rows, receipt, source_profiles):
    for row in rows:
        _validate_row(action, row, receipt, source_profiles)


def _validate_measured_contract(action, receipt, rows):
    facts = receipt.get("host_facts") or {}
    measured = facts.get("schema_version") == "woland.native-host-facts.v3"
    if _contract_profile_mismatch(facts, measured, _catalog_profiles(receipt)):
        raise ValueError("NATIVE_GATE_CONTRACT_PROFILE_MISMATCH")
    _validate_rows(action, rows, receipt, _source_profiles(measured))


def _validate_catalog(receipt):
    if receipt.get("catalog_response") is None:
        return
    _validate_process(receipt["catalog_process"], {"operation": "gate_schemas"},
                      receipt["catalog_response"], receipt["binary"])
    if native_digest(receipt["catalog_response"]) != receipt["catalog_sha256"]:
        raise ValueError("NATIVE_GATE_CATALOG_DRIFT")


def _expected_edges(required, receipt, transitions):
    required_edges = native_required_edges(required)
    if receipt.get("execution_complete", True):
        return required_edges
    return required_edges[:len(transitions)]


def _edges_cover(transitions, expected_edges):
    if type(transitions) is not list:
        return False
    return tuple(edge.get("intergate_id") for edge in transitions) == expected_edges


def _canonical_target(target):
    if target == "PFP-07-MASTER":
        return "PFP-07-THE-MASTER"
    return target


def _expected_edge_request(target_row, edge_row, intergate_id):
    expected_request = json.loads(json.dumps(target_row["request"]))
    expected_request["payload"]["_woland_scene"]["stage"] = "native_edge_target:" + intergate_id
    expected_request["history_edges"] = list(edge_row["request"]["history_edges"])
    return expected_request


def _edge_statuses(source_row, edge_row, edge):
    statuses = [_response_status(row["response"]) for row in (source_row, edge_row)]
    statuses.append(_response_status(edge["target_response"]))
    return statuses


def _expected_transition(action, edge, indexed):
    index = INTERGATE_IDS.index(edge["intergate_id"])
    source, target = INTERGATE_ENDPOINTS[index]
    canonical_target = _canonical_target(target)
    source_row, target_row, edge_row = indexed[source], indexed[canonical_target], indexed[edge["intergate_id"]]
    expected_request = _expected_edge_request(target_row, edge_row, edge["intergate_id"])
    statuses = _edge_statuses(source_row, edge_row, edge)
    passed = statuses == ["PASS", "PASS", "PASS"]
    return {"source_gate": source, "target_gate": target, "canonical_target_gate": canonical_target,
        "source_request_sha256": source_row["request_sha256"], "source_response_sha256": source_row["response_sha256"],
        "edge_request_sha256": edge_row["request_sha256"], "edge_response_sha256": edge_row["response_sha256"],
        "target_request": expected_request, "target_request_sha256": native_digest(expected_request),
        "target_response_sha256": native_digest(edge["target_response"]),
        "source_status": statuses[0], "edge_status": statuses[1], "target_status": statuses[2],
        "attempted": True, "admitted": action.native_gate_check.policy == "require_pass" and passed,
        "diagnostic_path_passed": passed, "role_flow_traversal": False, "authority_effect": "None"}, expected_request


def _edge_binding_mismatch(edge, expected):
    for key, value in expected.items():
        if edge.get(key) != value or type(edge.get(key)) is not type(value):
            return True
    return False


def _validate_transition(action, edge, indexed, binary):
    expected, expected_request = _expected_transition(action, edge, indexed)
    if _edge_binding_mismatch(edge, expected):
        raise ValueError("NATIVE_GATE_TRANSITION_BINDING_MISMATCH")
    _validate_process(edge["target_process"], expected_request, edge["target_response"], binary)


def _validate_transitions(action, receipt, required):
    transitions = receipt.get("transitions")
    expected_edges = _expected_edges(required, receipt, transitions)
    if not _edges_cover(transitions, expected_edges):
        raise ValueError("NATIVE_GATE_TRANSITION_COVERAGE_REQUIRED")
    indexed = {row["gate_id"]: row for row in receipt.get("results")}
    for edge in transitions:
        _validate_transition(action, edge, indexed, receipt["binary"])


def validate_native_gate_receipt(action, receipt: dict) -> None:
    """Pure retained-wire check. Host boundaries additionally replay predicates."""
    required = native_required_gate_ids(action)
    scoped = action.native_gate_check.gate_scope is not None
    if receipt.get("schema_version") == "woland.native-gate-reference.v1":
        if _reference_receipt_mismatch(action, receipt, required, scoped):
            raise ValueError("NATIVE_GATE_REFERENCE_MISMATCH")
        return
    if _batch_binding_mismatch(action, receipt, scoped):
        raise ValueError("NATIVE_GATE_BINDING_MISMATCH")
    if _scope_applicability_mismatch(action, receipt, scoped):
        raise ValueError("NATIVE_GATE_SCOPE_BINDING_MISMATCH")
    if _receipt_digest_changed(receipt):
        raise ValueError("NATIVE_GATE_RECEIPT_CHANGED")
    if _observation_required_missing(action, receipt):
        raise ValueError("NATIVE_GATE_OBSERVATION_TIME_REQUIRED")
    validate_native_artifact_snapshots(action, receipt.get("artifact_snapshots", {}))
    rows, expected_ids = _coverage_ids(required, receipt)
    if not _rows_cover(rows, expected_ids):
        raise ValueError("NATIVE_GATE_COVERAGE_REQUIRED: execute every declared native ID")
    _validate_measured_contract(action, receipt, rows)
    _validate_catalog(receipt)
    _validate_transitions(action, receipt, required)
