"""Two finite charpoly-first plans; no provider, ledger or runner side effects.

Runner integration: call preflight(seed_hash) BEFORE any paid candidate; use
public_context for every stage; check_candidate after candidate/repair; retain
the full check result but expose only its feedback to repair and solver_context
to solve. next_stage enforces one repair/gating. Only responses['solve'] is the
answer. The runtime separately verifies the unchanged task's actual seed bytes.
The checked assertion is an INTERMEDIATE artifact, never synthesized prose.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import native_sidecar as sidecar
import qm_native_charpoly as qm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAX_RAW_BYTES = 32_768
MAX_RAW_CONTEXT_BYTES = 8_192
MAX_FEEDBACK_BYTES = 1_536
MAX_JSON_DEPTH = 8
IMPLEMENTATION_FILES = (
    "charpoly_workflows.py", "qm_native_charpoly.py", "hamiltonian_artifact.py",
    "native_sidecar.py", "reference_runner.py", "live_campaign.py",
    "campaign_ledger.py", "budget_ledger.py", "openrouter_provider.py",
    "native_sidecar_manifest.json", "qm_native_charpoly_manifest.json",
    "native_sidecar_host/Cargo.toml", "native_sidecar_host/Cargo.lock",
    "native_sidecar_host/src/main.rs", "native_sidecar_host/src/production_charpoly.rs",
    "native_sidecar_host/source_binding.json", "native_sidecar_host/build_native.py",
    "native_sidecar_host/build_receipt.json",
)

_CANDIDATE = {"id": "charpoly", "max_output_tokens": 2400, "visible_artifacts": [],
    "instruction": 'Return ONLY one strict JSON object {"coefficients":...} matching the public coefficient contract. Compute the characteristic polynomial of the supplied public affine Hamiltonian for all three parameters. No markdown, prose, hashes, matrices, or other keys.'}
_REPAIR = {"id": "charpoly_repair", "max_output_tokens": 2400,
    "visible_artifacts": ["charpoly", "charpoly_feedback"],
    "instruction": 'Repair the previous intermediate coefficient proposal using the bounded public feedback. Return ONLY a complete strict JSON object {"coefficients":...}; no markdown, prose, hashes, matrices, or other keys.'}
_SOLVE = {"id": "solve", "max_output_tokens": 12000,
    "visible_artifacts": ["charpoly_context"],
    "instruction": "Answer the complete unchanged task. The supplied coefficients are an untrusted intermediate proposal, not a certification of your answer. Verify the mathematics you use, address all task obligations and parameter cases, and justify the final result. Return the final answer only."}
CHARPOLY_PLANS = {
    "qm_charpoly_checked_v1": {"stages": [deepcopy(_CANDIDATE), deepcopy(_REPAIR), deepcopy(_SOLVE)],
        "max_repairs": 1, "gate_solve": True, "max_total_output_tokens": 16800,
        "answer_stage": "solve", "checked": True,
        "scope": "Intermediate characteristic-polynomial certificate only; synthesized solve answer is not certified."},
    "qm_charpoly_ungated_v1": {"stages": [deepcopy(_CANDIDATE), deepcopy(_SOLVE)],
        "max_repairs": 0, "gate_solve": False, "max_total_output_tokens": 14400,
        "answer_stage": "solve", "checked": False,
        "scope": "Ungated intermediate coefficient proposal; checker verdict withheld from synthesis."},
}


class CandidateError(ValueError):
    pass


class WorkflowError(ValueError):
    pass


def implementation_files():
    return list(_FROZEN_SOURCE_PINS)


def _prepare_source_pins():
    """Fresh process captures the current verified build, not historical test pins."""
    pins = {}
    try:
        for name in IMPLEMENTATION_FILES:
            pins[name] = sidecar.file_sha(HERE / name)
        binary, native = sidecar.NativeHost().custody()
        pins[binary.relative_to(HERE).as_posix()] = native["binary_sha256"]
        return pins, native, None
    except (sidecar.Infrastructure, OSError, ValueError, TypeError, KeyError) as exc:
        return pins, None, "CHARPOLY_PREPARATION_FAILED:" + type(exc).__name__


def preflight(seed_hash):
    """Recheck process-frozen source/binary pins and native custody before dispatch.

    Historical test manifests are provenance only. A fresh process may capture
    a freshly rebuilt, independently custody-verified native host. This process
    refuses any source/build/binary change after its plans were prepared.
    """
    try:
        if _PREPARATION_ERROR:
            raise sidecar.Infrastructure(_PREPARATION_ERROR)
        for name, expected in _FROZEN_SOURCE_PINS.items():
            if sidecar.file_sha(HERE / name) != expected:
                raise sidecar.Infrastructure("CHARPOLY_SOURCE_CHANGED")
        packet = qm.prepare_public(seed_hash)
        binary, native = sidecar.NativeHost().custody()
        if native != _PREPARED_NATIVE_CUSTODY:
            raise sidecar.Infrastructure("CHARPOLY_NATIVE_CUSTODY_CHANGED")
        return {"status": "READY", "seed_sha256": seed_hash,
                "public_packet_sha256": packet["sha256"], "source_pins": dict(_FROZEN_SOURCE_PINS),
                "native_binary_path": str(binary), "native_custody": native,
                "implementation_files": implementation_files(), "provider_calls": 0}
    except sidecar.Infrastructure:
        raise
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise sidecar.Infrastructure("CHARPOLY_PREFLIGHT_FAILED:" + type(exc).__name__) from None


def public_context(seed_hash):
    """Public operands and coefficient format only: no answer polynomial or verdict."""
    contract = qm.public_contract(seed_hash)
    payload = contract["public_packet"]["payload"]
    coefficients_schema = contract["candidate_schema"]["properties"]["coefficients"]
    return {"schema": "pfp.charpoly-workflow.public-context.v1",
            "seed_sha256": seed_hash, "basis": payload["basis"],
            "pauli_semantics": payload["pauli_semantics"],
            "public_input_artifact": payload["public_input_artifact"],
            "coefficient_contract": {"type": "object", "additionalProperties": False,
                "required": ["coefficients"], "properties": {"coefficients": coefficients_schema}},
            "coefficient_convention": contract["coefficient_convention"],
            "source_binding": payload["source_binding"],
            "scope": "Intermediate characteristic-polynomial coefficients only; the full task has additional obligations."}


def _bounded_raw(text):
    if type(text) is not str:
        text = "[candidate response was not text]"
    replaced = False
    try:
        raw = text.encode("utf-8")
    except UnicodeEncodeError:
        raw = text.encode("utf-8", errors="replace")
        replaced = True
    return {"schema": "pfp.charpoly-workflow.solver-context.v1", "representation": "raw_candidate",
            "raw_text": raw[:MAX_RAW_CONTEXT_BYTES].decode("utf-8", errors="ignore"),
            "truncated": len(raw) > MAX_RAW_CONTEXT_BYTES, "original_utf8_bytes": len(raw),
            "utf8_replaced": replaced}


def _parse_candidate(text):
    if type(text) is not str:
        raise CandidateError("CANDIDATE_NOT_TEXT")
    try:
        raw = text.encode("utf-8")
    except UnicodeEncodeError:
        raise CandidateError("CANDIDATE_UTF8_INVALID") from None
    if len(raw) > MAX_RAW_BYTES:
        raise CandidateError("CANDIDATE_BYTE_LIMIT")
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == '"': quoted = False
        elif char == '"': quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH: raise CandidateError("CANDIDATE_DEPTH_LIMIT")
        elif char in "]}":
            depth -= 1
            if depth < 0: raise CandidateError("MALFORMED_JSON")
    try:
        value = sidecar.strict_json(text)
    except sidecar.Invalid as exc:
        code = str(exc)
        raise CandidateError(code if code in {"DUPLICATE_JSON_KEY", "FLOAT_FORBIDDEN"} else "MALFORMED_JSON") from None
    except (ValueError, RecursionError):
        raise CandidateError("MALFORMED_JSON") from None
    if type(value) is not dict or set(value) != {"coefficients"}:
        raise CandidateError("CLOSED_COEFFICIENTS_OBJECT_REQUIRED")
    try:
        sidecar.admit_coefficients(value["coefficients"], 4)
    except sidecar.Invalid as exc:
        raise CandidateError(str(exc)) from None
    return value


def _safe_feedback(feedback):
    """Reject unexpected fields; never relay a full receipt/polynomial to repair."""
    if type(feedback) is not dict or len(sidecar.canonical(feedback)) > MAX_FEEDBACK_BYTES:
        raise WorkflowError("FEEDBACK_INVALID")
    kind = feedback.get("kind")
    if kind in {"schema", "infrastructure"}:
        if set(feedback) != {"kind", "code"} or type(feedback["code"]) is not str or len(feedback["code"]) > 80:
            raise WorkflowError("FEEDBACK_INVALID")
    elif kind == "none":
        if set(feedback) != {"kind"}: raise WorkflowError("FEEDBACK_INVALID")
    elif kind == "exact_mismatch":
        if set(feedback) != {"kind", "witness"}: raise WorkflowError("FEEDBACK_INVALID")
        witness = feedback["witness"]
        if type(witness) is not dict or set(witness) != {"parameters", "lambda_power", "claimed", "observed", "difference"}:
            raise WorkflowError("FEEDBACK_INVALID")
        parameters = witness["parameters"]
        if (type(parameters) is not dict or set(parameters) != {"J", "Delta", "K"} or
            any(type(v) is not int or v not in range(-2, 3) for v in parameters.values()) or
            type(witness["lambda_power"]) is not int or witness["lambda_power"] not in range(5)):
            raise WorkflowError("FEEDBACK_INVALID")
        for key in ["claimed", "observed", "difference"]:
            if type(witness[key]) is not str or len(witness[key]) > 256:
                raise WorkflowError("FEEDBACK_INVALID")
            try: sidecar.rational(witness[key], bits=1024)
            except sidecar.Invalid: raise WorkflowError("FEEDBACK_INVALID") from None
    else:
        raise WorkflowError("FEEDBACK_INVALID")
    return deepcopy(feedback)


def check_candidate(raw_text, seed_hash):
    """Host-package/check an INTERMEDIATE assertion; sanitize all model-visible feedback."""
    context = _bounded_raw(raw_text)
    result = {"accepted": False, "status": "candidate_invalid",
              "solver_context": sidecar.canonical(context).decode("ascii"),
              "feedback": {"kind": "schema", "code": "MALFORMED_JSON"},
              "verification_receipt": {"schema": "pfp.charpoly-workflow.intermediate-check.v1",
                  "claim_scope": "intermediate_characteristic_polynomial_identity_only",
                  "final_answer_certified": False, "native_executed": False}}
    try:
        ready = preflight(seed_hash)
        receipt = result["verification_receipt"]
        receipt.update(seed_sha256=seed_hash, source_pins=ready["source_pins"],
                       native_custody=ready["native_custody"])
        value = _parse_candidate(raw_text)
        coefficients = value["coefficients"]
        result["solver_context"] = sidecar.canonical({"schema": "pfp.charpoly-workflow.solver-context.v1",
            "representation": "coefficients", "coefficients": coefficients}).decode("ascii")
        packet = qm.prepare_public(seed_hash)
        public = packet["payload"]["native_public_input"]
        assertion = sidecar.assertion_text(coefficients)
        assertion_bytes = assertion.encode("utf-8")
        candidate = {"schema": "pfp.qm-affine-charpoly-candidate.v1",
            "public_input_sha256": sidecar.digest(public), "obligation_id": public["obligation_id"],
            "answer_sha256": hashlib.sha256(assertion_bytes).hexdigest(),
            "assertion_span": [0, len(assertion_bytes)], "assertion_text": assertion,
            "coefficients": coefficients}
        checked = qm.verify(seed_hash, candidate, assertion, packet)
        status = checked["status"]
        if status in {"INFRASTRUCTURE_REFUSAL", "PUBLIC_BINDING_REFUSAL"}:
            raise sidecar.Infrastructure("INTERMEDIATE_CHECKER_UNAVAILABLE")
        if status not in {"CERTIFIED_IDENTITY", "REFUTED_IDENTITY", "UNSUPPORTED_OR_MALFORMED"}:
            raise sidecar.Infrastructure("INTERMEDIATE_CHECKER_PROTOCOL")
        native = checked.get("native_receipt", {})
        receipt.update(status=status, raw_candidate_sha256=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
            coefficient_payload_sha256=sidecar.digest(value), intermediate_assertion_sha256=candidate["answer_sha256"],
            intermediate_candidate_sha256=sidecar.digest(candidate), public_packet_sha256=packet["sha256"],
            public_input_sha256=sidecar.digest(public), native_executed=checked["native_executed"],
            native_binding={key: native.get(key) for key in ["binary_sha256", "build_receipt_sha256",
                "request_sha256", "response_sha256", "grid_points", "native_calls"]},
            unresolved=checked["unresolved"])
        result.update(status=status, accepted=status == "CERTIFIED_IDENTITY")
        if result["accepted"]:
            result["feedback"] = {"kind": "none"}
        elif status == "REFUTED_IDENTITY":
            witness = native["witness"]
            feedback = {"kind": "exact_mismatch", "witness": {"parameters": witness["parameters"],
                "lambda_power": witness["lambda_power"], "claimed": witness["claimed"],
                "observed": witness["native"], "difference": witness["difference"]}}
            try: result["feedback"] = _safe_feedback(feedback)
            except WorkflowError: result["feedback"] = {"kind": "schema", "code": "EXACT_MISMATCH_WITNESS_EXCEEDS_FEEDBACK_LIMIT"}
        else:
            result["feedback"] = {"kind": "schema", "code": "INTERMEDIATE_COEFFICIENT_ENCODING_REFUSED"}
    except CandidateError as exc:
        result["feedback"] = {"kind": "schema", "code": str(exc)}
    except (sidecar.Infrastructure, qm.PublicBindingError, OSError, KeyError, TypeError, ValueError):
        result.update(status="INFRASTRUCTURE_REFUSAL", accepted=False,
                      feedback={"kind": "infrastructure", "code": "host_infrastructure_failure"})
    result["verification_receipt"].update(status=result["status"], accepted=result["accepted"])
    return result


def next_stage(plan_id, checks):
    """Pure finite transition law over HOST-owned check results, not model labels."""
    if plan_id not in CHARPOLY_PLANS or type(checks) is not dict or set(checks) - {"charpoly", "charpoly_repair"}:
        raise WorkflowError("PLAN_STATE_INVALID")
    plan = CHARPOLY_PLANS[plan_id]
    if "charpoly_repair" in checks and (not plan["max_repairs"] or "charpoly" not in checks):
        raise WorkflowError("REPAIR_STATE_INVALID")
    for check in checks.values():
        if type(check) is not dict or type(check.get("accepted")) is not bool:
            raise WorkflowError("HOST_CHECK_REQUIRED")
        if check.get("status") == "INFRASTRUCTURE_REFUSAL":
            return {"stage": None, "terminal_status": "host_infrastructure_failure"}
        if check["accepted"] != (check.get("status") == "CERTIFIED_IDENTITY"):
            raise WorkflowError("HOST_CHECK_INCONSISTENT")
    if "charpoly" not in checks:
        return {"stage": "charpoly", "terminal_status": None}
    if not plan["gate_solve"]:
        return {"stage": "solve", "terminal_status": None}
    latest = checks.get("charpoly_repair", checks["charpoly"])
    if latest["accepted"]:
        return {"stage": "solve", "terminal_status": None}
    if "charpoly_repair" not in checks:
        return {"stage": "charpoly_repair", "terminal_status": None}
    return {"stage": None, "terminal_status": "charpoly_gate_failed"}


def stage_request(plan_id, stage, unchanged_task, seed_hash, artifacts):
    """Pure model-request material. Parent owns preflight, dispatch, budget and raw receipts."""
    if plan_id not in CHARPOLY_PLANS or type(unchanged_task) is not str or type(artifacts) is not dict:
        raise WorkflowError("STAGE_REQUEST_INVALID")
    spec = next((s for s in CHARPOLY_PLANS[plan_id]["stages"] if s["id"] == stage), None)
    if spec is None: raise WorkflowError("STAGE_NOT_REGISTERED")
    visible = {}
    for name in spec["visible_artifacts"]:
        if name not in artifacts: raise WorkflowError("STAGE_ARTIFACT_MISSING")
        if name == "charpoly_feedback":
            visible[name] = _safe_feedback(artifacts[name])
        elif name == "charpoly":
            visible[name] = _bounded_raw(artifacts[name])
        else:
            text = artifacts[name]
            if type(text) is not str or len(text.encode("utf-8")) > MAX_RAW_BYTES * 6 + 1024:
                raise WorkflowError("SOLVER_CONTEXT_INVALID")
            context = sidecar.strict_json(text)
            representation = context.get("representation") if type(context) is dict else None
            allowed = ({"schema", "representation", "coefficients"} if representation == "coefficients" else
                       {"schema", "representation", "raw_text", "truncated", "original_utf8_bytes", "utf8_replaced"})
            if (type(context) is not dict or set(context) != allowed or
                context.get("schema") != "pfp.charpoly-workflow.solver-context.v1" or
                representation not in {"coefficients", "raw_candidate"}):
                raise WorkflowError("SOLVER_CONTEXT_INVALID")
            visible[name] = context
    return {"stage": stage, "max_output_tokens": spec["max_output_tokens"],
            "instruction": spec["instruction"], "task": unchanged_task,
            "public_context": public_context(seed_hash), "visible_artifacts": visible}


# Preparing the registry verifies the current native build without executing it.
# Missing custody is deferred to preflight so unrelated workflows can still load.
_FROZEN_SOURCE_PINS, _PREPARED_NATIVE_CUSTODY, _PREPARATION_ERROR = _prepare_source_pins()
for _plan in CHARPOLY_PLANS.values():
    _plan["source_pins"] = dict(_FROZEN_SOURCE_PINS)
