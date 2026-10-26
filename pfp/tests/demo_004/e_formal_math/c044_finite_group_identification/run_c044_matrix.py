# AuthorityEffect: None.
"""
Empirical Matrix Sweep for C044 Finite Group Identification.
Benchmarks Space Bunny Alpha (stealth/space-bunny-alpha) against
LLaMA 3.3 70B and LLaMA 3.1 8B across 10 calibrated finite group tasks.
"""

import json
import sys
from functools import partial
from pathlib import Path

_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "omega_engine_pfp").is_dir() and (p / "omega_engine_woland").is_dir())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.judge_packet.checkers.dual_evaluator import (  # noqa: E402
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
        "max_tokens": 1024,
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "LLaMA 3.3 70B Instruct",
        "tier": "70B Dense",
        "max_tokens": 1024,
    },
    {
        "id": "meta-llama/llama-3.1-8b-instruct",
        "name": "LLaMA 3.1 8B Instruct",
        "tier": "8B Dense",
        "max_tokens": 1024,
    },
]

SYSTEM_PROMPT = """You are a rigorous mathematical solver participating in Challenge C044: Finite Group Identification under the Symbol Game protocol.
Given a finite group identification or comparison task:
- For IDENTIFY: Return JSON with {"case_id": "...", "status": "SOLVED", "kind": "IDENTIFIED", "rep_id": [order, index], "images": [img_1, ...]}
- For COMPARE: Return {"case_id": "...", "status": "SOLVED", "kind": "ISOMORPHIC", "images": [...]} or {"case_id": "...", "status": "SOLVED", "kind": "NOT_ISOMORPHIC", "invariant": "element_order_histogram", "G_value": {...}, "H_value": {...}}
- For OUT_OF_SCOPE: Return {"case_id": "...", "status": "OUT_OF_SCOPE", "witness": {"reason": "...", ...}}
Output ONLY valid RFC 8785 JSON without Markdown code fences."""


# The example ``note`` names the group (for example "Quaternion group Q8"), so it is
# answer-bearing and never sent; the case ID is replaced by an opaque token.
WITHHELD = ("note",)


def load_cases() -> list[dict]:
    """The first ten public examples, as in the original sweep."""
    pkg_root = Path(__file__).resolve().parent
    files = sorted((pkg_root / "participant_packet" / "examples").glob("c044_pub_*.json"))[:10]
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def build_prompt(case: dict, token: str) -> str:
    return build_user_prompt(case, token, withheld=WITHHELD)


def evaluate(case: dict, ans: dict) -> tuple[bool, str]:
    """Both judge checkers must accept (dual evaluator)."""
    return evaluate_dual(case, ans)[:2]


def run_matrix(*, argv=None) -> Path:
    """Exploratory model matrix; the key comes from the environment only and the run record is
    written to a new folder under the intelligence root (never outside the repository)."""
    runner = run_model_matrix if argv is None else partial(run_model_matrix_cli, argv=argv)
    folder = runner(
        challenge_id="c044",
        models=MODELS,
        cases=load_cases(),
        system_prompt=SYSTEM_PROMPT,
        evaluate=evaluate,
        prompt_builder=build_prompt,
        title="Symbol Game C044 Matrix Runner",
    )
    print(f"[DONE] Run record written to {folder}")
    return folder


if __name__ == "__main__":
    run_matrix(argv=sys.argv[1:])
