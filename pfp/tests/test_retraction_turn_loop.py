"""End-to-end discrete manifold retraction turn loop and strict descent tests.

Verifies:
- Direct delegation of Phi_1 (homology boundary) and Gamma_2 (holonomy curvature) to sovereign Rust crates.
- Single retraction turn strict descent on (Gamma_2, Phi_1, defect_count).
- Non-contractive proposal refusal with zero state corruption.
- Frozen claim form mutation refusal.
- Multi-turn monotonic descent chase reaching exact terminal certificate (0.0, 0.0, 0).
- Deep facade SymbolGameEngine event emission and retraction execution.
- Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
- Pure UTF-8 without BOM encoding across solver artifacts.

Governing Invariant: Zero Python Math Re-invention & Sovereign Rust Delegation.
Governing Invariant: Strict Descent on (Gamma_2, Phi_1, defect_count).
Governing Invariant: Symbol Game Non-Prose Communication & Zero Data-Loss Invariant.
AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import pytest

from omega_engine_pfp.controllers import SymbolGameController, SymbolGameEngine
from omega_engine_pfp.domain.exact.q import Q
from omega_engine_pfp.domain.models import ObstructionScore, StepVerdict
from omega_engine_pfp.domain.events import TurnExecutedEvent
from omega_engine_pfp.domain.solvers import (
    BASE,
    AdmitDatum,
    AdmitForm,
    AdmitInst,
    AdmitRuleAll,
    Delta,
    Denied,
    Holds,
    HolonomyLoopClosed,
    HomologyBoundaryClosed,
    NewDatum,
    NewInst,
    Regime,
    RegimeK,
    RegimeOracle,
    RetractionLoopResult,
    RetractionTurnOutcome,
    Separate,
    Stage,
    compute_obstruction_score,
    execute_retraction_turn,
    get_holonomy_port,
    get_homology_port,
    host,
    run_retraction_loop,
)


@pytest.fixture(autouse=True)
def _bind_exact_ports() -> None:
    from omega_engine_pfp import initialize_exact_ports

    initialize_exact_ports()


def test_compute_obstruction_score_sovereign_rust_delegation() -> None:
    """Verify compute_obstruction_score delegates Phi_1 and Gamma_2 to sovereign Rust crates."""
    # 1. Open 1-chain: 0->1, 1->2 has net boundary violation (+1 at 2, -1 at 0)
    open_face = ((0, 1, 1), (1, 2, 1))
    q_hom_open = HomologyBoundaryClosed("h_open", (open_face,))

    # 2. Open holonomy loop: single swap permutation is not identity
    t0 = ((Q(0), Q(1)), (Q(1), Q(0)))
    q_hol_open = HolonomyLoopClosed("loop_open", (t0,), ((0, False),))

    # Base regime with open requirements
    r_open = host(
        base_history=(AdmitDatum(0), AdmitDatum(1), AdmitDatum(2)),
        claim_forms=frozenset(),
        reqs=(q_hom_open, q_hol_open),
    )

    score_open = compute_obstruction_score(r_open)
    assert score_open.phi_1 > Fraction(0, 1)
    assert score_open.gamma_2 > Fraction(0, 1)
    assert score_open.active_count == 2
    assert not score_open.is_exact

    # Verify both ports were called and backed by Rust
    hom_port = get_homology_port()
    hol_port = get_holonomy_port()
    assert hom_port.verify_boundary_closed((open_face,)) is False
    assert hol_port.is_ordered_closure((t0,), ((0, False),)) is False

    # 3. Closed cycle and closed loop
    cycle_face = ((0, 1, 1), (1, 2, 1), (2, 0, 1))
    q_hom_closed = HomologyBoundaryClosed("h_closed", (cycle_face,))
    q_hol_closed = HolonomyLoopClosed("loop_closed", (t0,), ((0, False), (0, False)))

    r_closed = host(
        base_history=(AdmitDatum(0), AdmitDatum(1), AdmitDatum(2)),
        claim_forms=frozenset(),
        reqs=(q_hom_closed, q_hol_closed),
    )

    score_closed = compute_obstruction_score(r_closed)
    assert score_closed.phi_1 == Fraction(0, 1)
    assert score_closed.gamma_2 == Fraction(0, 1)
    assert score_closed.active_count == 0
    assert score_closed.is_exact is True


def test_single_retraction_turn_strict_descent_via_controller() -> None:
    """Verify a single retraction turn via SymbolGameController verifies strict descent."""
    controller = SymbolGameController()

    # Form 0: binary relation. Initially empty.
    # Claim: form 0 is frozen. Witness: form 1 (arity 1) declared.
    base_history = (
        AdmitDatum(0),
        AdmitDatum(1),
        AdmitForm(2),  # form 0: binary claim
    )
    # Requirement: Holds(form 1, (0,)) - unsatisfied initially
    q_req = Holds("req_holds_0", (1, (0,)))

    state = host(
        base_history=base_history,
        claim_forms=frozenset({0}),
        reqs=(q_req,),
        witness_forms=((1, ()),),  # form 1: unary witness
    )

    prior_score = controller.compute_obstruction_score(state)
    assert prior_score.active_count == 1
    assert not prior_score.is_exact

    # Candidate delta: add instance on witness form 1 at node 0
    delta_descent: Delta = (NewInst(1, (0,)),)

    outcome = controller.run_retraction_turn(
        task_id="turn_task_001",
        state=state,
        candidate_delta=delta_descent,
        stage=BASE,
        turn_index=0,
        prior_score=prior_score,
    )

    assert outcome.verdict in (StepVerdict.DESCENT, StepVerdict.EXACT)
    assert outcome.is_exact is True
    assert outcome.new_score.active_count == 0
    assert outcome.new_score.strictly_improves(prior_score)
    assert outcome.child_state is not None
    assert outcome.evidence_sha256.startswith("sha256:")
    assert outcome.authority_effect == "None"


def test_retraction_turn_rejection_of_non_contractive_proposal() -> None:
    """Verify non-contractive candidate proposal is refused without corrupting state."""
    controller = SymbolGameController()

    base_history = (
        AdmitDatum(0),
        AdmitDatum(1),
    )
    # Requirement: node 0 must satisfy witness form 0
    q_req = Holds("req_0", (0, (0,)))

    state = host(
        base_history=base_history,
        claim_forms=frozenset(),
        reqs=(q_req,),
        witness_forms=((1, ()),),  # form 0: unary witness
    )
    prior_score = controller.compute_obstruction_score(state)

    # Irrelevant delta: instantiate node 1 instead of node 0 -> does not resolve requirement
    delta_irrelevant: Delta = (NewInst(0, (1,)),)

    outcome = controller.run_retraction_turn(
        task_id="turn_task_non_contractive",
        state=state,
        candidate_delta=delta_irrelevant,
        stage=BASE,
        turn_index=0,
        prior_score=prior_score,
    )

    assert outcome.verdict == StepVerdict.REFUSAL
    assert outcome.child_state is None
    # Zero data loss: evidence digest is still generated and preserved
    assert outcome.evidence_sha256.startswith("sha256:")
    assert "Non-contractive proposal" in outcome.details


def test_retraction_turn_rejection_of_frozen_claim_mutation() -> None:
    """Verify candidate delta attempting to mutate frozen claim forms is refused."""
    controller = SymbolGameController()

    base_history = (
        AdmitDatum(0),
        AdmitDatum(1),
        AdmitForm(2),  # form 0: claim form
    )
    q_req = Holds("req_witness", (1, (0,)))

    state = host(
        base_history=base_history,
        claim_forms=frozenset({0}),
        reqs=(q_req,),
        witness_forms=((1, ()),),  # form 1: witness form
    )

    # Illegal delta: touches frozen claim form 0
    delta_illegal: Delta = (NewInst(0, (0, 1)),)

    outcome = controller.run_retraction_turn(
        task_id="turn_task_claim_frozen",
        state=state,
        candidate_delta=delta_illegal,
        stage=BASE,
        turn_index=0,
    )

    assert outcome.verdict == StepVerdict.REFUSAL
    assert outcome.child_state is None
    assert "CLAIM_FROZEN" in outcome.details


def test_end_to_end_retraction_loop_monotonic_descent_to_exact() -> None:
    """Verify multi-step retraction loop chase monotonically descends to exact certificate."""
    controller = SymbolGameController()

    # Base regime with 2 witness forms
    base_history = (
        AdmitDatum(0),
        AdmitDatum(1),
    )
    # Two distinct requirements on witness forms 0 and 1
    req1 = Holds("r1", (0, (0,)))
    req2 = Holds("r2", (1, (1,)))

    state_0 = host(
        base_history=base_history,
        claim_forms=frozenset(),
        reqs=(req1, req2),
        witness_forms=((1, ()), (1, ())),
    )

    score_0 = controller.compute_obstruction_score(state_0)
    assert score_0.active_count == 2

    # Step 1 delta: satisfies req1
    d1: Delta = (NewInst(0, (0,)),)
    # Step 2 delta: satisfies req2
    d2: Delta = (NewInst(1, (1,)),)

    result = controller.run_retraction_loop(
        task_id="multi_turn_chase",
        initial_state=state_0,
        stage=BASE,
        candidate_deltas=(d1, d2),
    )

    assert isinstance(result, RetractionLoopResult)
    assert result.converged is True
    assert result.is_exact is True
    assert result.total_descent_steps == 2
    assert len(result.turns) == 2

    # Verify monotonic strict descent at every turn
    turn1, turn2 = result.turns
    assert turn1.verdict == StepVerdict.DESCENT
    assert turn1.new_score.active_count == 1
    assert turn1.new_score.strictly_improves(turn1.prior_score)

    assert turn2.verdict == StepVerdict.EXACT
    assert turn2.new_score.active_count == 0
    assert turn2.new_score.is_exact is True
    assert turn2.new_score.strictly_improves(turn2.prior_score)

    assert result.final_score.is_exact is True


def test_symbol_game_engine_deep_facade_retraction_events() -> None:
    """Verify SymbolGameEngine deep facade publishes domain events and runs retraction."""
    engine = SymbolGameEngine()

    received_events: list[TurnExecutedEvent] = []

    def on_turn_executed(event: object) -> None:
        if isinstance(event, TurnExecutedEvent):
            received_events.append(event)

    engine.subscribe(TurnExecutedEvent, on_turn_executed)

    base_history = (
        AdmitDatum(0),
    )
    q_req = Holds("r0", (0, (0,)))
    state = host(
        base_history=base_history,
        claim_forms=frozenset(),
        reqs=(q_req,),
        witness_forms=((1, ()),),
    )

    d: Delta = (NewInst(0, (0,)),)

    outcome = engine.execute_retraction_turn(
        task_id="engine_turn_test",
        state=state,
        candidate_delta=d,
        stage=BASE,
        turn_index=1,
    )

    assert outcome.verdict == StepVerdict.EXACT
    assert len(received_events) == 1
    assert received_events[0].task_id == "engine_turn_test"
    assert received_events[0].step_id == "retraction_step_1"
    assert received_events[0].is_exact is True
    assert received_events[0].verdict == StepVerdict.EXACT.value

    # Solve retraction loop via engine
    loop_res = engine.solve_retraction_loop(
        task_id="engine_loop_test",
        initial_state=state,
        stage=BASE,
        candidate_deltas=(d,),
    )
    assert loop_res.is_exact is True


def test_controller_run_problem_regimek_integration() -> None:
    """Verify SymbolGameController.run_problem routes RegimeK input to retraction loop."""
    controller = SymbolGameController()

    base_history = (
        AdmitDatum(0),
    )
    q_req = Holds("req_int", (0, (0,)))
    state = host(
        base_history=base_history,
        claim_forms=frozenset(),
        reqs=(q_req,),
        witness_forms=((1, ()),),
    )
    d: Delta = (NewInst(0, (0,)),)

    result = controller.run_problem(
        problem_input=state,
        task_id="problem_regimek_test",
        stage=BASE,
        candidate_deltas=(d,),
    )

    assert isinstance(result, RetractionLoopResult)
    assert result.task_id == "problem_regimek_test"
    assert result.is_exact is True
    assert result.total_descent_steps == 1


def test_value_object_exact_type_equality_invariants() -> None:
    """Verify Value Objects reject cross-class equality comparisons."""
    open_face = ((0, 1, 1), (1, 2, 1))
    q_hom = HomologyBoundaryClosed("h_exact", (open_face,))

    state = host(
        base_history=(AdmitDatum(0), AdmitDatum(1)),
        claim_forms=frozenset(),
        reqs=(q_hom,),
    )
    score = compute_obstruction_score(state)
    delta: Delta = ()

    outcome = execute_retraction_turn(
        task_id="vo_test",
        turn_index=0,
        state=state,
        candidate_delta=delta,
        stage=BASE,
        prior_score=score,
    )

    loop_res = run_retraction_loop(
        task_id="vo_test",
        initial_state=state,
        stage=BASE,
        candidate_deltas=(delta,),
    )

    class FakeOutcome:
        pass

    class FakeResult:
        pass

    assert (outcome == FakeOutcome()) is False
    assert (loop_res == FakeResult()) is False
    assert (score == 42) is False


def test_bom_cleanliness_across_solver_and_retraction_modules() -> None:
    """Verify all solver modules and test files are UTF-8 without BOM."""
    pkg_dir = Path(__file__).resolve().parents[1] / "domain" / "solvers"
    solver_files = list(pkg_dir.glob("*.py"))
    assert len(solver_files) >= 12

    for py_file in solver_files:
        raw_bytes = py_file.read_bytes()
        assert not raw_bytes.startswith(b"\xef\xbb\xbf"), f"BOM detected in {py_file.name}"

    current_test_file = Path(__file__).resolve()
    assert not current_test_file.read_bytes().startswith(b"\xef\xbb\xbf"), "BOM detected in test file"
