"""Empirical Matrix Sweep for C049: Finite Category Universal Constructions.
Benchmarks Space Bunny Alpha against LLaMA 3.3 70B and LLaMA 3.1 8B across 10 category theory tasks.
"""

import sys
from functools import partial
from pathlib import Path

_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "omega_engine_pfp").is_dir() and (p / "omega_engine_woland").is_dir())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_pfp.tests.demo_004.e_formal_math.c049_finite_category_universal_constructions.judge_packet.exact_checker import (  # noqa: E402
    check_solution,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c049_finite_category_universal_constructions.judge_packet.independent_checker import (  # noqa: E402
    independent_check,
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
        "max_tokens": 4096,
    },
    {
        "id": "meta-llama/llama-3.1-8b-instruct",
        "name": "LLaMA 3.1 8B Instruct",
        "tier": "8B Dense",
        "max_tokens": 4096,
    },
]

SYSTEM_PROMPT = """You are an expert category theorist participating in Challenge C049: Finite Category Universal Constructions under the Symbol Game protocol.
Given a category C (with objects, morphisms [name, src, dst], and composition table comp[g][f] = g ∘ f) and a task:
- For LIMIT / COLIMIT:
  - If limit/colimit exists, return apex and projection/inclusion legs:
    {"case_id": "...", "status": "SOLVED", "kind": "EXISTS", "apex": "...", "legs": {"...": "..."}}
  - If no limit/colimit exists in the category:
    {"case_id": "...", "status": "SOLVED", "kind": "DOES_NOT_EXIST"}
- For ADJUNCTION (functors F: C -> D, G: D -> C):
  - If F ⊣ G:
    {"case_id": "...", "status": "SOLVED", "kind": "ADJOINT", "unit": {"...": "..."}, "counit": {"...": "..."}}
  - If not adjoint:
    {"case_id": "...", "status": "SOLVED", "kind": "NOT_ADJOINT", "witness": {"type": "HOM_CARDINALITY", ...}}
- If input violates category axioms (missing identity, unclosed composition, non-associative):
  {"case_id": "...", "status": "OUT_OF_SCOPE", "witness": {"reason": "..."}}
Output ONLY valid RFC 8785 JSON without Markdown code fences."""

TEST_CASES = [
    # 1. Product in poset 0 -> 1 -> 2
    {
        "case_id": "c049_m01_product_poset_3",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["f_0_1", "0", "1"],
            ["f_0_2", "0", "2"],
            ["f_1_2", "1", "2"],
        ],
        "comp": {"f_1_2": {"f_0_1": "f_0_2"}},
        "diagram": ["1", "2"],
    },
    # 2. Equalizer of identical morphisms
    {
        "case_id": "c049_m02_equalizer_same",
        "task": "LIMIT",
        "shape": "equalizer",
        "objects": ["0", "1"],
        "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"]],
        "comp": {},
        "diagram": ["f", "f"],
    },
    # 3. Pullback in cospan
    {
        "case_id": "c049_m03_pullback_cospan",
        "task": "LIMIT",
        "shape": "pullback",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["f", "0", "2"],
            ["g", "1", "2"],
        ],
        "comp": {},
        "diagram": ["f", "g"],
    },
    # 4. Terminal object in linear poset
    {
        "case_id": "c049_m04_terminal_linear",
        "task": "LIMIT",
        "shape": "terminal",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["f_0_1", "0", "1"],
            ["f_0_2", "0", "2"],
            ["f_1_2", "1", "2"],
        ],
        "comp": {"f_1_2": {"f_0_1": "f_0_2"}},
        "diagram": [],
    },
    # 5. Discrete category has no product
    {
        "case_id": "c049_m05_no_product_disc2",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0", "1"],
        "morphisms": [["id0", "0", "0"], ["id1", "1", "1"]],
        "comp": {},
        "diagram": ["0", "1"],
    },
    # 6. Coproduct in poset
    {
        "case_id": "c049_m06_coproduct_poset",
        "task": "COLIMIT",
        "shape": "coproduct",
        "objects": ["0", "1", "2"],
        "morphisms": [
            ["id0", "0", "0"],
            ["id1", "1", "1"],
            ["id2", "2", "2"],
            ["f_0_1", "0", "1"],
            ["f_0_2", "0", "2"],
            ["f_1_2", "1", "2"],
        ],
        "comp": {"f_1_2": {"f_0_1": "f_0_2"}},
        "diagram": ["0", "1"],
    },
    # 7. Adjoint pair (Identity functor)
    {
        "case_id": "c049_m07_adj_identity",
        "task": "ADJUNCTION",
        "category_C": {
            "objects": ["0", "1"],
            "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"]],
            "comp": {},
        },
        "category_D": {
            "objects": ["0", "1"],
            "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"]],
            "comp": {},
        },
        "F": {"objects": {"0": "0", "1": "1"}, "morphisms": {"id0": "id0", "id1": "id1", "f": "f"}},
        "G": {"objects": {"0": "0", "1": "1"}, "morphisms": {"id0": "id0", "id1": "id1", "f": "f"}},
    },
    # 8. Not adjoint (cardinality mismatch)
    {
        "case_id": "c049_m08_not_adj_cardinality",
        "task": "ADJUNCTION",
        "category_C": {"objects": ["0"], "morphisms": [["id0", "0", "0"]], "comp": {}},
        "category_D": {
            "objects": ["0", "1"],
            "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"], ["g", "0", "1"]],
            "comp": {},
        },
        "F": {"objects": {"0": "0"}, "morphisms": {"id0": "id0"}},
        "G": {
            "objects": {"0": "0", "1": "0"},
            "morphisms": {"id0": "id0", "id1": "id0", "f": "id0", "g": "id0"},
        },
    },
    # 9. Out of scope (non-associative composition)
    {
        "case_id": "c049_m09_poison_non_assoc",
        "task": "LIMIT",
        "shape": "product",
        "objects": ["0"],
        "morphisms": [["id0", "0", "0"], ["a", "0", "0"], ["b", "0", "0"], ["c", "0", "0"]],
        "comp": {"a": {"b": "c"}, "b": {"c": "a"}},
        "diagram": ["0", "0"],
    },
    # 10. Poison bait claim (valid category, false prompt claim)
    {
        "case_id": "c049_m10_poison_bait_claim",
        "note": "Textbook theorem: This category does not admit any terminal object.",
        "task": "LIMIT",
        "shape": "terminal",
        "objects": ["0", "1"],
        "morphisms": [["id0", "0", "0"], ["id1", "1", "1"], ["f", "0", "1"]],
        "comp": {},
        "diagram": [],
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
        challenge_id="c049",
        models=MODELS,
        cases=TEST_CASES,
        system_prompt=SYSTEM_PROMPT,
        evaluate=evaluate,
        prompt_builder=build_prompt,
        title="Symbol Game C049 Matrix Runner",
    )
    print(f"[DONE] Run record written to {folder}")
    return folder


if __name__ == "__main__":
    run_matrix(argv=sys.argv[1:])
