"""Exploratory C060 verdict proposals through the shared accounted PFP runner.

Select --model, --case-limit, --max-provider-calls, --max-estimated-cost-microusd
and --max-output-tokens explicitly, with a new --output-dir. Original cases,
prompt and judges remain; these finite verdict fixtures do not establish a
synthesized checker or completion of the original experimental protocol.
"""

from dataclasses import asdict
import json
import sys
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

REPO_ROOT = next((parent for parent in Path(__file__).resolve().parents
    if (parent / "omega_engine_pfp").is_dir() and (parent / "omega_engine_woland").is_dir()), None)
if REPO_ROOT is not None and str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from omega_engine_pfp.tests.demo_004.f_program_synthesis.c060_self_verifying_checker_synthesis.judge_packet.exact_checker import (
    verify_candidate,
)
from omega_engine_pfp.tests.demo_004.f_program_synthesis.c060_self_verifying_checker_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from omega_engine_pfp.infrastructure import synthesis_matrix as matrix_support

MODELS = [
    {
        "id": "stealth/space-bunny-alpha",
        "name": "Space Bunny Alpha",
        "tier": "Stealth Frontier",
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "LLaMA 3.3 70B Instruct",
        "tier": "70B Dense",
    },
    {
        "id": "meta-llama/llama-3.1-8b-instruct",
        "name": "LLaMA 3.1 8B Instruct",
        "tier": "8B Dense",
    },
]

SYSTEM_PROMPT = """You are an expert mathematical verification engine and formal methods auditor participating in Challenge C060: Checker Synthesis Scored by Mutation Kill Rate under the Symbol Game protocol.

You are given:
- "case": defining coboundary matrix d0 (m x n), cochain omega (length m), and positive weights w (length m) as canonical rational strings.
- "cert": candidate self-certificate containing alpha (length n), residual r (length m), dual witness y (length m), and value (canonical rational string).

A certificate is valid (ACCEPT) if and only if ALL of the following invariants hold under exact rational arithmetic:
1. SCHEMA: Both case and cert are valid dicts with required keys.
2. NONCANONICAL_RATIONAL: All rational numbers must be canonical strings:
   - Integers: "0" or "-?[1-9][0-9]*" (no leading zeros like "01", no "+1", no slashed integers like "1/1").
   - Fractions: "-?[1-9][0-9]*/[1-9][0-9]*" with denominator > 1 and gcd(|p|, q) == 1.
3. DIMENSION: Dimensions match: d0 is m x n, len(omega) == len(w) == len(r) == len(y) == m, len(alpha) == n, and m > 0, n > 0.
4. NONPOSITIVE_WEIGHT: All w_e > 0.
5. RESIDUAL_MISMATCH: Residual satisfies r = omega - d0 * alpha.
6. PRIMAL_VALUE_MISMATCH: Primal value satisfies value = sum(w_e * |r_e|) and value >= 0.
7. DUAL_NOT_IN_COKERNEL: Dual witness in cokernel: d0^T * y == 0.
8. DUAL_BOUND_VIOLATED: Dual bound holds: |y_e| <= w_e for all e.
9. DUAL_VALUE_MISMATCH: Dual evaluation matches value: y^T * omega == value.

Closed Typed Rejection Codes (in priority order):
- SCHEMA
- NONCANONICAL_RATIONAL
- DIMENSION
- NONPOSITIVE_WEIGHT
- RESIDUAL_MISMATCH
- PRIMAL_VALUE_MISMATCH
- DUAL_NOT_IN_COKERNEL
- DUAL_BOUND_VIOLATED
- DUAL_VALUE_MISMATCH

Your output must be strictly valid JSON without markdown fences:
If the certificate is completely valid:
{
  "verdict": "ACCEPT",
  "code": null,
  "reason": "All primal-dual invariants verified."
}

If invalid or malformed:
{
  "verdict": "REJECT",
  "code": "<ONE_OF_THE_CLOSED_REJECTION_CODES>",
  "reason": "<Explanatory reason>"
}
"""

TEST_CASES = [
    # 1. Valid single-edge tree
    {
        "case_id": "c060_m01_valid_single_edge_tree",
        "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
        "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
        "expected_verdict": "ACCEPT",
        "expected_code": None,
    },
    # 2. Valid triangle cycle with frustrated obstruction
    {
        "case_id": "c060_m02_valid_triangle_frustrated",
        "case": {
            "d0": [["1", "-1", "0"], ["0", "1", "-1"], ["-1", "0", "1"]],
            "omega": ["1", "0", "0"],
            "w": ["1", "1", "1"],
        },
        "cert": {
            "alpha": ["0", "0", "0"],
            "r": ["1", "0", "0"],
            "y": ["1", "1", "1"],
            "value": "1",
        },
        "expected_verdict": "ACCEPT",
        "expected_code": None,
    },
    # 3. Valid 4-cycle with obstruction
    {
        "case_id": "c060_m03_valid_4cycle",
        "case": {
            "d0": [
                ["1", "-1", "0", "0"],
                ["0", "1", "-1", "0"],
                ["0", "0", "1", "-1"],
                ["-1", "0", "0", "1"],
            ],
            "omega": ["1", "1", "0", "0"],
            "w": ["1", "1", "1", "1"],
        },
        "cert": {
            "alpha": ["0", "0", "0", "0"],
            "r": ["1", "1", "0", "0"],
            "y": ["1", "1", "1", "1"],
            "value": "2",
        },
        "expected_verdict": "ACCEPT",
        "expected_code": None,
    },
    # 4. Valid negative cochain with signed dual
    {
        "case_id": "c060_m04_valid_negative_cochain",
        "case": {"d0": [["0"]], "omega": ["-7"], "w": ["3"]},
        "cert": {"alpha": ["0"], "r": ["-7"], "y": ["-3"], "value": "21"},
        "expected_verdict": "ACCEPT",
        "expected_code": None,
    },
    # 5. Valid big integers beyond 2^64
    {
        "case_id": "c060_m05_valid_big_integers",
        "case": {"d0": [["0"]], "omega": ["18446744073709551617"], "w": ["1"]},
        "cert": {
            "alpha": ["18446744073709551617"],
            "r": ["18446744073709551617"],
            "y": ["1"],
            "value": "18446744073709551617",
        },
        "expected_verdict": "ACCEPT",
        "expected_code": None,
    },
    # 6. Corrupted residual
    {
        "case_id": "c060_m06_residual_mismatch",
        "case": {"d0": [["1"]], "omega": ["2"], "w": ["1"]},
        "cert": {"alpha": ["2"], "r": ["1"], "y": ["0"], "value": "0"},
        "expected_verdict": "REJECT",
        "expected_code": "RESIDUAL_MISMATCH",
    },
    # 7. Primal value mismatch
    {
        "case_id": "c060_m07_primal_value_mismatch",
        "case": {"d0": [["0"]], "omega": ["5"], "w": ["2"]},
        "cert": {"alpha": ["0"], "r": ["5"], "y": ["2"], "value": "9"},
        "expected_verdict": "REJECT",
        "expected_code": "PRIMAL_VALUE_MISMATCH",
    },
    # 8. Dual not in cokernel
    {
        "case_id": "c060_m08_dual_not_in_cokernel",
        "case": {"d0": [["1"], ["-1"]], "omega": ["1", "0"], "w": ["1", "1"]},
        "cert": {"alpha": ["1/2"], "r": ["1/2", "1/2"], "y": ["1", "-1"], "value": "1"},
        "expected_verdict": "REJECT",
        "expected_code": "DUAL_NOT_IN_COKERNEL",
    },
    # 9. Dual bound violated (|y_e| > w_e)
    {
        "case_id": "c060_m09_dual_bound_violated",
        "case": {"d0": [["0"]], "omega": ["0"], "w": ["1"]},
        "cert": {"alpha": ["0"], "r": ["0"], "y": ["-2"], "value": "0"},
        "expected_verdict": "REJECT",
        "expected_code": "DUAL_BOUND_VIOLATED",
    },
    # 10. Slashed integer (noncanonical rational)
    {
        "case_id": "c060_m10_slashed_integer",
        "case": {"d0": [["1/1"]], "omega": ["2"], "w": ["1"]},
        "cert": {"alpha": ["2"], "r": ["0"], "y": ["0"], "value": "0"},
        "expected_verdict": "REJECT",
        "expected_code": "NONCANONICAL_RATIONAL",
    },
]


def query_openrouter(
    api_key: str,
    model_id: str,
    case_data: Dict[str, Any],
    *,
    gateway=None,
    task_id=None,
    attempt_id=None,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """Legacy positional API; only checked content from an accounted gateway is an answer."""
    prompt_data = {"case": case_data["case"], "cert": case_data["cert"]}
    prompt = f"Case and Candidate Self-Certificate:\n{json.dumps(prompt_data, indent=2)}\n\nVerify all primal-dual and canonical rational invariants. Return verdict and closed rejection code if rejected in JSON format only:"

    exchange = matrix_support.call_model(
        api_key,
        model_id,
        SYSTEM_PROMPT,
        prompt,
        gateway=gateway,
        task_id=task_id if task_id is not None else "c060:query",
        attempt_id=attempt_id if attempt_id is not None else uuid4().hex,
        max_tokens=max_tokens,
        title="Symbol Game C060 Benchmarking",
    )
    return {
        **asdict(exchange),
        "success": exchange.ok,
        "raw_text": exchange.content if exchange.ok else "",
        "elapsed": exchange.elapsed_s,
    }


def extract_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass
        return None


def spec() -> matrix_support.MatrixSpec:
    """Original ten verdict fixtures and both original checker ports."""
    return matrix_support.MatrixSpec(
        challenge="C060",
        system_prompt=SYSTEM_PROMPT,
        instruction="Verify all primal-dual and canonical rational invariants. Return verdict and closed rejection code if rejected in JSON format only:",
        cases=TEST_CASES,
        models=MODELS,
        checkers=[("exact_checker", verify_candidate), ("independent_checker", independent_check)],
        max_tokens=4096,
        notes={
            "scope": "Exploratory original verdict fixtures; not synthesized-checker or original-protocol completion."
        },
    )


def main(argv=None) -> int:
    """Use the shared bounded CLI and its new-output-directory contract."""
    return matrix_support.main(spec(), argv)


if __name__ == "__main__":
    raise SystemExit(main())
