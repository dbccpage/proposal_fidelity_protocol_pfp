"""
symbol_game_toolkit.py — Paper 033 Practitioner's Field Manual, §4 and §7.

Two reusable helpers that let a practitioner apply the Symbol Game to their own
problem, driving the vendored graph governor (l1_symbol_game_governor.py):

  * prompt_scaffold(carrier, relations, demand)
        Emit the eight declared v3 surfaces as a copy-paste system contract,
        filled for a given carrier / relation set / active demand.

  * run_to_terminal(vertices, edges, claims)
        Build the declared finite complex, ASSERT the relational claims, drive
        the host's monotone-descent projection-replacement to a host-owned
        terminal (zero defect, or a surviving obstruction), and return the trace.

Everything is host-recomputed and exact (fractions.Fraction); the toolkit adds no
authority. It re-implements no mathematics: the host is the vendored governor.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Sequence, Tuple

from l1_symbol_game_governor import (
    Cochain1,
    ConstraintGraph,
    Edge,
    L1SymbolGameGovernor,
    compute_phi1,
)

# The closed nine-verb operator set (an unpriced rewrite is a smuggled axiom).
CLOSED_OPERATORS: Tuple[str, ...] = (
    "PROVE", "SHOW", "DECIDE", "EXHAUST", "REDUCE", "LAND", "PIN", "REFUSE", "OPEN",
)

# The seven typed refusal codes of the v3 governor.
REFUSAL_CODES: Tuple[str, ...] = (
    "FW-CARRIER", "FW-OP", "FW-MOVE", "FW-SCOPE", "FW-CHAIN", "FW-REPLAY", "FW-LEAD",
)


def prompt_scaffold(carrier: Sequence[str], relations: Sequence[str], demand: str) -> str:
    """Return the eight declared v3 surfaces, filled for this problem (copy-paste ready)."""
    carrier_list = ", ".join(carrier)
    relations_list = ", ".join(relations)
    ops_list = ", ".join(CLOSED_OPERATORS)
    refusals_list = ", ".join(REFUSAL_CODES)
    return f"""[SYSTEM: GOVERNOR CONTRACT]
You are a proposer with no verification authority. Emit exactly one JSON move
object per turn (schema TAU_SG_V1). Do not emit prose, apologies, or
self-certification. The host re-derives every step; "verified" claims are ignored.

[K: CARRIER SPECIFICATION]
carrier: [{carrier_list}]
CarrierDigest: SHA256:<host-filled>

[VOCABULARY]
relations: [{relations_list}]
operators: [{ops_list}]

[GLYPH CALCULUS]
# every ledger row begins with one operator above; an unpriced rewrite is refused

[LAWS/AXIOMS]
# the declared production rules R1/R2 the host will replay against

[REFUSALS]
# {refusals_list}

[D: ACTIVE DEMAND]
{demand}

[TAU]
# return one TAU_SG_V1 move object: move_type in [ASSERT, CUT, VERIFY, RETRACT]
"""


def run_to_terminal(
    vertices: Sequence[str],
    edges: Sequence[Tuple[str, str, int]],
    claims: Dict[Tuple[str, str], int],
    max_cuts: int = 16,
) -> Dict[str, object]:
    """
    Drive the PO-032 governor from a declared problem to a host-owned terminal.

    `vertices`  : the finite carrier.
    `edges`     : declared directed edges as (u, v, weight) with weight > 0.
    `claims`    : asserted relational differences, {(u, v): integer}.

    Returns {terminal, final_phi1, trace}: `terminal` is ACCEPTED_ZERO_DEFECT when
    the host reaches zero obstruction, else SURVIVOR_OBSTRUCTION with the surviving
    (irreducible) defect. Every recorded Phi_1 is the host's own recomputation.
    """
    graph = ConstraintGraph(
        vertices=tuple(vertices),
        edges=tuple(Edge(u, v, w) for (u, v, w) in edges),
    )
    gov = L1SymbolGameGovernor(graph)
    trace: List[Dict[str, str]] = []

    for (u, v), val in claims.items():
        verdict = gov.step_assert(u, v, Fraction(val))
        trace.append({
            "move": "ASSERT", "detail": f"{u}->{v}={val}",
            "status": verdict.status, "phi1": str(gov.primary_obstruction()),
        })

    # Monotone-descent projection-replacement: replace claims with the nearest
    # coboundary the host computes, until zero defect or no further progress.
    for _ in range(max_cuts):
        phi = gov.primary_obstruction()
        if phi == 0:
            break
        _, gauge = compute_phi1(
            graph, Cochain1({e.key: gov.edge_claims.get(e.key, Fraction(0)) for e in graph.edges})
        )
        proposed = {e.key: gauge[e.v] - gauge[e.u] for e in graph.edges}
        verdict = gov.step_cut(proposed_claims=proposed)
        trace.append({
            "move": "CUT", "detail": "projection-replacement",
            "status": verdict.status, "phi1": str(verdict.defect_after),
        })
        if not verdict.admitted or verdict.defect_after >= phi:
            break

    final_phi = gov.primary_obstruction()
    verify = gov.step_verify("ZERO_OBSTRUCTION")
    trace.append({
        "move": "VERIFY", "detail": "ZERO_OBSTRUCTION",
        "status": verify.status, "phi1": str(final_phi),
    })
    terminal = "ACCEPTED_ZERO_DEFECT" if final_phi == 0 else "SURVIVOR_OBSTRUCTION"
    return {"terminal": terminal, "final_phi1": str(final_phi), "trace": trace}


def main() -> None:
    print("=== prompt_scaffold(carrier=[a,b,c], relations=[R], demand='REDUCE holonomy on a->b->c->a') ===")
    print(prompt_scaffold(["a", "b", "c"], ["R"], "REDUCE holonomy on the cycle a->b->c->a to zero defect"))
    print("=== run_to_terminal on the section-5 holonomy defect (weights 1,2,2) ===")
    result = run_to_terminal(
        vertices=["a", "b", "c"],
        edges=[("a", "b", 1), ("b", "c", 2), ("c", "a", 2)],
        claims={("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1},
    )
    for step in result["trace"]:
        print(f"  {step['move']:<7} {step['detail']:<24} {step['status']:<16} Phi_1={step['phi1']}")
    print(f"  terminal: {result['terminal']} (final Phi_1 = {result['final_phi1']})")


__all__ = ["CLOSED_OPERATORS", "REFUSAL_CODES", "prompt_scaffold", "run_to_terminal"]


if __name__ == "__main__":
    main()
