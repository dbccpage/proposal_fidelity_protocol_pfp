"""evaluator.py
============

Evaluator engine for the 10 PFP Intergate transition dynamics and curvature obstructions.

Governing Epic: EPIC-OE-ADVERSARY-002
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional, Sequence

from adversary.domain.intergates.cogwar_shield import (
    check_claim_hygiene,
    check_false_urgency,
    check_four_part_summary,
    check_manufactured_consensus,
    check_sycophantic_yielding,
)
from adversary.domain.intergates.intergate_loader import (
    load_intergate_specs,
)
from adversary.domain.intergates.models import (
    CurvatureObstruction,
    IntergateEvaluationResult,
    IntergateSpec,
)
from adversary.domain.intergates.payload_contract import (
    LEGACY_DIAGNOSTIC_PROFILE,
    MEASURED_SOURCE_CONTRACT_PROFILE,
    SOURCE_CONTRACT_PROFILES,
    validate_payload,
)
from adversary.domain.native import NativeOperationPort


class IntergateEvaluator:
    """Evaluates transition dynamics across the 10 PFP intergates."""

    def __init__(self, specs: Optional[Dict[str, IntergateSpec]] = None, *,
                 native_evaluator: Callable[[str, dict, Sequence[str]], Mapping[str, Any]] | None = None, native_support: NativeOperationPort | None = None) -> None:
        self._native_support = native_support
        self._specs = load_intergate_specs() if specs is None else specs
        self._native_evaluator = native_evaluator
        self.last_native_result: dict[str, Any] | None = None

    def specification_digests(self) -> dict[str, str]:
        """Digests of the captured YAML bytes parsed into this evaluator."""
        return {spec.source_file: spec.source_sha256 for spec in self._specs.values()}

    def get_spec(self, intergate_id_or_edge: str) -> Optional[IntergateSpec]:
        """Resolve an intergate spec by ID or transition edge."""
        if intergate_id_or_edge in self._specs:
            return self._specs[intergate_id_or_edge]

        # Try matching by transition from/to (e.g. 'PFP-01->PFP-02')
        for spec in self._specs.values():
            edge = f"{spec.transition_from}->{spec.transition_to}"
            if intergate_id_or_edge in (edge, spec.name):
                return spec
        return None

    def evaluate_transition(
        self,
        intergate_id: str,
        payload: Dict[str, Any],
        history_edges: Sequence[str] = (),
    ) -> IntergateEvaluationResult:
        """Evaluate an intergate transition against declared invariants.

        Args:
            intergate_id: The ID of the intergate (e.g. 'PFP-IG-01-FLOW-BAND').
            payload: Dynamic carrier metrics and audit flags for the transition.
            history_edges: Prior transition edge identifiers to check for curvature cycling.

        Returns:
            An IntergateEvaluationResult with PASS, BLOCKED, or DIVERTED status.
        """
        self.last_native_result = None
        spec = self._specs.get(intergate_id)
        if spec is None:
            return IntergateEvaluationResult(
                intergate_id=intergate_id,
                status="BLOCKED",
                transition_from="UNKNOWN",
                transition_to="UNKNOWN",
                cognitive_vector="UNRESOLVED",
                curvature_obstruction=CurvatureObstruction(detected=False),
                refusal_code="INTERGATE_SPEC_NOT_FOUND",
                diagnostics=f"No intergate specification found for ID '{intergate_id}'",
                witness="intergate_spec_missing",
            )

        if type(payload) is not dict or (
            "residual_descent_observed" in payload
            and type(payload["residual_descent_observed"]) is not bool
        ):
            return self._blocked(spec, "INTERGATE_PAYLOAD_INVALID", "Invalid payload or descent flag")
        if type(history_edges) not in (list, tuple) or not all(type(edge) is str for edge in history_edges):
            return self._blocked(spec, "INTERGATE_PAYLOAD_INVALID", "History must be a sequence of edges")
        if "contract_profile" in payload and payload["contract_profile"] != LEGACY_DIAGNOSTIC_PROFILE:
            if payload["contract_profile"] not in SOURCE_CONTRACT_PROFILES:
                return self._blocked(spec, "INTERGATE_CONTRACT_PROFILE_UNSUPPORTED", "Unknown explicit contract profile")
            if self._native_evaluator is None:
                return self._blocked(spec, "INTERGATE_NATIVE_REQUIRED", "Source-contract evaluation requires the configured native owner")
            defect = validate_payload(spec.intergate_id, payload)
            if defect:
                return self._blocked(spec, "INTERGATE_PAYLOAD_INVALID", defect)
            return self._evaluate_source_profile(spec, payload, history_edges)

        # 1. Curvature Obstruction Check (Omega = d(omega) != 0)
        current_edge = f"{spec.transition_from}->{spec.transition_to}"
        cycle_count = sum(1 for edge in history_edges if edge == current_edge)
        if cycle_count >= 2 and "residual_descent_observed" not in payload:
            return self._blocked(spec, "INTERGATE_DESCENT_UNMEASURED", "Repeated edge requires an explicit descent observation")
        residual_descent = payload.get("residual_descent_observed", False)

        if cycle_count >= 2 and not residual_descent:
            curvature = CurvatureObstruction(
                detected=True,
                loop_edges=tuple(history_edges[-4:]) + (current_edge,),
                holonomy_norm=1.0,
                reason="Non-integrable cycle detected without net residual reduction",
            )
            return IntergateEvaluationResult(
                intergate_id=spec.intergate_id,
                status="DIVERTED",
                transition_from=spec.transition_from,
                transition_to="PFP-11-QUARANTINE",
                cognitive_vector="Curvature Diverted to Epistemic Quarantine",
                curvature_obstruction=curvature,
                refusal_code="CURVATURE_OBSTRUCTION_DETECTED",
                diagnostics="State sequence formed non-converging holonomy loop; diverting to quarantine stabilization",
                witness=f"curvature_loop_detected_{current_edge}",
            )

        defect = validate_payload(spec.intergate_id, payload)
        if defect:
            return self._blocked(spec, "INTERGATE_PAYLOAD_INVALID", defect)

        curvature_none = CurvatureObstruction(detected=False)

        # 2. Gate-Specific Dynamic Evaluation
        if spec.intergate_id == "PFP-IG-01-FLOW-BAND":
            delta_c = float(payload.get("prompt_complexity_delta", 1.0))
            c_model = float(payload.get("agent_capacity_score", 1.0))
            if delta_c < 0 or c_model <= 0:
                return self._blocked(spec, "INTERGATE_PAYLOAD_INVALID", "Complexity must be nonnegative and capacity positive")
            ratio = delta_c / c_model

            if ratio < 0.8:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="FLOW_STAGNATION_DETECTED",
                    diagnostics=f"Challenge-to-skill ratio {ratio:.2f} < 0.8 (under-challenge stagnation)",
                    witness="flow_band_stagnation_refusal",
                )
            if ratio > 1.2:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="FLOW_OVERWHELM_DETECTED",
                    diagnostics=f"Challenge-to-skill ratio {ratio:.2f} > 1.2 (over-challenge overwhelm)",
                    witness="flow_band_overwhelm_refusal",
                )

        elif spec.intergate_id == "PFP-IG-02-EPISTEMIC-SURPRISE":
            entropy_delta = float(payload.get("epistemic_entropy_delta", 0.0))
            gauge_shift = bool(payload.get("gauge_shift_applied", False))
            if entropy_delta < 0.05 and not gauge_shift:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="FRAME_BREAK_ABSENT",
                    diagnostics="No epistemic surprise or gauge shift observed across Gauge Breaker transition",
                    witness="epistemic_surprise_missing",
                )

        elif spec.intergate_id == "PFP-IG-03-COWARDICE-EVASION":
            severity = float(payload.get("critique_severity", 0.5))
            yields = bool(payload.get("yields_without_evidence", False))
            defect_admitted = bool(payload.get("has_typed_defect_admission", False))
            vagueness = float(payload.get("response_vagueness_index", 0.1))

            cowardice, reason = check_sycophantic_yielding(
                severity, yields, defect_admitted, vagueness
            )
            if cowardice:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="COWARDICE_YIELD_DETECTED",
                    diagnostics=reason,
                    witness="anti_cowardice_refusal",
                )

        elif spec.intergate_id == "PFP-IG-04-PLAYFUL-REVERSIBILITY":
            sandbox_isolated = bool(payload.get("sandbox_isolated", False))
            authority = str(payload.get("authority_effect", "None"))
            if not sandbox_isolated or authority != "None":
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="SANDBOX_ISOLATION_BREACH",
                    diagnostics="Playful reversibility requires pure sandbox isolation and zero authority effect",
                    witness="sandbox_isolation_breached",
                )

        elif spec.intergate_id == "PFP-IG-05-FALSE-URGENCY-DESENSITIZATION":
            text = str(payload.get("prompt_or_context_text", ""))
            urgency, reason = check_false_urgency(text, payload)
            if urgency:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="FALSE_URGENCY_INJECTED",
                    diagnostics=reason,
                    witness="false_urgency_sieve_refusal",
                )

        elif spec.intergate_id == "PFP-IG-06-AFFECTIVE-DEESCALATION":
            panic_active = bool(payload.get("panic_spiral_active", False))
            if panic_active:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="DIVERTED",
                    transition_from=spec.transition_from,
                    transition_to="PFP-08-SCAR-CHRONICLER",
                    cognitive_vector="De-escalating Panic to Prior-Lock Chronicling",
                    curvature_obstruction=curvature_none,
                    refusal_code="AFFECTIVE_PANIC_DIVERTED",
                    diagnostics="Affective distress spiral active; diverting to Scar Chronicler prior-lock chronicling",
                    witness="affective_panic_rejoin",
                )

        elif spec.intergate_id == "PFP-IG-07-MANUFACTURED-CONSENSUS":
            evaluators = list(payload.get("agent_evaluator_ids", []))
            seeds = list(payload.get("sampling_seeds", []))
            producer = str(payload.get("producer_id", ""))

            manufactured, reason = check_manufactured_consensus(evaluators, seeds, producer)
            if manufactured:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="ECHO_CHAMBER_CONSENSUS",
                    diagnostics=reason,
                    witness="manufactured_consensus_refusal",
                )

        elif spec.intergate_id == "PFP-IG-08-QUARANTINE-RECOVERY":
            stabilized = bool(payload.get("epistemic_quarantine_cleared", False))
            cycles = int(payload.get("stabilization_cycles", 0))
            if not stabilized or cycles < 2:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="QUARANTINE_HOLD_RETAINED",
                    diagnostics="Recovery from quarantine requires verified epistemic stabilization and >= 2 cycles",
                    witness="quarantine_hold_refusal",
                )

        elif spec.intergate_id == "PFP-IG-09-DECEPTION-COUNTERMEASURE":
            defense_bound = bool(payload.get("pattern_defense_bound", False))
            if not defense_bound:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="DECEPTION_SURFACE_UNMITIGATED",
                    diagnostics="Transition requires explicit binding of countermeasure pattern to defense register",
                    witness="deception_countermeasure_unbound",
                )

        elif spec.intergate_id == "PFP-IG-10-TERMINAL-REALITY-TETHER":
            summary = str(payload.get("candidate_summary_text", ""))
            verdict = str(payload.get("checker_receipt_verdict", ""))

            # 1. Claim hygiene word check
            is_clean, violations = check_claim_hygiene(summary)
            if not is_clean:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="HYPE_WORD_DETECTED",
                    diagnostics=f"Summary contains prohibited promotional vocabulary: {violations}",
                    witness="claim_hygiene_banned_word_refusal",
                )

            # 2. Four-part summary completeness
            is_complete, missing = check_four_part_summary(summary)
            if not is_complete:
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="SUMMARY_PART_MISSING",
                    diagnostics=f"Summary missing mandatory sections: {missing}",
                    witness="four_part_summary_incomplete_refusal",
                )

            # 3. Checker receipt check
            if verdict != "ACCEPTED":
                return IntergateEvaluationResult(
                    intergate_id=spec.intergate_id,
                    status="BLOCKED",
                    transition_from=spec.transition_from,
                    transition_to=spec.transition_to,
                    cognitive_vector=spec.cognitive_vector,
                    curvature_obstruction=curvature_none,
                    refusal_code="RECEIPT_NOT_ACCEPTED",
                    diagnostics=f"Checker receipt verdict was '{verdict}', expected 'ACCEPTED'",
                    witness="terminal_receipt_unaccepted_refusal",
                )

            binding_error = self._check_terminal_binding(payload, native_support=self._native_support)
            if binding_error:
                return self._blocked(spec, *binding_error)

        # Implemented diagnostic predicates passed; this is not authorization.
        return IntergateEvaluationResult(
            intergate_id=spec.intergate_id,
            status="PASS",
            transition_from=spec.transition_from,
            transition_to=spec.transition_to,
            cognitive_vector=spec.cognitive_vector,
            curvature_obstruction=curvature_none,
            refusal_code=None,
            diagnostics="Implemented diagnostic checks passed; no execution authority or full YAML conformance",
            witness=f"intergate_{spec.intergate_id}_admitted",
        )


    @staticmethod
    def _blocked(spec: IntergateSpec, code: str, reason: str) -> IntergateEvaluationResult:
        return IntergateEvaluationResult(
            intergate_id=spec.intergate_id, status="BLOCKED",
            transition_from=spec.transition_from, transition_to=spec.transition_to,
            cognitive_vector=spec.cognitive_vector,
            curvature_obstruction=CurvatureObstruction(detected=False),
            refusal_code=code, diagnostics=reason, witness=code.lower(),
        )

    def _evaluate_source_profile(self, spec, payload, history_edges):
        """Translate a checked native result; never fall back to legacy predicates."""
        import json
        import re

        try:
            result = self._native_evaluator(spec.intergate_id, payload, history_edges)
            status, refusal = result.get("status"), result.get("refusal_code")
            expected_target = "PFP-11-QUARANTINE" if status == "DIVERTED" else spec.transition_to
            allowed_statuses = (("PASS", "HOLD", "BLOCKED", "DIVERTED")
                if payload["contract_profile"] == MEASURED_SOURCE_CONTRACT_PROFILE else ("PASS", "BLOCKED", "DIVERTED"))
            if (result.get("contract_profile") != payload["contract_profile"]
                    or result.get("specification_sha256") != "sha256:" + spec.source_sha256
                    or result.get("intergate_id") != spec.intergate_id
                    or result.get("transition_from") != spec.transition_from
                    or result.get("transition_to") != expected_target
                    or result.get("authority_effect") != "None" or result.get("can_authorize") is not False
                    or type(result.get("source_profile_sha256")) is not str
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", result["source_profile_sha256"]) is None
                    or status not in allowed_statuses
                    or (status == "PASS" and refusal is not None)
                    or (status != "PASS" and (type(refusal) is not str or not refusal.strip()))):
                return self._blocked(spec, "INTERGATE_NATIVE_PROFILE_MISMATCH", "Native result does not bind the selected finite source contract")
            curvature = result["curvature_obstruction"]
            if (type(curvature["detected"]) is not bool
                    or curvature["detected"] != (status == "DIVERTED")
                    or status == "DIVERTED" and refusal != "CURVATURE_OBSTRUCTION_DETECTED"):
                raise ValueError("Malformed native curvature observation")
            if status == "HOLD":
                missing = result.get("missing_inputs")
                if (type(missing) is not list or not missing
                        or any(type(item) is not str or not item.strip() for item in missing)):
                    return self._blocked(spec, "INTERGATE_NATIVE_PROFILE_MISMATCH",
                        "HOLD requires the exact absent source observations")
            observed = IntergateEvaluationResult(intergate_id=spec.intergate_id, status=result["status"],
                transition_from=result["transition_from"], transition_to=result["transition_to"],
                cognitive_vector=result["cognitive_vector"],
                curvature_obstruction=CurvatureObstruction(**{**curvature, "loop_edges": tuple(curvature["loop_edges"])}),
                refusal_code=result["refusal_code"], diagnostics=result["diagnostics"], witness=result["witness"])
            self.last_native_result = json.loads(json.dumps(result, allow_nan=False, ensure_ascii=True))
            return observed
        except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError) as error:
            return self._blocked(spec, "INTERGATE_NATIVE_UNAVAILABLE", str(error))

    @staticmethod
    def _check_terminal_binding(payload: Dict[str, Any], *, native_support: NativeOperationPort | None) -> tuple[str, str] | None:
        from adversary.domain.evidence import parse_checker_receipt, sha256_ref

        receipt_hex = payload.get("checker_receipt_hex")
        candidate = payload.get("candidate_content")
        if type(receipt_hex) is not str or not receipt_hex or type(candidate) is not str:
            return "CHECKER_RECEIPT_REQUIRED", "Supply checker_receipt_hex and the exact UTF-8 candidate_content"
        # The native structure parser uses JSON Value (last duplicate wins).
        # Reject ambiguous wire bytes here before trusting its parsed binding.
        import json

        def unique_keys(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"Duplicate checker receipt key: {key}")
                result[key] = value
            return result

        def reject_constant(value):
            raise ValueError(f"Non-finite checker receipt value: {value}")

        try:
            candidate_bytes = candidate.encode("utf-8")
            receipt_bytes = bytes.fromhex(receipt_hex)
            json.loads(receipt_bytes.decode("utf-8"), object_pairs_hook=unique_keys,
                       parse_constant=reject_constant)
            if native_support is None:
                return "INTERGATE_NATIVE_UNAVAILABLE", "Native support port is not configured"
            receipt = parse_checker_receipt(receipt_bytes, native_support=native_support)
        except (ValueError, TypeError) as error:
            return "CHECKER_RECEIPT_MALFORMED", str(error)
        if receipt.verdict.value != payload["checker_receipt_verdict"]:
            return "CHECKER_RECEIPT_VERDICT_MISMATCH", "Receipt bytes disagree with the declared verdict"
        if receipt.candidate_content_sha256 != sha256_ref(candidate_bytes):
            return "CHECKER_RECEIPT_CANDIDATE_MISMATCH", "Receipt belongs to different candidate bytes"
        return None
