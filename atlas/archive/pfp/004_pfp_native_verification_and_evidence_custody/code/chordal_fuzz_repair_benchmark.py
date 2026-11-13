"""
100-Trial Chordal Projection Fuzz Repair Benchmark — Paper 032 (PO-032), Section 7.2.

Replays a deterministic sequence of seeds over random 2-tree (chordal) constraint
graphs with |V| in [5, 10] and measures the atomic projection-replacement repair:

  1. Build a random 2-tree G. A 2-tree is chordal and has exactly 2|V| - 3 edges
     and cycle rank |E| - |V| + 1 = |V| - 2 (every edge lies on a triangle).
  2. Assign integer edge claims. On a graph with cycles a generic integer claim
     is NOT a coboundary, so the primary obstruction
         Phi_1(claim) = min_{f in Q^V} || claim - delta f ||_{1}
     is strictly positive: there is a real holonomy defect to repair. (If a
     random draw happens to be an exact coboundary, a single chord claim is
     bumped by 1 to guarantee a nonzero defect; the count of such bumps is
     reported.)
  3. Apply ONE atomic projection-replacement (relational) CUT: the host computes
     the exact rational optimal gauge f* (via the totally unimodular LP of
     scaling_benchmark_v20) and replaces the claims with delta f* -- the nearest
     coboundary in the weighted L1 sense. Because delta f* is a coboundary,
     Phi_1(delta f*) = 0 exactly.
  4. The L1SymbolGameGovernor is driven through the same relational CUT to confirm
     that its monotonic-descent admission gate accepts the projection-replacement
     as an ExactRepair (defect_before > 0, defect_after = 0) without contaminating
     state.

Every quantity is computed with exact rational arithmetic (fractions.Fraction);
the benchmark performs no floating-point decisions. The Phi_1 values reported are
the genuine solver outputs, not asserted constants; the receipt records them per
trial together with a self-audit SHA-256 over the canonical results.

This measures deterministic host repair of a declared holonomy defect on chordal
graphs (claim PO032-C44). It does not measure a language model's ability to
discover the repairing CUT.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from .l1_symbol_game_governor import (
        Cochain1,
        ConstraintGraph,
        Edge,
        L1SymbolGameGovernor,
    )
    from .scaling_benchmark_v20 import solve_phi1_lp_exact_basis
except (ImportError, ValueError):
    from l1_symbol_game_governor import (
        Cochain1,
        ConstraintGraph,
        Edge,
        L1SymbolGameGovernor,
    )
    from scaling_benchmark_v20 import solve_phi1_lp_exact_basis


def build_2_tree(n: int, rng: random.Random) -> ConstraintGraph:
    """
    Builds a random 2-tree on ``n`` vertices (n >= 3).

    Construction: start from the triangle on v0, v1, v2; repeatedly pick an
    existing edge (a, b) and attach a new vertex adjacent to both a and b,
    forming a new triangle. All edges are oriented from the lower to the higher
    vertex index, so every edge is irreflexive. The result is chordal with
    exactly 2n - 3 edges.
    """
    if n < 3:
        raise ValueError(f"2-tree requires n >= 3, got {n}.")
    verts = [f"v{i:02d}" for i in range(n)]
    edges: List[Edge] = [
        Edge(verts[0], verts[1]),
        Edge(verts[0], verts[2]),
        Edge(verts[1], verts[2]),
    ]
    open_edges: List[Tuple[int, int]] = [(0, 1), (0, 2), (1, 2)]
    for k in range(3, n):
        a, b = rng.choice(open_edges)
        edges.append(Edge(verts[a], verts[k]))
        edges.append(Edge(verts[b], verts[k]))
        open_edges.append((a, k))
        open_edges.append((b, k))
    return ConstraintGraph(vertices=tuple(verts), edges=tuple(edges))


def coboundary_claims(
    graph: ConstraintGraph,
    gauge: Dict[str, Fraction],
) -> Dict[Tuple[str, str], Fraction]:
    """The 1-cochain delta f for a vertex potential f: (delta f)(u, v) = f(v) - f(u)."""
    return {
        e.key: gauge.get(e.v, Fraction(0)) - gauge.get(e.u, Fraction(0))
        for e in graph.edges
    }


@dataclass(frozen=True)
class ChordalTrialResult:
    """Outcome of a single deterministic 2-tree repair trial."""
    seed: int
    num_vertices: int
    num_edges: int
    cycle_rank: int
    phi1_before: str          # exact rational as canonical string
    phi1_after: str           # exact rational as canonical string ("0")
    defect_present: bool      # phi1_before > 0
    bumped: bool              # a chord was bumped to force a defect
    single_cut: bool          # zero defect reached after exactly one CUT
    governor_admitted: Optional[bool]
    governor_status: Optional[str]


def run_trial(seed: int, with_governor: bool = True) -> ChordalTrialResult:
    """
    Runs one deterministic trial: build a 2-tree, assign claims with a guaranteed
    holonomy defect, then repair to zero defect with a single projection-replacement
    CUT. Returns the exact solver outputs.
    """
    rng = random.Random(seed)
    n = 5 + (seed % 6)  # spread |V| deterministically over [5, 10]
    graph = build_2_tree(n, rng)

    claims_dict: Dict[Tuple[str, str], Fraction] = {
        e.key: Fraction(rng.randint(-5, 5)) for e in graph.edges
    }

    phi1_before, _ = solve_phi1_lp_exact_basis(graph, Cochain1(values=dict(claims_dict)))

    # Guarantee a genuine defect to repair. Every edge of a 2-tree lies on a
    # triangle, so bumping any edge introduces nonzero cycle holonomy.
    bumped = False
    if phi1_before == 0:
        chord = graph.edges[-1].key
        claims_dict[chord] = claims_dict[chord] + Fraction(1)
        phi1_before, _ = solve_phi1_lp_exact_basis(graph, Cochain1(values=dict(claims_dict)))
        bumped = True

    # Atomic projection-replacement: replace the claims with the nearest coboundary.
    _, gauge = solve_phi1_lp_exact_basis(graph, Cochain1(values=dict(claims_dict)))
    repaired_claims = coboundary_claims(graph, gauge)
    phi1_after, _ = solve_phi1_lp_exact_basis(graph, Cochain1(values=repaired_claims))

    governor_admitted: Optional[bool] = None
    governor_status: Optional[str] = None
    if with_governor:
        gov = L1SymbolGameGovernor(graph)
        for e in graph.edges:
            gov.step_assert(e.u, e.v, claims_dict[e.key])
        verdict = gov.step_cut(proposed_claims=repaired_claims)
        governor_admitted = verdict.admitted
        governor_status = verdict.status
        # The governor's independent (spanning-tree) evaluation must agree exactly.
        assert verdict.defect_before == phi1_before, (
            f"governor/LP disagree on phi1_before: {verdict.defect_before} vs {phi1_before}"
        )
        assert verdict.defect_after == phi1_after == Fraction(0), (
            f"governor/LP disagree on phi1_after: {verdict.defect_after} vs {phi1_after}"
        )

    return ChordalTrialResult(
        seed=seed,
        num_vertices=n,
        num_edges=len(graph.edges),
        cycle_rank=len(graph.edges) - n + 1,
        phi1_before=str(phi1_before),
        phi1_after=str(phi1_after),
        defect_present=phi1_before > 0,
        bumped=bumped,
        single_cut=(phi1_after == 0),
        governor_admitted=governor_admitted,
        governor_status=governor_status,
    )


def run_chordal_fuzz_benchmark(
    n_trials: int = 100,
    seed_base: int = 0,
    with_governor: bool = True,
) -> Dict[str, Any]:
    """
    Runs ``n_trials`` deterministic 2-tree repair trials and aggregates the result.
    """
    results = [run_trial(seed_base + i, with_governor=with_governor) for i in range(n_trials)]

    phi_before_vals = [Fraction(r.phi1_before) for r in results]
    n_repaired = sum(1 for r in results if r.single_cut)
    n_defect = sum(1 for r in results if r.defect_present)
    n_bumped = sum(1 for r in results if r.bumped)
    all_governor_exact = all(
        (r.governor_admitted is True and r.governor_status == "ExactRepair")
        for r in results
    ) if with_governor else None

    summary: Dict[str, Any] = {
        "benchmark_name": "100-Trial Chordal Projection Fuzz Repair Benchmark",
        "paper_section": "PO-032 Section 7.2",
        "n_trials": n_trials,
        "vertex_range": [min(r.num_vertices for r in results),
                         max(r.num_vertices for r in results)],
        "solver": "exact_rational_lp_totally_unimodular",
        "convergence_rate": n_repaired / n_trials,
        "atomic_projection_replacement_rate": n_repaired / n_trials,
        "trials_with_defect": n_defect,
        "trials_bumped_to_force_defect": n_bumped,
        "mean_phi1_before": str(sum(phi_before_vals, Fraction(0)) / n_trials),
        "median_phi1_before": str(sorted(phi_before_vals)[len(phi_before_vals) // 2]),
        "max_phi1_before": str(max(phi_before_vals)),
        "governor_all_exact_repair": all_governor_exact,
        "results": [asdict(r) for r in results],
    }
    return summary


def _integrity_digest(summary: Dict[str, Any]) -> str:
    """Deterministic SHA-256 over the per-trial results (timestamp excluded)."""
    canonical = json.dumps(summary["results"], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> None:
    t0 = time.perf_counter()
    summary = run_chordal_fuzz_benchmark(n_trials=100, with_governor=True)
    elapsed = time.perf_counter() - t0

    summary["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary["wall_time_sec"] = round(elapsed, 3)
    summary["integrity_sha256"] = _integrity_digest(summary)

    print("100-Trial Chordal Projection Fuzz Repair Benchmark (Paper 032 Section 7.2)")
    print(f"  trials                       : {summary['n_trials']}")
    print(f"  vertex range                 : |V| in {summary['vertex_range']}")
    print(f"  convergence rate             : {summary['convergence_rate'] * 100:.1f}%")
    print(f"  atomic projection-replacement: {summary['atomic_projection_replacement_rate'] * 100:.1f}%")
    print(f"  trials with genuine defect   : {summary['trials_with_defect']}/{summary['n_trials']}")
    print(f"  governor all ExactRepair     : {summary['governor_all_exact_repair']}")
    print(f"  mean/median/max Phi1 before  : {summary['mean_phi1_before']} / "
          f"{summary['median_phi1_before']} / {summary['max_phi1_before']}")
    print(f"  wall time                    : {summary['wall_time_sec']} s")

    receipt_path = Path(__file__).parent / "chordal_fuzz_repair_benchmark_receipt.json"
    receipt_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nAudit receipt saved to: {receipt_path.resolve()}")


__all__ = [
    "build_2_tree",
    "coboundary_claims",
    "ChordalTrialResult",
    "run_trial",
    "run_chordal_fuzz_benchmark",
]


if __name__ == "__main__":
    main()
