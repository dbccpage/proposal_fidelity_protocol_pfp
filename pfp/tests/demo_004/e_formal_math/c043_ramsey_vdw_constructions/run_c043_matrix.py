"""
Empirical Matrix Sweep for Challenge C043 (Ramsey & Van der Waerden Lower Bounds).
Evaluates Space Bunny Alpha, LLaMA-3.3-70B, LLaMA-3.1-8B, and GPT-4o.
"""

import json
import sys
from functools import partial
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent
REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "omega_engine_pfp").is_dir() and (p / "omega_engine_woland").is_dir())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from omega_engine_pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.judge_packet.checkers.dual_evaluator import (  # noqa: E402
    evaluate_dual,
)
from omega_engine_pfp.infrastructure.formal_matrix import (  # noqa: E402
    run_model_matrix,
    run_model_matrix_cli,
)

SYSTEM_PROMPT = "You are a formal mathematics solver. Respond ONLY with valid JSON. Do not include markdown ticks."

MODELS = [
    {
        "tier": "SpaceBunny",
        "id": "stealth/space-bunny-alpha",
        "name": "Space Bunny Alpha",
        "cost_per_m_in": 0.0,
        "cost_per_m_out": 0.0,
        "extra_params": {"reasoning": {"effort": "low"}},
        "temperature": 0.1,
    },
    {
        "tier": "70B",
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "LLaMA 3.3 70B Instruct",
        "cost_per_m_in": 0.12,
        "cost_per_m_out": 0.30,
        "extra_params": {},
        "temperature": 0.1,
    },
    {
        "tier": "8B",
        "id": "meta-llama/llama-3.1-8b-instruct",
        "name": "LLaMA 3.1 8B Instruct",
        "cost_per_m_in": 0.055,
        "cost_per_m_out": 0.055,
        "extra_params": {},
        "temperature": 0.1,
    },
]


def load_public_cases():
    ex_dir = PKG_ROOT / "participant_packet" / "examples"
    cases = []
    for p in sorted(ex_dir.glob("*.json")):
        with open(p, "r", encoding="utf-8") as f:
            cases.append(json.load(f))
    return cases


def build_prompt(case: dict, token: str) -> str:
    """Case parameters only, under an opaque per-run token instead of the case ID."""
    ctype = case["type"]
    if ctype == "ramsey2":
        n = case["n"]
        s = case["s"]
        t = case["t"]
        m = n * (n - 1) // 2
        fixed = case.get("fixed", [])
        return (
            f"Solve Two-Colour Ramsey problem R({s},{t},{n}):\n"
            f"- Graph: Complete graph K_{n} with {m} edges.\n"
            f"- Edge order: Lexicographic pairs (0,1), (0,2)...(n-2, n-1).\n"
            f"- Constraint: No monochromatic K_{s} in colour 0, and no monochromatic K_{t} in colour 1.\n"
            f"- Fixed pre-coloured edges: {fixed}\n"
            f'If feasible, output JSON: {{"case_id": "{token}", "status": "SOLVED", "kind": "COLOURING", "colours": "<{m}-char binary string over 0 and 1>"}}\n'
            f'If fixed edges already contain a monochromatic clique, output: {{"case_id": "{token}", "status": "OUT_OF_SCOPE", "witness": {{"reason": "FIXED_COLOURS_CONTAIN_MONO", "structure": [list of vertex indices]}}}}\n'
            f'If provably impossible at or above known Ramsey bound R({s},{t}), output: {{"case_id": "{token}", "status": "OUT_OF_SCOPE", "witness": {{"reason": "PROVABLY_INFEASIBLE_SAT", "proof_type": "DRAT", "drat_proof": ["0"]}}}}\n'
            f'Otherwise if unable to solve within limits: {{"case_id": "{token}", "status": "UNKNOWN", "code": "NOT_FOUND_WITHIN_LIMIT"}}\n'
            f"Respond ONLY with valid JSON."
        )
    elif ctype == "ramsey3":
        n = case["n"]
        m = n * (n - 1) // 2
        fixed = case.get("fixed", [])
        return (
            f"Solve Three-Colour Triangle Ramsey problem on K_{n}:\n"
            f"- Graph: Complete graph K_{n} with {m} edges.\n"
            f"- Edge order: Lexicographic pairs (0,1), (0,2)...(n-2, n-1).\n"
            f"- Constraint: No monochromatic triangle (K_3) in any of colours 0, 1, 2.\n"
            f"- Fixed pre-coloured edges: {fixed}\n"
            f'If feasible, output JSON: {{"case_id": "{token}", "status": "SOLVED", "kind": "COLOURING", "colours": "<{m}-char string over 0, 1, 2>"}}\n'
            f'If fixed edges already contain a monochromatic triangle, output: {{"case_id": "{token}", "status": "OUT_OF_SCOPE", "witness": {{"reason": "FIXED_COLOURS_CONTAIN_MONO", "structure": [v1, v2, v3]}}}}\n'
            f"Respond ONLY with valid JSON."
        )
    elif ctype == "vdw":
        r = case["r"]
        k = case["k"]
        n = case["n"]
        fixed = case.get("fixed", [])
        return (
            f"Solve Van der Waerden problem W({r},{k},{n}):\n"
            f"- Domain: {n} elements indexed 0 to {n - 1}.\n"
            f"- Constraint: No monochromatic {k}-term arithmetic progression in any of {r} colours.\n"
            f"- Fixed pre-coloured elements: {fixed} (pairs of [position, colour])\n"
            f'If feasible, output JSON: {{"case_id": "{token}", "status": "SOLVED", "kind": "COLOURING", "colours": "<{n}-char string over 0..{r - 1}>"}}\n'
            f'If fixed elements already contain a monochromatic AP, output: {{"case_id": "{token}", "status": "OUT_OF_SCOPE", "witness": {{"reason": "FIXED_COLOURS_CONTAIN_MONO", "structure": [list of AP positions]}}}}\n'
            f'If provably impossible at or above known Van der Waerden bound W({r},{k}), output: {{"case_id": "{token}", "status": "OUT_OF_SCOPE", "witness": {{"reason": "PROVABLY_INFEASIBLE_SAT", "proof_type": "DRAT", "drat_proof": ["0"]}}}}\n'
            f'Otherwise if unable to solve within limits: {{"case_id": "{token}", "status": "UNKNOWN", "code": "NOT_FOUND_WITHIN_LIMIT"}}\n'
            f"Respond ONLY with valid JSON."
        )
    return "Solve case. Output JSON."


def evaluate(case: dict, ans: dict) -> tuple[bool, str]:
    """Both judge checkers must accept; an UNKNOWN is an abstention, never a pass."""
    ok, msg, _receipt = evaluate_dual(case, ans)
    return ok, msg


def run_sweep(*, argv=None) -> Path:
    """Exploratory model matrix; writes a new run folder under the intelligence root."""
    runner = run_model_matrix if argv is None else partial(run_model_matrix_cli, argv=argv)
    folder = runner(
        challenge_id="c043",
        models=MODELS,
        cases=load_public_cases(),
        system_prompt=SYSTEM_PROMPT,
        evaluate=evaluate,
        prompt_builder=build_prompt,
        title="The Symbol Game C043 Sweep",
        pause_sec=0.5,
    )
    print(f"Full execution logs written to {folder}")
    return folder


if __name__ == "__main__":
    run_sweep(argv=sys.argv[1:])
