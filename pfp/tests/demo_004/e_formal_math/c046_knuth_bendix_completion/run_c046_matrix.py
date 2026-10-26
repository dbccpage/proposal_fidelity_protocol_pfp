# AuthorityEffect: None.
"""
Empirical Matrix Sweep for C046: Knuth-Bendix Completion.
Benchmarks Space Bunny Alpha (stealth/space-bunny-alpha) against
LLaMA 3.3 70B and LLaMA 3.1 8B across 10 calibrated term rewriting tasks.
"""

import sys
from functools import partial
from pathlib import Path

_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "omega_engine_pfp").is_dir() and (p / "omega_engine_woland").is_dir())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.judge_packet.checkers.dual_evaluator import (  # noqa: E402
    evaluate_dual,
)
from omega_engine_pfp.infrastructure.formal_matrix import (  # noqa: E402
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

SYSTEM_PROMPT = """You are a rigorous formal logician and term rewriting expert participating in Challenge C046: Knuth-Bendix Completion under the Symbol Game protocol.
Given an equational reasoning task:
- For COMPLETE: Return JSON with {"case_id": "...", "status": "SOLVED", "task": "COMPLETE", "converged": true, "rules_count": int, "rules": [{"lhs": "...", "rhs": "..."}, ...], "joinability_certificates_count": int}
- For CHECK_CONFLUENCE: Return JSON with {"case_id": "...", "status": "SOLVED", "task": "CHECK_CONFLUENCE", "is_confluent": true|false, "critical_pairs_count": int, "unjoinable_count": int}
- For REDUCE: Return JSON with {"case_id": "...", "status": "SOLVED", "task": "REDUCE", "term": "...", "normal_form": "..."}
- For REFUSED: Return JSON with {"case_id": "...", "status": "REFUSED", "reason": "ORDER_FAILURE"|"MALFORMED_TERM"|"MAX_STEPS_EXCEEDED"|"MALFORMED_INPUT", "witness": {...}}
Output ONLY valid RFC 8785 JSON without Markdown code fences."""

TEST_CASES = [
    {
        "case_id": "c046_m01_group_complete",
        "task": "COMPLETE",
        "equations": [
            ["mul(e, x)", "x"],
            ["mul(inv(x), x)", "e"],
            ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
        ],
        "precedence": {"inv": 100, "mul": 50, "e": 10},
    },
    {
        "case_id": "c046_m02_monoid_complete",
        "task": "COMPLETE",
        "equations": [
            ["mul(1, x)", "x"],
            ["mul(x, 1)", "x"],
            ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
        ],
        "precedence": {"mul": 50, "1": 10},
    },
    {
        "case_id": "c046_m03_semilattice_complete",
        "task": "COMPLETE",
        "equations": [["meet(x, x)", "x"], ["meet(x, 1)", "x"], ["meet(x, 0)", "0"]],
        "precedence": {"meet": 50, "1": 10, "0": 5},
    },
    {
        "case_id": "c046_m04_check_confluent_group",
        "task": "CHECK_CONFLUENCE",
        "rules": [
            ["mul(e, x)", "x"],
            ["mul(inv(x), x)", "e"],
            ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
            ["mul(inv(x), mul(x, y))", "y"],
            ["inv(e)", "e"],
            ["mul(x, e)", "x"],
            ["mul(x, inv(x))", "e"],
            ["inv(inv(x))", "x"],
            ["mul(x, mul(inv(x), y))", "y"],
            ["mul(x, inv(mul(y, x)))", "inv(y)"],
        ],
    },
    {
        "case_id": "c046_m05_check_non_confluent_group",
        "task": "CHECK_CONFLUENCE",
        "rules": [
            ["mul(e, x)", "x"],
            ["mul(inv(x), x)", "e"],
            ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
        ],
    },
    {
        "case_id": "c046_m06_reduce_inv_inv",
        "task": "REDUCE",
        "rules": [
            ["mul(e, x)", "x"],
            ["mul(inv(x), x)", "e"],
            ["inv(inv(x))", "x"],
            ["mul(x, e)", "x"],
        ],
        "term": "mul(inv(inv(x)), e)",
    },
    {
        "case_id": "c046_m07_reduce_nested",
        "task": "REDUCE",
        "rules": [
            ["mul(e, x)", "x"],
            ["mul(inv(x), x)", "e"],
            ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
            ["mul(x, e)", "x"],
        ],
        "term": "mul(mul(inv(x), x), mul(y, e))",
    },
    {
        "case_id": "c046_m08_refusal_commutativity",
        "task": "COMPLETE",
        "equations": [["mul(x, y)", "mul(y, x)"]],
        "precedence": {"mul": 50},
    },
    {
        "case_id": "c046_m09_refusal_malformed_term",
        "task": "COMPLETE",
        "equations": [["mul(x, inv(y", "x"]],
    },
    {
        "case_id": "c046_m10_refusal_step_budget",
        "task": "COMPLETE",
        "equations": [
            ["mul(e, x)", "x"],
            ["mul(inv(x), x)", "e"],
            ["mul(mul(x, y), z)", "mul(x, mul(y, z))"],
        ],
        "precedence": {"inv": 100, "mul": 50, "e": 10},
        "max_steps": 2,
    },
]


WITHHELD = ()


def build_prompt(case: dict, token: str) -> str:
    """Opaque token; the case ID (it names the expected outcome) is never sent."""
    return build_user_prompt(case, token, withheld=WITHHELD)


def evaluate(case: dict, ans: dict) -> tuple[bool, str]:
    """Both judge checkers must accept (dual evaluator)."""
    return evaluate_dual(case, ans)[:2]


def run_matrix(*, argv=None) -> Path:
    """Exploratory model matrix; writes a new run folder under the intelligence root."""
    runner = run_model_matrix if argv is None else partial(run_model_matrix_cli, argv=argv)
    folder = runner(
        challenge_id="c046",
        models=MODELS,
        cases=TEST_CASES,
        system_prompt=SYSTEM_PROMPT,
        evaluate=evaluate,
        prompt_builder=build_prompt,
        title="Symbol Game C046 Matrix Runner",
    )
    print(f"[DONE] Run record written to {folder}")
    return folder


if __name__ == "__main__":
    run_matrix(argv=sys.argv[1:])
