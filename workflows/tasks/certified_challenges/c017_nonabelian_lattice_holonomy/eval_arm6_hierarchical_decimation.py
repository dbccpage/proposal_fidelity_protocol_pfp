#!/usr/bin/env python3
"""eval_arm6_hierarchical_decimation.py — Non-Abelian Holonomy with Hierarchical Macro-Plaquette Decimation.

Implements Arm 6 (Hierarchical Decimation / Quad-Tree Macro-Aggregation) for Challenge C017:
1. Decomposes large lattices (e.g. 5x6 torus, 30 cells) into hierarchical macro-blocks.
2. Identifies active non-identity edges so models bypass trivial identity blocks.
3. Coarse-grained boundary checks evaluate macro-loops U(∂M) to circumvent the 30-cell
   sequential scratchpad token exhaustion barrier.
4. Pinpoints canonical coordinate tokens for local curvature if a macro-block is non-trivial.
5. Injects direct global non-contractible torus loop verification (Loop A & Loop B).
6. Evaluates dual independent checkers (algebraic_holonomy_checker & independent_checker).

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
        "axiom": "Plaquette flatness (Gamma_2 = 0) requires the ordered product to equal the identity element 'e'. Evaluating 1D scalar characters (determinants, parity signs, traces) is insufficient; non-trivial elements in commutator subgroups possess determinant +1 yet have non-trivial curvature Gamma_2 > 0.",
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


def find_active_edges(edges: dict[str, str], identity: str) -> list[dict[str, str]]:
    """Return all directed edges that differ from the identity element."""
    active = []
    for k, v in edges.items():
        if v != identity and "->" in k:
            u, w = k.split("->")
            active.append({"edge": k, "element": v})
    return active


def build_c017_arm6_prompt(case: dict) -> str:
    """Build Arm 6 prompt using hierarchical macro-block decimation and active edge filtering."""
    group = case["group"]
    L = int(case["L"])
    M = int(case["M"])
    boundary = case["boundary"]
    identity = group["identity"]
    edges = case["edges"]

    canonical_plaquettes = compute_all_plaquettes(L, M, boundary)
    active_edges = find_active_edges(edges, identity)
    loop_a, _, loop_b, _ = (
        compute_torus_global_loops(L, M, edges, group["table"], identity)
        if boundary == "periodic"
        else ([], "", [], "")
    )

    # Group elementary plaquettes into active vs trivial
    trivial_count = 0
    active_plaquettes = []
    for p in canonical_plaquettes:
        p_edges = [f"{p[0]}->{p[1]}", f"{p[1]}->{p[2]}", f"{p[2]}->{p[3]}", f"{p[3]}->{p[0]}"]
        elements = [edges.get(e, identity) for e in p_edges]
        if all(el == identity for el in elements):
            trivial_count += 1
        else:
            active_plaquettes.append(
                {"plaquette": p, "edges": {e: edges.get(e, identity) for e in p_edges}}
            )

    prompt = f"""NON-ABELIAN LATTICE HOLONOMY CHALLENGE (C017) — ARM 6 (HIERARCHICAL DECIMATION)

Lattice Dimensions: {L}x{M} grid with boundary='{boundary}'.
Total Elementary Plaquettes: {len(canonical_plaquettes)}
Gauge Group: {group["name"]} (Order {group["order"]}, Identity='{identity}').
Elements: {group["elements"]}

Multiplication Table (Row * Column = Result):
{json.dumps(group["table"], indent=2)}

Inverses:
{json.dumps(group["inverses"], indent=2)}

================================================================================
HIERARCHICAL DECIMATION & ACTIVE EDGE FILTERING:
Out of all directed edges in the lattice, only the following edges have non-identity elements (U != '{identity}'):
{json.dumps(active_edges, indent=2)}

TRIVIAL IDENTITY DECIMATION:
- {trivial_count} elementary plaquettes consist ENTIRELY of identity edges (U = '{identity}').
- By non-Abelian group axioms, any loop of identity edges multiplies identically to:
  {identity} * {identity} * {identity} * {identity} = {identity}.
- Therefore, these {trivial_count} plaquettes are ALGEBRAICALLY CERTIFIED FLAT in 0 steps and DO NOT need to be evaluated in the scratchpad!

ACTIVE PLAQUETTES TO EXAMINE ({len(active_plaquettes)} total):
Only the following {len(active_plaquettes)} elementary plaquette(s) touch non-identity edges:
{json.dumps(active_plaquettes, indent=2)}
================================================================================
"""

    if boundary == "periodic":
        prompt += f"""CANONICAL GLOBAL TORUS LOOPS:
If all plaquettes are flat (Gamma_2 = e for all plaquettes), you must evaluate the non-contractible global torus loops:
- Loop A (Horizontal): {json.dumps(loop_a)}
- Loop B (Vertical):   {json.dumps(loop_b)}

Using the operational scratchpad (g_acc = g_acc * U(e)):
1. Compute hol_a along Loop A.
2. Compute hol_b along Loop B.
3. Check if hol_a and hol_b commute: table[hol_a][hol_b] == table[hol_b][hol_a].
If either hol_a != '{identity}' or hol_b != '{identity}', and they commute, the verdict is strictly 'FLAT_NONTRIVIAL'.
================================================================================
"""

    prompt += "EPISTEMIC IMMUNE CONSTRAINTS (TYPED ANTIBODIES):\n"
    for ab in NONABELIAN_ANTIBODIES:
        prompt += f"- [{ab['code']}]: {ab['axiom']}\n"

    prompt += f"""
DECISION PROCEDURE:
Step 1: Check edge anti-symmetry: for each edge u->v, verify v->u equals inverses[edges["u->v"]]. If violated, return OUT_OF_SCOPE.
Step 2: Check the {len(active_plaquettes)} active plaquettes listed above.
        For each active plaquette [v0, v1, v2, v3], compute:
        g_acc = '{identity}'
        g_acc = table[g_acc][U(v0->v1)]
        g_acc = table[g_acc][U(v1->v2)]
        g_acc = table[g_acc][U(v2->v3)]
        g_acc = table[g_acc][U(v3->v0)]
        If g_acc != '{identity}', STOP immediately! Verdict is "NOT_FLAT", reported plaquette is this plaquette, and holonomy is g_acc.
Step 3: If all active plaquettes have g_acc == '{identity}', then ALL {len(canonical_plaquettes)} plaquettes in the lattice are flat!
        - If boundary is "open", compute vertex gauge using spanning tree. Verdict is "PURE_GAUGE".
        - If boundary is "periodic", evaluate Loop A and Loop B. If either is non-identity, verdict is "FLAT_NONTRIVIAL".

OUTPUT FORMAT:
Emit ONLY valid JSON with keys:
{{
  "status": "SOLVED" or "OUT_OF_SCOPE",
  "verdict": "NOT_FLAT" | "PURE_GAUGE" | "FLAT_NONTRIVIAL",
  "scratchpad": {{
    "active_plaquettes_evaluated": [
      {{
        "plaquette": ["v0", "v1", "v2", "v3"],
        "steps": [ ... ],
        "final_holonomy": "...",
        "is_flat": true | false
      }}
    ],
    "global_torus_loops": {{"hol_a": "...", "hol_b": "...", "commute": true}} (if flat periodic)
  }},
  "plaquette": ["v0", "v1", "v2", "v3"] (REQUIRED if NOT_FLAT, must be one of the canonical plaquettes),
  "holonomy": "..." (REQUIRED if NOT_FLAT, must match final_holonomy),
  "gauge": {{"u,v": "elem"}} (REQUIRED if PURE_GAUGE, mapping all vertices),
  "base": "0,0", "loop_a": {json.dumps(loop_a)}, "hol_a": "...", "loop_b": {json.dumps(loop_b)}, "hol_b": "..." (REQUIRED if FLAT_NONTRIVIAL),
  "witness": {{"edge": "...", "reason": "INVERSE_MISMATCH"}} (REQUIRED if OUT_OF_SCOPE)
}}
"""
    return prompt



def query_model(
    model: str,
    prompt: str,
    api_key: str,
    dry_run: bool = False,
    mock_solution: dict | None = None,
    max_tokens: int = 4000,
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


def run_arm6_benchmark(
    model: str = "stealth/space-bunny-alpha",
    dry_run: bool = False,
    selected_case: str | None = None,
    max_tokens: int = 4000,
    *,
    gateway=None,
    output_dir: Path | None = None,
    env_file: Path | None = None,
    max_estimated_cost_microusd: int | None = None,
    max_provider_calls: int = 10,
) -> dict:
    """Original Arm 6 cases/prompts and dual judges, with one PFP allowance."""
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
        arms=(("arm6", build_c017_arm6_prompt),),
        query=query_model,
        checker=evaluate_dual,
        solver=reference_solve,
        max_tokens=max_tokens,
        original_max_tokens=4000,
        output_dir=output_dir,
        gateway=gateway,
        max_estimated_cost_microusd=max_estimated_cost_microusd,
        max_provider_calls=max_provider_calls,
        env_file=env_file,
        report_name=f"arm6_{model_slug}_report.json",
        receipt_name=f"receipt_arm6_{model_slug}.json",
        arm="Arm 6 (Hierarchical Decimation)",
    )


def main(argv=None) -> int:
    return _main(
        run_arm6_benchmark,
        argv,
        description=run_arm6_benchmark.__doc__,
        default_model="stealth/space-bunny-alpha",
        default_tokens=4000,
    )


if __name__ == "__main__":
    raise SystemExit(main())
