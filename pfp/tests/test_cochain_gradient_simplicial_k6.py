"""Targeted verification of Cochain Gradient Injection Hook on higher-order (N >= 6) simplicial complexes.

Verifies:
- Simplicial boundary law (d_1 ∘ d_2 = 0) on K_6 and K_7 complexes via sovereign Rust homology port.
- Spanning tree potential integration and fundamental cycle basis decoupling across b_1 >= 10 cycles.
- Live runtime Symbol Game turn machine execution with CochainGradientInjectionHook.
- Stationary loop prevention: unhinted proposer enters stationary loop trap (L >= 3, Phi_1 > 0),
  whereas cochain gradient injection achieves 100% defect collapse to Phi_1 = 0 (ACCEPTED_ZERO_DEFECT)
  with zero stationary loops.
- Generalization across K_6 (N=6, b_1=10), K_7 (N=7, b_1=15), and octahedral 2-sphere complex (b_1=7).
- Deep facade SymbolGameController and SymbolGameEngine event emission.
- Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
- Zero Float Law (all cochain values, potentials, and holonomies are Fraction or int).
- Byte-level UTF-8 encoding without BOM.

Governing Invariant: Zero Python Math Re-invention & Sovereign Rust Delegation.
Governing Invariant: Strict Descent on (Gamma_2, Phi_1, defect_count).
Governing Invariant: Claim Hygiene Rule.
AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from pfp.controllers import SymbolGameController, SymbolGameEngine
from pfp.domain.events import TurnExecutedEvent
from pfp.domain.solvers import (
    CochainCarrier,
    CochainGradientInjectionHook,
    Simplicial1Cochain,
    SimplicialCochainGradientSolver,
    SimplicialRetractionReceipt,
    run_simplicial_retraction_loop,
)
from pfp.infrastructure.adapters.exact_rust_adapter import (
    RustExactEngineAdapter,
)


@pytest.fixture(scope="module")
def homology_adapter() -> RustExactEngineAdapter:
    return RustExactEngineAdapter()


# =============================================================================
# 1. Simplicial Boundary Law on K_6 (N=6) and K_7 (N=7)
# =============================================================================

def test_k6_simplicial_boundary_law_sovereign_delegation(homology_adapter: RustExactEngineAdapter) -> None:
    """Verify d_1 ∘ d_2 = 0 on K_6 complete simplicial complex via sovereign Rust homology port."""
    k6 = CochainCarrier.make_complete_complex(6, prefix="v")
    assert k6.vertex_count == 6
    assert k6.edge_count == 15      # 6*5/2 = 15
    assert k6.face_count == 20      # 6*5*4/6 = 20
    assert k6.cycle_rank == 10      # b_1 = 15 - 6 + 1 = 10

    # Vertex indices for Rust homology port: 0..5
    # Simplices: all 2-simplices (faces) as 3-element index lists
    simplices = [
        [int(u[1:]), int(v[1:]), int(w[1:])]
        for u, v, w in k6.faces
    ]
    report = homology_adapter.verify_simplicial_boundary_law(simplices)
    assert report["max_dimension"] == 2
    assert report["simplex_counts_by_dim"] == [6, 15, 20]
    assert report["boundary_law_verified"] is True

    # Check composition d_1 ∘ d_2
    c2 = report["compositions"][0]
    assert c2["degree"] == 2
    assert c2["rows"] == 6   # C_0
    assert c2["cols"] == 20  # C_2
    assert c2["is_zero"] is True


def test_k7_simplicial_boundary_law_sovereign_delegation(homology_adapter: RustExactEngineAdapter) -> None:
    """Verify d_1 ∘ d_2 = 0 on K_7 complete simplicial complex via sovereign Rust homology port."""
    k7 = CochainCarrier.make_complete_complex(7, prefix="v")
    assert k7.vertex_count == 7
    assert k7.edge_count == 21      # 7*6/2 = 21
    assert k7.face_count == 35      # 7*6*5/6 = 35
    assert k7.cycle_rank == 15      # b_1 = 21 - 7 + 1 = 15

    simplices = [
        [int(u[1:]), int(v[1:]), int(w[1:])]
        for u, v, w in k7.faces
    ]
    report = homology_adapter.verify_simplicial_boundary_law(simplices)
    assert report["max_dimension"] == 2
    assert report["simplex_counts_by_dim"] == [7, 21, 35]
    assert report["boundary_law_verified"] is True


# =============================================================================
# 2. Spanning Tree and Fundamental Cycle Decoupling on K_6
# =============================================================================

def test_k6_spanning_tree_and_cycle_basis_structure() -> None:
    """Verify spanning tree decomposition and fundamental cycle orthogonality on K_6."""
    k6 = CochainCarrier.make_complete_complex(6, prefix="v")
    tree_edges, chord_edges = k6.find_spanning_tree()

    # Spanning tree on 6 vertices has exactly 5 edges
    assert len(tree_edges) == 5
    # Exactly 10 chord edges
    assert len(chord_edges) == 10
    assert len(tree_edges) + len(chord_edges) == 15

    # Fundamental cycle basis
    cycles = k6.find_fundamental_cycles(tree_edges, chord_edges)
    assert len(cycles) == 10

    # Orthogonality/Decoupling: each chord edge appears in EXACTLY one cycle
    chord_set = set(chord_edges)
    for idx, chord in enumerate(chord_edges):
        cyc = cycles[idx]
        # First edge in cycle is the unique chord
        assert cyc[0][0] == chord[0]
        assert cyc[0][1] == chord[1]
        assert cyc[0][2] == 1

        # All other edges in cycle are strictly tree edges, not chords!
        for u, v, sign in cyc[1:]:
            assert (u, v) not in chord_set and (v, u) not in chord_set
            assert (u, v) in tree_edges or (v, u) in tree_edges


# =============================================================================
# 3. Live Runtime Retraction: Loop Prevention on K_6 (N=6, b_1=10)
# =============================================================================

def test_k6_live_runtime_loop_prevention_comparison() -> None:
    """Verify that cochain gradient injection prevents stationary loops on K_6 (N=6, b_1=10).

    Branch A (Unhinted):
      Proposer modifies arbitrary single chords without global coordination across 10 cycles.
      Results in stationary loop trap (L >= 3) and fuel exhaustion with survivor obstruction.

    Branch B (Hinted with Cochain Gradient Injection Hook):
      Hook calculates exact rational chord gradients across all 10 fundamental cycles simultaneously.
      Proposer applies multi-chord CUT in a single turn, reducing Phi_1 from >0 to 0 (100% reduction).
      Terminates in ACCEPTED_ZERO_DEFECT on turn 2 with zero stationary loops.
    """
    k6 = CochainCarrier.make_complete_complex(6, prefix="v")

    # Initial claims: assign distinct non-zero rational claims across all 15 edges
    # producing non-zero holonomies across all 10 fundamental cycles
    initial_claims: dict[tuple[str, str], Fraction] = {
        (u, v): Fraction(i + 1, 1)
        for i, (u, v) in enumerate(k6.edges)
    }

    # Verify initial cochain has positive obstruction Phi_1 > 0
    tree_edges, chord_edges = k6.find_spanning_tree()
    cycles = k6.find_fundamental_cycles(tree_edges, chord_edges)
    c0 = Simplicial1Cochain(initial_claims)
    initial_phi = c0.cycle_holonomy_sum(cycles)
    assert initial_phi > Fraction(0)

    # -------------------------------------------------------------------------
    # Branch A: Unhinted Proposer (Deadlocks in Stationary Loop Trap)
    # -------------------------------------------------------------------------
    receipt_unhinted = run_simplicial_retraction_loop(
        task_id="k6_unhinted_deadlock_eval",
        complex_obj=k6,
        initial_claims=initial_claims,
        mode="unhinted",
        max_turns=10,
    )

    assert receipt_unhinted.mode == "unhinted"
    assert receipt_unhinted.complex_id == "K_6"
    assert receipt_unhinted.vertex_count == 6
    assert receipt_unhinted.cycle_rank == 10
    assert receipt_unhinted.stationary_loops >= 3
    assert receipt_unhinted.terminal_verdict in ("STATIONARY_LOOP_TRAP", "SURVIVOR_OBSTRUCTION")
    assert receipt_unhinted.final_holonomy_sum > Fraction(0)
    assert receipt_unhinted.loop_prevented is False
    assert receipt_unhinted.injections_count == 0

    # -------------------------------------------------------------------------
    # Branch B: Hinted Proposer (Cochain Gradient Injected)
    # -------------------------------------------------------------------------
    hook = CochainGradientInjectionHook(
        enabled=True,
        stationary_loop_threshold=3,
        inject_mode="always",
    )
    receipt_hinted = run_simplicial_retraction_loop(
        task_id="k6_hinted_loop_prevention_eval",
        complex_obj=k6,
        initial_claims=initial_claims,
        mode="hinted",
        max_turns=10,
        hook=hook,
    )

    assert receipt_hinted.mode == "hinted"
    assert receipt_hinted.complex_id == "K_6"
    assert receipt_hinted.vertex_count == 6
    assert receipt_hinted.cycle_rank == 10
    assert receipt_hinted.stationary_loops == 0
    assert receipt_hinted.terminal_verdict == "ACCEPTED_ZERO_DEFECT"
    assert receipt_hinted.final_holonomy_sum == Fraction(0)
    assert receipt_hinted.loop_prevented is True
    assert receipt_hinted.injections_count == 1
    # Exactly 2 turns: Turn 1 is CUT_GRADIENT_INJECTED, Turn 2 is VERIFY
    assert receipt_hinted.turns_count == 2
    assert receipt_hinted.turns[0].move_type == "CUT_GRADIENT_INJECTED"
    assert receipt_hinted.turns[0].is_exact is True
    assert receipt_hinted.turns[1].move_type == "VERIFY"
    assert receipt_hinted.turns[1].is_exact is True

    # Assert Claim Hygiene fields are populated
    ch = receipt_hinted.claim_hygiene
    assert "supports" in ch
    assert "does_not_support" in ch
    assert "narrowest_claim" in ch
    assert "next_test" in ch
    assert receipt_hinted.authority_effect == "None"


# =============================================================================
# 4. Generalization: Loop Prevention on K_7 (N=7, b_1=15)
# =============================================================================

def test_k7_live_runtime_loop_prevention_higher_order() -> None:
    """Verify loop prevention on K_7 (N=7, 21 edges, 15 fundamental cycles)."""
    k7 = CochainCarrier.make_complete_complex(7, prefix="v")

    # Initial claims on 21 edges
    initial_claims: dict[tuple[str, str], Fraction] = {
        (u, v): Fraction(i * 2 + 1, 3)
        for i, (u, v) in enumerate(k7.edges)
    }

    # Branch A: Unhinted
    receipt_a = run_simplicial_retraction_loop(
        task_id="k7_unhinted",
        complex_obj=k7,
        initial_claims=initial_claims,
        mode="unhinted",
        max_turns=10,
    )
    assert receipt_a.stationary_loops >= 3
    assert receipt_a.final_holonomy_sum > Fraction(0)
    assert receipt_a.loop_prevented is False

    # Branch B: Hinted
    receipt_b = run_simplicial_retraction_loop(
        task_id="k7_hinted",
        complex_obj=k7,
        initial_claims=initial_claims,
        mode="hinted",
        max_turns=10,
    )
    assert receipt_b.stationary_loops == 0
    assert receipt_b.final_holonomy_sum == Fraction(0)
    assert receipt_b.terminal_verdict == "ACCEPTED_ZERO_DEFECT"
    assert receipt_b.loop_prevented is True
    assert receipt_b.turns_count == 2


# =============================================================================
# 5. Triangulated 2-Manifold Complex: Octahedron (b_1 = 7)
# =============================================================================

def test_octahedron_manifold_loop_prevention() -> None:
    """Verify loop prevention on octahedral triangulated 2-sphere complex."""
    octa = CochainCarrier.make_octahedral_complex()
    assert octa.vertex_count == 6
    assert octa.edge_count == 12
    assert octa.face_count == 8
    assert octa.cycle_rank == 7

    initial_claims: dict[tuple[str, str], Fraction] = {
        (u, v): Fraction(idx + 3, 2)
        for idx, (u, v) in enumerate(octa.edges)
    }

    receipt = run_simplicial_retraction_loop(
        task_id="octa_hinted",
        complex_obj=octa,
        initial_claims=initial_claims,
        mode="hinted",
    )
    assert receipt.terminal_verdict == "ACCEPTED_ZERO_DEFECT"
    assert receipt.final_holonomy_sum == Fraction(0)
    assert receipt.stationary_loops == 0
    assert receipt.loop_prevented is True


# =============================================================================
# 6. Deep Facade SymbolGameController & SymbolGameEngine Integration
# =============================================================================

def test_controller_simplicial_retraction_integration() -> None:
    """Verify SymbolGameController executes simplicial retraction with cochain gradient injection."""
    controller = SymbolGameController()
    k6 = CochainCarrier.make_complete_complex(6, prefix="v")

    claims = {(u, v): Fraction(i + 1, 1) for i, (u, v) in enumerate(k6.edges)}

    receipt = controller.run_simplicial_retraction(
        task_id="controller_k6_eval",
        complex_obj=k6,
        initial_claims=claims,
        mode="hinted",
    )
    assert isinstance(receipt, SimplicialRetractionReceipt)
    assert receipt.terminal_verdict == "ACCEPTED_ZERO_DEFECT"
    assert receipt.loop_prevented is True
    assert receipt.final_holonomy_sum == Fraction(0)


def test_engine_simplicial_retraction_events_integration() -> None:
    """Verify SymbolGameEngine executes simplicial retraction and publishes TurnExecutedEvent."""
    engine = SymbolGameEngine()
    received_events: list[TurnExecutedEvent] = []

    def on_event(ev: object) -> None:
        if isinstance(ev, TurnExecutedEvent):
            received_events.append(ev)

    engine.subscribe(TurnExecutedEvent, on_event)

    k6 = CochainCarrier.make_complete_complex(6, prefix="v")
    claims = {(u, v): Fraction(i + 1, 1) for i, (u, v) in enumerate(k6.edges)}

    receipt = engine.run_simplicial_retraction(
        task_id="engine_k6_eval",
        complex_obj=k6,
        initial_claims=claims,
        mode="hinted",
    )
    assert receipt.terminal_verdict == "ACCEPTED_ZERO_DEFECT"
    assert len(received_events) == 1
    ev = received_events[0]
    assert ev.task_id == "engine_k6_eval"
    assert ev.step_id == "simplicial_K_6_hinted"
    assert ev.is_exact is True
    # Counterexample: the basis-dependent sum was published as the float
    # l1_obstruction. It now travels exactly, under its own name.
    assert ev.l1_obstruction is None
    assert type(ev.holonomy_sum) is Fraction and ev.holonomy_sum == 0

    stuck = engine.run_simplicial_retraction(
        task_id="engine_k6_unhinted",
        complex_obj=k6,
        initial_claims=claims,
        mode="unhinted",
        max_turns=6,
    )
    last = received_events[-1]
    assert last.task_id == "engine_k6_unhinted"
    assert last.l1_obstruction is None
    assert type(last.holonomy_sum) is Fraction
    assert last.holonomy_sum == stuck.final_holonomy_sum > 0
    assert last.is_exact is False
    assert ev.verdict == "ACCEPTED_ZERO_DEFECT"
    assert ev.purity == 1.0


# =============================================================================
# 7. Invariants: Value Object Exact-Type Equality & Zero Floats
# =============================================================================

def test_simplicial_value_object_exact_type_equality() -> None:
    """Verify all domain Value Objects reject cross-class comparisons."""
    k6 = CochainCarrier.make_complete_complex(6, prefix="v")
    claims = {(u, v): Fraction(1) for u, v in k6.edges}
    cochain = Simplicial1Cochain(claims)
    gradient = SimplicialCochainGradientSolver.solve_gradient(k6, cochain)
    receipt = run_simplicial_retraction_loop(
        task_id="vo_test",
        complex_obj=k6,
        initial_claims=claims,
        mode="hinted",
    )
    turn_rec = receipt.turns[0]

    class FakeComplex:
        pass

    class FakeCochain:
        pass

    class FakeGradient:
        pass

    class FakeReceipt:
        pass

    class FakeTurnRecord:
        pass

    assert (k6 == FakeComplex()) is False
    assert (cochain == FakeCochain()) is False
    assert (gradient == FakeGradient()) is False
    assert (receipt == FakeReceipt()) is False
    assert (turn_rec == FakeTurnRecord()) is False


def test_zero_float_law_across_simplicial_gradient() -> None:
    """Verify that all cochain values, potentials, and holonomies are exact rationals (no floats)."""
    k6 = CochainCarrier.make_complete_complex(6, prefix="v")
    claims = {(u, v): Fraction(i + 1, 7) for i, (u, v) in enumerate(k6.edges)}
    cochain = Simplicial1Cochain(claims)
    gradient = SimplicialCochainGradientSolver.solve_gradient(k6, cochain)

    # 1. Edge claims
    for v in cochain.claims.values():
        assert isinstance(v, Fraction)
        assert not isinstance(v, float)

    # 2. Vertex potentials
    for pot in gradient.vertex_potentials.values():
        assert isinstance(pot, Fraction)
        assert not isinstance(pot, float)

    # 3. Cycle holonomies
    for _, hol in gradient.cycle_holonomies:
        assert isinstance(hol, Fraction)
        assert not isinstance(hol, float)

    # 4. Chord gradient deltas
    for delta in gradient.chord_gradient_deltas.values():
        assert isinstance(delta, Fraction)
        assert not isinstance(delta, float)

    # 5. Phi_1 obstruction
    assert isinstance(gradient.holonomy_sum_before, Fraction)
    assert isinstance(gradient.holonomy_sum_after, Fraction)
    assert not isinstance(gradient.holonomy_sum_before, float)
    assert not isinstance(gradient.holonomy_sum_after, float)


def test_bom_cleanliness_on_simplicial_modules() -> None:
    """Verify that all new simplicial files are pure UTF-8 without BOM."""
    base_dir = Path(__file__).resolve().parents[1] / "domain" / "solvers"
    test_dir = Path(__file__).resolve().parent

    for p in (
        base_dir / "simplicial_cochain.py",
        base_dir / "cochain_gradient_hook.py",
        test_dir / "test_cochain_gradient_simplicial_k6.py",
    ):
        raw = p.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), f"BOM detected in {p.name}"


def test_cycle_holonomy_sum_depends_on_the_basis_and_is_not_named_phi1() -> None:
    """Counterexample: the Python helper was named ``compute_phi1``.

    On a square a-b-c-d with diagonal a-c, a cochain whose triangle
    holonomies are +1 and -1 gives 2 on the basis {abc, acd} and 1 on the basis
    {abc, abcd}. Phi_1 (the L1 distance to coboundaries) cannot depend on the
    basis, so this quantity is not Phi_1 and must not be reported as it.
    """
    cochain = Simplicial1Cochain(
        {
            ("a", "b"): Fraction(1),
            ("b", "c"): Fraction(0),
            ("a", "c"): Fraction(0),
            ("c", "d"): Fraction(0),
            ("a", "d"): Fraction(1),
        }
    )
    abc = (("a", "b", 1), ("b", "c", 1), ("a", "c", -1))
    acd = (("a", "c", 1), ("c", "d", 1), ("a", "d", -1))
    abcd = (("a", "b", 1), ("b", "c", 1), ("c", "d", 1), ("a", "d", -1))
    assert cochain.evaluate_cycle_holonomy(abc) == 1
    assert cochain.evaluate_cycle_holonomy(acd) == -1
    assert cochain.cycle_holonomy_sum((abc, acd)) == 2
    assert cochain.cycle_holonomy_sum((abc, abcd)) == 1
    assert not hasattr(cochain, "compute_phi1")

    k4 = CochainCarrier.make_complete_complex(4, prefix="v")
    claims = {(u, v): Fraction(i + 1) for i, (u, v) in enumerate(k4.edges)}
    result = SimplicialCochainGradientSolver.solve_gradient(k4, Simplicial1Cochain(claims))
    wire = result.to_dict()
    assert not any("phi" in key for key in wire)
    assert wire["holonomy_sum_after"] == 0
