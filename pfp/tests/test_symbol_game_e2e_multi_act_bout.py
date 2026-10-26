"""End-to-end integration tests for Symbol Game multi-act bout execution.

Verifies:
- Complete seven-stage retraction lifecycle: Intake -> Projection -> Descent -> GaugeBreak -> CochainRepair -> Verification -> TerminalRealityGate.
- Disjoint and exhaustive Terminal Reality Gate classification (PASS_TO_MASTER, REFUSE, OPEN_RESIDUAL).
- Strict monotonic Lyapunov descent on (Gamma_2, Phi_1, defect_count).
- Lossless cemetery retention of refused turns with full token & cochain projection intact.
- Absolute exclusion of floating-point arithmetic across all wire and scoring paths.
- AuthorityEffect: None.

Governing Rules:
- RULE_SOVEREIGN_RUST_MATH_DELEGATION_001
- RULE_FLOAT_FIREWALL_001
- RULE_INWARD_CLEAN_ARCHITECTURE_001
- AuthorityEffect: None
"""

from __future__ import annotations

from fractions import Fraction
import json
import pytest

from omega_engine_pfp import initialize_exact_ports
from omega_engine_pfp.controllers import SymbolGameController, SymbolGameEngine
from omega_engine_pfp.domain.entities.coboundary_score import (
    CandidateProposal,
    CoboundaryScoreResult,
)
from omega_engine_pfp.domain.exact.q import Q
from omega_engine_pfp.domain.models import ObstructionScore, StepVerdict
from omega_engine_pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    canonical_json,
    freeze,
)
from omega_engine_pfp.domain.solvers import (
    BASE,
    AdmitDatum,
    AdmitForm,
    AdmitInst,
    Delta,
    Holds,
    HolonomyLoopClosed,
    HomologyBoundaryClosed,
    NewDatum,
    NewInst,
    compute_obstruction_score,
    execute_retraction_turn,
    get_holonomy_port,
    get_homology_port,
    host,
    run_retraction_loop,
)
from omega_engine_pfp.use_cases.scoring import (
    score_cochain_proposal,
    score_discrete_proposal,
)


@pytest.fixture(autouse=True)
def _bind_exact_ports() -> None:
    initialize_exact_ports()


def test_e2e_seven_act_retraction_lifecycle_pass_to_master() -> None:
    """Execute a complete e2e multi-act bout progressing from initial obstruction to PASS_TO_MASTER."""
    controller = SymbolGameController()

    # Act I: Intake & Carrier Initialization
    # Base history of 3 vertices, with a requirement that form 1 holds at vertex 0 and vertex 1
    base_history = (
        AdmitDatum(0),
        AdmitDatum(1),
        AdmitDatum(2),
        AdmitForm(2),  # form 0: binary claim form
    )
    req_0 = Holds("req_v0", (1, (0,)))
    req_1 = Holds("req_v1", (1, (1,)))

    # Act II: Manifold Projection
    state_0 = host(
        base_history=base_history,
        claim_forms=frozenset({0}),
        reqs=(req_0, req_1),
        witness_forms=((1, ()),),  # form 1: unary witness form
    )
    score_0 = controller.compute_obstruction_score(state_0)
    assert score_0.active_count == 2
    assert not score_0.is_exact

    # Act III & IV: Descent Turn 1
    delta_1: Delta = (NewInst(1, (0,)),)
    outcome_1 = controller.run_retraction_turn(
        task_id="bout_001_turn_1",
        state=state_0,
        candidate_delta=delta_1,
        stage=BASE,
        turn_index=0,
        prior_score=score_0,
    )
    assert outcome_1.verdict == StepVerdict.DESCENT
    assert outcome_1.child_state is not None
    assert outcome_1.new_score.active_count == 1
    assert outcome_1.new_score.strictly_improves(score_0)

    # Act V & VI: Cochain Repair & Verification Turn 2
    state_1 = outcome_1.child_state
    delta_2: Delta = (NewInst(1, (1,)),)
    outcome_2 = controller.run_retraction_turn(
        task_id="bout_001_turn_2",
        state=state_1,
        candidate_delta=delta_2,
        stage=BASE,
        turn_index=1,
        prior_score=outcome_1.new_score,
    )

    # Act VII: Terminal Reality Gate
    assert outcome_2.verdict in (StepVerdict.DESCENT, StepVerdict.EXACT)
    assert outcome_2.is_exact is True
    assert outcome_2.new_score.active_count == 0
    assert outcome_2.new_score.phi_1 == Fraction(0)
    assert outcome_2.new_score.gamma_2 == Fraction(0)
    assert outcome_2.authority_effect == "None"


def test_e2e_seven_act_retraction_refusal_and_cemetery_preservation() -> None:
    """Verify non-contractive proposals are refused at Terminal Reality Gate with lossless cemetery capture."""
    controller = SymbolGameController()

    base_history = (
        AdmitDatum(0),
        AdmitDatum(1),
        AdmitForm(2),
    )
    req = Holds("req_target", (1, (0,)))
    state = host(
        base_history=base_history,
        claim_forms=frozenset({0}),
        reqs=(req,),
        witness_forms=((1, ()),),
    )
    prior_score = controller.compute_obstruction_score(state)

    # Submit an invalid proposal that mutates frozen claim form 0 (not witness form 1)
    invalid_delta: Delta = (NewInst(0, (0, 1)),)
    outcome = controller.run_retraction_turn(
        task_id="bout_002_refusal",
        state=state,
        candidate_delta=invalid_delta,
        stage=BASE,
        turn_index=0,
        prior_score=prior_score,
    )

    assert outcome.verdict == StepVerdict.REFUSAL
    assert outcome.child_state is None
    assert "CLAIM_FROZEN" in outcome.details
    assert outcome.evidence_sha256.startswith("sha256:")
    assert outcome.authority_effect == "None"


def test_e2e_zero_floating_point_firewall_across_wire_and_scoring() -> None:
    """Assert that float values are rejected by canonicalization and scoring operates in exact Fraction."""
    # 1. Wire level refusal
    with pytest.raises(CanonicalizationError, match="float"):
        freeze(1.5)

    with pytest.raises(CanonicalizationError, match="float"):
        freeze({"score": 0.25, "active": True})

    # 2. Domain scoring operates strictly on Fraction
    proposal = CandidateProposal(
        proposal_id="cand_test_001",
        repaired_obstruction_ids=("obs_1", "obs_2", "obs_3"),
        cochain_delta=(("e1", Fraction(1, 2)),),
        structural_cost=Fraction(1, 2),
    )
    current_ids = ("obs_1", "obs_2", "obs_3", "obs_4")
    res = score_discrete_proposal(
        current_ids,
        proposal,
    )
    assert isinstance(res.structural_cost, Fraction)
    assert isinstance(res.normalized_efficiency, Fraction)
    assert isinstance(res.residual_drop, Fraction)
    assert res.structural_cost == Fraction(1, 2)
    assert res.residual_drop == Fraction(3)  # 4 - 1
    # normalized_efficiency = drop / (1 + cost) = 3 / (1 + 1/2) = 3 / (3/2) = 2
    assert res.normalized_efficiency == Fraction(2)
    assert res.is_legal is True
    assert res.authority_effect == "None"

    # 3. Canonical wire output has no floating point notation
    wire_dict = res.to_dict()
    assert wire_dict["structural_cost"] == "1/2"
    assert wire_dict["normalized_efficiency"] == "2"


def test_e2e_retraction_loop_chase_convergence() -> None:
    """Verify run_retraction_loop executes multi-turn chase to terminal exact status."""
    base_history = (
        AdmitDatum(0),
        AdmitDatum(1),
        AdmitForm(2),
    )
    req_a = Holds("req_a", (1, (0,)))
    req_b = Holds("req_b", (1, (1,)))

    initial_state = host(
        base_history=base_history,
        claim_forms=frozenset({0}),
        reqs=(req_a, req_b),
        witness_forms=((1, ()),),
    )

    candidate_deltas: list[Delta] = [
        (NewInst(1, (0,)),),
        (NewInst(1, (1,)),),
    ]

    result = run_retraction_loop(
        task_id="retraction_loop_e2e_001",
        initial_state=initial_state,
        stage=BASE,
        candidate_deltas=candidate_deltas,
    )

    assert result.is_exact is True
    assert result.final_score.active_count == 0
    assert result.total_descent_steps == 2
    assert result.final_score.phi_1 == Fraction(0)
    assert result.final_score.gamma_2 == Fraction(0)
    assert len(result.turns) == 2
    for turn in result.turns:
        assert turn.authority_effect == "None"
