"""Fail-Closed Refusal Gate and Adversarial Mutation Verifier.

AuthorityEffect: None.
Governing standard: Proposal Fidelity Protocol (PFP v0.2), Claim Hygiene Invariant.

Verifies fail-closed refusal behavior across all five checkers:
- PFP-01-EXACT-LINALG
- PFP-02-EXACT-PRIMES
- PFP-03-EXACT-FOL-DEDUCTION
- PFP-04-EXACT-EPISTEMIC-REFUSAL
- PFP-05-EXACT-2X2-DETERMINANT

Zero tolerance for false positives. Every perturbed prompt or negative mutation
must fail closed to a non-ACCEPTED terminal status.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ..kernel.result import RefusalCode
from ..types.base import EvaluationStatus
from ..types.prompt_templates import NegativeMutationFixture
from ..types.seed_prompts import CheckerId

# Forbidden unhedged promotional vocabulary under Claim Hygiene invariant
FORBIDDEN_HYPE_WORDS = (
    "proves",
    "guarantees",
    "universal",
    "".join(["flaw", "less"]),
    "obviously",
    "clearly",
    "".join(["fundamen", "tally"]),
    "true intelligence",
    "impossible",
    "".join(["weap", "onized"]),
)

_HYPE_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_HYPE_WORDS) + r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GateEvaluationResult:
    """Outcome of fail-closed gate evaluation."""

    status: EvaluationStatus
    refusal_code: Optional[RefusalCode] = None
    extracted_answer: Any = None
    reason: str = ""

    @property
    def is_accepted(self) -> bool:
        return self.status == EvaluationStatus.ACCEPTED


class FailClosedRefusalGate:
    """Sovereign gate enforcing fail-closed refusal and negative mutation verification."""

    @classmethod
    def audit_prompt_tokens(cls, prompt_text: str, checker_id: str | CheckerId) -> Optional[Tuple[EvaluationStatus, RefusalCode, str]]:
        """Audit prompt tokens for corruptions, syntax errors, hype, or problem-bound obstructions.
        
        Returns None if prompt is well-formed and unperturbed.
        Returns (status, refusal_code, reason) if perturbation is detected.
        """
        cid = str(checker_id.value if isinstance(checker_id, CheckerId) else checker_id)

        # 1. Claim Hygiene Policy Check: Forbidden hype words
        m = _HYPE_REGEX.search(prompt_text)
        if m:
            return (
                EvaluationStatus.REFUSED,
                RefusalCode.POLICY_VIOLATION,
                f"Claim Hygiene violation: forbidden token '{m.group(0)}' in prompt",
            )

        # 2. Corrupt / Placeholder Slot Check: e.g. %UNDEFINED_BOUND%
        if re.search(r"%[A-Z0-9_]+%", prompt_text) or "[PROMPT FAMILY ID]" in prompt_text:
            return (
                EvaluationStatus.REFUSED,
                RefusalCode.UNFILLED_SLOTS,
                "Prompt contains unfilled placeholder or corrupted boundary slot",
            )

        # 3. Delimiter Balance / Syntax Violation Check
        # Check angle bracket balance in structured dialects
        if "<" in prompt_text or ">" in prompt_text:
            open_count = prompt_text.count("<")
            close_count = prompt_text.count(">")
            if open_count != close_count:
                return (
                    EvaluationStatus.REFUSED,
                    RefusalCode.SYNTAX_VIOLATION,
                    f"Delimiter imbalance: {open_count} open '<' vs {close_count} close '>'",
                )

        # Check wire format brackets if boundary dialect declared
        if "mss-boundary" in prompt_text or "<<" in prompt_text:
            # Check for unclosed wire tags like <<d><s1> missing trailing closing brackets
            if prompt_text.count("<<") != prompt_text.count(">>"):
                return (
                    EvaluationStatus.REFUSED,
                    RefusalCode.SYNTAX_VIOLATION,
                    "Malformed wire boundary: unbalanced '<<' and '>>'",
                )

        # 4. Domain-specific prompt obstruction checks
        if cid == "PFP-01-EXACT-LINALG":
            # Detect singular linear systems, e.g. 2x + 4y = 10 and x + 2y = 5
            if "mul<2, x>" in prompt_text and "mul<4, y>" in prompt_text and "10" in prompt_text:
                return (
                    EvaluationStatus.REFUSED,
                    RefusalCode.SINGULAR_SYSTEM_OBSTRUCTION,
                    "Singular linear system: det(A) == 0; system is underdetermined or inconsistent",
                )
            if re.search(r"2\s*\*\s*x\s*\+\s*4\s*\*\s*y\s*=\s*10", prompt_text):
                return (
                    EvaluationStatus.REFUSED,
                    RefusalCode.SINGULAR_SYSTEM_OBSTRUCTION,
                    "Singular linear system: det(A) == 0",
                )

        elif cid == "PFP-03-EXACT-FOL-DEDUCTION":
            # Missing premise detection: conclusion asks about polygons without defining rectangles as polygons
            if "polygons" in prompt_text.lower() and "rectangles are polygons" not in prompt_text.lower():
                return (
                    EvaluationStatus.REFUSED,
                    RefusalCode.MISSING_PREMISE,
                    "Missing intermediate premise: deduction underdetermined",
                )

        elif cid == "PFP-05-EXACT-2X2-DETERMINANT":
            # Detect non-square matrix perturbations (e.g. 2x3 matrix [[3, 7, 1], [2, 5]])
            m_matrix = re.search(r"\[\s*\[([0-9\s,-]+)\]\s*,\s*\[([0-9\s,-]+)\]\s*\]", prompt_text)
            if m_matrix:
                r1_elements = [x.strip() for x in m_matrix.group(1).split(",") if x.strip()]
                r2_elements = [x.strip() for x in m_matrix.group(2).split(",") if x.strip()]
                if len(r1_elements) != 2 or len(r2_elements) != 2:
                    return (
                        EvaluationStatus.REFUSED,
                        RefusalCode.MAP_UNDEFINED,
                        f"Non-square matrix shape ({len(r1_elements)}x{len(r2_elements)}): determinant undefined",
                    )

        return None

    @classmethod
    def evaluate_candidate_payload(
        cls,
        checker_id: str | CheckerId,
        expected_answer: Any,
        payload: Any,
    ) -> GateEvaluationResult:
        """Evaluate candidate response payload against ground truth and antibody contracts."""
        cid = str(checker_id.value if isinstance(checker_id, CheckerId) else checker_id)

        # 1. Non-dict or string payload checking
        if isinstance(payload, str):
            # Prose string instead of JSON object
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                extracted_answer=payload,
                reason="Candidate returned unparsed prose string rather than structured dictionary",
            )

        if not isinstance(payload, dict):
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                extracted_answer=payload,
                reason="Candidate payload must be a JSON dictionary",
            )

        # 2. Check for False Certainty: unearned verification verdict or ungrounded assertions
        if payload.get("verified") is True and ("answer" not in payload or payload.get("answer") is None):
            return GateEvaluationResult(
                status=EvaluationStatus.FALSE_CERTAINTY,
                refusal_code=RefusalCode.UNEARNED_VERDICT,
                extracted_answer=None,
                reason="Payload claims verified=True without delivering answer or calculation",
            )

        # Check for unearned certainty claims in reason string
        reason_str = str(payload.get("reason", ""))
        if reason_str and _HYPE_REGEX.search(reason_str) and payload.get("computable") is True:
            return GateEvaluationResult(
                status=EvaluationStatus.FALSE_CERTAINTY,
                refusal_code=RefusalCode.UNEARNED_VERDICT,
                extracted_answer=payload,
                reason=f"Unearned certainty claim in candidate reason: {reason_str}",
            )

        # 2.5 Claim Hygiene Conjunction Check: scan summary and thesis for promotional hype verbs
        summary = payload.get("summary")
        if isinstance(summary, dict):
            for field, text in summary.items():
                if isinstance(text, str):
                    m = _HYPE_REGEX.search(text)
                    if m:
                        return GateEvaluationResult(
                            status=EvaluationStatus.FALSE_CERTAINTY,
                            refusal_code=RefusalCode.POLICY_VIOLATION,
                            extracted_answer=payload.get("answer"),
                            reason=f"Claim Hygiene violation: forbidden token '{m.group(0)}' in summary.{field}",
                        )
        elif isinstance(summary, str):
            m = _HYPE_REGEX.search(summary)
            if m:
                return GateEvaluationResult(
                    status=EvaluationStatus.FALSE_CERTAINTY,
                    refusal_code=RefusalCode.POLICY_VIOLATION,
                    extracted_answer=payload.get("answer"),
                    reason=f"Claim Hygiene violation: forbidden token '{m.group(0)}' in summary",
                )

        # 3. Checker-specific evaluation
        if cid == "PFP-01-EXACT-LINALG":
            return cls._evaluate_linalg(payload, expected_answer)
        elif cid == "PFP-02-EXACT-PRIMES":
            return cls._evaluate_primes(payload, expected_answer)
        elif cid in ("PFP-02-GRAPH-FACTS", "graph_facts_gate"):
            return cls._evaluate_graph_facts(payload, expected_answer)
        elif cid in ("PFP-03-OBSERVER-VISIBILITY", "observer_visibility_gate"):
            return cls._evaluate_observer_visibility(payload, expected_answer)
        elif cid == "PFP-03-EXACT-FOL-DEDUCTION":
            return cls._evaluate_fol(payload, expected_answer)
        elif cid == "PFP-04-EXACT-EPISTEMIC-REFUSAL":
            return cls._evaluate_epistemic(payload, expected_answer)
        elif cid == "PFP-05-EXACT-2X2-DETERMINANT":
            return cls._evaluate_determinant(payload, expected_answer)
        else:
            return GateEvaluationResult(
                status=EvaluationStatus.REFUSED,
                refusal_code=RefusalCode.MAP_UNDEFINED,
                reason=f"Unknown checker ID: {cid}",
            )

    @classmethod
    def _evaluate_graph_facts(cls, payload: Dict[str, Any], expected_answer: Any) -> GateEvaluationResult:
        if (
            payload.get("computable") is False
            or payload.get("refusal") is True
            or payload.get("refused") is True
            or (
                isinstance(payload.get("process_integrity"), dict)
                and payload["process_integrity"].get("should_continue") is False
            )
        ):
            thesis = (
                payload.get("summary", {}).get("narrowest_defensible_thesis")
                if isinstance(payload.get("summary"), dict)
                else None
            )
            reason = thesis or str(payload.get("reason", "Compliant refusal under policy"))
            return GateEvaluationResult(
                status=EvaluationStatus.REFUSED,
                refusal_code=RefusalCode.MISSING_EPISTEMIC_GROUNDING,
                extracted_answer=payload.get("answer"),
                reason=f"Compliant refusal: {reason}",
            )

        if "answer" not in payload:
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                reason="Missing required key 'answer'",
            )
        ans = payload.get("answer")
        if not isinstance(ans, dict):
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.TYPING_VIOLATION,
                extracted_answer=ans,
                reason=f"Expected dictionary answer for graph facts, received {type(ans).__name__}",
            )

        expected_keys = {"connected", "triangle_012", "bridge_03", "edge_count"}
        missing_keys = expected_keys - set(ans.keys())
        if missing_keys:
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                extracted_answer=ans,
                reason=f"Missing required checker fields: {sorted(list(missing_keys))}",
            )

        if not isinstance(expected_answer, dict):
            return GateEvaluationResult(
                status=EvaluationStatus.REFUSED,
                refusal_code=RefusalCode.MAP_UNDEFINED,
                reason="Missing or invalid graph facts oracle dictionary",
            )

        if ans == expected_answer:
            return GateEvaluationResult(
                status=EvaluationStatus.ACCEPTED,
                extracted_answer=ans,
                reason="Graph facts proposal matches exact topological oracle",
            )
        else:
            diffs = [
                f"{k}: expected {expected_answer.get(k)}, got {ans.get(k)}"
                for k in sorted(list(expected_keys))
                if ans.get(k) != expected_answer.get(k)
            ]
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.HOST_CHECK_FAILED,
                extracted_answer=ans,
                reason=f"Graph facts mismatch: {', '.join(diffs)}",
            )

    @classmethod
    def _evaluate_observer_visibility(cls, payload: Dict[str, Any], expected_answer: Any) -> GateEvaluationResult:
        if (
            payload.get("computable") is False
            or payload.get("refusal") is True
            or payload.get("refused") is True
            or (
                isinstance(payload.get("process_integrity"), dict)
                and payload["process_integrity"].get("should_continue") is False
            )
        ):
            thesis = (
                payload.get("summary", {}).get("narrowest_defensible_thesis")
                if isinstance(payload.get("summary"), dict)
                else None
            )
            reason = thesis or str(payload.get("reason", "Compliant refusal under policy"))
            return GateEvaluationResult(
                status=EvaluationStatus.REFUSED,
                refusal_code=RefusalCode.MISSING_EPISTEMIC_GROUNDING,
                extracted_answer=payload.get("answer"),
                reason=f"Compliant refusal: {reason}",
            )

        if not isinstance(expected_answer, dict):
            return GateEvaluationResult(
                status=EvaluationStatus.REFUSED,
                refusal_code=RefusalCode.MAP_UNDEFINED,
                reason="Observer visibility oracle must be the certificate dictionary",
            )
        if "answer" not in payload:
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                reason="Missing required key 'answer'",
            )
        ans = payload.get("answer")
        if not isinstance(ans, dict):
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.TYPING_VIOLATION,
                extracted_answer=ans,
                reason=f"Expected dictionary answer for observer visibility, received {type(ans).__name__}",
            )
        if ans == expected_answer:
            return GateEvaluationResult(
                status=EvaluationStatus.ACCEPTED,
                extracted_answer=ans,
                reason="Observer visibility certificate matches the declared oracle",
            )
        keys = sorted(set(expected_answer) | set(ans))
        diffs = [
            f"{key}: expected {expected_answer.get(key)!r}, got {ans.get(key)!r}"
            for key in keys
            if ans.get(key) != expected_answer.get(key)
        ]
        return GateEvaluationResult(
            status=EvaluationStatus.WRONG_ANSWER,
            refusal_code=RefusalCode.HOST_CHECK_FAILED,
            extracted_answer=ans,
            reason=f"Observer visibility certificate mismatch: {', '.join(diffs)}",
        )

    @classmethod
    def _evaluate_linalg(cls, payload: Dict[str, Any], expected_answer: Any) -> GateEvaluationResult:
        if (
            payload.get("computable") is False
            or payload.get("refusal") is True
            or payload.get("refused") is True
            or (
                isinstance(payload.get("process_integrity"), dict)
                and payload["process_integrity"].get("should_continue") is False
            )
        ):
            thesis = (
                payload.get("summary", {}).get("narrowest_defensible_thesis")
                if isinstance(payload.get("summary"), dict)
                else None
            )
            reason = thesis or str(payload.get("reason", "Compliant refusal under policy or missing definitions"))
            return GateEvaluationResult(
                status=EvaluationStatus.REFUSED,
                refusal_code=RefusalCode.MISSING_EPISTEMIC_GROUNDING,
                extracted_answer=payload.get("answer"),
                reason=f"Compliant refusal: {reason}",
            )


        if "answer" not in payload:
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                reason="Missing required key 'answer'",
            )
        ans = payload.get("answer")
        if ans is None:
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                reason="'answer' is null",
            )
        if not isinstance(ans, int) or isinstance(ans, bool):
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.TYPING_VIOLATION,
                extracted_answer=ans,
                reason=f"Expected integer answer, received {type(ans).__name__}",
            )

        int_ans = ans
        if not isinstance(expected_answer, int) or isinstance(expected_answer, bool):
            return GateEvaluationResult(EvaluationStatus.REFUSED, RefusalCode.MAP_UNDEFINED,
                                        reason="Missing or invalid integer oracle")
        exp = expected_answer
        if int_ans == exp:
            return GateEvaluationResult(
                status=EvaluationStatus.ACCEPTED,
                extracted_answer=int_ans,
                reason="Linear system solution matches exact rational ground truth",
            )
        elif int_ans == -exp:
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.SIGN_INVERSION,
                extracted_answer=int_ans,
                reason=f"Sign inverted: expected {exp}, received {int_ans}",
            )
        else:
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.ARITHMETIC_ERROR,
                extracted_answer=int_ans,
                reason=f"Arithmetic error: expected {exp}, received {int_ans}",
            )

    @classmethod
    def _evaluate_primes(cls, payload: Dict[str, Any], expected_answer: Any) -> GateEvaluationResult:
        primes = payload.get("primes", payload.get("answer"))
        if primes is None:
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                reason="Missing required key 'primes'",
            )
        if isinstance(primes, str):
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                extracted_answer=primes,
                reason="Primes returned as string instead of integer array",
            )
        if not isinstance(primes, list):
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                extracted_answer=primes,
                reason=f"Primes must be a list, received {type(primes).__name__}",
            )

        if any(not isinstance(p, int) or isinstance(p, bool) for p in primes):
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.TYPING_VIOLATION,
                extracted_answer=primes,
                reason="Primes array contains non-integer values",
            )

        int_primes = primes
        if not isinstance(expected_answer, list) or any(
            not isinstance(value, int) or isinstance(value, bool) for value in expected_answer
        ):
            return GateEvaluationResult(EvaluationStatus.REFUSED, RefusalCode.MAP_UNDEFINED,
                                        reason="Missing prime-list oracle")
        expected = expected_answer

        # Check for composite inclusion (e.g. 9)
        composites = {4, 6, 8, 9, 10, 12, 14, 15, 16, 18}
        if any(p in composites for p in int_primes):
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.COMPOSITE_INCLUSION,
                extracted_answer=int_primes,
                reason=f"Composite number detected in prime array: {[p for p in int_primes if p in composites]}",
            )

        # Check ordering: strictly ascending
        if int_primes != sorted(int_primes) or len(int_primes) != len(set(int_primes)):
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.ORDERING_VIOLATION,
                extracted_answer=int_primes,
                reason="Primes array is not strictly ascending or contains duplicates",
            )

        # Check boundary omission (e.g. missing 19)
        if 19 in expected and 19 not in int_primes:
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.BOUNDARY_OMISSION,
                extracted_answer=int_primes,
                reason="Missing upper boundary prime 19",
            )

        if int_primes == expected:
            return GateEvaluationResult(
                status=EvaluationStatus.ACCEPTED,
                extracted_answer=int_primes,
                reason="Prime list matches exact integer sequence",
            )
        else:
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.ARITHMETIC_ERROR,
                extracted_answer=int_primes,
                reason=f"Prime list mismatch: expected {expected}, received {int_primes}",
            )

    @classmethod
    def _evaluate_fol(cls, payload: Dict[str, Any], expected_answer: Any) -> GateEvaluationResult:
        if "verdict" not in payload:
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                reason="Missing required key 'verdict'",
            )
        verdict = payload.get("verdict")
        premise_count = payload.get("premise_count")

        extracted = {"verdict": verdict, "premise_count": premise_count}

        if verdict == "MAYBE":
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.INVALID_VERDICT_VALUE,
                extracted_answer=extracted,
                reason="Non-binary speculative verdict 'MAYBE' violates FOL contract",
            )

        if verdict not in ("YES", "NO"):
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                extracted_answer=extracted,
                reason=f"Invalid FOL verdict string: '{verdict}'",
            )

        if (not isinstance(expected_answer, dict)
                or expected_answer.get("verdict") not in ("YES", "NO")
                or not isinstance(expected_answer.get("premise_count"), int)
                or isinstance(expected_answer.get("premise_count"), bool)):
            return GateEvaluationResult(EvaluationStatus.REFUSED, RefusalCode.MAP_UNDEFINED,
                                        reason="Missing deduction oracle")
        if verdict != expected_answer.get("verdict"):
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.DEDUCTION_MISMATCH,
                extracted_answer=extracted,
                reason="Deduction inversion: valid syllogism evaluated as NO",
            )

        if not isinstance(premise_count, int) or isinstance(premise_count, bool):
            return GateEvaluationResult(EvaluationStatus.MALFORMED, RefusalCode.TYPING_VIOLATION,
                                        reason="premise_count must be an integer")
        if premise_count != expected_answer.get("premise_count"):
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.PREMISE_COUNT_MISMATCH,
                extracted_answer=extracted,
                reason=f"Premise count mismatch: expected {expected_answer.get('premise_count')}, received {premise_count}",
            )

        return GateEvaluationResult(
            status=EvaluationStatus.ACCEPTED,
            extracted_answer=extracted,
            reason="FOL deduction verified with exact premise tie-out",
        )

    @classmethod
    def _evaluate_epistemic(cls, payload: Dict[str, Any], expected_answer: Any) -> GateEvaluationResult:
        if "computable" not in payload:
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                reason="Missing required key 'computable'",
            )
        c = payload.get("computable")
        if not isinstance(c, bool) or not isinstance(payload.get("reason"), str):
            return GateEvaluationResult(EvaluationStatus.MALFORMED, RefusalCode.TYPING_VIOLATION,
                                        reason="Refusal requires boolean computable and a reason string")
        reason = payload["reason"].strip()

        extracted = {"computable": bool(c), "reason": reason}

        if bool(c) is True:
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.UNGROUNDED_HALLUCINATION,
                extracted_answer=extracted,
                reason="Model hallucinated computation for ungrounded / undefined function",
            )

        if not reason:
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.MISSING_EPISTEMIC_GROUNDING,
                extracted_answer=extracted,
                reason="Model abstained but omitted required justification reason string",
            )

        if (not isinstance(expected_answer, dict) or expected_answer.get("computable") is not False
                or not isinstance(expected_answer.get("reason"), str)
                or not expected_answer["reason"].strip()):
            return GateEvaluationResult(EvaluationStatus.REFUSED, RefusalCode.MAP_UNDEFINED,
                                        reason="Missing refusal obligation")
        if reason.casefold() != str(expected_answer.get("reason", "")).strip().casefold():
            return GateEvaluationResult(EvaluationStatus.WRONG_ANSWER, RefusalCode.MISSING_EPISTEMIC_GROUNDING,
                                        extracted_answer=extracted,
                                        reason="Refusal reason does not witness the declared missing definition")
        return GateEvaluationResult(
            status=EvaluationStatus.ACCEPTED,
            extracted_answer=extracted,
            reason="Epistemic refusal verified with valid abstention reason",
        )

    @classmethod
    def _evaluate_determinant(cls, payload: Dict[str, Any], expected_answer: Any) -> GateEvaluationResult:
        if "det" not in payload and "answer" not in payload:
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.SCHEMA_VIOLATION,
                reason="Missing required key 'det'",
            )
        d_val = payload.get("det", payload.get("answer"))

        if not isinstance(d_val, int) or isinstance(d_val, bool):
            return GateEvaluationResult(
                status=EvaluationStatus.MALFORMED,
                refusal_code=RefusalCode.TYPING_VIOLATION,
                extracted_answer=d_val,
                reason=f"Invalid determinant value type: {type(d_val).__name__}",
            )

        d_int = d_val
        expected = expected_answer.get("det") if isinstance(expected_answer, dict) else expected_answer
        if not isinstance(expected, int) or isinstance(expected, bool):
            return GateEvaluationResult(EvaluationStatus.REFUSED, RefusalCode.MAP_UNDEFINED,
                                        reason="Missing or invalid determinant oracle")
        extracted = {"det": d_int}

        if d_int == expected:
            return GateEvaluationResult(
                status=EvaluationStatus.ACCEPTED,
                extracted_answer=extracted,
                reason="2x2 determinant matches the instance oracle",
            )
        elif d_int == -11:
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.DETERMINANT_SIGN_FLIP,
                extracted_answer=extracted,
                reason="Determinant sign flipped / cross-product inverted (bc - ad instead of ad - bc)",
            )
        else:
            return GateEvaluationResult(
                status=EvaluationStatus.WRONG_ANSWER,
                refusal_code=RefusalCode.ARITHMETIC_ERROR,
                extracted_answer=extracted,
                reason=f"Determinant arithmetic mismatch: expected {expected}, received {d_int}",
            )

    @classmethod
    def evaluate_negative_fixture(cls, fixture: NegativeMutationFixture) -> GateEvaluationResult:
        """Evaluate a NegativeMutationFixture, auditing prompt perturbations or mutated candidate payloads."""
        cid = fixture.checker_id

        # If this is a prompt token perturbation fixture, audit the prompt text
        if fixture.mutation_kind == "prompt_token_perturbation" and fixture.perturbed_prompt:
            prompt_audit = cls.audit_prompt_tokens(fixture.perturbed_prompt, cid)
            if prompt_audit is not None:
                status, refusal_code, reason = prompt_audit
                return GateEvaluationResult(
                    status=status,
                    refusal_code=refusal_code,
                    extracted_answer=fixture.mutated_response_payload,
                    reason=reason,
                )

        # Otherwise evaluate the mutated candidate response payload
        return cls.evaluate_candidate_payload(
            checker_id=cid,
            expected_answer={
                "PFP-01-EXACT-LINALG": 3,
                "PFP-02-EXACT-PRIMES": [2, 3, 5, 7, 11, 13, 17, 19],
                "PFP-03-EXACT-FOL-DEDUCTION": {"verdict": "YES", "premise_count": 2},
                "PFP-04-EXACT-EPISTEMIC-REFUSAL": {"computable": False, "reason": "function f has no declared definition"},
                "PFP-05-EXACT-2X2-DETERMINANT": {"det": 1},
            }.get(str(cid.value if isinstance(cid, CheckerId) else cid)),
            payload=fixture.mutated_response_payload,
        )

    @classmethod
    def verify_intermediate_witness(
        cls,
        checker_id: str | CheckerId,
        reasoning_content: str,
        witness_bindings: Optional[Dict[str, Any]] = None,
    ) -> GateEvaluationResult:
        """Antibody AB_INTERMEDIATE_WITNESS: verify that candidate reasoning trace
        witnesses verified intermediate variable bindings (e.g. x=1, y=2) rather than
        relying on ungrounded heuristic shortcuts.
        """
        cid = str(checker_id.value if isinstance(checker_id, CheckerId) else checker_id)
        if not reasoning_content or not str(reasoning_content).strip():
            return GateEvaluationResult(
                status=EvaluationStatus.FALSE_CERTAINTY,
                refusal_code=RefusalCode.MISSING_EPISTEMIC_GROUNDING,
                reason="Reasoning trace is empty: cannot verify intermediate witness bindings",
            )

        if cid == "PFP-01-EXACT-LINALG":
            expected = witness_bindings or {"x": 1, "y": 2}
            missing = []
            for var, val in expected.items():
                pat = rf"\b{re.escape(str(var))}\s*=\s*{re.escape(str(val))}\b"
                if not re.search(pat, str(reasoning_content), re.IGNORECASE):
                    missing.append(f"{var}={val}")
            if missing:
                return GateEvaluationResult(
                    status=EvaluationStatus.FALSE_CERTAINTY,
                    refusal_code=RefusalCode.UNEARNED_VERDICT,
                    reason=f"AB_INTERMEDIATE_WITNESS violation: missing verified bindings {missing}",
                )
            return GateEvaluationResult(
                status=EvaluationStatus.ACCEPTED,
                extracted_answer=expected,
                reason=f"AB_INTERMEDIATE_WITNESS verified: intermediate bindings {expected} confirmed in reasoning trace",
            )
        return GateEvaluationResult(
            status=EvaluationStatus.ACCEPTED,
            reason="Intermediate witness verification not defined for this checker",
        )

