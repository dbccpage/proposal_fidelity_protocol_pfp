"""Replay the field manual's Level 7 capstone with the packaged governor.

This is a scripted exercise. A selected native calculator's errors propagate;
without native configuration the governor uses exact Python enumeration.
The transcript is not a canonical native receipt or a live provider trial.
"""

from __future__ import annotations

import os
from fractions import Fraction as Q

from l1_symbol_game_governor import ConstraintGraph, Edge, L1SymbolGameGovernor


def run_capstone(verbose: bool = True) -> dict:
    graph = ConstraintGraph(("a", "b", "c"), (Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "a", 3)))
    governor = L1SymbolGameGovernor(graph)
    path = "native" if os.environ.get("CORE_FUNCTIONAL_GRAPH_BIN") else "python-enumeration"
    outcomes = []

    def say(message):
        if verbose:
            print(message)

    def record(action, verdict, metric):
        outcomes.append({
            "action": action, "status": verdict.status, "admitted": verdict.admitted,
            "metric": metric, "before": verdict.defect_before, "after": verdict.defect_after,
        })
        say(f"{action}: {verdict.status}, admitted={verdict.admitted}; {metric}: {verdict.defect_before} -> {verdict.defect_after}")

    say(f"Calculator: {path}; edges = (ab, bc, ca); weights = (1, 2, 3)")
    for edge in graph.edges:
        assertion = governor.step_assert(*edge.key, Q(1))
    snapshot = assertion.step_id
    original = dict(governor.edge_claims)
    original_minimum = governor.primary_obstruction()
    say(f"ASSERT: Phi_w = {original_minimum}; D_c = {governor.section_defect()}; snapshot = {snapshot}")

    record("empty CUT", governor.step_cut(proposed_claims={}), "Phi_w")
    bad = {(edge.u, edge.v): Q(value) for edge, value in zip(graph.edges, (5, 0, 0))}
    record("bad CUT", governor.step_cut(proposed_claims=bad), "Phi_w")
    refused_state_preserved = governor.edge_claims == original

    partial = {edge.key: Q(value) for edge, value in zip(graph.edges, (0, 1, 1))}
    record("partial improvement CUT", governor.step_cut(proposed_claims=partial), "Phi_w")
    repair = {edge.key: Q(value) for edge, value in zip(graph.edges, (-2, 1, 1))}
    record("exact repair CUT", governor.step_cut(proposed_claims=repair), "Phi_w")
    record("ZERO_OBSTRUCTION", governor.step_verify("ZERO_OBSTRUCTION"), "D_c")
    record("RETRACT", governor.step_retract(snapshot, reason="Level 7 capstone"), "D_c")
    restored_minimum = governor.primary_obstruction()
    say(f"Restored claims: {tuple(governor.edge_claims[edge.key] for edge in graph.edges)}; Phi_w = {restored_minimum}")

    return {
        "calculation_path": path, "weights": (1, 2, 3), "snapshot_id": snapshot,
        "original_minimum": original_minimum, "outcomes": outcomes,
        "refused_state_preserved": refused_state_preserved,
        "restored_claims": dict(governor.edge_claims), "restored_minimum": restored_minimum,
    }


if __name__ == "__main__":
    run_capstone()
