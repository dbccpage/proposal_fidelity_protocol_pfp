#!/usr/bin/env python3
"""eval_arm5_hybrid.py — Non-Abelian Holonomy (Gamma_2 > 0) Arm 5 (Full Hybrid) Evaluation.

Implements Arm 5 (Full Hybrid) for Challenge C017:
1. Pins down canonical plaquette coordinate tokens directly in the prompt grammar.
2. Injects mandatory step-by-step path-multiplication scratchpads (g_acc = g_acc * U(e)).
3. Injects spanning tree BFS gauge propagation rules for pure-gauge states.
4. Integrates the 4 non-Abelian typed epistemic antibodies.
5. Evaluates live models (LLaMA-3.3-70B) against dual independent checkers.

AuthorityEffect: None.
Protocol: SG-CP v1 (Challenge C017).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "pfp").is_dir() and (parent / "adversary").is_dir()
    ),
    None,
)
if REPO_ROOT is not None and str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from c017_nonabelian_lattice_holonomy.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c017_nonabelian_lattice_holonomy.reference_solver.lattice_holonomy import (
    compute_all_plaquettes,
    compute_torus_global_loops,
)

from c017_nonabelian_lattice_holonomy.eval_epistemic_immune_transfer import (
    _main,
    _model_slug,
    _query,
    _run_cases,
)
from c017_nonabelian_lattice_holonomy.reference_solver.solver import (
    solve as reference_solve,
)

# Non-Abelian Typed Antibodies
NONABELIAN_ANTIBODIES = [
    {
        "code": "ANTI_ORDER_REVERSAL",
        "axiom": "Path holonomy must multiply edges strictly along traversal direction: U(P) = U_{01} * U_{12} * U_{23} * U_{30}. In non-Abelian groups, A * B != B * A; reverse-order multiplication causes false flatness certifications.",
    },
    {
        "code": "ANTI_ABELIANIZATION_TRAP",
        "axiom": "Plaquette flatness (Gamma_2 = 0) requires the ordered product to equal the identity element 'e'. Evaluating 1D scalar characters (determinants, parity signs, traces) is insufficient; non-trivial elements in commutator subgroups (e.g., r^2 in S_3, -1 in Q_8) possess determinant +1 yet have non-trivial curvature Gamma_2 > 0.",
    },
    {
        "code": "ANTI_TORUS_TRIVIALITY_CONFUSION",
        "axiom": "On periodic boundaries (Torus T^2), zero local curvature on all plaquettes does NOT imply pure gauge. You must evaluate the non-contractible cycles A and B across periodic boundaries; if either holonomy is non-identity, the connection is FLAT_NONTRIVIAL.",
    },
    {
        "code": "ANTI_INVERSE_MISMATCH_BYPASS",
        "axiom": "Every oriented edge u->v with element U must have v->u with element U^{-1}. If any edge violates this, the input is OUT_OF_SCOPE with reason INVERSE_MISMATCH.",
    },
]


def build_c017_arm5_prompt(case: dict) -> str:
    """Build structured Arm 5 (Full Hybrid) prompt for non-Abelian lattice holonomy deduction."""
    group = case["group"]
    L = int(case["L"])
    M = int(case["M"])
    boundary = case["boundary"]
    identity = group["identity"]

    # Compute canonical plaquettes and loops
    canonical_plaquettes = compute_all_plaquettes(L, M, boundary)
    loop_a, _, loop_b, _ = (
        compute_torus_global_loops(L, M, case["edges"], group["table"], identity)
        if boundary == "periodic"
        else ([], "", [], "")
    )

    prompt = f"""NON-ABELIAN LATTICE HOLONOMY CHALLENGE (C017) — ARM 5 FULL HYBRID

Lattice Dimensions: {L}x{M} square grid with boundary='{boundary}'.
Gauge Group: {group["name"]} (Order {group["order"]}, Identity='{identity}').
Group Elements: {group["elements"]}

Multiplication Table (Row * Column = Result):
{json.dumps(group["table"], indent=2)}

Group Inverses:
{json.dumps(group["inverses"], indent=2)}

Edge Connections (Directed edge u->v has element U(u->v)):
{json.dumps(case["edges"], indent=2)}

================================================================================
CANONICAL PLAQUETTE COORDINATE TOKENS (STRICT CONVENTION):
The dual evaluator requires elementary plaquettes to be reported in exact canonical order:
P(r, c) = ["{"{"}r{"}"},{"{"}c{"}"}", "{"{"}r+1{"}"},{"{"}c{"}"}", "{"{"}r+1{"}"},{"{"}c+1{"}"}", "{"{"}r{"}"},{"{"}c+1{"}"}"]

Here is the complete list of valid canonical plaquettes for this {L}x{M} lattice:
{json.dumps(canonical_plaquettes, indent=2)}

Any reported plaquette MUST be an exact match to one of the arrays above!
DO NOT use counter-clockwise indexing (e.g. ['0,0', '0,1', '1,1', '1,0']) or reversed traversal.

The 4 directed boundary edges for plaquette [v0, v1, v2, v3] are strictly:
  Edge 1: v0 -> v1
  Edge 2: v1 -> v2
  Edge 3: v2 -> v3
  Edge 4: v3 -> v0
================================================================================
OPERATIONAL PATH-MULTIPLICATION SCRATCHPAD RULE (g_acc = g_acc * U(e)):
To evaluate the holonomy along any cycle [v0, v1, ..., vk]:
1. Start with accumulator: g_acc = "{identity}"
2. For each consecutive directed edge u->v in sequence:
   Look up element U = edges["u->v"].
   Look up row g_acc, column U directly in the provided Multiplication Table:
   g_acc_next = table[g_acc][U]
   g_acc = g_acc_next
   DO NOT guess products mentally; look up the exact cell in the table!
3. The final g_acc after the last edge is the exact holonomy.
================================================================================
"""

    if boundary == "periodic":
        prompt += f"""CANONICAL GLOBAL TORUS LOOPS:
If all plaquettes are flat (Gamma_2 = 0), you must evaluate global non-contractible loops:
- Loop A (Horizontal): {json.dumps(loop_a)}
- Loop B (Vertical):   {json.dumps(loop_b)}
Evaluate hol_a along Loop A and hol_b along Loop B using g_acc = g_acc * U(e).
If hol_a != '{identity}' or hol_b != '{identity}', verdict is 'FLAT_NONTRIVIAL'.
================================================================================
"""

    prompt += "EPISTEMIC IMMUNE CONSTRAINTS (TYPED ANTIBODIES):\n"
    for ab in NONABELIAN_ANTIBODIES:
        prompt += f"- [{ab['code']}]: {ab['axiom']}\n"

    prompt += """
DECISION PROCEDURE:
Step 1: Check edge anti-symmetry: for each edge u->v, verify that v->u exists and equals inverses[edges["u->v"]]. If violated, return OUT_OF_SCOPE.
Step 2: Check each canonical plaquette one by one in order using the operational scratchpad (g_acc = g_acc * U(e)).
        If any plaquette has holonomy != identity, STOP immediately! Verdict is "NOT_FLAT".
Step 3: If all plaquettes are flat:
        - If boundary is "open", compute gauge for all vertices using the spanning tree algorithm. Verdict is "PURE_GAUGE".
        - If boundary is "periodic", evaluate Loop A and Loop B. Verdict is "FLAT_NONTRIVIAL".

OUTPUT FORMAT:
Emit ONLY valid JSON with keys:
{
  "status": "SOLVED" or "OUT_OF_SCOPE",
  "verdict": "NOT_FLAT" | "PURE_GAUGE" | "FLAT_NONTRIVIAL",
  "scratchpad": {
    "evaluated_plaquettes": [
      {
        "plaquette": ["v0", "v1", "v2", "v3"],
        "steps": [
          {"edge": "v0->v1", "U": "...", "g_in": "...", "g_out": "..."},
          {"edge": "v1->v2", "U": "...", "g_in": "...", "g_out": "..."},
          {"edge": "v2->v3", "U": "...", "g_in": "...", "g_out": "..."},
          {"edge": "v3->v0", "U": "...", "g_in": "...", "g_out": "..."}
        ],
        "final_holonomy": "...",
        "is_flat": true | false
      }
    ],
    "tree_gauge_propagation": {"0,0": "e", ...} (if flat open),
    "global_torus_loops": {"hol_a": "...", "hol_b": "..."} (if flat periodic)
  },
  "plaquette": ["v0", "v1", "v2", "v3"] (REQUIRED if NOT_FLAT, must be one of the listed canonical plaquettes),
  "holonomy": "..." (REQUIRED if NOT_FLAT, must match final_holonomy),
  "gauge": {"u,v": "elem"} (REQUIRED if PURE_GAUGE, mapping all vertices),
  "base": "0,0", "loop_a": [...], "hol_a": "...", "loop_b": [...], "hol_b": "..." (REQUIRED if FLAT_NONTRIVIAL),
  "witness": {"edge": "...", "reason": "INVERSE_MISMATCH"} (REQUIRED if OUT_OF_SCOPE)
}
"""
    return prompt



def query_model(
    model: str,
    prompt: str,
    api_key: str,
    dry_run: bool = False,
    mock_solution: dict | None = None,
    max_tokens: int = 6000,
    *,
    gateway=None,
    task_id=None,
    attempt_id=None,
) -> tuple[dict, dict]:
    """Original decoding bound through the shared accounted PFP owner."""
    return _query(
        model,
        prompt,
        dry_run=dry_run,
        mock_solution=mock_solution,
        max_tokens=max_tokens,
        temperature=0.05,
        gateway=gateway,
        task_id=task_id,
        attempt_id=attempt_id,
    )


def run_arm5_benchmark(
    model: str = "meta-llama/llama-3.3-70b-instruct",
    dry_run: bool = False,
    selected_case: str | None = None,
    max_tokens: int = 6000,
    *,
    gateway=None,
    output_dir: Path | None = None,
    env_file: Path | None = None,
    max_estimated_cost_microusd: int | None = None,
    max_provider_calls: int = 10,
) -> dict:
    """Original Arm 5 cases/prompts and dual judges, with one PFP allowance."""
    c017_cases_dir = Path(__file__).parent / "judge_packet" / "cases"
    all_test_cases = [
        ("pois_01_s3_commutator_trap", c017_cases_dir / "poisoned" / "pois_01.json"),
        ("base_01_s3_open_nonflat", c017_cases_dir / "base" / "base_01.json"),
        ("base_02_s3_open_puregauge", c017_cases_dir / "base" / "base_02.json"),
        ("base_03_s3_periodic_torus", c017_cases_dir / "base" / "base_03.json"),
        ("base_13_q8_open_nonflat", c017_cases_dir / "base" / "base_13.json"),
    ]
    test_cases = [c for c in all_test_cases if selected_case is None or selected_case in c[0]]
    model_slug = _model_slug(model)
    return _run_cases(
        model=model,
        dry_run=dry_run,
        case_files=test_cases,
        arms=(("arm5", build_c017_arm5_prompt),),
        query=query_model,
        checker=evaluate_dual,
        solver=reference_solve,
        max_tokens=max_tokens,
        original_max_tokens=6000,
        output_dir=output_dir,
        gateway=gateway,
        max_estimated_cost_microusd=max_estimated_cost_microusd,
        max_provider_calls=max_provider_calls,
        env_file=env_file,
        report_name=f"arm5_{model_slug}_report.json",
        receipt_name=f"receipt_arm5_{model_slug}.json",
        arm="Arm 5 (Full Hybrid)",
    )


def main(argv=None) -> int:
    return _main(
        run_arm5_benchmark,
        argv,
        description=run_arm5_benchmark.__doc__,
        default_model="meta-llama/llama-3.3-70b-instruct",
        default_tokens=6000,
    )


if __name__ == "__main__":
    raise SystemExit(main())
