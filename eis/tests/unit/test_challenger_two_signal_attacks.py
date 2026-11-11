"""Challenger 2 Empirical Adversarial Stress Test Suite for Milestone 1.

Verifies:
1. Two-Signal Collapse Attacks:
   - Varied casing on forbidden observers ('Model', 'llm', 'Agent', 'detector').
   - Overlapping evidence spans and identical digests.
   - Attack on derived Signal 2: demonstrates failure modes of `Signal2Danger.derive_from_signal1_match`.
2. Signal 1 Normalization vs Gating:
   - Signal 1 alone returns DIAGNOSTIC_ONLY with normalized payload (never HOLD/REFUSE).
   - Signal 1 + registered host danger (REPLAY_FAILURE, MALFORMED_PAYLOAD, PROTECTED_FIELD_VIOLATION,
     MANIFEST_CONTAMINATION) triggers DEFENSIVE_LOCKDOWN or QUARANTINED.
   - Zero signals returns TOLERATED.
3. Host Health Gating Attacks:
   - Fail-closed verification on missing receipt, unverified status, unhealthy status, subject mismatch,
     and profile mismatch.
   - Attack demonstrating model-authored HostHealthReceiptV1 vulnerability.
   - Attack demonstrating unvalidated timestamp vulnerability.
4. QM Invariant Antibody Suite Falsification:
   - Autoimmune false-positive on 'no transition occurs' in Ab04.
   - Decimal and range leak attacks across Ab02, Ab03, Ab06, Ab07, Ab08, Ab09, Ab10.

AuthorityEffect: None.
Evaluator Firewall: Strictly preserved. Zero private answers or evaluator constants referenced.
"""

from __future__ import annotations

import pytest

from eis.domain.danger_signals import (
    SignalIndependenceRefusal,
    signal1_digest,
)
from eis.domain.guard_activation import (
    ActivationRefusal,
    DangerSignalReceiptV1,
    DetectorHitRefV1,
)
from eis.domain.value_objects import (
    DangerDecision,
    DangerSeverity,
    Signal1Match,
    Signal2Danger,
)
from eis.use_cases.two_signal_regulation import (
    HostHealthReceiptV1,
    QMInvariantAntibodySuiteV1,
    TwoSignalRegulatorV1,
    evaluate_guard_activation,
)

# ============================================================================
# Section 1: Two-Signal Collapse Attacks
# ============================================================================


class TestTwoSignalCollapseAttacks:
    """Adversarial stress-testing of Two-Signal collapse boundary."""

    @pytest.fixture
    def regulator(self) -> TwoSignalRegulatorV1:
        return TwoSignalRegulatorV1()

    @pytest.fixture
    def base_signal1(self) -> Signal1Match:
        return Signal1Match(
            epitope_name="unreduced_rational",
            pattern_matched='"q": "2/2"',
            confidence=1.0,
            offset=10,
            detector_id="regex_detector",
        )

    @pytest.mark.parametrize(
        "forbidden_observer",
        [
            "MODEL",
            "Model",
            "model",
            "mOdEl",
            "LLM",
            "llm",
            "Llm",
            "AGENT",
            "Agent",
            "agent",
            "aGeNt",
            "DETECTOR",
            "Detector",
            "detector",
            "MATCHER",
            "Matcher",
            "matcher",
            "regex_detector",
            "REGEX_DETECTOR",
            "Regex_Detector",
        ],
    )
    def test_forbidden_observer_casing_variations_refused(
        self,
        regulator: TwoSignalRegulatorV1,
        base_signal1: Signal1Match,
        forbidden_observer: str,
    ):
        """All variations of forbidden observer casing are refused with TWO_SIGNAL_COLLAPSE."""
        s2 = Signal2Danger(
            danger_type="REPLAY_FAILURE",
            observer_id=forbidden_observer,
            severity=DangerSeverity.HIGH,
            evidence_digest="sha256:1111111111111111111111111111111111111111111111111111111111111111",
        )
        with pytest.raises(SignalIndependenceRefusal) as exc_info:
            regulator.evaluate(
                content="test",
                matches=(base_signal1,),
                danger=s2,
                detector_id="regex_detector",
            )
        assert exc_info.value.code == "TWO_SIGNAL_COLLAPSE"

    def test_identical_evidence_digest_refused(
        self,
        regulator: TwoSignalRegulatorV1,
        base_signal1: Signal1Match,
    ):
        """Signal 2 carrying the exact digest of Signal 1 matches is refused with TWO_SIGNAL_COLLAPSE."""
        digest = signal1_digest((base_signal1,))
        s2 = Signal2Danger(
            danger_type="REPLAY_FAILURE",
            observer_id="HOST_REPLAY_CHECK",
            severity=DangerSeverity.HIGH,
            evidence_digest=digest,
        )
        with pytest.raises(SignalIndependenceRefusal) as exc_info:
            regulator.evaluate(
                content="test",
                matches=(base_signal1,),
                danger=s2,
                detector_id="regex_detector",
            )
        assert exc_info.value.code == "TWO_SIGNAL_COLLAPSE"

    @pytest.mark.parametrize(
        "span",
        [
            ((10, 22),),  # Exact match span: offset=10, len=12 ('"q": "2/2"')
            ((5, 15),),   # Left overlap
            ((15, 25),),  # Right overlap
            ((0, 30),),   # Enclosing span
            ((12, 18),),  # Interior span
        ],
    )
    def test_overlapping_evidence_spans_refused(
        self,
        regulator: TwoSignalRegulatorV1,
        base_signal1: Signal1Match,
        span: tuple[tuple[int, int], ...],
    ):
        """Any overlapping token span between Signal 1 and Signal 2 is refused with TWO_SIGNAL_COLLAPSE."""
        s2 = Signal2Danger(
            danger_type="REPLAY_FAILURE",
            observer_id="HOST_REPLAY_CHECK",
            severity=DangerSeverity.HIGH,
            evidence_digest="sha256:2222222222222222222222222222222222222222222222222222222222222222",
            evidence_spans=span,
        )
        with pytest.raises(SignalIndependenceRefusal) as exc_info:
            regulator.evaluate(
                content='0123456789"q": "2/2"0123456789',
                matches=(base_signal1,),
                danger=s2,
                detector_id="regex_detector",
                offsets_are_content=True,
            )
        assert exc_info.value.code == "TWO_SIGNAL_COLLAPSE"

    def test_derived_from_signal1_falsification_exact_code(
        self,
        regulator: TwoSignalRegulatorV1,
        base_signal1: Signal1Match,
    ):
        """Signal2Danger.derive_from_signal1_match is refused with TWO_SIGNAL_COLLAPSE."""
        s2_derived = Signal2Danger.derive_from_signal1_match(base_signal1)
        with pytest.raises(SignalIndependenceRefusal) as exc_info:
            regulator.evaluate(
                content="test",
                matches=(base_signal1,),
                danger=s2_derived,
                detector_id="regex_detector",
            )
        assert exc_info.value.code == "TWO_SIGNAL_COLLAPSE"

    def test_forged_derived_danger_bypasses_independence_check(
        self,
        regulator: TwoSignalRegulatorV1,
        base_signal1: Signal1Match,
    ):
        """Forged derived danger with registered host type is refused with TWO_SIGNAL_COLLAPSE."""
        s2_forged = Signal2Danger(
            danger_type="REPLAY_FAILURE",
            severity=DangerSeverity.HIGH,
            defect_count=1,
            evidence_digest="sha256:3333333333333333333333333333333333333333333333333333333333333333",
            observer_id="HOST_CHECK",
            is_derived=True,
            derived_from=base_signal1,
        )
        with pytest.raises(SignalIndependenceRefusal) as exc_info:
            regulator.evaluate(
                content="test",
                matches=(base_signal1,),
                danger=s2_forged,
                detector_id="regex_detector",
            )
        assert exc_info.value.code == "TWO_SIGNAL_COLLAPSE"


# ============================================================================
# Section 2: Signal 1 Normalization vs Gating
# ============================================================================


class TestSignal1NormalizationVsGating:
    """Verification of Matzinger two-signal law: Signal 1 alone is diagnostic-only."""

    @pytest.fixture
    def regulator(self) -> TwoSignalRegulatorV1:
        return TwoSignalRegulatorV1()

    def test_zero_signals_tolerated(self, regulator: TwoSignalRegulatorV1):
        """Zero matches and no danger signal yields TOLERATED."""
        outcome = regulator.evaluate("clean content", (), None, detector_id="regex")
        assert outcome.decision == DangerDecision.TOLERATED
        assert outcome.normalized_content == "clean content"

    def test_signal1_alone_is_diagnostic_only_never_refuses(self, regulator: TwoSignalRegulatorV1):
        """Signal 1 match without host tissue danger NEVER raises refusal or triggers lockdown."""
        s1 = Signal1Match(
            epitope_name="fraction",
            pattern_matched='"2/2"',
            confidence=1.0,
            offset=0,
            detector_id="regex",
        )
        candidate = '{"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "2/2"}]]}'
        outcome = regulator.evaluate(candidate, (s1,), None, detector_id="regex")
        assert outcome.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert outcome.normalized_content is not None
        # Value-preserving normalization reduced "2/2" to "1"
        assert '"q":"1"' in outcome.normalized_content or '"q": "1"' in outcome.normalized_content
        assert outcome.signal2_danger is None

    @pytest.mark.parametrize(
        "danger_type,severity,expected_decision",
        [
            ("REPLAY_FAILURE", DangerSeverity.MEDIUM, DangerDecision.DEFENSIVE_LOCKDOWN),
            ("REPLAY_FAILURE", DangerSeverity.HIGH, DangerDecision.QUARANTINED),
            ("MALFORMED_PAYLOAD", DangerSeverity.CRITICAL, DangerDecision.QUARANTINED),
            ("PROTECTED_FIELD_VIOLATION", DangerSeverity.MEDIUM, DangerDecision.DEFENSIVE_LOCKDOWN),
            ("MANIFEST_CONTAMINATION", DangerSeverity.HIGH, DangerDecision.QUARANTINED),
        ],
    )
    def test_signal1_and_independent_host_danger_activates(
        self,
        regulator: TwoSignalRegulatorV1,
        danger_type: str,
        severity: DangerSeverity,
        expected_decision: DangerDecision,
    ):
        """Signal 1 paired with independent host danger triggers defensive lockdown or quarantine."""
        s1 = Signal1Match(
            epitope_name="format",
            pattern_matched="p",
            confidence=1.0,
            offset=0,
            detector_id="detector_1",
        )
        s2 = Signal2Danger(
            danger_type=danger_type,
            observer_id="HOST_VERIFIER",
            severity=severity,
            evidence_digest="sha256:4444444444444444444444444444444444444444444444444444444444444444",
        )
        outcome = regulator.evaluate("content", (s1,), s2, detector_id="detector_1")
        assert outcome.decision == expected_decision
        assert outcome.normalized_content is None


# ============================================================================
# Section 3: Host Health Gating Attacks
# ============================================================================


class TestHostHealthGatingAttacks:
    """Adversarial stress-testing of evaluate_guard_activation."""

    @pytest.fixture
    def base_hit(self) -> DetectorHitRefV1:
        return DetectorHitRefV1(
            hit_id="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            spec_id="spec_test",
            failure_code="fail_test",
            subject_id="sha256:1111111111111111111111111111111111111111111111111111111111111111",
        )

    @pytest.fixture
    def base_danger(self) -> DangerSignalReceiptV1:
        return DangerSignalReceiptV1(
            signal_kind="REPLAY_FAILURE",
            observer_id="HOST_CHECK",
            subject_id="sha256:1111111111111111111111111111111111111111111111111111111111111111",
            evidence_digest="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        )

    def test_missing_host_health_refuses(
        self,
        base_hit: DetectorHitRefV1,
        base_danger: DangerSignalReceiptV1,
    ):
        """Missing host health receipt raises HOST_HEALTH_UNAVAILABLE."""
        with pytest.raises(ActivationRefusal) as exc_info:
            evaluate_guard_activation(
                profile_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999",
                hit=base_hit,
                danger=base_danger,
                externally_admitted=True,
                suspended=False,
                host_health=None,
            )
        assert exc_info.value.code == "HOST_HEALTH_UNAVAILABLE"

    @pytest.mark.parametrize("bad_status", ["UNHEALTHY", "UNAVAILABLE"])
    def test_unhealthy_or_unavailable_status_refuses(
        self,
        base_hit: DetectorHitRefV1,
        base_danger: DangerSignalReceiptV1,
        bad_status: str,
    ):
        """Unhealthy or unavailable host health status raises HOST_HEALTH_UNHEALTHY."""
        receipt = HostHealthReceiptV1(
            observer_id="HOST_SUPERVISOR",
            status=bad_status,
            subject_id=base_hit.subject_id,
            profile_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999",
        )
        with pytest.raises(ActivationRefusal) as exc_info:
            evaluate_guard_activation(
                profile_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999",
                hit=base_hit,
                danger=base_danger,
                externally_admitted=True,
                suspended=False,
                host_health=receipt,
            )
        assert exc_info.value.code == "HOST_HEALTH_UNHEALTHY"

    def test_unverified_status_refuses(
        self,
        base_hit: DetectorHitRefV1,
        base_danger: DangerSignalReceiptV1,
    ):
        """Unverified host health status raises HOST_HEALTH_UNVERIFIED."""
        receipt = HostHealthReceiptV1(
            observer_id="HOST_SUPERVISOR",
            status="UNVERIFIED",
            subject_id=base_hit.subject_id,
            profile_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999",
        )
        with pytest.raises(ActivationRefusal) as exc_info:
            evaluate_guard_activation(
                profile_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999",
                hit=base_hit,
                danger=base_danger,
                externally_admitted=True,
                suspended=False,
                host_health=receipt,
            )
        assert exc_info.value.code == "HOST_HEALTH_UNVERIFIED"

    def test_subject_mismatch_refuses(
        self,
        base_hit: DetectorHitRefV1,
        base_danger: DangerSignalReceiptV1,
    ):
        """Host health receipt subject mismatch raises SUBJECT_MISMATCH."""
        receipt = HostHealthReceiptV1(
            observer_id="HOST_SUPERVISOR",
            status="HEALTHY",
            subject_id="sha256:9999999999999999999999999999999999999999999999999999999999999999",
            profile_digest="sha256:8888888888888888888888888888888888888888888888888888888888888888",
        )
        with pytest.raises(ActivationRefusal) as exc_info:
            evaluate_guard_activation(
                profile_digest="sha256:8888888888888888888888888888888888888888888888888888888888888888",
                hit=base_hit,
                danger=base_danger,
                externally_admitted=True,
                suspended=False,
                host_health=receipt,
            )
        assert exc_info.value.code == "SUBJECT_MISMATCH"

    def test_profile_mismatch_refuses(
        self,
        base_hit: DetectorHitRefV1,
        base_danger: DangerSignalReceiptV1,
    ):
        """Host health receipt profile mismatch raises TWO_SIGNAL_COLLAPSE."""
        receipt = HostHealthReceiptV1(
            observer_id="HOST_SUPERVISOR",
            status="HEALTHY",
            subject_id=base_hit.subject_id,
            profile_digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
        )
        with pytest.raises(ActivationRefusal) as exc_info:
            evaluate_guard_activation(
                profile_digest="sha256:1111111111111111111111111111111111111111111111111111111111111111",
                hit=base_hit,
                danger=base_danger,
                externally_admitted=True,
                suspended=False,
                host_health=receipt,
            )
        assert exc_info.value.code == "TWO_SIGNAL_COLLAPSE"

    def test_model_authored_host_health_voucher_vulnerability(
        self,
        base_hit: DetectorHitRefV1,
        base_danger: DangerSignalReceiptV1,
    ):
        """HostHealthReceiptV1 refuses model-authored observer IDs ('MODEL')."""
        with pytest.raises(ValueError, match="FORBIDDEN_OBSERVER"):
            HostHealthReceiptV1(
                observer_id="MODEL",
                status="HEALTHY",
                subject_id=base_hit.subject_id,
                profile_digest="sha256:7777777777777777777777777777777777777777777777777777777777777777",
            )

    def test_tampered_timestamp_unvalidated_vulnerability(self):
        """HostHealthReceiptV1 validates timestamp and refuses corrupted/tampered strings."""
        with pytest.raises(ValueError, match="timestamp"):
            HostHealthReceiptV1(
                observer_id="HOST_CHECK",
                status="HEALTHY",
                subject_id="sha256:1111111111111111111111111111111111111111111111111111111111111111",
                profile_digest="sha256:2222222222222222222222222222222222222222222222222222222222222222",
                timestamp="NOT_A_TIMESTAMP_CORRUPTED_OR_TAMPERED",
            )


# ============================================================================
# Section 4: QM Invariant Antibody Suite Falsification
# ============================================================================


class TestQMInvariantAntibodyFalsification:
    """Adversarial stress-testing and boundary falsification of QMInvariantAntibodySuiteV1."""

    def test_ab04_autoimmune_false_positive_on_valid_physics(self):
        """Ab04 passes valid physics statement 'so no transition occurs' without autoimmune false positive."""
        valid_text = (
            "Complete Quantum Mechanics Derivation for Hamiltonian H:\n"
            "Obligation 1: Spectrum & Projectors: Eigenvalues are E_1, E_2, E_3, E_4 with spectral projectors. "
            "Exceptional cases: J = Delta = 0 yields degeneracy where branch guards are required.\n"
            "Obligation 2: Transition Probability: P_01_to_10(t) = (J^2/(J^2+Delta^2)) * sin^2(omega * t). "
            "Initial condition P(0) = 0 satisfied identically since sin^2(0) = 0.\n"
            "Obligation 3: State Metrics: For reduced density matrix rho_1, von Neumann entropy "
            "satisfies S(rho_1) in [0, 1] bit, concurrence C in [0, 1], and CHSH expectation in [2, 2*sqrt(2)].\n"
            "Obligation 4: Thermal Gibbs State: High temperature partition function limit at beta = 0 gives "
            "Z(beta=0) = Tr(I_4) = 4. Partial transpose eigenvalues satisfy Peres-Horodecki criterion.\n"
            "Obligation 5: Consistency Checks: Trace normalization Tr(rho) = 1 verified. Initial condition P(0)=0. "
            "Decoupled limit: at J = 0, P(t) = 0, so no transition occurs. Branch guard at J = Delta = 0 explicit."
        )
        receipt = QMInvariantAntibodySuiteV1.evaluate(valid_text)
        ab04_finding = next(f for f in receipt.findings if f.antibody_id == "Ab04_DecoupledLimitStationarity")
        assert ab04_finding.passed is True
        assert "Stationarity under decoupled limit J = 0 verified" in ab04_finding.evidence

    def test_ab02_decimal_leak_on_initial_probability(self):
        """Ab02 rejects non-zero decimal value P(0) = 0.5."""
        text = "Initial condition transition probability P(0) = 0.5 at t = 0."
        finding = QMInvariantAntibodySuiteV1._check_ab02_initial_transition_probability(text)
        assert finding.passed is False
        assert "Contradicts initial boundary condition" in finding.evidence

    def test_ab03_decimal_leak_on_probability_range(self):
        """Ab03 rejects probability range violation P = 1.5."""
        text = "The transition probability is P = 1.5 at time t."
        finding = QMInvariantAntibodySuiteV1._check_ab03_probability_range(text)
        assert finding.passed is False
        assert "Probability range violation detected" in finding.evidence

    def test_ab06_decimal_and_multi_digit_leak_on_partition_function(self):
        """Ab06 rejects invalid partition function limits Z(0) = 4.5 and Z(0) = 42."""
        for bad_val in ["4.5", "42"]:
            text = f"High temperature partition function Z(0) = {bad_val}."
            finding = QMInvariantAntibodySuiteV1._check_ab06_high_temperature_partition_function(text)
            assert finding.passed is False
            assert "Contradicts high-temperature partition limit" in finding.evidence

    def test_ab07_decimal_leak_on_concurrence_range(self):
        """Ab07 rejects concurrence range violation C = 1.5."""
        text = "Pure-state concurrence is C = 1.5."
        finding = QMInvariantAntibodySuiteV1._check_ab07_concurrence_range(text)
        assert finding.passed is False
        assert "Concurrence range violation detected" in finding.evidence

    def test_ab08_decimal_and_format_leak_on_entropy_bits(self):
        """Ab08 rejects single-qubit entropy violations S(rho_1) = 1.5 bits and S(rho_1) = 2 bits."""
        text1 = "Single-qubit entropy is S(rho_1) = 1.5 bits."
        finding1 = QMInvariantAntibodySuiteV1._check_ab08_single_qubit_entropy_bits(text1)
        assert finding1.passed is False
        assert "Single-qubit entropy exceeds 1-bit physical bound" in finding1.evidence

        text2 = "Obligation 3: von Neumann entropy S(rho_1) = 2 bits."
        finding2 = QMInvariantAntibodySuiteV1._check_ab08_single_qubit_entropy_bits(text2)
        assert finding2.passed is False
        assert "Single-qubit entropy exceeds 1-bit physical bound" in finding2.evidence

    def test_ab09_tsirelson_and_classical_floor_leak(self):
        """Ab09 rejects only values outside the physical range |S| <= 2*sqrt(2)."""
        text1 = "The maximal CHSH = 2.95."
        finding1 = QMInvariantAntibodySuiteV1._check_ab09_chsh_bound_range(text1)
        assert finding1.passed is False
        assert "CHSH expectation violates Tsirelson ceiling" in finding1.evidence

        # Below the local-hidden-variable bound is still physical (no Bell violation).
        text2 = "The maximal CHSH = 1.5."
        assert QMInvariantAntibodySuiteV1._check_ab09_chsh_bound_range(text2).passed is True

    def test_ab09_maximally_mixed_state_is_physical(self):
        """PR #63 review regression: rho = I/4 gives S = 0 for every CHSH setting."""
        for text in ("For rho = I/4 the CHSH = 0.", "CHSH = -1.2", "CHSH = 2*sqrt(2)", "CHSH < 2"):
            assert QMInvariantAntibodySuiteV1._check_ab09_chsh_bound_range(text).passed is True, text
        for text in ("CHSH = 2.83", "CHSH = -3", "CHSH > 2*sqrt(2)"):
            assert QMInvariantAntibodySuiteV1._check_ab09_chsh_bound_range(text).passed is False, text

    def test_ab10_decimal_leak_on_trace_normalization(self):
        """Ab10 rejects trace normalization violation Tr(rho) = 1.5."""
        text = "Density matrix trace normalization Tr(rho) = 1.5."
        finding = QMInvariantAntibodySuiteV1._check_ab10_cross_section_consistency(text)
        assert finding.passed is False
        assert "Density matrix trace normalization violated" in finding.evidence
