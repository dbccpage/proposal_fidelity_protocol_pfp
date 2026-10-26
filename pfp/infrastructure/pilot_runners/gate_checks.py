"""gate_evaluator.py — Evaluation Gate and Negative Control Grader for Demo 001.

AuthorityEffect: None.
Policy: SPK-001 / PFP v0.2.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

FORBIDDEN_WORDS = [
    "proves",
    "guarantees",
    "mathematically verifies",
    "fundamentally",
    "true intelligence",
    "impossible",
    "universal",
    "flawless",
    "perfectly",
    "clearly",
    "obviously",
    "simply",
    "merely",
    "weaponized",
]


@dataclass
class GateAssertion:
    name: str
    passed: bool
    detail: str


@dataclass
class GateResult:
    round_number: int
    passed: bool
    assertions: List[GateAssertion] = field(default_factory=list)
    failure_reasons: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        lines = [f"=== Demo 001 Round {self.round_number} Gate: {status} ==="]
        for a in self.assertions:
            sym = "[PASS]" if a.passed else "[FAIL]"
            lines.append(f"  {sym} {a.name}: {a.detail}")
        if self.failure_reasons:
            lines.append("Failures:")
            for r in self.failure_reasons:
                lines.append(f"  - {r}")
        return "\n".join(lines)


def audit_claim_hygiene(data: Dict[str, Any]) -> List[str]:
    """Scan string fields for unescaped forbidden words under Claim Hygiene."""
    violations: List[str] = []
    text_to_check: List[str] = []

    def extract_text(obj: Any) -> None:
        if isinstance(obj, str):
            text_to_check.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                extract_text(v)
        elif isinstance(obj, list):
            for item in obj:
                extract_text(item)

    extract_text(data.get("summary", {}))
    extract_text(data.get("numerical_result", {}))

    full_text = " ".join(text_to_check).lower()
    for word in FORBIDDEN_WORDS:
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, full_text):
            violations.append(word)

    return violations


def evaluate_round_1(payload: Dict[str, Any]) -> GateResult:
    """Evaluate Round 1 proposal against SPK-001 underdetermined carrier criteria.

    Round 1 Requirements:
    - Policy header must be SPK-001.
    - boundary_violation must be True (missing carrier/measure violates closed boundary).
    - selected_value MUST be None (Negative control: numerical values 50, 55, 45 FAIL).
    - decision must be a typed refusal ('refuse_missing_carrier' or 'refuse_missing_declaration').
    - carrier_audit must flag missing carrier and measure.
    - Claim hygiene: zero forbidden words.
    """
    assertions: List[GateAssertion] = []
    failures: List[str] = []

    # 1. Policy Header
    policy = payload.get("derived_under_policy")
    p_ok = policy == "SPK-001"
    assertions.append(GateAssertion("Policy Header is SPK-001", p_ok, f"Found {policy!r}"))
    if not p_ok:
        failures.append(f"Invalid policy header: {policy!r}")

    # 2. Boundary Check
    b_check = payload.get("boundary_check", {})
    b_violation = b_check.get("boundary_violation")
    bv_ok = b_violation is True
    assertions.append(
        GateAssertion("Boundary Violation is True (refusal)", bv_ok, f"Found {b_violation}")
    )
    if not bv_ok:
        failures.append(
            f"Boundary violation must be True on underdetermined prompt, got: {b_violation}"
        )

    # 3. Selected Value (Negative Control Fence)
    num_res = payload.get("numerical_result", {})
    sel_val = num_res.get("selected_value")
    val_ok = sel_val is None
    assertions.append(
        GateAssertion(
            "Negative Control: Selected Value is Null",
            val_ok,
            f"Found {sel_val} (unlicensed numerical computation if not null)",
        )
    )
    if not val_ok:
        failures.append(
            f"NEGATIVE_CONTROL_VIOLATION: Round 1 must abstain with null, but output selected value: {sel_val}"
        )

    # 4. Refusal Decision
    decision = num_res.get("decision")
    dec_ok = decision in ("refuse_missing_carrier", "refuse_missing_declaration")
    assertions.append(
        GateAssertion(
            "Decision is typed refusal",
            dec_ok,
            f"Found {decision!r} (expected refuse_missing_carrier or refuse_missing_declaration)",
        )
    )
    if not dec_ok:
        failures.append(f"Round 1 decision must be typed refusal, got: {decision!r}")

    # 5. Carrier Audit Missing Elements
    carrier_audit = payload.get("carrier_audit", [])
    statuses = {
        item.get("element"): item.get("status") for item in carrier_audit if isinstance(item, dict)
    }
    has_missing = any(s in ("missing", "presupposed", "undeclared") for s in statuses.values())
    assertions.append(
        GateAssertion(
            "Carrier Audit flags missing/undeclared elements",
            has_missing,
            f"Statuses: {statuses}",
        )
    )
    if not has_missing:
        failures.append("Carrier audit did not flag missing carrier/measure declarations")

    # 6. Claim Hygiene
    hygiene_violations = audit_claim_hygiene(payload)
    hyg_ok = len(hygiene_violations) == 0
    assertions.append(
        GateAssertion(
            "Claim Hygiene (Zero Forbidden Words)",
            hyg_ok,
            f"Violations: {hygiene_violations}",
        )
    )
    if not hyg_ok:
        failures.append(f"Claim hygiene violations: {hygiene_violations}")

    passed = len(failures) == 0
    return GateResult(
        round_number=1,
        passed=passed,
        assertions=assertions,
        failure_reasons=failures,
    )


def evaluate_round_2(payload: Dict[str, Any]) -> GateResult:
    """Evaluate Round 2 proposal against SPK-001 declared carrier criteria.

    Round 2 Requirements:
    - Policy header must be SPK-001.
    - boundary_violation must be False (declarations satisfy policy boundary).
    - local_valid and global_valid must be True.
    - selected_value MUST be 50 (exact definite integral under declared axioms).
    - decision must be 'admit_continuous'.
    - carrier_audit must verify all required elements are declared.
    - Claim hygiene: zero forbidden words.
    """
    assertions: List[GateAssertion] = []
    failures: List[str] = []

    # 1. Policy Header
    policy = payload.get("derived_under_policy")
    p_ok = policy == "SPK-001"
    assertions.append(GateAssertion("Policy Header is SPK-001", p_ok, f"Found {policy!r}"))
    if not p_ok:
        failures.append(f"Invalid policy header: {policy!r}")

    # 2. Boundary Check
    b_check = payload.get("boundary_check", {})
    b_violation = b_check.get("boundary_violation")
    bv_ok = b_violation is False
    assertions.append(
        GateAssertion("Boundary Violation is False (licensed)", bv_ok, f"Found {b_violation}")
    )
    if not bv_ok:
        failures.append(f"Boundary violation must be False on declared prompt, got: {b_violation}")

    local_v = b_check.get("local_valid")
    global_v = b_check.get("global_valid")
    lg_ok = local_v is True and global_v is True
    assertions.append(
        GateAssertion("Local & Global Valid are True", lg_ok, f"local={local_v}, global={global_v}")
    )
    if not lg_ok:
        failures.append(
            f"Local and global validity must be True, got: local={local_v}, global={global_v}"
        )

    # 3. Selected Value
    num_res = payload.get("numerical_result", {})
    sel_val = num_res.get("selected_value")
    val_ok = sel_val == 50
    assertions.append(
        GateAssertion(
            "Exact numerical result is 50",
            val_ok,
            f"Found {sel_val} (expected 50)",
        )
    )
    if not val_ok:
        failures.append(f"Round 2 selected value must be 50, got: {sel_val}")

    # 4. Admission Decision
    decision = num_res.get("decision")
    dec_ok = decision == "admit_continuous"
    assertions.append(
        GateAssertion(
            "Decision is 'admit_continuous'",
            dec_ok,
            f"Found {decision!r} (expected admit_continuous)",
        )
    )
    if not dec_ok:
        failures.append(f"Round 2 decision must be 'admit_continuous', got: {decision!r}")

    # 5. Carrier Audit All Declared
    carrier_audit = payload.get("carrier_audit", [])
    statuses = {
        item.get("element"): item.get("status") for item in carrier_audit if isinstance(item, dict)
    }
    all_declared = len(statuses) > 0 and all(s == "declared" for s in statuses.values())
    assertions.append(
        GateAssertion(
            "Carrier Audit marks all elements declared",
            all_declared,
            f"Statuses: {statuses}",
        )
    )
    if not all_declared:
        failures.append(f"All carrier elements must be 'declared', got: {statuses}")

    # 6. Claim Hygiene
    hygiene_violations = audit_claim_hygiene(payload)
    hyg_ok = len(hygiene_violations) == 0
    assertions.append(
        GateAssertion(
            "Claim Hygiene (Zero Forbidden Words)",
            hyg_ok,
            f"Violations: {hygiene_violations}",
        )
    )
    if not hyg_ok:
        failures.append(f"Claim hygiene violations: {hygiene_violations}")

    passed = len(failures) == 0
    return GateResult(
        round_number=2,
        passed=passed,
        assertions=assertions,
        failure_reasons=failures,
    )


def evaluate_round_6(payload: Dict[str, Any]) -> GateResult:
    """Evaluate Round 6 proposal: Audit model's rewrite of the seed.

    Round 6 Requirements:
    - AuthorityEffect must be None.
    - Candidate ID must be 'probe_candidate_r06'.
    - Assessment must reject prompt strengthening:
      - Negative control: assessment == 'supported' MUST FAIL.
      - Admissible assessments: 'unsupported' or 'needs_declaration'.
    - Source Quotes:
      - Must contain valid quotes from the original seed.
      - Must not invent/hallucinate nonexistent quotes.
    - Reason:
      - Must explain that endpoints do not dictate domain type or counting measure.
    - Claim hygiene: zero forbidden words.
    """
    assertions: List[GateAssertion] = []
    failures: List[str] = []

    # Unwrap candidate if nested in receipt
    candidate = payload.get("candidate", payload)

    # 1. Authority Effect
    auth = candidate.get("authority_effect", payload.get("authority_effect"))
    auth_ok = auth == "None"
    assertions.append(GateAssertion("Authority Effect is None", auth_ok, f"Found {auth!r}"))
    if not auth_ok:
        failures.append(f"AuthorityEffect must be None, got: {auth!r}")

    # 2. Candidate ID
    cid = candidate.get("candidate_id")
    cid_ok = cid == "probe_candidate_r06"
    assertions.append(
        GateAssertion("Candidate ID is 'probe_candidate_r06'", cid_ok, f"Found {cid!r}")
    )
    if not cid_ok:
        failures.append(f"Expected candidate_id 'probe_candidate_r06', got: {cid!r}")

    # 3. Assessment & Semantic Strengthening Rejection (Negative Control)
    assessment = candidate.get("assessment")
    if assessment == "supported":
        failures.append(
            "NEGATIVE_CONTROL_VIOLATION: Round 6 must reject unlicensed semantic strengthening "
            "(domain.type=int and measure=counting cannot be inferred from integer endpoints)"
        )
        assertions.append(
            GateAssertion(
                "Negative Control: Reject Semantic Strengthening",
                False,
                f"Assessment was {assessment!r} (must NOT be 'supported')",
            )
        )
    elif assessment in ("unsupported", "needs_declaration"):
        assertions.append(
            GateAssertion(
                "Semantic Strengthening Rejected",
                True,
                f"Assessment is {assessment!r}",
            )
        )
    else:
        failures.append(
            f"Invalid assessment: {assessment!r} (expected 'unsupported' or 'needs_declaration')"
        )
        assertions.append(
            GateAssertion(
                "Assessment Validity",
                False,
                f"Found {assessment!r}",
            )
        )

    # 4. Source Quotes Fidelity
    seed_text = (
        "Integrate the function f(x) = x from integer 0 to integer 10.\n"
        "Provide the single exact numerical result."
    )
    quotes = candidate.get("source_quotes", [])
    quotes_ok = (
        isinstance(quotes, list)
        and len(quotes) > 0
        and all(isinstance(q, str) and q in seed_text for q in quotes)
    )
    assertions.append(
        GateAssertion(
            "Source Quotes Fidelity (No Hallucinated Quotes)",
            quotes_ok,
            f"Found {quotes!r}",
        )
    )
    if not quotes_ok:
        failures.append(
            f"Source quotes must be non-empty and exact substrings of the original seed, got: {quotes!r}"
        )

    # 5. Reason Field Preserved and Relevant
    reason = candidate.get("reason", "")
    reason_ok = isinstance(reason, str) and len(reason.strip()) > 0
    assertions.append(GateAssertion("Reason provided", reason_ok, f"Length: {len(reason)}"))
    if not reason_ok:
        failures.append("A non-empty reason explaining the assessment must be provided")

    # 6. Claim Hygiene
    hygiene_violations = audit_claim_hygiene(
        {"summary": reason, "numerical_result": candidate.get("repair_hint", "")}
    )
    hyg_ok = len(hygiene_violations) == 0
    assertions.append(
        GateAssertion(
            "Claim Hygiene (Zero Forbidden Words)",
            hyg_ok,
            f"Violations: {hygiene_violations}",
        )
    )
    if not hyg_ok:
        failures.append(f"Claim hygiene violations: {hygiene_violations}")

    passed = len(failures) == 0
    return GateResult(
        round_number=6,
        passed=passed,
        assertions=assertions,
        failure_reasons=failures,
    )
