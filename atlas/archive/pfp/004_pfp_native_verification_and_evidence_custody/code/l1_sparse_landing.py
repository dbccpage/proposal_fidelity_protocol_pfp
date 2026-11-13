"""
Weighted Null-Space Property and Unique Sparse Landing — Paper 032 (PO-032), Section 5.4.

Exact rational verification of the finite uniqueness/sparsity account consolidated from
legacy Paper 040i (`040i_sparse_landing_l1_repair_uniqueness`):

  * The landing value is the weighted L1 obstruction mass
        Phi_1([W_E]) = min_{c0} || W_E - delta c0 ||_{1,omega}
    over the declared finite complex; the optimal residual r* = W_E - delta c0* is
    computed exactly by the totally unimodular LP of scaling_benchmark_v20.

  * Weighted null-space property (Def 5.2): a support S has the weighted NSP for the
    repair gauge W = im(delta) if  sum_{e in S} omega_e |w_e| < sum_{e not in S} omega_e |w_e|
    for every nonzero coboundary w in W.

  * Unique sparse landing (Thm 5.3 / Prop 5.5): a strict complementary dual g in the
    cycle space (W^perp = ker(partial_1)) with g_e = omega_e sign(r*_e) on S,
    strict |g_e| < omega_e off S, and W cap R^S = {0}, certifies that r* is the unique
    minimizer. NSP_S implies these conditions; this module builds the dual certificate
    exactly over Q.

  * Sparsity bound (Thm 5.4): |supp(r*)| <= dim(Q^1) = cycle rank beta_1 = |E| - |V| + c.

All arithmetic is exact (fractions.Fraction); no floating-point decision is taken. The
module verifies scoring geometry on the declared complex; it does not adjudicate semantic
truth and makes no claim about a language model's internal representations (see §2.4, §11).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

try:
    from .l1_symbol_game_governor import ConstraintGraph, Edge
    from .scaling_benchmark_v20 import Cochain1, solve_phi1_lp_exact_basis
except (ImportError, ValueError):
    from l1_symbol_game_governor import Cochain1, ConstraintGraph, Edge
    from scaling_benchmark_v20 import solve_phi1_lp_exact_basis


# ---------------------------------------------------------------------------
# Exact rational linear algebra (Gaussian elimination over Q)
# ---------------------------------------------------------------------------

def _rref(rows: List[List[Fraction]]) -> Tuple[List[List[Fraction]], List[int]]:
    """Reduced row echelon form over Q. Returns (rref_rows, pivot_columns)."""
    mat = [list(r) for r in rows]
    if not mat:
        return mat, []
    n_cols = len(mat[0])
    pivots: List[int] = []
    pivot_row = 0
    for col in range(n_cols):
        sel = None
        for r in range(pivot_row, len(mat)):
            if mat[r][col] != 0:
                sel = r
                break
        if sel is None:
            continue
        mat[pivot_row], mat[sel] = mat[sel], mat[pivot_row]
        piv = mat[pivot_row][col]
        mat[pivot_row] = [x / piv for x in mat[pivot_row]]
        for r in range(len(mat)):
            if r != pivot_row and mat[r][col] != 0:
                factor = mat[r][col]
                mat[r] = [a - factor * b for a, b in zip(mat[r], mat[pivot_row])]
        pivots.append(col)
        pivot_row += 1
        if pivot_row == len(mat):
            break
    return mat, pivots


def null_space(rows: List[List[Fraction]], n_cols: int) -> List[List[Fraction]]:
    """Exact basis of the right null space {x : A x = 0} of the matrix given by `rows`."""
    if not rows:
        return [[Fraction(1) if j == i else Fraction(0) for j in range(n_cols)]
                for i in range(n_cols)]
    rref, pivots = _rref(rows)
    pivot_set = set(pivots)
    free_cols = [c for c in range(n_cols) if c not in pivot_set]
    basis: List[List[Fraction]] = []
    for free in free_cols:
        vec = [Fraction(0)] * n_cols
        vec[free] = Fraction(1)
        for r, pc in enumerate(pivots):
            vec[pc] = -rref[r][free]
        basis.append(vec)
    return basis


def solve_linear(A: List[List[Fraction]], b: List[Fraction]) -> Optional[List[Fraction]]:
    """One exact solution x of A x = b, or None if inconsistent. A is m x n."""
    if not A:
        return [] if all(v == 0 for v in b) else None
    n = len(A[0])
    aug = [list(A[i]) + [b[i]] for i in range(len(A))]
    rref, pivots = _rref(aug)
    # Inconsistent if a pivot is in the augmented (last) column.
    if n in pivots:
        return None
    x = [Fraction(0)] * n
    for r, pc in enumerate(pivots):
        if pc < n:
            x[pc] = rref[r][n]
    return x


# ---------------------------------------------------------------------------
# Graph operators
# ---------------------------------------------------------------------------

def incidence_rows(graph: ConstraintGraph) -> List[List[Fraction]]:
    """Node-edge incidence matrix partial_1 (|V| x |E|): +1 target, -1 source, 0 else."""
    v_index = {v: i for i, v in enumerate(graph.vertices)}
    rows = [[Fraction(0)] * len(graph.edges) for _ in graph.vertices]
    for j, e in enumerate(graph.edges):
        rows[v_index[e.v]][j] += Fraction(1)
        rows[v_index[e.u]][j] += Fraction(-1)
    return rows


def cycle_space_basis(graph: ConstraintGraph) -> List[List[Fraction]]:
    """Basis of the cycle space W^perp = ker(partial_1) (exact)."""
    return null_space(incidence_rows(graph), len(graph.edges))


def edge_weights(graph: ConstraintGraph) -> List[int]:
    return [e.weight for e in graph.edges]


def residual_from_gauge(graph: ConstraintGraph, target: Dict[Tuple[str, str], Fraction],
                        gauge: Dict[str, Fraction]) -> List[Fraction]:
    """r_e = W_E(e) - (delta gauge)(e) = W_E(e) - (gauge[v] - gauge[u])."""
    out: List[Fraction] = []
    for e in graph.edges:
        claim = target.get(e.key, Fraction(0))
        out.append(claim - (gauge.get(e.v, Fraction(0)) - gauge.get(e.u, Fraction(0))))
    return out


# ---------------------------------------------------------------------------
# Landing and uniqueness certification
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LandingCertificate:
    """Exact certificate for the weighted L1 landing on a declared complex."""
    phi1: Fraction
    residual: List[Fraction]
    support: List[int]
    sparsity: int
    cycle_rank: int
    sparsity_bound_ok: bool
    unique: bool
    dual_witness: Optional[List[Fraction]]
    reason: str


def l1_landing(graph: ConstraintGraph,
               target: Dict[Tuple[str, str], Fraction]) -> Tuple[Fraction, Dict[str, Fraction]]:
    """Exact (Phi_1, optimal gauge c0*) via the totally unimodular LP."""
    return solve_phi1_lp_exact_basis(graph, Cochain1(values=dict(target)))


def certify_unique_landing(graph: ConstraintGraph,
                           target: Dict[Tuple[str, str], Fraction]) -> LandingCertificate:
    """
    Computes the exact optimal residual and applies the Proposition 5.5 strict
    complementary-dual test to certify uniqueness of the ℓ1 landing.
    """
    phi1, gauge = l1_landing(graph, target)
    residual = residual_from_gauge(graph, target, gauge)
    weights = edge_weights(graph)
    support = [j for j, r in enumerate(residual) if r != 0]
    sparsity = len(support)

    n_components = len(graph.connected_components())
    cycle_rank = len(graph.edges) - len(graph.vertices) + n_components
    sparsity_bound_ok = sparsity <= cycle_rank

    # Prop 5.5 dual: find g in the cycle space (W^perp) with g_e = omega_e * sign(r*_e)
    # on S. Cycle space is spanned by `basis`; solve for coefficients mu.
    basis = cycle_space_basis(graph)
    unique = False
    dual_witness: Optional[List[Fraction]] = None
    reason = ""

    if not support:
        # r* = 0 is the exact landing on Zero; it is the unique minimizer of a norm.
        unique = True
        reason = "exact landing on Zero (Phi_1 = 0); r* = 0 is the unique minimizer."
    elif not basis:
        # No cycles: the graph is a forest, every claim is a coboundary, r* = 0 handled above.
        unique = True
        reason = "acyclic carrier: repair gauge is all of C^1, landing is unique."
    else:
        # Constraints on S: sum_k mu_k * basis[k][e] = omega_e * sign(r*_e)  for e in S.
        A = [[basis[k][e] for k in range(len(basis))] for e in support]
        b = [Fraction(weights[e] * (1 if residual[e] > 0 else -1)) for e in support]
        mu = solve_linear(A, b)
        if mu is None:
            reason = ("no complementary dual on the support (NSP fails); "
                      "landing not certified unique.")
        else:
            g = [sum((mu[k] * basis[k][e] for k in range(len(basis))), Fraction(0))
                 for e in range(len(graph.edges))]
            # Strict slack off S: |g_e| < omega_e for e not in S.
            off_support = [e for e in range(len(graph.edges)) if e not in set(support)]
            strict_ok = all(abs(g[e]) < weights[e] for e in off_support)
            # W cap R^S = {0}: no nonzero coboundary supported within S.
            trivial_intersection = _coboundary_support_trivial(graph, set(support))
            if strict_ok and trivial_intersection:
                unique = True
                dual_witness = g
                reason = ("strict complementary dual in cycle space with "
                          "W ∩ R^S = {0}: unique landing (Prop 5.5).")
            elif not strict_ok:
                reason = ("dual bound not strict off the support (NSP fails); "
                          "landing not certified unique.")
            else:
                reason = "nontrivial coboundary supported within S; not certified unique."

    return LandingCertificate(
        phi1=phi1,
        residual=residual,
        support=support,
        sparsity=sparsity,
        cycle_rank=cycle_rank,
        sparsity_bound_ok=sparsity_bound_ok,
        unique=unique,
        dual_witness=dual_witness,
        reason=reason,
    )


def _coboundary_support_trivial(graph: ConstraintGraph, support: set) -> bool:
    """True iff the only coboundary delta c0 supported within `support` is zero."""
    # delta c0 (e) = 0 for every edge e NOT in support. Solve for c0 up to the constant
    # gauge; W ∩ R^S = {0} iff those equations force delta c0 = 0 on S as well, i.e. the
    # off-support edges connect every vertex into a single class.
    parent = {v: v for v in graph.vertices}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for j, e in enumerate(graph.edges):
        if j not in support:
            ru, rv = find(e.u), find(e.v)
            if ru != rv:
                parent[ru] = rv
    # If all vertices share one class, every coboundary is 0 off-support => 0 on-support too.
    roots = {find(v) for v in graph.vertices}
    return len(roots) == 1


def weighted_l1_cost(residual: Sequence[Fraction], weights: Sequence[int]) -> Fraction:
    return sum((Fraction(w) * abs(r) for r, w in zip(residual, weights)), Fraction(0))


# ---------------------------------------------------------------------------
# Canonical 3-cycle worked example (Paper 032 §5.4)
# ---------------------------------------------------------------------------

def three_cycle(weights: Tuple[int, int, int]) -> ConstraintGraph:
    """Directed 3-cycle 0->1->2->0 with the given edge weights (core_0, core_1, core_2)."""
    w0, w1, w2 = weights
    return ConstraintGraph(
        vertices=("0", "1", "2"),
        edges=(Edge("0", "1", w0), Edge("1", "2", w1), Edge("2", "0", w2)),
    )


def three_cycle_demo() -> Dict[str, object]:
    """Runs the uniform vs asymmetric 3-cycle contrast of §5.4."""
    target = {("0", "1"): Fraction(1), ("1", "2"): Fraction(0), ("2", "0"): Fraction(0)}

    uniform = certify_unique_landing(three_cycle((1, 1, 1)), target)
    asymmetric = certify_unique_landing(three_cycle((1, 2, 2)), target)

    # Explicit tie for uniform weights: (1,0,0) and (0,1,0) share cost 1.
    tie_a = weighted_l1_cost([Fraction(1), Fraction(0), Fraction(0)], [1, 1, 1])
    tie_b = weighted_l1_cost([Fraction(0), Fraction(1), Fraction(0)], [1, 1, 1])

    return {
        "uniform_weights": {
            "phi1": str(uniform.phi1),
            "support": uniform.support,
            "unique": uniform.unique,
            "reason": uniform.reason,
            "tie_witness_costs": [str(tie_a), str(tie_b)],
        },
        "asymmetric_weights": {
            "phi1": str(asymmetric.phi1),
            "support": asymmetric.support,
            "sparsity": asymmetric.sparsity,
            "cycle_rank": asymmetric.cycle_rank,
            "unique": asymmetric.unique,
            "dual_witness": [str(x) for x in asymmetric.dual_witness] if asymmetric.dual_witness else None,
            "reason": asymmetric.reason,
        },
    }


def run_landing_benchmark() -> Dict[str, object]:
    """Certifies landing/uniqueness/sparsity across a small family of instances."""
    instances: List[Dict[str, object]] = []

    # 3-cycle across a sweep of weights; asymmetric (lightest-unique) vs uniform (tie).
    target3 = {("0", "1"): Fraction(1), ("1", "2"): Fraction(0), ("2", "0"): Fraction(0)}
    for w in [(1, 1, 1), (1, 2, 2), (1, 2, 3), (2, 3, 5), (1, 1, 2)]:
        cert = certify_unique_landing(three_cycle(w), target3)
        instances.append({
            "family": "3-cycle",
            "weights": list(w),
            "phi1": str(cert.phi1),
            "sparsity": cert.sparsity,
            "cycle_rank": cert.cycle_rank,
            "sparsity_bound_ok": cert.sparsity_bound_ok,
            "unique": cert.unique,
        })

    # A weighted 4-cycle and a diamond (two cycles) as further instances.
    square = ConstraintGraph(
        vertices=("a", "b", "c", "d"),
        edges=(Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "d", 2), Edge("a", "d", 3)),
    )
    target_sq = {("a", "b"): Fraction(1), ("b", "c"): Fraction(0),
                 ("c", "d"): Fraction(0), ("a", "d"): Fraction(0)}
    cert_sq = certify_unique_landing(square, target_sq)
    instances.append({
        "family": "4-cycle", "weights": [1, 2, 2, 3], "phi1": str(cert_sq.phi1),
        "sparsity": cert_sq.sparsity, "cycle_rank": cert_sq.cycle_rank,
        "sparsity_bound_ok": cert_sq.sparsity_bound_ok, "unique": cert_sq.unique,
    })

    all_sparsity_ok = all(inst["sparsity_bound_ok"] for inst in instances)
    summary: Dict[str, object] = {
        "benchmark_name": "Weighted NSP Unique Sparse Landing Certification",
        "paper_section": "PO-032 Section 5.4",
        "solver": "exact_rational_lp_plus_dual_certificate",
        "n_instances": len(instances),
        "all_sparsity_bounds_satisfied": all_sparsity_ok,
        "three_cycle_demo": three_cycle_demo(),
        "instances": instances,
    }
    return summary


def main() -> None:
    summary = run_landing_benchmark()
    summary["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    canonical = json.dumps(summary["instances"], sort_keys=True, separators=(",", ":"))
    summary["integrity_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    demo = summary["three_cycle_demo"]
    print("Weighted NSP Unique Sparse Landing (Paper 032 Section 5.4)")
    print(f"  3-cycle, uniform weights (1,1,1):   unique={demo['uniform_weights']['unique']}"
          f"  (tie costs {demo['uniform_weights']['tie_witness_costs']})")
    print(f"  3-cycle, asymmetric weights (1,2,2): unique={demo['asymmetric_weights']['unique']}"
          f"  support={demo['asymmetric_weights']['support']}"
          f"  dual={demo['asymmetric_weights']['dual_witness']}")
    print(f"  instances certified                 : {summary['n_instances']}")
    print(f"  all sparsity bounds satisfied       : {summary['all_sparsity_bounds_satisfied']}")

    receipt_path = Path(__file__).parent / "l1_sparse_landing_receipt.json"
    receipt_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nAudit receipt saved to: {receipt_path.resolve()}")


__all__ = [
    "null_space",
    "solve_linear",
    "incidence_rows",
    "cycle_space_basis",
    "LandingCertificate",
    "l1_landing",
    "certify_unique_landing",
    "weighted_l1_cost",
    "three_cycle",
    "three_cycle_demo",
    "run_landing_benchmark",
]


if __name__ == "__main__":
    main()
