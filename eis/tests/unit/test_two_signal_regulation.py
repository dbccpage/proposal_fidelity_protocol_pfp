"""Unit tests for Two-Signal Epistemic Immune Regulation (Milestone 1).

Verifies:
1. Thymic Central Tolerance (`ThymusSelfPanelBuilder`, `NormalizedMatcher`):
   - Falsification of naive strict-syntax detector via autoimmune apoptosis
   - Passing of normalized value-preserving matcher (zero autoimmune violations)
   - Proper match on genuine malformed antigens
2. Matzinger Two-Signal Danger Gate (`TwoSignalRegulatorV1`):
   - Signal 1 alone yields non-destructive diagnostic disposition (normalized output)
   - Signal 1 AND independent Host Signal 2 yields DEFENSIVE_LOCKDOWN / QUARANTINED
   - Rejection of Two-Signal Collapse (model-authored danger, duplicate predicate, overlapping spans)
3. Public-Invariant Mathematical Antibody Suite (`QMInvariantAntibodySuiteV1`):
   - Clean textbook pass across all 10 invariants
   - Hard invariant: final_answer_certified is ALWAYS False
   - Precise individual falsification of each invariant failure mode
4. Acquired Antibody Promotion via Conflict-Graph MIS (`AcquiredAntibodyPromotionV1`):
   - 5 correlated observations from same model/scaffold collapse to MIS = 1 ('Candidate')
   - 3 independent observations achieve MIS = 3 ('Provisional')
   - Refusal of propagated references and placeholders
5. Guard Activation & Host Health Adapters (`HostHealthReceiptV1`, `evaluate_guard_activation`):
   - Healthy activation success
   - Rejection on missing, unverified, unhealthy, or mismatched host health
"""

import re

import pytest

from eis.domain.danger_signals import SignalIndependenceRefusal
from eis.domain.guard_activation import (
    ActivationRefusal,
    DangerSignalReceiptV1,
    DetectorHitRefV1,
    GuardActivationReceiptV1,
)
from eis.domain.provisional_promotion import (
    ProvisionalPromotionEngineV1,
    RawObservationV1,
)
from eis.domain.thymus import ThymusGate
from eis.domain.value_objects import (
    DangerDecision,
    DangerSeverity,
    DetectorRule,
    Signal1Match,
    Signal2Danger,
)
from eis.use_cases.two_signal_regulation import (
    AcquiredAntibodyPromotionV1,
    HostHealthReceiptV1,
    NormalizedMatcher,
    QMInvariantAntibodySuiteV1,
    ThymusSelfPanelBuilder,
    TwoSignalRegulatorV1,
    evaluate_guard_activation,
)

# ============================================================================
# Section 1: Thymic Central Tolerance & Autoimmune Apoptosis Falsification
# ============================================================================


def test_thymus_self_panel_builder_fixtures_valid():
    """Verify that ThymusSelfPanelBuilder constructs a non-empty panel of clean fixtures."""
    panel = ThymusSelfPanelBuilder.build_self_panel()
    assert isinstance(panel, tuple)
    assert len(panel) >= 5
    for fixture in panel:
        assert isinstance(fixture, str)
        assert len(fixture.strip()) > 0


def test_naive_strict_detector_triggers_autoimmune_apoptosis():
    """A naive strict-syntax detector triggers autoimmune apoptosis on healthy self-panel."""
    panel = ThymusSelfPanelBuilder.build_self_panel()
    gate = ThymusGate(self_panel=panel)

    # Naive detector rule that naively flags unreduced fractions like "2/2" or "1/1" as defects
    naive_rule = DetectorRule(
        rule_id="naive_rational_syntax_detector",
        target_epitope="charpoly_format",
        match_pattern=r'"q": "[0-9]{1,5}/[0-9]{1,5}"',
        matcher_id="regex",
    )

    result = gate.evaluate_rule(naive_rule)

    # Must be purged under negative selection
    assert result.is_admitted is False
    assert result.autoimmune_violations > 0
    assert result.first_violating_sample is not None
    assert "Autoimmune apoptosis" in result.rationale
    assert "Purged." in result.rationale


def test_normalized_matcher_passes_central_tolerance():
    """A value-preserving normalized matcher passes Thymus central tolerance with 0 violations."""
    panel = ThymusSelfPanelBuilder.build_self_panel()
    gate = ThymusGate(self_panel=panel)

    # Same target pattern evaluated through NormalizedMatcher (which normalizes via charpoly_wire)
    normalized_rule = DetectorRule(
        rule_id="normalized_rational_detector",
        target_epitope="charpoly_format",
        match_pattern=r'"q": "[0-9]{1,5}/[0-9]{1,5}"',
        matcher_id="normalized_charpoly",
    )
    matcher = NormalizedMatcher(matcher_id="normalized_charpoly")

    result = gate.evaluate_rule(normalized_rule, matcher=matcher)

    # Must pass central tolerance certification
    assert result.is_admitted is True
    assert result.autoimmune_violations == 0
    assert result.first_violating_sample is None
    assert "Self-tolerance certified" in result.rationale


def test_normalized_matcher_flags_genuine_malformed_antigen():
    """NormalizedMatcher still catches genuine polynomial syntax violations."""
    matcher = NormalizedMatcher(matcher_id="normalized_charpoly")
    rule = DetectorRule(
        rule_id="detect_out_of_profile_powers",
        target_epitope="charpoly_profile",
        match_pattern=r'"powers":\s*\[[5-9]',
        matcher_id="normalized_charpoly",
    )

    # Genuinely defective antigen: power exponent 5 violates degree bound <= 4
    bad_antigen = '{"coefficients": [[], [], [], [], [{"powers": [5, 0, 0], "q": "1"}]]}'
    matches = matcher.match_antigen(bad_antigen, (rule,))

    assert len(matches) == 1
    assert matches[0].detector_id == "detect_out_of_profile_powers"
    assert "powers" in matches[0].pattern_matched


def test_thymus_screening_matcher_binding_mismatch():
    """ThymusGate refuses rule when the matcher_id does not match the screening matcher."""
    gate = ThymusGate(self_panel=ThymusSelfPanelBuilder.build_self_panel())
    rule = DetectorRule(
        rule_id="rule_with_other_matcher",
        target_epitope="test",
        match_pattern=r"test",
        matcher_id="custom_matcher",
    )
    matcher = NormalizedMatcher(matcher_id="normalized_charpoly")

    result = gate.evaluate_rule(rule, matcher=matcher)
    assert result.is_admitted is False
    assert "MATCHER_BINDING_MISMATCH" in result.rationale


# ============================================================================
# Section 2: Matzinger Two-Signal Danger Gate
# ============================================================================


def test_two_signal_zero_signals_tolerated():
    """Zero signals yields DangerDecision.TOLERATED."""
    regulator = TwoSignalRegulatorV1()
    content = '{"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "1"}]]}'

    outcome = regulator.evaluate(
        content=content,
        matches=(),
        danger=None,
        detector_id="regex",
    )

    assert outcome.decision == DangerDecision.TOLERATED
    assert outcome.normalized_content == content
    assert outcome.signal2_danger is None
    assert "Tolerated" in outcome.rationale


def test_two_signal_signal1_alone_yields_diagnostic_only():
    """Signal 1 alone yields DIAGNOSTIC_ONLY disposition and returns normalized artifact."""
    regulator = TwoSignalRegulatorV1()
    unnormalized_wire = (
        '{"coefficients": [[{"powers": [0, 0, 0], "q": "+0"}], [], [], [], [{"powers": [0, 0, 0], "q": "2/2"}]]}'
    )
    s1 = Signal1Match(
        epitope_name="unreduced_rational",
        pattern_matched="2/2",
        confidence=1.0,
        offset=0,
        detector_id="syntax_linter",
    )

    outcome = regulator.evaluate(
        content=unnormalized_wire,
        matches=(s1,),
        danger=None,
        detector_id="syntax_linter",
    )

    assert outcome.decision == DangerDecision.DIAGNOSTIC_ONLY
    assert outcome.normalized_content is not None
    # 2/2 reduced to 1 and +0 omitted
    assert '"q":"1"' in outcome.normalized_content
    assert '"2/2"' not in outcome.normalized_content
    assert "non-destructive diagnostic disposition" in outcome.rationale


def test_two_signal_signal1_and_independent_host_danger_activates():
    """Signal 1 AND independent Host Signal 2 yields DEFENSIVE_LOCKDOWN or QUARANTINED."""
    regulator = TwoSignalRegulatorV1()
    content = "candidate derivation"
    s1 = Signal1Match(
        epitope_name="algebraic_flaw",
        pattern_matched="omega_err",
        confidence=1.0,
        offset=0,
        detector_id="charpoly_detector",
    )
    s2 = Signal2Danger(
        danger_type="REPLAY_FAILURE",
        severity=DangerSeverity.MEDIUM,
        defect_count=1,
        evidence_digest="sha256:1111111111111111111111111111111111111111111111111111111111111111",
        observer_id="HOST_NATIVE_REPLAY",
    )

    outcome = regulator.evaluate(
        content=content,
        matches=(s1,),
        danger=s2,
        detector_id="charpoly_detector",
    )

    assert outcome.decision == DangerDecision.DEFENSIVE_LOCKDOWN
    assert outcome.normalized_content is None
    assert outcome.signal2_danger == s2
    assert "Activated under Two-Signal Law" in outcome.rationale


def test_two_signal_signal1_and_critical_host_danger_quarantines():
    """Signal 1 AND critical host danger yields DangerDecision.QUARANTINED."""
    regulator = TwoSignalRegulatorV1()
    s1 = Signal1Match(
        epitope_name="bad_token",
        pattern_matched="err",
        confidence=1.0,
        offset=0,
        detector_id="detector_1",
    )
    s2 = Signal2Danger(
        danger_type="PROTECTED_FIELD_VIOLATION",
        severity=DangerSeverity.CRITICAL,
        defect_count=2,
        evidence_digest="sha256:2222222222222222222222222222222222222222222222222222222222222222",
        observer_id="HOST_SECURITY_MONITOR",
    )

    outcome = regulator.evaluate(
        content="data",
        matches=(s1,),
        danger=s2,
        detector_id="detector_1",
    )

    assert outcome.decision == DangerDecision.QUARANTINED


def test_two_signal_collapse_model_authored_danger_refused():
    """Model-authored danger signal is refused with TWO_SIGNAL_COLLAPSE."""
    regulator = TwoSignalRegulatorV1()
    s1 = Signal1Match(
        epitope_name="tag",
        pattern_matched="p",
        confidence=1.0,
        offset=0,
        detector_id="detector_1",
    )
    s2_bad = Signal2Danger(
        danger_type="REPLAY_FAILURE",
        observer_id="MODEL",
        evidence_digest="sha256:3333333333333333333333333333333333333333333333333333333333333333",
    )

    with pytest.raises(SignalIndependenceRefusal, match="TWO_SIGNAL_COLLAPSE"):
        regulator.evaluate(
            content="test",
            matches=(s1,),
            danger=s2_bad,
            detector_id="detector_1",
        )


def test_two_signal_collapse_derived_from_signal1_refused():
    """Danger derived from Signal 1 match is refused with TWO_SIGNAL_COLLAPSE."""
    regulator = TwoSignalRegulatorV1()
    s1 = Signal1Match(
        epitope_name="tag",
        pattern_matched="p",
        confidence=1.0,
        offset=0,
        detector_id="detector_1",
    )
    s2_derived = Signal2Danger.derive_from_signal1_match(s1)

    with pytest.raises(SignalIndependenceRefusal) as exc_info:
        regulator.evaluate(
            content="test",
            matches=(s1,),
            danger=s2_derived,
            detector_id="detector_1",
        )
    assert exc_info.value.code == "TWO_SIGNAL_COLLAPSE"


def test_two_signal_collapse_forged_derived_danger_refused():
    """Forged derived danger with registered host danger type is refused with TWO_SIGNAL_COLLAPSE."""
    regulator = TwoSignalRegulatorV1()
    s1 = Signal1Match(
        epitope_name="tag",
        pattern_matched="p",
        confidence=1.0,
        offset=0,
        detector_id="detector_1",
    )
    s2_forged = Signal2Danger(
        danger_type="REPLAY_FAILURE",
        severity=DangerSeverity.HIGH,
        defect_count=1,
        evidence_digest="sha256:3333333333333333333333333333333333333333333333333333333333333333",
        observer_id="HOST_CHECK",
        is_derived=True,
        derived_from=s1,
    )
    with pytest.raises(SignalIndependenceRefusal) as exc_info:
        regulator.evaluate(
            content="test",
            matches=(s1,),
            danger=s2_forged,
            detector_id="detector_1",
        )
    assert exc_info.value.code == "TWO_SIGNAL_COLLAPSE"


def test_two_signal_collapse_duplicate_predicate_refused():
    """Detector predicate matching Signal 2 danger type is refused as TWO_SIGNAL_COLLAPSE."""
    regulator = TwoSignalRegulatorV1()
    s1 = Signal1Match(
        epitope_name="tag",
        pattern_matched="p",
        confidence=1.0,
        offset=0,
        detector_id="detector_1",
    )
    s2 = Signal2Danger(
        danger_type="REPLAY_FAILURE",
        observer_id="HOST_CHECKER",
        evidence_digest="sha256:4444444444444444444444444444444444444444444444444444444444444444",
    )

    with pytest.raises(SignalIndependenceRefusal, match="TWO_SIGNAL_COLLAPSE"):
        regulator.evaluate(
            content="test",
            matches=(s1,),
            danger=s2,
            detector_id="detector_1",
            detector_predicates=frozenset({"REPLAY_FAILURE"}),
        )


def test_two_signal_collapse_overlapping_evidence_spans_refused():
    """Signal 1 match overlapping Signal 2 evidence span is refused as TWO_SIGNAL_COLLAPSE."""
    regulator = TwoSignalRegulatorV1()
    s1 = Signal1Match(
        epitope_name="token",
        pattern_matched="bad",
        confidence=1.0,
        offset=10,  # Characters 10..13
        detector_id="detector_1",
    )
    s2 = Signal2Danger(
        danger_type="MALFORMED_PAYLOAD",
        observer_id="HOST_PARSER",
        evidence_digest="sha256:5555555555555555555555555555555555555555555555555555555555555555",
        evidence_spans=((8, 15),),  # Overlaps [10, 13)
    )

    with pytest.raises(SignalIndependenceRefusal, match="TWO_SIGNAL_COLLAPSE"):
        regulator.evaluate(
            content="0123456789bad0000",
            matches=(s1,),
            danger=s2,
            detector_id="detector_1",
            offsets_are_content=True,
        )


def test_two_signal_unwitnessed_danger_refused():
    """Signal 2 naming no observer raises UNWITNESSED_DANGER_SIGNAL."""
    regulator = TwoSignalRegulatorV1()
    s1 = Signal1Match(
        epitope_name="token",
        pattern_matched="bad",
        confidence=1.0,
        offset=0,
        detector_id="detector_1",
    )
    s2 = Signal2Danger(
        danger_type="REPLAY_FAILURE",
        observer_id="",
        evidence_digest="sha256:6666666666666666666666666666666666666666666666666666666666666666",
    )

    with pytest.raises(SignalIndependenceRefusal, match="UNWITNESSED_DANGER_SIGNAL"):
        regulator.evaluate(
            content="test",
            matches=(s1,),
            danger=s2,
            detector_id="detector_1",
        )


def test_two_signal_unregistered_danger_kind_refused():
    """Signal 2 with unregistered danger type raises UNREGISTERED_DANGER_KIND."""
    regulator = TwoSignalRegulatorV1()
    s1 = Signal1Match(
        epitope_name="token",
        pattern_matched="bad",
        confidence=1.0,
        offset=0,
        detector_id="detector_1",
    )
    s2 = Signal2Danger(
        danger_type="MY_CUSTOM_DANGER",
        observer_id="HOST_INSPECTOR",
        evidence_digest="sha256:7777777777777777777777777777777777777777777777777777777777777777",
    )

    with pytest.raises(SignalIndependenceRefusal, match="UNREGISTERED_DANGER_KIND"):
        regulator.evaluate(
            content="test",
            matches=(s1,),
            danger=s2,
            detector_id="detector_1",
        )


# ============================================================================
# Section 3: Public-Invariant Mathematical Antibody Suite
# ============================================================================

CLEAN_QM_DERIVATION = """
Self-Contained Derivation for Two Distinguishable Spin-1/2 Systems:

Obligation 1: Full spectrum and spectral projectors of H
The Hamiltonian in computational basis |00>, |01>, |10>, |11> decomposes into 1D blocks and a 2D central block.
Full eigenvalues: lambda_1 = K, lambda_2 = -K, lambda_3 = -K + 2*sqrt(J^2+Delta^2), lambda_4 = -K - 2*sqrt(J^2+Delta^2).
Spectral projectors P_k = |v_k><v_k| form a complete resolution of identity.
In the exceptional degeneracy limit J = Delta = 0, the central block degenerates with lambda_3 = lambda_4 = -K,
and the branch guard safeguards division by zero since omega = 2*sqrt(J^2+Delta^2) = 0.

Obligation 2: Time evolution and transition probability P_01_to_10(t)
Initial state is |01>. Exact state |psi(t)> exhibits Rabi oscillations in the 2D subspace.
Transition probability: P_01_to_10(t) = (J^2 / (J^2 + Delta^2)) * sin^2(omega * t).
At t = 0, initial condition P_01_to_10(0) = 0 is satisfied.
For all t, probability range P in [0, 1] holds since J^2 / (J^2 + Delta^2) <= 1.
In the decoupled limit at J = 0, P(t) = 0 identically for all t (stationarity).
Branch guards handle J = Delta = 0 explicitly where transition probability is identically zero.

Obligation 3: Reduced density matrix, entropy, concurrence, and CHSH
Tracing over the second spin yields reduced density matrix rho_1(t).
The single-qubit von Neumann entropy S(rho_1) is strictly in [0, 1] bits, attaining 1 bit when maximally mixed.
The pure-state concurrence C(t) satisfies C in [0, 1], with maximum reachability when Delta = 0.
The maximal CHSH expectation over local projective measurements satisfies local floor >= 2 and
Tsirelson ceiling <= 2*sqrt(2).

Obligation 4: Gibbs state at inverse temperature beta and partial transpose
For beta >= 0, Gibbs density matrix rho_beta = exp(-beta * H) / Z_beta.
At beta = 0, high-temperature partition function limit Z(beta=0) = Tr(I_4) = 4.
Partial transpose rho_beta^(T_2) eigenvalues are computed analytically; thermal entanglement occurs
if and only if the lowest eigenvalue of the partial transpose is strictly negative (Peres-Horodecki criterion).

Obligation 5: Independent consistency checks
1. Trace normalization: Tr(rho) = 1 is preserved for all states.
2. Initial condition: P(0) = 0 verified.
3. Decoupled limit: J = 0 yields stationary state with zero transition probability.
4. Exceptional limit: J = Delta = 0 explicit piecewise safeguards prevent division by zero.
"""


def test_qm_invariant_antibody_suite_clean_derivation_passes_all_10():
    """A clean derivation satisfying all textbook public invariants passes 10/10 antibodies."""
    receipt = QMInvariantAntibodySuiteV1.evaluate(CLEAN_QM_DERIVATION)

    assert receipt.total_antibodies == 10
    assert receipt.passed_count == 10
    assert receipt.all_passed is True
    # Critical invariant: final_answer_certified MUST always be False
    assert receipt.final_answer_certified is False
    assert "Textbook public-invariant sanity check only" in receipt.limitation_notice


def test_qm_invariant_final_answer_certified_always_false():
    """Verify that final_answer_certified is always False, regardless of passing state."""
    receipt_pass = QMInvariantAntibodySuiteV1.evaluate(CLEAN_QM_DERIVATION)
    assert receipt_pass.final_answer_certified is False

    receipt_fail = QMInvariantAntibodySuiteV1.evaluate("broken short text")
    assert receipt_fail.final_answer_certified is False


def test_ab01_fails_on_truncation_or_missing_parts():
    """Ab01 fails when derivation is truncated or missing required obligations."""
    truncated = CLEAN_QM_DERIVATION[:300] + "..."
    receipt = QMInvariantAntibodySuiteV1.evaluate(truncated)

    ab01 = next(f for f in receipt.findings if f.antibody_id == "Ab01_StructuralCompleteness")
    assert ab01.passed is False
    assert "dangling" in ab01.evidence or "Missing" in ab01.evidence


def test_ab02_fails_on_nonzero_initial_transition_probability():
    """Ab02 fails if initial transition probability P(0) != 0."""
    bad_text = CLEAN_QM_DERIVATION.replace("initial condition P_01_to_10(0) = 0", "initial condition P_01_to_10(0) = 1")
    receipt = QMInvariantAntibodySuiteV1.evaluate(bad_text)

    ab02 = next(f for f in receipt.findings if f.antibody_id == "Ab02_InitialTransitionProbability")
    assert ab02.passed is False
    assert "Contradicts initial boundary condition" in ab02.evidence


def test_ab03_fails_on_probability_range_violation():
    """Ab03 fails when transition probability exceeds 1."""
    bad_text = CLEAN_QM_DERIVATION + "\nNotice that P > 1 when prefactor is unnormalized."
    receipt = QMInvariantAntibodySuiteV1.evaluate(bad_text)

    ab03 = next(f for f in receipt.findings if f.antibody_id == "Ab03_ProbabilityRange")
    assert ab03.passed is False
    assert "Probability range violation" in ab03.evidence


def test_ab04_fails_on_decoupled_limit_violation():
    """Ab04 fails when transitions are claimed to occur at J = 0."""
    bad_text = CLEAN_QM_DERIVATION.replace(
        "at J = 0, P(t) = 0 identically for all t (stationarity)",
        "at J = 0, transitions occur with P = 1",
    )
    receipt = QMInvariantAntibodySuiteV1.evaluate(bad_text)

    ab04 = next(f for f in receipt.findings if f.antibody_id == "Ab04_DecoupledLimitStationarity")
    assert ab04.passed is False


def test_ab05_fails_on_missing_branch_guards_zero_denominator():
    """Ab05 fails when branch guard for J = Delta = 0 is omitted."""
    bad_text = re.sub(
        r"(?i)branch guards?|degenerac\w+|J\s*=\s*Delta\s*=\s*0|exceptional\s+limit",
        "regular_case",
        CLEAN_QM_DERIVATION,
    )
    receipt = QMInvariantAntibodySuiteV1.evaluate(bad_text)

    ab05 = next(f for f in receipt.findings if f.antibody_id == "Ab05_BranchGuardsZeroDenominator")
    assert ab05.passed is False
    assert "Missing explicit branch handling" in ab05.evidence


def test_ab06_fails_on_wrong_high_temperature_partition_limit():
    """Ab06 fails when partition function at beta = 0 contradicts Z_0 = 4."""
    bad_text = CLEAN_QM_DERIVATION.replace("Z(beta=0) = Tr(I_4) = 4", "Z(beta=0) = 1")
    receipt = QMInvariantAntibodySuiteV1.evaluate(bad_text)

    ab06 = next(f for f in receipt.findings if f.antibody_id == "Ab06_HighTemperaturePartitionFunction")
    assert ab06.passed is False
    assert "Contradicts high-temperature partition limit" in ab06.evidence


def test_ab07_fails_on_concurrence_range_violation():
    """Ab07 fails when pure-state concurrence exceeds 1."""
    bad_text = CLEAN_QM_DERIVATION + "\nConcurrence evaluates to C = 2 for this state."
    receipt = QMInvariantAntibodySuiteV1.evaluate(bad_text)

    ab07 = next(f for f in receipt.findings if f.antibody_id == "Ab07_ConcurrenceRange")
    assert ab07.passed is False
    assert "Concurrence range violation" in ab07.evidence


def test_ab08_fails_on_single_qubit_entropy_bits_violation():
    """Ab08 fails when single-qubit entropy exceeds 1 bit."""
    bad_text = CLEAN_QM_DERIVATION + "\nThe reduced entropy evaluates to S = 2 bits."
    receipt = QMInvariantAntibodySuiteV1.evaluate(bad_text)

    ab08 = next(f for f in receipt.findings if f.antibody_id == "Ab08_SingleQubitEntropyInBits")
    assert ab08.passed is False
    assert "Single-qubit entropy exceeds 1-bit" in ab08.evidence


def test_ab09_fails_on_chsh_bound_range_violation():
    """Ab09 fails when CHSH expectation violates Tsirelson ceiling <= 2*sqrt(2)."""
    bad_text = CLEAN_QM_DERIVATION + "\nUnder maximal measurement angles, expectation = 4."
    receipt = QMInvariantAntibodySuiteV1.evaluate(bad_text)

    ab09 = next(f for f in receipt.findings if f.antibody_id == "Ab09_CHSHBoundRange")
    assert ab09.passed is False
    assert "Tsirelson ceiling" in ab09.evidence


def test_ab10_fails_on_cross_section_consistency_violation():
    """Ab10 fails when trace normalization Tr(rho) != 1."""
    bad_text = CLEAN_QM_DERIVATION + "\nThe density matrix is unnormalized density matrix with Tr = 0."
    receipt = QMInvariantAntibodySuiteV1.evaluate(bad_text)

    ab10 = next(f for f in receipt.findings if f.antibody_id == "Ab10_CrossSectionConsistency")
    assert ab10.passed is False
    assert "trace normalization violated" in ab10.evidence.lower()


# ============================================================================
# Section 4: Acquired Antibody Promotion via Conflict-Graph MIS
# ============================================================================


def test_correlated_observations_collapse_to_candidate():
    """5 observations from same model/scaffold collapse to support_count = 1 ('Candidate')."""
    promotion_mgr = AcquiredAntibodyPromotionV1()

    # 5 observations sharing the same model and scaffold
    correlated_obs = tuple(
        RawObservationV1(
            occurrence_id=f"run_0{i}",
            generating_model_id="deepseek/deepseek-v3.2",
            scaffold_digest="sha256:scaffold_alpha_000000000000000000000000000000000000000000000000",
            precedent_set_digest="sha256:prec_00000000000000000000000000000000000000000000000000000000",
            inheritance_root="sha256:root_00000000000000000000000000000000000000000000000000000000",
        )
        for i in range(5)
    )

    support, promotion = promotion_mgr.evaluate_promotion(
        candidate_id="defect:unhandled_rational_wire",
        observations=correlated_obs,
    )

    # In a complete 5-clique, maximum independent set size is strictly 1
    assert support.support_count == 1
    assert support.eligible_for_provisional is False
    assert promotion.new_custody == "Candidate"
    assert promotion.review_queued is False


def test_independent_observations_promote_to_provisional():
    """3 observations from independent channels achieve MIS = 3 and promote to 'Provisional'."""
    promotion_mgr = AcquiredAntibodyPromotionV1()

    # 3 independent observations with distinct models, scaffolds, precedents, and roots
    independent_obs = (
        RawObservationV1(
            occurrence_id="run_alpha",
            generating_model_id="model_a",
            scaffold_digest="sha256:scaffold_a00000000000000000000000000000000000000000000000000000",
            precedent_set_digest="sha256:prec_a000000000000000000000000000000000000000000000000000000",
            inheritance_root="sha256:root_a000000000000000000000000000000000000000000000000000000",
        ),
        RawObservationV1(
            occurrence_id="run_beta",
            generating_model_id="model_b",
            scaffold_digest="sha256:scaffold_b00000000000000000000000000000000000000000000000000000",
            precedent_set_digest="sha256:prec_b000000000000000000000000000000000000000000000000000000",
            inheritance_root="sha256:root_b000000000000000000000000000000000000000000000000000000",
        ),
        RawObservationV1(
            occurrence_id="run_gamma",
            generating_model_id="model_c",
            scaffold_digest="sha256:scaffold_c00000000000000000000000000000000000000000000000000000",
            precedent_set_digest="sha256:prec_c000000000000000000000000000000000000000000000000000000",
            inheritance_root="sha256:root_c000000000000000000000000000000000000000000000000000000",
        ),
    )

    support, promotion = promotion_mgr.evaluate_promotion(
        candidate_id="defect:invariant_chsh_overflow",
        observations=independent_obs,
    )

    # Empty graph E_3 yields MIS = 3
    assert support.support_count == 3
    assert support.eligible_for_provisional is True
    assert promotion.new_custody == "Provisional"
    assert promotion.review_queued is True
    assert promotion.enforcement_authorized is False
    assert promotion.authority_effect == "None"


def test_propagated_reference_rejected_from_support():
    """An observation with is_propagated_reference=True raises ValueError."""
    promotion_mgr = AcquiredAntibodyPromotionV1()
    obs = (
        RawObservationV1(
            occurrence_id="obs_prop",
            generating_model_id="model_x",
            is_propagated_reference=True,
        ),
    )

    with pytest.raises(ValueError, match="PROPAGATED_REFERENCE_CANNOT_BE_OBSERVATION"):
        promotion_mgr.compute_support(obs)


def test_placeholder_candidate_refuses_promotion():
    """A candidate ID containing 'placeholder' or 'defect:defect:' refuses promotion."""
    engine = ProvisionalPromotionEngineV1()

    # Even with high support count
    res = engine.promote_candidate_if_eligible("defect:defect:placeholder_spec", 5, [])
    assert res.new_custody == "Placeholder refuses promotion"
    assert res.review_queued is False


# ============================================================================
# Section 5: Guard Activation & Host Health Adapters
# ============================================================================

PROFILE_DIGEST = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SUBJECT_ID = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
HIT_ID = "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
DANGER_EVIDENCE = "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"


def test_evaluate_guard_activation_healthy_success():
    """Valid hit + independent danger + healthy host health activates successfully."""
    hit = DetectorHitRefV1(
        hit_id=HIT_ID,
        spec_id="spec_test",
        failure_code="code_fail",
        subject_id=SUBJECT_ID,
    )
    danger = DangerSignalReceiptV1(
        signal_kind="REPLAY_FAILURE",
        observer_id="HOST_CHECKER",
        subject_id=SUBJECT_ID,
        evidence_digest=DANGER_EVIDENCE,
    )
    health = HostHealthReceiptV1(
        observer_id="HOST_WATCHDOG",
        status="HEALTHY",
        subject_id=SUBJECT_ID,
        profile_digest=PROFILE_DIGEST,
    )

    receipt = evaluate_guard_activation(
        profile_digest=PROFILE_DIGEST,
        hit=hit,
        danger=danger,
        externally_admitted=True,
        suspended=False,
        disposition="REFUSE",
        host_health=health,
    )

    assert isinstance(receipt, GuardActivationReceiptV1)
    assert receipt.profile_digest == PROFILE_DIGEST
    assert receipt.hit_id == HIT_ID
    assert receipt.disposition == "REFUSE"
    assert "HOST_CHECKER" in receipt.independence_basis


def test_evaluate_guard_activation_host_health_unavailable():
    """Missing host health raises HOST_HEALTH_UNAVAILABLE."""
    hit = DetectorHitRefV1(hit_id=HIT_ID, spec_id="spec_test", failure_code="code_fail", subject_id=SUBJECT_ID)
    danger = DangerSignalReceiptV1(
        signal_kind="REPLAY_FAILURE", observer_id="HOST_CHECKER", subject_id=SUBJECT_ID, evidence_digest=DANGER_EVIDENCE
    )

    with pytest.raises(ActivationRefusal, match="HOST_HEALTH_UNAVAILABLE"):
        evaluate_guard_activation(
            profile_digest=PROFILE_DIGEST,
            hit=hit,
            danger=danger,
            externally_admitted=True,
            suspended=False,
            host_health=None,
        )


def test_evaluate_guard_activation_host_health_unhealthy():
    """Host health reporting UNHEALTHY raises HOST_HEALTH_UNHEALTHY."""
    hit = DetectorHitRefV1(hit_id=HIT_ID, spec_id="spec_test", failure_code="code_fail", subject_id=SUBJECT_ID)
    danger = DangerSignalReceiptV1(
        signal_kind="REPLAY_FAILURE", observer_id="HOST_CHECKER", subject_id=SUBJECT_ID, evidence_digest=DANGER_EVIDENCE
    )
    health = HostHealthReceiptV1(
        observer_id="HOST_WATCHDOG",
        status="UNHEALTHY",
        subject_id=SUBJECT_ID,
        profile_digest=PROFILE_DIGEST,
    )

    with pytest.raises(ActivationRefusal, match="HOST_HEALTH_UNHEALTHY"):
        evaluate_guard_activation(
            profile_digest=PROFILE_DIGEST,
            hit=hit,
            danger=danger,
            externally_admitted=True,
            suspended=False,
            host_health=health,
        )


def test_evaluate_guard_activation_host_health_unverified():
    """Host health reporting UNVERIFIED raises HOST_HEALTH_UNVERIFIED."""
    hit = DetectorHitRefV1(hit_id=HIT_ID, spec_id="spec_test", failure_code="code_fail", subject_id=SUBJECT_ID)
    danger = DangerSignalReceiptV1(
        signal_kind="REPLAY_FAILURE", observer_id="HOST_CHECKER", subject_id=SUBJECT_ID, evidence_digest=DANGER_EVIDENCE
    )
    health = HostHealthReceiptV1(
        observer_id="HOST_WATCHDOG",
        status="UNVERIFIED",
        subject_id=SUBJECT_ID,
        profile_digest=PROFILE_DIGEST,
    )

    with pytest.raises(ActivationRefusal, match="HOST_HEALTH_UNVERIFIED"):
        evaluate_guard_activation(
            profile_digest=PROFILE_DIGEST,
            hit=hit,
            danger=danger,
            externally_admitted=True,
            suspended=False,
            host_health=health,
        )


def test_evaluate_guard_activation_subject_mismatch():
    """Host health with mismatched subject_id raises SUBJECT_MISMATCH."""
    hit = DetectorHitRefV1(hit_id=HIT_ID, spec_id="spec_test", failure_code="code_fail", subject_id=SUBJECT_ID)
    danger = DangerSignalReceiptV1(
        signal_kind="REPLAY_FAILURE", observer_id="HOST_CHECKER", subject_id=SUBJECT_ID, evidence_digest=DANGER_EVIDENCE
    )
    diff_subject = "sha256:9999999999999999999999999999999999999999999999999999999999999999"
    health = HostHealthReceiptV1(
        observer_id="HOST_WATCHDOG",
        status="HEALTHY",
        subject_id=diff_subject,
        profile_digest=PROFILE_DIGEST,
    )

    with pytest.raises(ActivationRefusal, match="SUBJECT_MISMATCH"):
        evaluate_guard_activation(
            profile_digest=PROFILE_DIGEST,
            hit=hit,
            danger=danger,
            externally_admitted=True,
            suspended=False,
            host_health=health,
        )


def test_evaluate_guard_activation_profile_mismatch():
    """Host health with mismatched profile_digest raises TWO_SIGNAL_COLLAPSE."""
    hit = DetectorHitRefV1(hit_id=HIT_ID, spec_id="spec_test", failure_code="code_fail", subject_id=SUBJECT_ID)
    danger = DangerSignalReceiptV1(
        signal_kind="REPLAY_FAILURE", observer_id="HOST_CHECKER", subject_id=SUBJECT_ID, evidence_digest=DANGER_EVIDENCE
    )
    diff_profile = "sha256:8888888888888888888888888888888888888888888888888888888888888888"
    health = HostHealthReceiptV1(
        observer_id="HOST_WATCHDOG",
        status="HEALTHY",
        subject_id=SUBJECT_ID,
        profile_digest=diff_profile,
    )

    with pytest.raises(ActivationRefusal, match="TWO_SIGNAL_COLLAPSE"):
        evaluate_guard_activation(
            profile_digest=PROFILE_DIGEST,
            hit=hit,
            danger=danger,
            externally_admitted=True,
            suspended=False,
            host_health=health,
        )


def test_host_health_receipt_validation():
    """HostHealthReceiptV1 enforces type and validation invariants."""
    with pytest.raises(ValueError, match="observer_id"):
        HostHealthReceiptV1(observer_id="", status="HEALTHY", subject_id=SUBJECT_ID, profile_digest=PROFILE_DIGEST)

    with pytest.raises(ValueError, match="invalid host health status"):
        HostHealthReceiptV1(
            observer_id="HOST", status="BOGUS_STATUS", subject_id=SUBJECT_ID, profile_digest=PROFILE_DIGEST
        )

    with pytest.raises(ValueError, match="subject_id"):
        HostHealthReceiptV1(
            observer_id="HOST", status="HEALTHY", subject_id="bad_digest", profile_digest=PROFILE_DIGEST
        )

    with pytest.raises(ValueError, match="profile_digest"):
        HostHealthReceiptV1(observer_id="HOST", status="HEALTHY", subject_id=SUBJECT_ID, profile_digest="bad_digest")

    with pytest.raises(ValueError, match="authority_effect"):
        HostHealthReceiptV1(
            observer_id="HOST",
            status="HEALTHY",
            subject_id=SUBJECT_ID,
            profile_digest=PROFILE_DIGEST,
            authority_effect="Binding",
        )


def test_evaluate_proposal_aligns_detector_id_from_matcher():
    """TwoSignalRegulatorV1.evaluate_proposal derives detector_id from matcher.matcher_id."""
    regulator = TwoSignalRegulatorV1()
    matcher = NormalizedMatcher(matcher_id="custom_poly_matcher")
    rule = DetectorRule(
        rule_id="r1",
        target_epitope="poly",
        match_pattern=r'"q":\s*"1"',
        matcher_id="custom_poly_matcher",
    )
    candidate = '{"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "1"}]]}'
    outcome = regulator.evaluate_proposal(
        candidate,
        matcher=matcher,
        rules=(rule,),
    )
    assert outcome.decision == DangerDecision.DIAGNOSTIC_ONLY
    assert len(outcome.signal1_matches) == 1
    # When danger has same observer_id as matcher_id, it is refused as TWO_SIGNAL_COLLAPSE
    danger = Signal2Danger(
        danger_type="REPLAY_FAILURE",
        observer_id="custom_poly_matcher",
        severity=DangerSeverity.HIGH,
        evidence_digest="sha256:5555555555555555555555555555555555555555555555555555555555555555",
    )
    with pytest.raises(SignalIndependenceRefusal) as exc_info:
        regulator.evaluate_proposal(
            candidate,
            matcher=matcher,
            rules=(rule,),
            host_signal2=danger,
        )
    assert exc_info.value.code == "TWO_SIGNAL_COLLAPSE"


def test_host_health_receipt_refuses_forbidden_observers():
    """HostHealthReceiptV1 refuses forbidden observers with case-insensitive matching."""
    for forbidden in ["MODEL", "model", "Model", "LLM", "llm", "AGENT", "agent", "DETECTOR", "MATCHER"]:
        with pytest.raises(ValueError, match="FORBIDDEN_OBSERVER"):
            HostHealthReceiptV1(
                observer_id=forbidden,
                status="HEALTHY",
                subject_id=SUBJECT_ID,
                profile_digest=PROFILE_DIGEST,
            )


def test_host_health_receipt_validates_timestamp():
    """HostHealthReceiptV1 validates that timestamp is a non-empty ISO-8601 UTC string."""
    # Valid timestamp passes
    receipt = HostHealthReceiptV1(
        observer_id="HOST_WATCHDOG",
        status="HEALTHY",
        subject_id=SUBJECT_ID,
        profile_digest=PROFILE_DIGEST,
        timestamp="2026-11-11T05:00:00Z",
    )
    assert receipt.timestamp == "2026-11-11T05:00:00Z"

    # Invalid timestamp strings raise ValueError
    for bad_ts in ["", "   ", "NOT_A_TIMESTAMP", "2026-11-11", "2026-11-11T05:00:00+05:00"]:
        with pytest.raises(ValueError, match="timestamp"):
            HostHealthReceiptV1(
                observer_id="HOST_WATCHDOG",
                status="HEALTHY",
                subject_id=SUBJECT_ID,
                profile_digest=PROFILE_DIGEST,
                timestamp=bad_ts,
            )


def test_ab04_passes_on_no_transition_occurs():
    """Ab04 passes physically valid statement 'no transition occurs'."""
    text = "Decoupled limit: at J = 0, P(t) = 0, so no transition occurs."
    finding = QMInvariantAntibodySuiteV1._check_ab04_decoupled_limit_stationarity(text)
    assert finding.passed is True
    assert "Stationarity under decoupled limit J = 0 verified" in finding.evidence


def test_qm_antibodies_reject_decimal_and_range_leaks():
    """Verify that QM antibodies reject out-of-bounds decimal and range values."""
    # Ab02 rejects P(0) = 0.5
    f02 = QMInvariantAntibodySuiteV1._check_ab02_initial_transition_probability("Transition P(0) = 0.5 at t=0.")
    assert f02.passed is False

    # Ab03 rejects P = 1.5
    f03 = QMInvariantAntibodySuiteV1._check_ab03_probability_range("Transition probability P = 1.5.")
    assert f03.passed is False

    # Ab06 rejects Z(0) = 4.5 and Z(0) = 42
    f06_dec = QMInvariantAntibodySuiteV1._check_ab06_high_temperature_partition_function("Limit Z(0) = 4.5.")
    assert f06_dec.passed is False
    f06_multi = QMInvariantAntibodySuiteV1._check_ab06_high_temperature_partition_function("Limit Z(0) = 42.")
    assert f06_multi.passed is False

    # Ab07 rejects C = 1.5
    f07 = QMInvariantAntibodySuiteV1._check_ab07_concurrence_range("Pure-state concurrence C = 1.5.")
    assert f07.passed is False

    # Ab08 rejects S(rho_1) = 1.5 bits and 2 bits
    f08_dec = QMInvariantAntibodySuiteV1._check_ab08_single_qubit_entropy_bits("Entropy S(rho_1) = 1.5 bits.")
    assert f08_dec.passed is False
    f08_multi = QMInvariantAntibodySuiteV1._check_ab08_single_qubit_entropy_bits(
        "von Neumann entropy S(rho_1) = 2 bits."
    )
    assert f08_multi.passed is False

    # Ab09 rejects CHSH = 2.95 and CHSH = 1.5
    f09_ceil = QMInvariantAntibodySuiteV1._check_ab09_chsh_bound_range("Maximal CHSH = 2.95.")
    assert f09_ceil.passed is False
    f09_floor = QMInvariantAntibodySuiteV1._check_ab09_chsh_bound_range("Maximal CHSH = 1.5.")
    assert f09_floor.passed is False

    # Ab10 rejects Tr(rho) = 1.5
    f10 = QMInvariantAntibodySuiteV1._check_ab10_cross_section_consistency("Trace normalization Tr(rho) = 1.5.")
    assert f10.passed is False
