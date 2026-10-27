# AuthorityEffect: None.
"""
Empirical Matrix Sweep for C045: Knot Polynomials from Planar Diagrams.
Benchmarks Space Bunny Alpha (stealth/space-bunny-alpha) against
LLaMA 3.3 70B and LLaMA 3.1 8B across 10 calibrated knot topology tasks.
"""

import sys
from functools import partial
from pathlib import Path

_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "pfp").is_dir() and (p / "adversary").is_dir())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from pfp.tests.demo_004.e_formal_math.c045_knot_polynomials_from_pd.judge_packet.checkers.dual_evaluator import (  # noqa: E402
    evaluate_dual,
)
from pfp.infrastructure.formal_matrix import (  # noqa: E402
    build_user_prompt,
    run_model_matrix,
    run_model_matrix_cli,
)

MODELS = [
    {
        "id": "stealth/space-bunny-alpha",
        "name": "Space Bunny Alpha",
        "tier": "Stealth Frontier",
        "max_tokens": 4096,
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

SYSTEM_PROMPT = """You are a rigorous mathematical topologist participating in Challenge C045: Knot Polynomials from Planar Diagrams under the Symbol Game protocol.
Given a knot planar diagram task:
- For COMPUTE_POLYNOMIALS: Return JSON with {"case_id": "...", "status": "SOLVED", "task": "COMPUTE_POLYNOMIALS", "writhe": int, "kauffman_bracket": {"power": coeff, ...}, "jones_polynomial": {"power": coeff, ...}, "alexander_polynomial": {"power": coeff, ...}, "identified_knot": "3_1"|"4_1"|..., "chirality": "RIGHT_HANDED"|"LEFT_HANDED"|"ACHIRAL"}
- For IDENTIFY: Return JSON with {"case_id": "...", "status": "SOLVED", "task": "IDENTIFY", "identified_knot": "...", "chirality": "...", "invariants": {"writhe": int, "jones_polynomial": {...}, "alexander_polynomial": {...}}}
- For COMPARE: Return JSON with {"case_id": "...", "status": "SOLVED", "task": "COMPARE", "kind": "SAME_INVARIANTS", "invariants": {...}} or {"case_id": "...", "status": "SOLVED", "task": "COMPARE", "kind": "DIFFERENT_INVARIANTS", "separating_invariant": "jones_polynomial"|"alexander_polynomial", "val_1": {...}, "val_2": {...}}
- For REFUSED: Return JSON with {"case_id": "...", "status": "REFUSED", "reason": "EDGE_LABEL_MULTIPLICITY"|"ORIENTATION_INCONSISTENT"|"NON_PLANAR", "witness": {...}}
Output ONLY valid RFC 8785 JSON without Markdown code fences."""


TEST_CASES = [
    {"case_id": "c045_m01_unknot", "task": "COMPUTE_POLYNOMIALS", "pd": []},
    {
        "case_id": "c045_m02_trefoil_identify",
        "task": "IDENTIFY",
        "pd": [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]],
    },
    {
        "case_id": "c045_m03_trefoil_polynomials",
        "task": "COMPUTE_POLYNOMIALS",
        "pd": [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]],
    },
    {
        "case_id": "c045_m04_figure8_identify",
        "task": "IDENTIFY",
        "pd": [[4, 2, 5, 1], [8, 6, 1, 5], [6, 3, 7, 4], [2, 7, 3, 8]],
    },
    {
        "case_id": "c045_m05_figure8_polynomials",
        "task": "COMPUTE_POLYNOMIALS",
        "pd": [[4, 2, 5, 1], [8, 6, 1, 5], [6, 3, 7, 4], [2, 7, 3, 8]],
    },
    {
        "case_id": "c045_m06_cinquefoil_identify",
        "task": "IDENTIFY",
        "pd": [[1, 7, 2, 6], [3, 9, 4, 8], [5, 1, 6, 10], [7, 3, 8, 2], [9, 5, 10, 4]],
    },
    {
        "case_id": "c045_m07_compare_trefoil_figure8",
        "task": "COMPARE",
        "pd_1": [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]],
        "pd_2": [[4, 2, 5, 1], [8, 6, 1, 5], [6, 3, 7, 4], [2, 7, 3, 8]],
    },
    {
        "case_id": "c045_m08_compare_trefoil_gauge",
        "task": "COMPARE",
        "pd_1": [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]],
        "pd_2": [[3, 1, 4, 6], [5, 3, 6, 2], [1, 5, 2, 4]],
    },
    {
        "case_id": "c045_m09_refusal_corrupt_edge",
        "task": "COMPUTE_POLYNOMIALS",
        "pd": [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 9]],
    },
    {
        "case_id": "c045_m10_refusal_bad_understrand",
        "task": "COMPUTE_POLYNOMIALS",
        "pd": [[1, 5, 4, 2], [3, 1, 4, 6], [5, 3, 6, 2]],
    },
]


def build_prompt(case: dict, token: str) -> str:
    """User prompt under an opaque token; the case ID (which names the knot) is never sent."""
    return build_user_prompt(case, token)


def run_matrix(*, argv=None) -> Path:
    """Exploratory model matrix; writes a new run folder under the intelligence root."""
    runner = run_model_matrix if argv is None else partial(run_model_matrix_cli, argv=argv)
    folder = runner(
        challenge_id="c045",
        models=MODELS,
        cases=TEST_CASES,
        system_prompt=SYSTEM_PROMPT,
        evaluate=lambda case, ans: evaluate_dual(case, ans)[:2],
        prompt_builder=build_prompt,
        title="Symbol Game C045 Matrix Runner",
    )
    print(f"[DONE] Run record written to {folder}")
    return folder


if __name__ == "__main__":
    run_matrix(argv=sys.argv[1:])
