"""Bounded PFP proposal checking and answer-free repair feedback.

The proposer never supplies its own verdict. Domain judges are injected ports;
this use case neither solves the task nor compares against stored answers.
AuthorityEffect: None.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping, Sequence

from ..domain.pfp_ingress import strict_json


@dataclass(frozen=True)
class ProposalCheck:
    status: str
    failure_class: str
    judges: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Host-authored, bounded guidance. Raw judge diagnostics can contain answers and
# therefore never cross back into the model prompt.
REPAIR_RULES = {
    "ENVELOPE": "Return exactly the declared SPK-001 JSON envelope, without fences or prose.",
    "CERTIFICATE": "Recompute the witness from the input. Check dimensions, identifiers, exact arithmetic, and every certificate equation before submitting.",
    "SCOPE": "An abstention is not a solution. Use a declared refusal only when its input predicate holds; otherwise supply a checkable witness.",
    "WIRE_DISCRIMINATOR": "Use exactly the status and kind literals declared in the task schema. They are separate fields; never invent values or change letter case.",
    "COBOUNDARY_RESIDUAL": "Integrate differences along a spanning tree, then compute every edge residual from its endpoint potentials instead of guessing a pattern. Certify the repaired cochain and a matching feasible circulation.",
    "PAULI_PHASE": "Track signed Pauli products and independent generator relations before searching sectors. Enumerate admissible joint eigenvalue sectors; derive energy, all minimizers, and degeneracy from that same sector list.",
}


def parse_proposal(raw: str) -> dict[str, Any]:
    """Strict common envelope; task-specific typing remains the domain judge's job."""
    if type(raw) is not str or len(raw.encode("utf-8")) > 1_048_576:
        raise ValueError("REPLY_SIZE_OR_TYPE")
    try:
        payload = strict_json(raw)
    except Exception as exc:
        raise ValueError("INVALID_EXACT_JSON") from exc
    keys = {"derived_under_policy", "summary", "process_integrity", "sections", "answer"}
    if type(payload) is not dict or set(payload) != keys:
        raise ValueError("ENVELOPE_KEYS")
    if payload["derived_under_policy"] != "SPK-001" or payload["sections"] != []:
        raise ValueError("ENVELOPE_POLICY_OR_SECTIONS")
    summary = payload["summary"]
    required = {"narrowest_defensible_thesis", "evidence_scope", "next_concrete_test"}
    if type(summary) is not dict or set(summary) != required:
        raise ValueError("ENVELOPE_SUMMARY")
    if any(type(v) is not str or not v.strip() for v in summary.values()):
        raise ValueError("ENVELOPE_SUMMARY_TEXT")
    integrity = payload["process_integrity"]
    if type(integrity) is not dict or set(integrity) != {
        "seed_allows_theory_refutation", "detected_prompt_biases", "should_continue"
    }:
        raise ValueError("ENVELOPE_INTEGRITY")
    if any(type(integrity[k]) is not bool for k in ("seed_allows_theory_refutation", "should_continue")):
        raise ValueError("ENVELOPE_BOOLEAN")
    if type(integrity["detected_prompt_biases"]) is not list or any(
        type(v) is not str for v in integrity["detected_prompt_biases"]
    ):
        raise ValueError("ENVELOPE_BIASES")
    if type(payload["answer"]) is not dict:
        raise ValueError("ENVELOPE_ANSWER_OBJECT")
    return payload


def normalize_judgement(value: Any) -> tuple[bool, str]:
    """Only known checker shapes; never bool(value) or numeric coercion."""
    if type(value) is bool:
        return value, "ACCEPT" if value else "REJECT"
    if type(value) is tuple and len(value) in (2, 3) and type(value[0]) is bool and type(value[1]) is str:
        return value[0], value[1]
    if type(value) is dict and value.get("verdict") in ("PASS", "FAIL"):
        reason = value.get("reason", value.get("details"))
        if type(reason) is str:
            return value["verdict"] == "PASS", reason
    raise ValueError("INVALID_CHECKER_RESULT")


class CheckProposalUseCase:
    def execute(
        self, case: Mapping[str, Any], raw_reply: str,
        judges: Sequence[tuple[str, Callable[[Any, Any], Any]]],
    ) -> ProposalCheck:
        try:
            answer = parse_proposal(raw_reply)["answer"]
        except (ValueError, TypeError):
            return ProposalCheck("PROVIDER_COMPLETED", "ENVELOPE")
        return self.check_answer(case, answer, judges)

    def check_answer(self, case: Mapping[str, Any], answer: dict[str, Any], judges) -> ProposalCheck:
        """Also accepts explicitly labelled NO_LLM controls without forging envelopes."""
        if not judges:
            return ProposalCheck("INFRASTRUCTURE_ERROR", "UNREGISTERED_CHECKER")
        results = []
        for name, judge in judges:
            try:
                accepted, reason = normalize_judgement(judge(deepcopy(case), deepcopy(answer)))
                results.append({"judge": name, "accepted": accepted, "reason": reason})
            except Exception as exc:
                results.append({"judge": name, "error": type(exc).__name__, "reason": str(exc)})
                return ProposalCheck("CHECKER_DEFECT", "CHECKER", tuple(results))
        if len({r["accepted"] for r in results}) != 1:
            return ProposalCheck("CHECKER_DEFECT", "DISAGREEMENT", tuple(results))
        refusal = answer.get("status") in ("UNKNOWN", "OUT_OF_SCOPE")
        if all(r["accepted"] for r in results):
            return ProposalCheck("TYPED_REFUSAL" if refusal else "HOST_ACCEPTED", "NONE", tuple(results))
        failure_class = "SCOPE" if refusal else "CERTIFICATE"
        if not refusal:
            if any("invalid status" in r["reason"].lower() or "unexpected status" in r["reason"].lower() for r in results):
                failure_class = "WIRE_DISCRIMINATOR"
            elif any(r["judge"].startswith("circulation_checker:") and "coboundary relation broken" in r["reason"] for r in results):
                failure_class = "COBOUNDARY_RESIDUAL"
            elif any(r["judge"] == "algebraic_checker:verify_certificate" and
                     ("Decomposition algebraic mismatch" in r["reason"] or "Reported energy" in r["reason"]) for r in results):
                failure_class = "PAULI_PHASE"
        return ProposalCheck("PROVIDER_COMPLETED", failure_class, tuple(results))


def repair_feedback(result: ProposalCheck) -> str | None:
    """Checker failures stop dependent stages; wrong candidates get bounded guidance."""
    return REPAIR_RULES.get(result.failure_class)
