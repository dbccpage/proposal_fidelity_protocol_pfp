"""
play_demo.py — the worked session of the practitioner guide (paper.md, Section 4).

A complete, runnable session driven against the vendored graph governor
(`l1_symbol_game_governor.py` in this directory). It demonstrates the four moves
(ASSERT, CUT, VERIFY, RETRACT) and the monotonic-descent admission gate on a
three-node holonomy defect.

Run from the package directory:  py -3.12 code/play_demo.py

The proposer (here, scripted) has no verification authority: every Phi_1 value
printed is recomputed by the host, not asserted by the proposer. The governor
uses the native graph calculator when CORE_FUNCTIONAL_GRAPH_BIN is set and
propagates its errors. Otherwise it computes by exact Python enumeration.
The returned session record names the selected path; it is not a native receipt.
"""

from __future__ import annotations

import os
from fractions import Fraction

from l1_symbol_game_governor import ConstraintGraph, Edge, L1SymbolGameGovernor


def run_session(verbose: bool = True) -> dict:
    """Drives the worked session and returns the observed host verdicts."""
    graph = ConstraintGraph(
        vertices=("a", "b", "c"),
        edges=(Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "a", 3)),
    )
    gov = L1SymbolGameGovernor(graph)

    def say(*args):
        if verbose:
            print(*args)

    calculation_path = "native" if os.environ.get("CORE_FUNCTIONAL_GRAPH_BIN") else "python-enumeration"
    say(f"Calculator: {calculation_path}; weights = (1, 2, 3)")

    # --- ASSERT: the proposer's three relational claims; the host records them.
    gov.step_assert("a", "b", Fraction(1))
    gov.step_assert("b", "c", Fraction(1))
    v_last_assert = gov.step_assert("c", "a", Fraction(1))
    phi_after_assert = gov.primary_obstruction()
    snapshot = v_last_assert.step_id
    say(f"ASSERT x3 -> Phi_1 = {phi_after_assert}   (holonomy 1+1+1 = 3, a genuine defect)")

    # --- CUT (rejected): a defect-INCREASING proposal is refused fail-closed.
    bad = {("a", "b"): Fraction(5), ("b", "c"): Fraction(0), ("c", "a"): Fraction(0)}
    v_bad = gov.step_cut(proposed_claims=bad)
    say(f"CUT (bad)  -> {v_bad.status}: {v_bad.defect_before} -> {v_bad.defect_after}, "
        f"admitted={v_bad.admitted}  (state untouched)")

    # --- CUT (repair): replace claims with the nearest coboundary; host recomputes.
    repaired = {("a", "b"): Fraction(-2), ("b", "c"): Fraction(1), ("c", "a"): Fraction(1)}
    v_good = gov.step_cut(proposed_claims=repaired)
    say(f"CUT (repair) -> {v_good.status}: {v_good.defect_before} -> {v_good.defect_after}, "
        f"admitted={v_good.admitted}")

    # --- VERIFY: the host confirms zero defect from its own store.
    v_verify = gov.step_verify("ZERO_OBSTRUCTION")
    say(f"VERIFY ZERO_OBSTRUCTION -> admitted={v_verify.admitted}")

    # --- RETRACT: roll state back to the post-ASSERT snapshot; defect returns to 3.
    gov.step_retract(snapshot, reason="demonstrate rollback")
    phi_after_retract = gov.primary_obstruction()
    say(f"RETRACT to {snapshot} -> Phi_1 = {phi_after_retract}   (pre-repair state restored)")

    return {
        "calculation_path": calculation_path,
        "weights": (1, 2, 3),
        "phi_after_assert": phi_after_assert,
        "bad_status": v_bad.status,
        "bad_admitted": v_bad.admitted,
        "repair_status": v_good.status,
        "repair_before": v_good.defect_before,
        "repair_after": v_good.defect_after,
        "verify_admitted": v_verify.admitted,
        "phi_after_retract": phi_after_retract,
    }


def main() -> None:
    print("PFP worked session (practitioner guide, Section 4); host = vendored governor")
    run_session(verbose=True)


if __name__ == "__main__":
    main()
