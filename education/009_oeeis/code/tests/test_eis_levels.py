"""Comprehensive unit tests for Epistemic Immune System (Levels 00–10).

AuthorityEffect: None.
"""

from __future__ import annotations

from eis_core import (
    Antibody,
    Antigen,
    AntimorphismEmitter,
    ClonalSelectionEngine,
    ExternalAdmissionBoundary,
    FixtureGate,
    InnateBarrier,
    ProvisionalCustody,
    RolePartition,
    SelfSpec,
    SupportPolicy,
    ThymusGate,
    TregSupervisor,
    TwoSignalGuard,
)


def test_level_00_innate_barriers():
    barrier = InnateBarrier(max_bytes=100)
    # Valid payload
    ag_valid = Antigen(
        id=1, payload="def add(a: int, b: int) -> int: return a + b", claims=(), source="local"
    )
    ok, err = barrier.validate_payload(ag_valid)
    assert ok is True
    assert err is None

    # Oversized payload
    ag_huge = Antigen(id=2, payload="x" * 200, claims=(), source="external")
    ok_huge, err_huge = barrier.validate_payload(ag_huge)
    assert ok_huge is False
    assert "exceeds limit" in err_huge

    # Forbidden hype word
    ag_hype = Antigen(
        id=3,
        payload="This safe ASI architecture solves all problems",
        claims=(),
        source="untrusted",
    )
    ok_hype, err_hype = barrier.validate_payload(ag_hype)
    assert ok_hype is False
    assert "Forbidden" in err_hype


def test_level_01_component_role_partitioning():
    # Strict triad separation
    assert (
        RolePartition.verify_triad_separation("agent_proposer", "agent_reviewer", "agent_verifier")
        is True
    )

    # Collision of roles rejected
    assert (
        RolePartition.verify_triad_separation("agent_proposer", "agent_proposer", "agent_verifier")
        is False
    )
    assert (
        RolePartition.verify_triad_separation("agent_proposer", "agent_reviewer", "agent_reviewer")
        is False
    )


def test_level_02_fixture_polarity_and_near_misses():
    gate = FixtureGate()
    gate.add_positive_fixture("assert x > 0")
    gate.add_negative_fixture("assert x >= 0")  # near-miss boundary

    def strict_gt_detector(text: str) -> bool:
        return ">" in text and ">=" not in text

    passed, accuracy = gate.evaluate_detector(strict_gt_detector)
    assert passed is True
    assert accuracy == 1.0

    def loose_detector(text: str) -> bool:
        return ">" in text  # erroneously matches near-miss

    passed_loose, accuracy_loose = gate.evaluate_detector(loose_detector)
    assert passed_loose is False
    assert accuracy_loose == 0.5


def test_level_03_central_tolerance_and_thymus_gate():
    core_spec = SelfSpec(spec_id=1, name="retraction_identity", invariant_pattern="r(u(x)) == x")
    thymus = ThymusGate(protected_specs=[core_spec])

    # Safe antibody targeting an external failure pattern
    safe_ab = Antibody(
        id=101, target_pattern="unbounded_recursion_overflow", affinity_threshold=0.8
    )
    admitted, conflicting_spec = thymus.test_negative_selection(safe_ab)
    assert admitted is True
    assert conflicting_spec is None

    # Self-reactive antibody attacking protected baseline specification
    autoimmune_ab = Antibody(id=102, target_pattern="r(u(x)) == x", affinity_threshold=0.9)
    admitted_auto, conflicting_spec_auto = thymus.test_negative_selection(autoimmune_ab)
    assert admitted_auto is False
    assert conflicting_spec_auto.name == "retraction_identity"


def test_level_04_learned_guard_two_signal_activation():
    ab = Antibody(id=201, target_pattern="hallucinated_import", affinity_threshold=0.7)
    guard = TwoSignalGuard(ab)

    # Signal 1 only: quiescent (no alarm without co-stimulatory danger signal)
    status_s1 = guard.evaluate("contains hallucinated_import here", danger_signal_present=False)
    assert status_s1 == "SIGNAL1_ONLY_QUIESCENT"

    # Both Signal 1 and Signal 2: fully activated immune response
    status_both = guard.evaluate("contains hallucinated_import here", danger_signal_present=True)
    assert status_both == "ACTIVATED_IMMUNE_RESPONSE"

    # Anergic antibody is suppressed regardless of signals
    anergic_ab = Antibody(
        id=202, target_pattern="hallucinated_import", affinity_threshold=0.7, is_anergic=True
    )
    anergic_guard = TwoSignalGuard(anergic_ab)
    assert (
        anergic_guard.evaluate("contains hallucinated_import here", danger_signal_present=True)
        == "SUPPRESSED_BY_TREG"
    )


def test_level_05_independent_observation_support_policy():
    policy = SupportPolicy(required_k=3)

    # 3 distinct channels approving
    witnesses_pass = [("channel_pytest", True), ("channel_linter", True), ("channel_lean4", True)]
    assert policy.check_consensus(witnesses_pass) is True

    # Duplicate channel does not satisfy k=3 independent witnesses
    witnesses_duplicate = [
        ("channel_pytest", True),
        ("channel_pytest", True),
        ("channel_linter", True),
    ]
    assert policy.check_consensus(witnesses_duplicate) is False


def test_level_06_provisional_custody_and_review_queue():
    custody = ProvisionalCustody(probation_evaluations=3)
    ab = Antibody(id=301, target_pattern="invalid_jwt_parse", affinity_threshold=0.85)
    custody.admit_provisional(ab)

    assert custody.is_promoted(301) is False
    custody.record_evaluation(301, was_false_alarm=False)
    custody.record_evaluation(301, was_false_alarm=False)
    assert custody.is_promoted(301) is False

    # 3rd clean evaluation triggers promotion
    promoted = custody.record_evaluation(301, was_false_alarm=False)
    assert promoted is True
    assert custody.is_promoted(301) is True


def test_level_07_clonal_selection_and_affinity():
    engine = ClonalSelectionEngine()
    ab = Antibody(id=401, target_pattern="syntax error unclosed paren", affinity_threshold=0.7)

    # Compute affinity
    aff = engine.compute_affinity(ab, "syntax error unclosed paren in parser")
    assert aff == 1.0  # all antibody tokens present in target

    # Somatic hypermutation
    refined = engine.somatic_hypermutation(ab, "lineno")
    assert "lineno" in refined.target_pattern
    assert refined.affinity_threshold > ab.affinity_threshold


def test_level_08_regulatory_supervision_and_anergy():
    treg = TregSupervisor(false_positive_threshold=0.20)
    ab = Antibody(id=501, target_pattern="overly_aggressive_filter", affinity_threshold=0.6)

    # Low false positives: no anergy
    assert treg.evaluate_regulatory_status(total_triggers=10, false_positives=1) is False

    # High false positives (3 / 10 = 30% >= 20%): triggers anergy
    should_suppress = treg.evaluate_regulatory_status(total_triggers=10, false_positives=3)
    assert should_suppress is True

    suppressed = treg.induce_anergy(ab)
    assert suppressed.is_anergic is True


def test_level_09_external_admission_boundary():
    innate = InnateBarrier(max_bytes=500)
    thymus = ThymusGate(protected_specs=[])
    perimeter = ExternalAdmissionBoundary(innate=innate, thymus=thymus)

    # Untrusted antigen with hype words rejected fail-closed
    ag_bad = Antigen(
        id=601, payload="We achieved flawless code execution", claims=(), source="external"
    )
    admitted, receipt = perimeter.filter_antigen(ag_bad)

    assert admitted is False
    assert receipt["admitted"] is False
    assert receipt["stage"] == "INNATE_BARRIER"
    assert receipt["authority_effect"] == "None"


def test_level_10_antimorphism_polarity_and_telemetry():
    emitter = AntimorphismEmitter()
    rcpt = emitter.emit_receipt(
        event_name="ANTIGEN_PROCESSED",
        subject_id=701,
        details={"result": "REFUSED", "reason_code": "CLAIM_HYGIENE_BREACH"},
        is_success=False,
    )

    assert rcpt["receipt_id"] == 1
    assert rcpt["authority_effect"] == "None"
    assert "digest" in rcpt
    assert len(rcpt["digest"]) == 64
    assert len(emitter.receipts) == 1
