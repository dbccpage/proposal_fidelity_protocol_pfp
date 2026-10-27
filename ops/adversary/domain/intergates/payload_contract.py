"""Inputs for implemented diagnostic checks, distinct from PFP design schemas.

These metrics are telemetry; they are not exact cochain or correctness evidence.
AuthorityEffect: None.
"""
from __future__ import annotations

import math

PAYLOAD_FIELDS = {
    "PFP-IG-01-FLOW-BAND": {"prompt_complexity_delta": "number", "agent_capacity_score": "number"},
    "PFP-IG-02-EPISTEMIC-SURPRISE": {"epistemic_entropy_delta": "number", "gauge_shift_applied": "bool"},
    "PFP-IG-03-COWARDICE-EVASION": {"critique_severity": "number", "response_vagueness_index": "number", "yields_without_evidence": "bool", "has_typed_defect_admission": "bool"},
    "PFP-IG-04-PLAYFUL-REVERSIBILITY": {"sandbox_isolated": "bool", "authority_effect": "text"},
    "PFP-IG-05-FALSE-URGENCY-DESENSITIZATION": {"prompt_or_context_text": "text"},
    "PFP-IG-06-AFFECTIVE-DEESCALATION": {"panic_spiral_active": "bool"},
    "PFP-IG-07-MANUFACTURED-CONSENSUS": {"agent_evaluator_ids": "texts", "sampling_seeds": "ints", "producer_id": "nonempty_text"},
    "PFP-IG-08-QUARANTINE-RECOVERY": {"epistemic_quarantine_cleared": "bool", "stabilization_cycles": "int"},
    "PFP-IG-09-DECEPTION-COUNTERMEASURE": {"pattern_defense_bound": "bool"},
    "PFP-IG-10-TERMINAL-REALITY-TETHER": {"candidate_summary_text": "text", "checker_receipt_verdict": "text"},
}

# Explicit finite resolution of the retained design YAML. The unprofiled
# diagnostics above remain compatible; native owns the source-profile laws.
SOURCE_CONTRACT_PROFILE = "pfp-intergates-source-v1"
MEASURED_SOURCE_CONTRACT_PROFILE = "pfp-intergates-source-v2"
SOURCE_CONTRACT_PROFILES = (SOURCE_CONTRACT_PROFILE, MEASURED_SOURCE_CONTRACT_PROFILE)
LEGACY_DIAGNOSTIC_PROFILE = "legacy-diagnostic-v1"
SOURCE_PAYLOAD_FIELDS = {
    "PFP-IG-01-FLOW-BAND": {"round_number": "int", "prompt_complexity_score": "number",
        "agent_capacity_score": "number", "feedback_loop_ms": "int", "feedback_loop_limit_ms": "int",
        "prior_round": "nullable_object"},
    "PFP-IG-02-EPISTEMIC-SURPRISE": {"round_number": "int", "previous_prompt_kl_divergence": "number",
        "carrier_isomorphism_valid": "bool", "carrier_mapping": "object"},
    "PFP-IG-03-COWARDICE-EVASION": {**PAYLOAD_FIELDS["PFP-IG-03-COWARDICE-EVASION"],
        "typed_defect": "nullable_object", "sponsor_challenge_present": "bool",
        "response_evidence_hex": "text", "explicit_refusal": "bool"},
    "PFP-IG-04-PLAYFUL-REVERSIBILITY": {"sandbox_boundary_active": "bool",
        "declared_authority_effect": "text", "has_production_side_effects": "bool",
        "canonical_before_hex": "text", "canonical_after_hex": "text",
        "sandbox_before_hex": "text", "sandbox_restored_hex": "text"},
    "PFP-IG-05-FALSE-URGENCY-DESENSITIZATION": {"prompt_text": "text", "urgency_indicators": "texts",
        "sanitized_prompt_text": "text", "verification_started_ms": "int", "verification_completed_ms": "int",
        "minimum_buffer_ms": "int", "declared_time_constraint": "text"},
    "PFP-IG-06-AFFECTIVE-DEESCALATION": {"turn_number": "int", "antagonism_score": "number",
        "prior_turn": "nullable_object", "has_acknowledged_error": "bool", "repair_action_proposed": "text",
        "scar_before": "texts", "scar_after": "texts", "deescalation_envelope": "text"},
    "PFP-IG-07-MANUFACTURED-CONSENSUS": {**PAYLOAD_FIELDS["PFP-IG-07-MANUFACTURED-CONSENSUS"],
        "producer_context_hex": "text", "evaluator_contexts": "object",
        "dissenting_evaluator_ids": "texts", "dissent_records": "objects"},
    "PFP-IG-08-QUARANTINE-RECOVERY": {"quarantine_cause": "nonempty_text", "harm_class": "nonempty_text",
        "repair_before_hex": "nonempty_text", "repair_after_hex": "nonempty_text",
        "candidate_content": "text", "checker_receipt_hex": "nonempty_text", "checker_receipt_verdict": "text"},
    "PFP-IG-09-DECEPTION-COUNTERMEASURE": {"detected_exploit_uids": "texts", "exploit_severities": "numbers",
        "bound_countermeasure_uids": "texts", "applied_countermeasure_uids": "texts"},
    "PFP-IG-10-TERMINAL-REALITY-TETHER": {**PAYLOAD_FIELDS["PFP-IG-10-TERMINAL-REALITY-TETHER"],
        "candidate_content": "text", "checker_receipt_hex": "nonempty_text"},
}
SOURCE_TRUST_FIELDS = {"task_id": "nonempty_text", "source_digest": "nonempty_text",
    "trust_policy": "object", "expected_binding": "object", "now": "int",
    "witness_issuers": "object", "dual_witnesses": "objects", "checker_issuer": "nonempty_text",
    "checker_id": "nonempty_text", "checker_attestation": "object", "timestamp_issuer": "nonempty_text",
    "timestamp_witness": "object"}


def _finite_number(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _matches(value: object, kind: str) -> bool:
    match kind:
        case "number":
            return _finite_number(value)
        case "bool":
            return type(value) is bool
        case "int":
            return isinstance(value, int) and not isinstance(value, bool) and value >= 0
        case "text":
            return type(value) is str
        case "nonempty_text":
            return type(value) is str and bool(value.strip())
        case "texts":
            return type(value) is list and all(_matches(item, "nonempty_text") for item in value)
        case "ints":
            return type(value) is list and all(_matches(item, "int") for item in value)
        case "numbers":
            return type(value) is list and all(_finite_number(item) for item in value)
        case "object":
            return type(value) is dict
        case "nullable_object":
            return value is None or type(value) is dict
        case "objects":
            return type(value) is list and all(type(item) is dict for item in value)
        case _:
            return False


def missing_source_inputs(intergate_id: str, payload: dict) -> tuple[str, ...]:
    """Names only: absence never supplies a default observation or a verdict."""
    return tuple(key for key in SOURCE_PAYLOAD_FIELDS.get(intergate_id, {}) if key not in payload)


def validate_payload(intergate_id: str, payload: object) -> str | None:
    source_profile = type(payload) is dict and payload.get("contract_profile") in SOURCE_CONTRACT_PROFILES
    measured_profile = source_profile and payload["contract_profile"] == MEASURED_SOURCE_CONTRACT_PROFILE
    fields = (SOURCE_PAYLOAD_FIELDS if source_profile else PAYLOAD_FIELDS).get(intergate_id)
    if fields is None:
        return "No implemented diagnostic for this intergate"
    if type(payload) is not dict:
        return "Payload must be a JSON object"
    def matches(value, kind):
        if measured_profile and kind == "int":
            return type(value) is int and 0 <= value < 2 ** 64
        if measured_profile and kind == "ints":
            return type(value) is list and all(matches(item, "int") for item in value)
        if source_profile and kind == "number":
            # Native compares JSON integers exactly; do not overflow a float
            # merely to validate their type. Legacy limits remain unchanged.
            return type(value) is int or (type(value) is float and math.isfinite(value))
        if source_profile and kind == "numbers":
            return type(value) is list and all(matches(item, "number") for item in value)
        return _matches(value, kind)

    for key, kind in fields.items():
        # V1 keeps its historical missing-as-invalid behavior. V2 sends absent
        # observations to the native owner, which returns a captured HOLD.
        # A supplied malformed value is still invalid even if other keys lack
        # measurements; absence must not conceal a hostile supplied operand.
        if measured_profile and key not in payload:
            continue
        if key not in payload or not matches(payload[key], kind):
            return f"{key} must be supplied as {kind}"
    if measured_profile:
        for key in fields:
            if key.endswith("_hex") and key in payload:
                value = payload[key]
                try:
                    decoded = bytes.fromhex(value)
                except ValueError:
                    return f"{key} must be lower-case hex bytes"
                if decoded.hex() != value or (not decoded and key != "response_evidence_hex"):
                    return f"{key} must be lower-case hex bytes with the required nonempty value"
    for key in ("residual_descent_observed", "bypass_gates_requested"):
        if key in payload and type(payload[key]) is not bool:
            return f"{key} must be a boolean"
    if source_profile:
        for key, kind in SOURCE_TRUST_FIELDS.items():
            if key in payload and not matches(payload[key], kind):
                return f"{key} must be supplied as {kind}"
    return None
