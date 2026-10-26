"""gate_evaluator.py — Gate Evaluator and Negative Control Grader for Demo 002.

AuthorityEffect: None.
Policy: SPK-001 / PFP v0.2.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import convert_xor, parse_expr, standard_transformations

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
    demo_id: str
    passed: bool
    assertions: list[GateAssertion] = field(default_factory=list)
    failure_reasons: list[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        lines = [f"=== {self.demo_id} Gate Evaluation: {status} ==="]
        for a in self.assertions:
            sym = "[PASS]" if a.passed else "[FAIL]"
            lines.append(f"  {sym} {a.name}: {a.detail}")
        if self.failure_reasons:
            lines.append("Failures:")
            for r in self.failure_reasons:
                lines.append(f"  - {r}")
        return "\n".join(lines)


def audit_claim_hygiene(data: Any) -> list[str]:
    """Scan string fields for unescaped forbidden words under Claim Hygiene."""
    violations: list[str] = []

    def scan_value(val: Any, path: str) -> None:
        if isinstance(val, str):
            for word in FORBIDDEN_WORDS:
                pattern = r"\b" + re.escape(word) + r"\b"
                if re.search(pattern, val, re.IGNORECASE):
                    lower_val = val.lower()
                    # Check if quoted or negated as a negative pattern / rejection
                    if (
                        f"'{word}'" in lower_val
                        or f'"{word}"' in lower_val
                        or "prohibit" in lower_val
                        or f"rather than {word}" in lower_val
                        or f"not {word}" in lower_val
                    ):
                        continue
                    violations.append(f"{path}: contains forbidden word '{word}'")
        elif isinstance(val, dict):
            for k, v in val.items():
                scan_value(v, f"{path}.{k}")
        elif isinstance(val, list):
            for i, v in enumerate(val):
                scan_value(v, f"{path}[{i}]")

    scan_value(data, "root")
    return violations


def _symbols() -> dict[str, Any]:
    x, y = sp.symbols("x y")
    return {"x": x, "y": y, "exp": sp.exp, "ln": sp.log, "log": sp.log}


def _parse(text: str) -> sp.Expr:
    return parse_expr(
        text,
        local_dict=_symbols(),
        transformations=standard_transformations + (convert_xor,),
    )


def test_bivariate_mixed_derivative_oracle(primitive: str, expected_mixed_partial: str) -> bool:
    """Return whether d2(primitive)/dx dy equals the expected mixed partial."""
    if not isinstance(primitive, str) or not isinstance(expected_mixed_partial, str):
        return False
    x, y = sp.symbols("x y")
    try:
        got = sp.diff(_parse(primitive), x, y)
        expected = _parse(expected_mixed_partial)
    except (sp.SympifyError, SyntaxError, TypeError, ValueError, AttributeError):
        return False
    return sp.simplify(got - expected) == 0


def test_refusal_payload_masking_oracle(payload: dict[str, Any]) -> bool:
    """A refusal may carry only status, authority, reason, and missing declarations."""
    if not isinstance(payload, dict):
        return False
    status = payload.get("status", "")
    if not isinstance(status, str):
        return False
    if "refuse" in status or status == "needs_declaration":
        allowed = {"status", "authority_effect", "reason", "missing_declarations"}
        for key, value in payload.items():
            if key not in allowed and value is not None:
                return False
    return True


def test_separable_factor_oracle(control: dict[str, Any]) -> bool:
    """Integrate each declared factor and compare the product with the declared value."""
    if not isinstance(control, dict):
        return False
    x, y = sp.symbols("x y")
    try:
        for key, var in (("factor_x", x), ("factor_y", y)):
            factor = control[key]
            integrand = _parse(str(factor["integrand"]))
            lower = _parse(str(factor["limits"][0]))
            upper = _parse(str(factor["limits"][1]))
            claimed = _parse(str(factor["value"]))
            got = sp.integrate(integrand, (var, lower, upper))
            if sp.simplify(got - claimed) != 0:
                return False
        product = Fraction(str(control["factor_x"]["value"])) * Fraction(
            str(control["factor_y"]["value"])
        )
        return product == Fraction(str(control["product_value"]))
    except (
        KeyError,
        TypeError,
        ValueError,
        ZeroDivisionError,
        sp.SympifyError,
        SyntaxError,
        AttributeError,
    ):
        return False


def _lookup(root: dict[str, Any], *keys: str) -> Any:
    current: Any = root
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def evaluate_generalization_antibodies(
    generalized_antibodies: list[dict[str, Any]],
    demo_002_spec: dict[str, Any],
) -> GateResult:
    """Evaluate generated antibodies against Demo 002 requirements."""
    assertions: list[GateAssertion] = []
    failures: list[str] = []

    # 1. Non-Empty Antibody Catalog
    count = len(generalized_antibodies)
    ab_ok = count >= 4
    assertions.append(
        GateAssertion(
            "Antibody Catalog Population",
            ab_ok,
            f"Found {count} generalized antibodies (minimum 4 required)",
        )
    )
    if not ab_ok:
        failures.append(f"Insufficient antibodies generated: {count} < 4")

    # 2. Rule Identity Honesty (RULE_IMMUNE_ANTIBODY_HYGIENE_001)
    ephemeral_keys = {"run_id", "task_id", "timestamp", "pid", "model", "model_name"}
    id_leaks = []
    for ab in generalized_antibodies:
        ab_id = ab.get("generalized_antibody_id", "")
        for eph in ephemeral_keys:
            if eph in ab_id.lower():
                id_leaks.append(f"{ab_id} contains ephemeral token '{eph}'")
    id_ok = len(id_leaks) == 0
    assertions.append(
        GateAssertion(
            "Rule Identity Honesty (RULE_IMMUNE_ANTIBODY_HYGIENE_001)",
            id_ok,
            f"Ephemeral tokens in rule IDs: {id_leaks if not id_ok else 'None'}",
        )
    )
    if not id_ok:
        failures.append(f"Antibody IDs contain ephemeral execution tokens: {id_leaks}")

    # 3. Non-Answer-Bearing Invariant (No Scalar Equality Predicates)
    answer_bearing_violations = []
    for ab in generalized_antibodies:
        ab_id = ab.get("generalized_antibody_id", "")
        pred = ab.get("invariant_check_predicate", "")
        # Check if predicate asserts a fixed numerical answer like '== 50' or '== 0.25'
        if re.search(r"==\s*(50|55|45|0\.25|1/4)\b", pred):
            answer_bearing_violations.append(f"{ab_id} has answer-bearing predicate: '{pred}'")
    pred_ok = len(answer_bearing_violations) == 0
    assertions.append(
        GateAssertion(
            "Non-Answer-Bearing Invariant (No Hardcoded Scalar Solutions)",
            pred_ok,
            f"Answer-bearing predicates: {answer_bearing_violations if not pred_ok else 'None'}",
        )
    )
    if not pred_ok:
        failures.append(
            f"Antibodies contain answer-bearing predicates: {answer_bearing_violations}"
        )

    # 4. Zero-Model Execution for Host Oracles
    oracle_violations = []
    for ab in generalized_antibodies:
        ab_id = ab.get("generalized_antibody_id", "")
        contract = ab.get("host_oracle_contract", {})
        if not contract.get("zero_model_execution"):
            oracle_violations.append(f"{ab_id} missing zero_model_execution: true")
    orc_ok = len(oracle_violations) == 0
    assertions.append(
        GateAssertion(
            "Host Oracle Zero-Model Execution Guarantee",
            orc_ok,
            f"Oracle violations: {oracle_violations if not orc_ok else 'None'}",
        )
    )
    if not orc_ok:
        failures.append(
            f"Host oracle contracts fail zero-model execution requirement: {oracle_violations}"
        )

    # 5. Host checks on the declared Demo 002 fixtures
    spec = demo_002_spec if isinstance(demo_002_spec, dict) else {}
    expected_partial = _lookup(
        spec, "positive_controls", "control_1_exact_symbolic_primitive", "mixed_partial"
    )
    exact_primitive = _lookup(
        spec, "positive_controls", "control_1_exact_symbolic_primitive", "primitive"
    )
    fake_primitive = _lookup(
        spec, "injected_defect_fixtures", "fixture_1_weak_checker_linear_fit", "proposed_primitive"
    )
    leaked_payload = _lookup(
        spec, "injected_defect_fixtures", "fixture_3_refusal_payload_leakage", "payload"
    )
    separable = _lookup(spec, "positive_controls", "control_2_separable_factorization")
    declared_region = _lookup(
        spec, "seed_problem", "declared_profile", "boundary_specification", "region_type"
    )
    injected_boundary = _lookup(
        spec,
        "injected_defect_fixtures",
        "fixture_2_boundary_topology_conflation",
        "proposed_boundary",
    )

    derivative_ok = (
        isinstance(expected_partial, str)
        and isinstance(exact_primitive, str)
        and isinstance(fake_primitive, str)
        and test_bivariate_mixed_derivative_oracle(exact_primitive, expected_partial)
        and not test_bivariate_mixed_derivative_oracle(fake_primitive, expected_partial)
    )
    assertions.append(
        GateAssertion(
            "Mixed partial of the declared primitive matches, and the injected primitive does not",
            derivative_ok,
            f"expected partial {expected_partial!r}",
        )
    )
    if not derivative_ok:
        failures.append("Demo 002 mixed-partial host check failed on the declared fixtures")

    leakage_ok = isinstance(leaked_payload, dict) and not test_refusal_payload_masking_oracle(
        leaked_payload
    )
    assertions.append(
        GateAssertion(
            "Injected refusal payload is rejected",
            leakage_ok,
            f"payload keys {list(leaked_payload) if isinstance(leaked_payload, dict) else None}",
        )
    )
    if not leakage_ok:
        failures.append("Demo 002 refusal-payload host check failed on the declared fixture")

    factor_ok = isinstance(separable, dict) and test_separable_factor_oracle(separable)
    assertions.append(
        GateAssertion(
            "Declared separable factors integrate to the declared product",
            factor_ok,
            "control_2_separable_factorization",
        )
    )
    if not factor_ok:
        failures.append("Demo 002 separable-factor host check failed")

    boundary_ok = (
        isinstance(declared_region, str)
        and isinstance(injected_boundary, str)
        and declared_region != injected_boundary
    )
    assertions.append(
        GateAssertion(
            "Injected boundary name differs from the declared region",
            boundary_ok,
            f"declared {declared_region!r}; injected {injected_boundary!r}",
        )
    )
    if not boundary_ok:
        failures.append("Demo 002 boundary fixture does not differ from the declared region")

    # 6. Positive Controls Non-Contagion Check
    # Verify that positive controls have explicit non-contagion guarantees
    contagion_violations = []
    for ab in generalized_antibodies:
        ab_id = ab.get("generalized_antibody_id", "")
        guarantee = ab.get("contamination_prevention_guarantee", "")
        if not guarantee or len(guarantee.strip()) < 10:
            contagion_violations.append(f"{ab_id} lacks detailed non-contagion guarantee")
    cont_ok = len(contagion_violations) == 0
    assertions.append(
        GateAssertion(
            "Non-Contagion Guarantee on Valid Controls",
            cont_ok,
            f"Missing guarantees: {contagion_violations if not cont_ok else 'None'}",
        )
    )
    if not cont_ok:
        failures.append(f"Antibodies lack non-contagion guarantees: {contagion_violations}")

    # 7. Claim Hygiene
    hygiene_violations = audit_claim_hygiene(generalized_antibodies)
    hyg_ok = len(hygiene_violations) == 0
    assertions.append(
        GateAssertion(
            "Claim Hygiene (Zero Forbidden Words)",
            hyg_ok,
            f"Violations: {hygiene_violations if not hyg_ok else 'None'}",
        )
    )
    if not hyg_ok:
        failures.append(f"Claim hygiene violations: {hygiene_violations}")

    passed = len(failures) == 0
    return GateResult(
        demo_id="DEMO_002_GENERALIZATION",
        passed=passed,
        assertions=assertions,
        failure_reasons=failures,
    )
