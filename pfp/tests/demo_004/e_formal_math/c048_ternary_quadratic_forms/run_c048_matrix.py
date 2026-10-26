"""Empirical Matrix Sweep for C048: Ternary Quadratic Forms.
Benchmarks Space Bunny Alpha against LLaMA 3.3 70B and LLaMA 3.1 8B across 10 Diophantine tasks.
"""

import json
import sys
from functools import partial
from pathlib import Path

_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "omega_engine_pfp").is_dir() and (p / "omega_engine_woland").is_dir())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_pfp.tests.demo_004.e_formal_math.c048_ternary_quadratic_forms.judge_packet.exact_checker import (  # noqa: E402
    check_solution,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c048_ternary_quadratic_forms.judge_packet.independent_checker import (  # noqa: E402
    independent_check,
)
from omega_engine_pfp.infrastructure.formal_matrix import (  # noqa: E402
    run_model_matrix,
    run_model_matrix_cli,
)

MODELS = [
    {
        "id": "stealth/space-bunny-alpha",
        "name": "Space Bunny Alpha",
        "tier": "Stealth Frontier",
        "max_tokens": 2048,
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "LLaMA 3.3 70B Instruct",
        "tier": "70B Dense",
        "max_tokens": 2048,
    },
    {
        "id": "meta-llama/llama-3.1-8b-instruct",
        "name": "LLaMA 3.1 8B Instruct",
        "tier": "8B Dense",
        "max_tokens": 2048,
    },
]

SYSTEM_PROMPT = """You are an expert arithmetic geometer and number theorist participating in Challenge C048: Ternary Quadratic Forms under the Symbol Game protocol.
Given integer coefficients a, b, c for a*x^2 + b*y^2 + c*z^2 = 0:
- If a non-trivial integer solution (x, y, z) != (0, 0, 0) exists:
  Return JSON: {"case_id": "...", "status": "SOLVED", "kind": "RATIONAL_POINT", "x": "...", "y": "...", "z": "..."}
- If no non-trivial solution exists by Hasse-Minkowski, return a place where Hilbert symbol (-ac, -bc)_place = -1:
  Return JSON: {"case_id": "...", "status": "SOLVED", "kind": "LOCAL_OBSTRUCTION", "place": "inf"|"2"|"p"}
- If input has non-integer coefficients:
  Return JSON: {"case_id": "...", "status": "OUT_OF_SCOPE", "witness": {"reason": "MALFORMED_COEFFICIENT"}}
Output ONLY valid RFC 8785 JSON without Markdown code fences."""

TEST_CASES = [
    {"case_id": "c048_m01_solv_11_m2", "a": "1", "b": "1", "c": "-2"},
    {"case_id": "c048_m02_solv_pyth", "a": "1", "b": "1", "c": "-1"},
    {"case_id": "c048_m03_solv_35_m8", "a": "3", "b": "5", "c": "-8"},
    {"case_id": "c048_m04_solv_27_m9", "a": "2", "b": "7", "c": "-9"},
    {"case_id": "c048_m05_obstr_inf_111", "a": "1", "b": "1", "c": "1"},
    {"case_id": "c048_m06_obstr_inf_235", "a": "2", "b": "3", "c": "5"},
    {"case_id": "c048_m07_obstr_2_11_m7", "a": "1", "b": "1", "c": "-7"},
    {"case_id": "c048_m08_obstr_p_12_m7", "a": "1", "b": "2", "c": "-7"},
    {"case_id": "c048_m09_malformed", "a": "not_an_int", "b": "1", "c": "-2"},
    {
        "case_id": "c048_m10_poison_claim_no_solution",
        "note": "Famous obstruction: This form has no rational points under any conditions.",
        "a": "1",
        "b": "1",
        "c": "-1",
    },
]


def build_prompt(case: dict, token: str) -> str:
    """Opaque token plus the coefficients only (the case ID names the verdict)."""
    view = {"case_id": token, "a": case["a"], "b": case["b"], "c": case["c"]}
    return f"Case ID: {token}\nInput:\n{json.dumps(view, indent=2)}"


def evaluate(case: dict, ans: dict) -> tuple[bool, str]:
    """Both judge checkers must accept."""
    ok_exact, msg_exact = check_solution(case, ans)
    ok_indep, msg_indep = independent_check(case, ans)
    return ok_exact and ok_indep, f"exact: {msg_exact}; independent: {msg_indep}"


def run_matrix(*, argv=None) -> Path:
    """Exploratory model matrix; writes a new run folder under the intelligence root."""
    runner = run_model_matrix if argv is None else partial(run_model_matrix_cli, argv=argv)
    folder = runner(
        challenge_id="c048",
        models=MODELS,
        cases=TEST_CASES,
        system_prompt=SYSTEM_PROMPT,
        evaluate=evaluate,
        prompt_builder=build_prompt,
        title="Symbol Game C048 Matrix Runner",
    )
    print(f"[DONE] Run record written to {folder}")
    return folder


if __name__ == "__main__":
    run_matrix(argv=sys.argv[1:])
