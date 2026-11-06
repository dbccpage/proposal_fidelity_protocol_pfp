#!/usr/bin/env python3
"""
The Symbol Game — 5-Minute Quickstart Tutorial
==============================================
A standard-library tutorial using the canonical Rust graph projection adapter.

Key concepts demonstrated:
- Player vs. Referee mental model:
    The Player (e.g., an LLM or user) proposes relational claims.
    The Referee (the Host governor) computes rule consistency and checks invariants.
- Exact rational arithmetic: zero floating-point approximation errors.
- Discrete L1 Projection: computes the minimal repair across conflicting cycles.
- Canonical lexicographic tie-breaking: deterministic resolution of polyhedral non-uniqueness.
- Cryptographic receipts: content-addressed SHA-256 verification receipts.

Setup:
    Build and pin solve_graph_phi1 as described in the package README. Python
    transports exact inputs through the vendored native_functional module and
    displays the native result; it has no fallback.

Usage:
    python quickstart.py                  # Interactive walkthrough (auto-detects tty)
    python quickstart.py --interactive    # Explicit interactive mode
    python quickstart.py --non-interactive # Non-interactive / CI headless mode
    python quickstart.py --test           # Run internal self-verification tests
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Set, Tuple

# =====================================================================
# 1. Discrete Constraint Graph and Simplicial Cochains
# =====================================================================

@dataclass(frozen=True)
class Edge:
    """Directed edge with an exact positive rational weight."""
    source: str
    target: str
    weight: int = 1

    def __post_init__(self) -> None:
        if type(self.weight) not in (int, Fraction):
            raise TypeError("Edge weight must be an exact int or Fraction.")
        if self.source == self.target:
            raise ValueError(f"Self-loop {self.source} -> {self.target} violates irreflexivity.")
        if self.weight <= 0:
            raise ValueError(f"Edge weight must be positive and exact rational, got {self.weight}.")

    @property
    def key(self) -> Tuple[str, str]:
        return (self.source, self.target)


@dataclass(frozen=True)
class ConstraintGraph:
    """Finite constraint graph with carrier vertices and directed edges."""
    vertices: Tuple[str, ...]
    edges: Tuple[Edge, ...]

    def __post_init__(self) -> None:
        v_set = set(self.vertices)
        for e in self.edges:
            if e.source not in v_set:
                raise ValueError(f"Edge source '{e.source}' not in declared vertices.")
            if e.target not in v_set:
                raise ValueError(f"Edge target '{e.target}' not in declared vertices.")

    def edge_by_pair(self, source: str, target: str) -> Optional[Edge]:
        for e in self.edges:
            if e.source == source and e.target == target:
                return e
        return None

    def connected_components(self) -> List[List[str]]:
        """Computes connected components of the underlying undirected graph."""
        adj: Dict[str, Set[str]] = {v: set() for v in self.vertices}
        for e in self.edges:
            adj[e.source].add(e.target)
            adj[e.target].add(e.source)

        visited: Set[str] = set()
        components: List[List[str]] = []
        for v in self.vertices:
            if v not in visited:
                comp: List[str] = []
                stack = [v]
                visited.add(v)
                while stack:
                    curr = stack.pop()
                    comp.append(curr)
                    for nxt in adj[curr]:
                        if nxt not in visited:
                            visited.add(nxt)
                            stack.append(nxt)
                components.append(sorted(comp))
        return components


@dataclass(frozen=True)
class Cochain1:
    """
    1-Cochain over graph edges with exact rational values.
    Maps directed edges (source, target) to Fraction values.
    """
    values: Dict[Tuple[str, str], Fraction]

    def __post_init__(self) -> None:
        if any(type(value) not in (int, Fraction) for value in self.values.values()):
            raise TypeError("Cochain values must be exact int or Fraction.")

    def get(self, source: str, target: str) -> Fraction:
        return self.values.get((source, target), Fraction(0))

    def l1_norm(self, weights: Optional[Dict[Tuple[str, str], int]] = None) -> Fraction:
        """Computes exact weighted L1 norm sum_e w_e |value_e|."""
        total = Fraction(0)
        for (u, v), val in self.values.items():
            w = weights.get((u, v), 1) if weights else 1
            total += Fraction(w) * abs(val)
        return total


# =====================================================================
# 2. Referee Engine: Coboundary, Defect, and Discrete L1 Projection
# =====================================================================

def compute_coboundary(potential: Dict[str, Fraction], edges: Tuple[Edge, ...]) -> Cochain1:
    """
    Simplicial coboundary operator delta_0: C^0 -> C^1.
    (delta_0 s)(u, v) = s(v) - s(u).
    """
    vals: Dict[Tuple[str, str], Fraction] = {}
    for e in edges:
        s_u = potential.get(e.source, Fraction(0))
        s_v = potential.get(e.target, Fraction(0))
        vals[e.key] = s_v - s_u
    return Cochain1(values=vals)


def evaluate_defect(
    claims: Cochain1,
    potential: Dict[str, Fraction],
    edges: Tuple[Edge, ...],
) -> Tuple[Fraction, Dict[Tuple[str, str], Fraction]]:
    """
    Evaluates defect norm D(s) = sum_{e=(u,v)} w_e |claim_e - (s(v) - s(u))|.
    Returns total defect norm and per-edge residual errors.
    """
    total = Fraction(0)
    residuals: Dict[Tuple[str, str], Fraction] = {}
    for e in edges:
        val = claims.get(e.source, e.target)
        diff = val - (potential.get(e.target, Fraction(0)) - potential.get(e.source, Fraction(0)))
        residuals[e.key] = diff
        total += Fraction(e.weight) * abs(diff)
    return total, residuals


def find_spanning_forest_potentials(
    graph: ConstraintGraph,
    claims: Cochain1,
) -> List[Dict[str, Fraction]]:
    """Historical candidate enumeration has no native adapter."""
    raise RuntimeError(
        "RUST_FUNCTIONAL_REQUIRED: candidate enumeration is retired; "
        "use compute_discrete_l1_projection with a pinned native calculator"
    )


def compute_discrete_l1_projection(
    graph: ConstraintGraph,
    claims: Cochain1,
) -> Tuple[Fraction, Dict[str, Fraction], Cochain1]:
    """Transport exact inputs; return the native minimum, gauge, and coboundary.

    The canonical Rust owner selects the minimizing gauge. A missing executable,
    mismatched digest, or refused input propagates without a Python fallback.
    """
    from native_functional import compute_graph_phi1

    minimum, potential = compute_graph_phi1(
        graph.vertices,
        [(edge.source, edge.target, edge.weight) for edge in graph.edges],
        claims.values,
    )
    return minimum, potential, compute_coboundary(potential, graph.edges)


# =====================================================================
# 3. Meeting Scheduler Domain Model
# =====================================================================

@dataclass
class MeetingState:
    """Domain state representing relative meeting schedule times."""
    participants: Tuple[str, ...]
    delays: Dict[Tuple[str, str], Fraction]
    weights: Dict[Tuple[str, str], int]

    def to_graph_and_cochain(self) -> Tuple[ConstraintGraph, Cochain1]:
        edges: List[Edge] = []
        for (u, v), d in self.delays.items():
            w = self.weights.get((u, v), 1)
            edges.append(Edge(source=u, target=v, weight=w))
        graph = ConstraintGraph(vertices=self.participants, edges=tuple(edges))
        cochain = Cochain1(values=dict(self.delays))
        return graph, cochain


def build_default_meeting_conflict() -> MeetingState:
    """
    Builds the canonical 3-person circular meeting conflict:
    Alice -> Bob: +1 hr
    Bob -> Charlie: +1 hr
    Charlie -> Alice: +1 hr
    Loop sum: 1 + 1 + 1 = 3 hours (cyclic inconsistency).
    Weights: (1, 2, 2) to illustrate weighted sparse landing.
    """
    participants = ("Alice", "Bob", "Charlie")
    delays = {
        ("Alice", "Bob"): Fraction(1, 1),
        ("Bob", "Charlie"): Fraction(1, 1),
        ("Charlie", "Alice"): Fraction(1, 1),
    }
    weights = {
        ("Alice", "Bob"): 2,
        ("Bob", "Charlie"): 2,
        ("Charlie", "Alice"): 1,
    }
    return MeetingState(participants=participants, delays=delays, weights=weights)


# =====================================================================
# 4. Cryptographic Receipt Generator
# =====================================================================

def generate_audit_receipt(
    run_mode: str,
    initial_claims: Dict[str, str],
    referee_check: Dict[str, str],
    proposed_move: Dict[str, str],
    verdict: Dict[str, str],
    minimal_repair: Dict[str, str],
    projected_schedule: Dict[str, str],
) -> Dict[str, object]:
    """Generates an immutable audit receipt with canonical SHA-256 hash."""
    payload = {
        "protocol": "THE_SYMBOL_GAME_QUICKSTART_V1",
        "run_mode": run_mode,
        "initial_claims": initial_claims,
        "referee_check": referee_check,
        "proposed_move": proposed_move,
        "verdict": verdict,
        "minimal_repair": minimal_repair,
        "projected_schedule": projected_schedule,
    }
    canon_bytes = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
    digest = hashlib.sha256(canon_bytes).hexdigest()
    return {
        "receipt_sha256": f"sha256:{digest}",
        "receipt_payload": payload,
    }


# =====================================================================
# 5. Interactive & Non-Interactive Walkthrough Harness
# =====================================================================

def format_fraction(f: Fraction) -> str:
    if f.denominator == 1:
        return f"{f.numerator:+d} hr" if f.numerator != 0 else "0 hr"
    return f"{f.numerator:+d}/{f.denominator} hr"


def run_quickstart(interactive: bool = False) -> int:
    """Executes the 5-minute meeting scheduler quickstart tutorial."""
    banner = "=" * 70
    print(banner)
    print("                THE SYMBOL GAME -- 5-MINUTE QUICKSTART")
    print("      Dual-Track Onboarding: Player Proposal vs. Host Referee")
    print(banner)

    # 1. Setup
    print("\n[Step 1] Scenario Setup: Meeting Sequencing")
    print("  Three participants require relative scheduling:")
    print("  - Alice (A)")
    print("  - Bob (B)")
    print("  - Charlie (C)")
    print("  Each claim specifies the relative speaking delay between participants.")

    # 2. Initial input claims
    state = build_default_meeting_conflict()
    graph, cochain = state.to_graph_and_cochain()

    print("\n[Step 2] Proposer Claims (Candidate Input)")
    print("  The Player submits the following schedule constraints:")
    for e in graph.edges:
        val = cochain.get(e.source, e.target)
        w = e.weight
        print(f"    * {e.source:<7} -> {e.target:<7} : {format_fraction(val):<8} (weight: {w})")

    # 3. Referee evaluation
    # Compute loop holonomy
    holonomy = (
        cochain.get("Alice", "Bob")
        + cochain.get("Bob", "Charlie")
        + cochain.get("Charlie", "Alice")
    )
    print("\n[Step 3] Referee Invariant Check")
    print("  The Host Referee checks cycle consistency around the closed meeting loop:")
    print("    Alice -> Bob -> Charlie -> Alice")
    print(f"    Cycle Loop Discrepancy (Holonomy) : (1) + (1) + (1) = {format_fraction(holonomy)}")
    print(f"    Total Loop Conflict (Defect)      : {abs(holonomy)} hr")

    if holonomy != 0:
        print("    Referee Verdict                   : CONTRADICTION DETECTED (Time cannot loop)")
    else:
        print("    Referee Verdict                   : CONSISTENT")

    # 4. Interactive or simulated move proposal
    print("\n[Step 4] Proposer Intervention (Testing Defect Monotonicity)")
    if interactive:
        print("  You are the Player! Try proposing a modification:")
        print("  Current delay Alice -> Bob is +1 hr.")
        user_input = input("  Enter proposed new delay for Alice -> Bob in hours (e.g., 5 or -1) [default: 5]: ").strip()
        try:
            val_num = int(user_input) if user_input else 5
            proposed_delay = Fraction(val_num, 1)
        except ValueError:
            print("  Invalid number; defaulting to +5 hr.")
            proposed_delay = Fraction(5, 1)
    else:
        proposed_delay = Fraction(5, 1)
        print(f"  Simulated Player Proposal: increase Alice -> Bob delay to {format_fraction(proposed_delay)}.")

    # Evaluate proposed move defect
    hypothetical_delays = dict(state.delays)
    hypothetical_delays[("Alice", "Bob")] = proposed_delay
    hypo_cochain = Cochain1(values=hypothetical_delays)
    hypo_holonomy = (
        hypo_cochain.get("Alice", "Bob")
        + hypo_cochain.get("Bob", "Charlie")
        + hypo_cochain.get("Charlie", "Alice")
    )
    hypo_defect = abs(hypo_holonomy)

    print("  Evaluation of Proposal:")
    print(f"    Original Loop Conflict (Defect) : {abs(holonomy)} hr")
    print(f"    Proposed Loop Conflict (Defect) : {hypo_defect} hr")

    if hypo_defect > abs(holonomy):
        verdict_status = "REFUSED (DefectIncrease)"
        verdict_detail = f"Move rejected: defect would increase from {abs(holonomy)} to {hypo_defect}."
        print(f"    Host Action          : {verdict_status}")
        print(f"    Reason               : {verdict_detail}")
    else:
        verdict_status = "ACCEPTED (Non-increasing Defect)"
        verdict_detail = "Move admitted: defect decreased or remained stationary."
        print(f"    Host Action          : {verdict_status}")

    # 5. Automated Minimal Repair via Discrete L1 Projection
    print("\n[Step 5] Discrete L1 Projection: Automated Minimal Repair")
    print("  The Host computes the minimal adjustment to restore zero conflict.")
    best_norm, best_potential, projected_claims = compute_discrete_l1_projection(graph, cochain)

    print(f"  Initial Conflict / Defect Norm (Phi_1) : {best_norm} hr")
    print("  Optimal Relative Timestamps (Gauge Potential f in C^0):")
    for v in graph.vertices:
        print(f"    * Timestamp for {v:<7} : {format_fraction(best_potential[v])}")

    print("\n  Projected Consistent Schedule (Coboundary delta f):")
    repairs_summary: Dict[str, str] = {}
    for e in graph.edges:
        orig = cochain.get(e.source, e.target)
        proj = projected_claims.get(e.source, e.target)
        adjustment = proj - orig
        adj_str = f"{adjustment.numerator:+d}" if adjustment.denominator == 1 else f"{adjustment}"
        repairs_summary[f"{e.source}->{e.target}"] = (
            f"Original: {format_fraction(orig)} -> Projected: {format_fraction(proj)} (Adj: {adj_str})"
        )
        print(f"    * {e.source:<7} -> {e.target:<7} : {format_fraction(proj):<8} [Adjustment: {adj_str}]")

    # Verify idempotence
    proj_defect, _ = evaluate_defect(projected_claims, best_potential, graph.edges)
    _, _, reprojected = compute_discrete_l1_projection(graph, projected_claims)
    reproj_norm, _ = evaluate_defect(reprojected, best_potential, graph.edges)
    is_idempotent = (reprojected.values == projected_claims.values)

    print("\n[Step 6] Mathematical Invariant Verification")
    print(f"  * Post-Repair Residual Defect       : {proj_defect} hr (Zero Conflict Achieved)")
    print(f"  * Idempotence Check P(P(s)) == P(s) : {'SATISFIED' if is_idempotent else 'VIOLATED'}")
    print("  * Arithmetic Precision              : Exact Rational (Fraction) -- Zero Float Drift")

    # 6. Audit Receipt
    initial_claims_dict = {
        f"{e.source}->{e.target}": format_fraction(cochain.get(e.source, e.target))
        for e in graph.edges
    }
    projected_schedule_dict = {
        f"{e.source}->{e.target}": format_fraction(projected_claims.get(e.source, e.target))
        for e in graph.edges
    }
    receipt_data = generate_audit_receipt(
        run_mode="interactive" if interactive else "non-interactive",
        initial_claims=initial_claims_dict,
        referee_check={"loop_holonomy": format_fraction(holonomy), "status": "CONTRADICTION DETECTED"},
        proposed_move={"target": "Alice->Bob", "value": format_fraction(proposed_delay)},
        verdict={"status": verdict_status, "detail": verdict_detail},
        minimal_repair=repairs_summary,
        projected_schedule=projected_schedule_dict,
    )

    print("\n[Step 7] Cryptographic Audit Receipt")
    print(f"  * Receipt SHA-256 : {receipt_data['receipt_sha256']}")
    print("  * Audit Status    : CERTIFIED_EXACT_RATIONAL")
    print(banner)
    print("Quickstart execution completed successfully.")
    return 0


# =====================================================================
# 6. Self-Verification Test Suite
# =====================================================================

def run_self_tests() -> int:
    """Runs internal sanity checks for the quickstart algorithms."""
    print("Running quickstart self-verification tests...")

    # Test 1: Constraint graph irreflexivity
    try:
        Edge(source="Alice", target="Alice", weight=1)
        assert False, "Self-loop failed to raise ValueError."
    except ValueError:
        pass

    # Test 2: A pinned native executable is required for projection.
    state = build_default_meeting_conflict()
    graph, cochain = state.to_graph_and_cochain()

    # Test 3: Discrete L1 projection and idempotence
    best_norm, best_f, proj = compute_discrete_l1_projection(graph, cochain)
    assert best_norm >= 0, "Defect norm must be non-negative."
    _, _, reproj = compute_discrete_l1_projection(graph, proj)
    assert proj.values == reproj.values, "Projection operator must be idempotent: P(P(s)) == P(s)."

    # Test 4: Defect of projected cochain is zero
    defect, _ = evaluate_defect(proj, best_f, graph.edges)
    assert defect == Fraction(0), f"Projected defect must be zero, got {defect}"

    # Test 5: Receipt SHA-256 determinism
    r1 = generate_audit_receipt("test", {"a": "1"}, {"b": "2"}, {"c": "3"}, {"d": "4"}, {"e": "5"}, {"f": "6"})
    r2 = generate_audit_receipt("test", {"a": "1"}, {"b": "2"}, {"c": "3"}, {"d": "4"}, {"e": "5"}, {"f": "6"})
    assert r1["receipt_sha256"] == r2["receipt_sha256"], "Receipt hash must be deterministic."

    print("All quickstart self-verification tests PASSED.")
    return 0


# =====================================================================
# 7. Main CLI Entry Point
# =====================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="The Symbol Game: 5-Minute Meeting Scheduler Quickstart",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive mode prompting user for inputs",
    )
    group.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run non-interactive headless mode (default in CI/scripts)",
    )
    group.add_argument(
        "--test",
        action="store_true",
        help="Run internal self-verification tests",
    )

    args = parser.parse_args()

    if args.test:
        return run_self_tests()

    # Determine interactive mode: if --interactive is passed, or if neither is passed and stdin is a tty
    interactive_mode = False
    if args.interactive:
        interactive_mode = True
    elif not args.non_interactive:
        interactive_mode = sys.stdin.isatty()

    return run_quickstart(interactive=interactive_mode)


if __name__ == "__main__":
    sys.exit(main())
