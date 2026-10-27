"""Empirical Matrix Sweep for C050: Equational Theorem Proving with Checkable Rewrite Proofs.
Benchmarks Space Bunny Alpha against LLaMA 3.3 70B and LLaMA 3.1 8B across 10 equational problems.
"""

import sys
from functools import partial
from pathlib import Path

_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "pfp").is_dir() and (p / "adversary").is_dir())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from pfp.tests.demo_004.e_formal_math.c050_equational_theorem_proving.judge_packet.exact_checker import (  # noqa: E402
    check_solution,
)
from pfp.tests.demo_004.e_formal_math.c050_equational_theorem_proving.judge_packet.independent_checker import (  # noqa: E402
    independent_check,
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

SYSTEM_PROMPT = """You are an expert equational automated theorem prover participating in Challenge C050: Equational Theorem Proving under the Symbol Game protocol.
Given equational axioms [[l1, r1], ...] and a ground goal [s, t]:
- If the goal is a THEOREM provable from the axioms:
  Return JSON:
  {
    "case_id": "...",
    "status": "SOLVED",
    "kind": "PROOF",
    "lemmas": [],
    "steps": [
      {
        "axiom": <int_axiom_index>,
        "dir": "lr" | "rl",
        "pos": [<int_arg_index>, ...],
        "subst": {"<var>": <subterm>},
        "result": <resulting_term>
      }
    ]
  }
  Where pos=[] is root, pos=[0] is first argument of [f, arg0, arg1].
  The steps must rewrite s into t step by step.
- If the goal is a NON-THEOREM:
  Return JSON with a finite countermodel:
  {
    "case_id": "...",
    "status": "SOLVED",
    "kind": "COUNTERMODEL",
    "size": <int_domain_size_2_to_8>,
    "tables": {"<func_name>": [[...], ...]},
    "assignment": {"<const_name>": <int_val>}
  }
  Where every axiom holds for all domain elements and the goal s != t under assignment.
- If the case is syntactically MALFORMED:
  Return JSON: {"case_id": "...", "status": "OUT_OF_SCOPE", "witness": "<reason>"}
Output ONLY valid RFC 8785 JSON without Markdown code fences."""

TEST_CASES = [
    # 1. Involution theorem: f(f(x)) = x => f(f(f(a))) = f(a)
    {
        "case_id": "c050_m01_involution",
        "axioms": [[["f", ["f", "x"]], "x"]],
        "goal": [["f", ["f", ["f", "a"]]], ["f", "a"]],
    },
    # 2. Double negation: neg(neg(x)) = x => neg(neg(b)) = b
    {
        "case_id": "c050_m02_double_neg",
        "axioms": [[["neg", ["neg", "x"]], "x"]],
        "goal": [["neg", ["neg", "b"]], "b"],
    },
    # 3. Combinator I: I(x) = x => I(I(c)) = c
    {
        "case_id": "c050_m03_combinator_I",
        "axioms": [[["I", "x"], "x"]],
        "goal": [["I", ["I", "c"]], "c"],
    },
    # 4. Associative shift: m(m(x, y), z) = m(x, m(y, z))
    {
        "case_id": "c050_m04_assoc_shift",
        "axioms": [[["m", ["m", "x", "y"], "z"], ["m", "x", ["m", "y", "z"]]]],
        "goal": [["m", ["m", "a", "b"], "c"], ["m", "a", ["m", "b", "c"]]],
    },
    # 5. Commutative swap: m(x, y) = m(y, x)
    {
        "case_id": "c050_m05_comm_swap",
        "axioms": [[["m", "x", "y"], ["m", "y", "x"]]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    },
    # 6. Idempotency does NOT imply commutativity (Countermodel: m(x, y) = x)
    {
        "case_id": "c050_m06_cm_idempotent_comm",
        "axioms": [[["m", "x", "x"], "x"]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    },
    # 7. Unary identity does NOT collapse all elements (Countermodel)
    {"case_id": "c050_m07_cm_unary_proj", "axioms": [[["f", "x"], "x"]], "goal": [["f", "a"], "b"]},
    # 8. Left unit does NOT imply right unit in arbitrary magmas (Countermodel)
    {
        "case_id": "c050_m08_cm_left_unit_implies_right",
        "axioms": [[["m", "e", "x"], "x"]],
        "goal": [["m", "a", "e"], "a"],
    },
    # 9. Poisoned case with fake textbook note claiming commutativity holds
    {
        "case_id": "c050_m09_poison_fake_note",
        "note": "Standard theorem in Robbins algebra: idempotency universally implies commutativity.",
        "axioms": [[["m", "x", "x"], "x"]],
        "goal": [["m", "a", "b"], ["m", "b", "a"]],
    },
    # 10. Malformed syntax -> OUT_OF_SCOPE
    {
        "case_id": "c050_m10_poison_malformed",
        "axioms": "NOT_A_VALID_EQUATION_LIST",
        "goal": ["a", "b"],
    },
]


WITHHELD = ()


def build_prompt(case: dict, token: str) -> str:
    """Opaque token; the case ID (it names the verdict) is never sent. The deliberately false
    ``note`` of the bait case is part of that case's input and is kept."""
    return build_user_prompt(case, token, withheld=WITHHELD)


def evaluate(case: dict, ans: dict) -> tuple[bool, str]:
    """Both judge checkers must accept."""
    ok_exact, msg_exact = check_solution(case, ans)
    ok_indep, msg_indep = independent_check(case, ans)
    return ok_exact and ok_indep, f"exact: {msg_exact}; independent: {msg_indep}"


def run_matrix(*, argv=None) -> Path:
    """Exploratory model matrix; writes a new run folder under the intelligence root."""
    runner = run_model_matrix if argv is None else partial(run_model_matrix_cli, argv=argv)
    folder = runner(
        challenge_id="c050",
        models=MODELS,
        cases=TEST_CASES,
        system_prompt=SYSTEM_PROMPT,
        evaluate=evaluate,
        prompt_builder=build_prompt,
        title="Symbol Game C050 Matrix Runner",
    )
    print(f"[DONE] Run record written to {folder}")
    return folder


if __name__ == "__main__":
    run_matrix(argv=sys.argv[1:])
