"""Demo 1: replay of the manuscript's finite graph-repair witnesses.

Checks, with exact rational arithmetic, the list given in the manuscript's
reproduction section:
  - the triangle with reports (1, 1, 1) and penalties (1, 2, 3) costs 6 at the
    zero potential and 3 at (0, -2, -1);
  - the circulation (1, 1, 1) is feasible with value 3, so 3 is the minimum;
  - changing the third report to -2 makes the reports exact;
  - a dual with an entry deleted, an over-capacity circulation, a leaking
    circulation, an unknown endpoint and a zero penalty are all rejected;
  - a tied uniform cycle has several optimal residual vectors;
  - a strictly decreasing rational sequence exhausts its fuel without reaching
    the minimum, so the run ends unfinished rather than convergent.

Every expected outcome is checked; run_demo1() returns False on any mismatch.
These are deterministic fixtures, not replays of model transcripts.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from symbol_game_governor import (  # noqa: E402
    ConstraintGraph,
    Edge,
    MoveType,
    Phi1Certificate,
    StepVerdict,
    SymbolGameGovernor,
    compute_exact_phi_1,
    verify_phi_1_certificate,
)

VERTICES = ("a", "b", "c")
TRIANGLE = (("a", "b", 1), ("b", "c", 2), ("c", "a", 3))
REPORTS = {("a", "b"): Fraction(1), ("b", "c"): Fraction(1), ("c", "a"): Fraction(1)}


def cost(edges, reports, potential) -> Fraction:
    """D_c(s) = sum_e w_e |c_e - (s_v - s_u)|, computed independently of the governor."""
    return sum((w * abs(reports.get((u, v), 0) - (potential[v] - potential[u])) for u, v, w in edges), Fraction(0))


def _check(label: str, condition: bool, results: list) -> None:
    results.append(condition)
    print(f"{'OK  ' if condition else 'FAIL'} {label}")


def triangle_witnesses(results: list) -> None:
    print("\n--- Triangle: reports (1,1,1), penalties (1,2,3) ---")
    zero = {v: Fraction(0) for v in VERTICES}
    best = {"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)}
    _check(f"D_c(0,0,0) = {cost(TRIANGLE, REPORTS, zero)} (expected 6)", cost(TRIANGLE, REPORTS, zero) == 6, results)
    _check(f"D_c(0,-2,-1) = {cost(TRIANGLE, REPORTS, best)} (expected 3)", cost(TRIANGLE, REPORTS, best) == 3, results)

    circulation = {("a", "b"): Fraction(1), ("b", "c"): Fraction(1), ("c", "a"): Fraction(1)}
    certificate = Phi1Certificate(Fraction(3), best, circulation, Fraction(0))
    _check("primal (0,-2,-1) and circulation (1,1,1) verify with value 3",
           verify_phi_1_certificate(VERTICES, TRIANGLE, REPORTS, certificate), results)

    computed = compute_exact_phi_1(VERTICES, TRIANGLE, REPORTS)
    potential = ", ".join(f"{v}={computed.primal_potentials[v]}" for v in VERTICES)
    circulation = ", ".join(f"{u}->{v}={computed.dual_circulations[u, v]}" for u, v, _ in TRIANGLE)
    print(f"     builder: phi_1={computed.phi_1}; potential {potential}; circulation {circulation}")
    _check("reference builder returns a verified certificate with minimum 3",
           computed.phi_1 == 3 and verify_phi_1_certificate(VERTICES, TRIANGLE, REPORTS, computed), results)

    graph = ConstraintGraph(VERTICES, tuple(Edge(u, v, w) for u, v, w in TRIANGLE))
    governor = SymbolGameGovernor(graph, dict(REPORTS))
    refused = governor.execute_move(MoveType.CUT, {"potentials": {"b": 5, "c": -5}})
    _check(f"cost-increasing CUT refused: {refused.feedback.split('.')[0]}",
           not refused.admitted and governor.section == zero, results)
    admitted = governor.execute_move(MoveType.CUT, {"potentials": {"b": -2, "c": -1}})
    _check(f"CUT to (0,-2,-1) admitted: D {6} -> {admitted.defect}, phi_1 unchanged at {admitted.phi_1}",
           admitted.admitted and admitted.defect == 3 and admitted.phi_1 == 3, results)
    verified = governor.execute_move(MoveType.VERIFY, {})
    _check("VERIFY reports a minimal nonzero obstruction, not exactness",
           verified.admitted and verified.verdict == StepVerdict.HOLD, results)

    exact_reports = dict(REPORTS)
    exact_reports[("c", "a")] = Fraction(-2)
    exact = compute_exact_phi_1(VERTICES, TRIANGLE, exact_reports)
    _check(f"third report changed to -2: phi_1 = {exact.phi_1} (expected 0)", exact.phi_1 == 0, results)


def rejected_witnesses(results: list) -> None:
    print("\n--- Malformed certificates and problems are rejected ---")
    best = {"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)}
    deleted = {("a", "b"): Fraction(1), ("b", "c"): Fraction(1)}
    _check("dual with one entry deleted",
           not verify_phi_1_certificate(VERTICES, TRIANGLE, REPORTS, Phi1Certificate(Fraction(3), best, deleted, Fraction(0))),
           results)
    zero = {v: Fraction(0) for v in VERTICES}
    over = {("a", "b"): Fraction(2), ("b", "c"): Fraction(2), ("c", "a"): Fraction(2)}
    _check("over-capacity circulation whose value 6 equals the zero potential's cost",
           not verify_phi_1_certificate(VERTICES, TRIANGLE, REPORTS, Phi1Certificate(Fraction(6), zero, over, Fraction(0))),
           results)
    leak = {("a", "b"): Fraction(1), ("b", "c"): Fraction(2), ("c", "a"): Fraction(0)}
    _check("leaking flow whose value 3 equals the optimal cost",
           not verify_phi_1_certificate(VERTICES, TRIANGLE, REPORTS, Phi1Certificate(Fraction(3), best, leak, Fraction(0))),
           results)
    for label, edges in (("unknown endpoint", (("a", "x", 1),)), ("zero penalty", (("a", "b", 0),))):
        try:
            compute_exact_phi_1(VERTICES, edges, {})
            _check(label, False, results)
        except ValueError as error:
            _check(f"{label}: {error}", True, results)


def tied_cycle(results: list) -> None:
    print("\n--- Uniform penalties: tied optima ---")
    uniform = (("a", "b", 1), ("b", "c", 1), ("c", "a", 1))
    potentials = [
        {"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)},  # residuals (3, 0, 0)
        {"a": Fraction(0), "b": Fraction(1), "c": Fraction(-1)},   # residuals (0, 3, 0)
        {"a": Fraction(0), "b": Fraction(0), "c": Fraction(0)},    # residuals (1, 1, 1)
    ]
    costs = [cost(uniform, REPORTS, p) for p in potentials]
    phi = compute_exact_phi_1(VERTICES, uniform, REPORTS).phi_1
    _check(f"residuals (3,0,0), (0,3,0), (1,1,1) each cost {', '.join(map(str, costs))} = phi_1 {phi}",
           set(costs) == {phi} == {3}, results)


def rational_descent(results: list, fuel: int = 10) -> None:
    print(f"\n--- Strict rational descent with fuel {fuel} ---")
    graph = ConstraintGraph(("a", "b"), (Edge("a", "b", 1),))
    governor = SymbolGameGovernor(graph, {("a", "b"): 1})
    costs = []
    for t in range(1, fuel + 1):
        step = governor.execute_move(MoveType.CUT, {"potentials": {"b": 1 - Fraction(1, 2**t)}})
        if not step.admitted:
            break
        costs.append(step.defect)
    strictly = all(later < earlier for earlier, later in zip([Fraction(1)] + costs, costs))
    _check(f"{len(costs)} admitted CUTs, each strictly lower; last cost {costs[-1] if costs else None}",
           len(costs) == fuel and strictly, results)
    final = governor.execute_move(MoveType.VERIFY, {})
    _check("fuel exhausted with cost above the minimum 0: run ends UNFINISHED, not converged",
           not final.admitted and costs[-1] > 0 == final.phi_1, results)


def run_demo1() -> bool:
    print("=" * 70)
    print("DEMO 1: MANUSCRIPT GRAPH-REPAIR WITNESSES")
    print("=" * 70)
    results: list = []
    triangle_witnesses(results)
    rejected_witnesses(results)
    tied_cycle(results)
    rational_descent(results)
    passed = all(results)
    print("\n" + "=" * 70)
    print(f"DEMO 1 {'PASSED' if passed else 'FAILED'}: {sum(results)}/{len(results)} expected outcomes")
    print("=" * 70)
    return passed


if __name__ == "__main__":
    raise SystemExit(0 if run_demo1() else 1)
