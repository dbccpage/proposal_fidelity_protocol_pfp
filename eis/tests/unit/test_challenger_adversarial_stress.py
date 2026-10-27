"""Adversarial Stress Test Suite for Epistemic Immune System, Allostery, and Evolution.

Author: challenger_2 (Empirical Adversarial Challenger)
AuthorityEffect: None.

Exhaustively verifies:
1. Two-Signal Independence (F-IMMUNE-04):
   - Signal 1 alone (without Signal 2) -> DIAGNOSTIC_ONLY, is_suppressed=False.
   - Signal 2 alone (without Signal 1) across all DangerSeverity levels -> DIAGNOSTIC_ONLY, is_suppressed=False.
   - Both signals strictly required for immune suppression (QUARANTINED / DEFENSIVE_LOCKDOWN, is_suppressed=True).
   - evaluate_conjunction truth table and Two-Signal Collapse traps.
   - ImmuneEvaluationEngineV1 custody tiers and conjunction logic.
2. Allosteric Quorum & Hill Cooperativity:
   - Silence / zero signals -> is_activated=False.
   - Sub-threshold binding: single sensor at cap (S=1 < 2) -> H(1)=0.20 < 0.50 -> False.
   - Sub-threshold sum with multiple sensors (S=1.5 < 2) -> False.
   - Cooperative multi-sensor quorum: 2 sensors at cap (S=2) -> H(2)=0.50 >= 0.50 -> True, quorum_size=2.
   - Cooperative multi-sensor quorum: 3 sensors (S=3) -> H(3)=9/13 -> True.
   - Sensor cap enforcement: value > per_sensor_cap -> raises AllosteryRefusal("SIGNAL_ABOVE_SENSOR_CAP").
   - Duplicate sensor detection (case-insensitive) -> raises AllosteryRefusal("DUPLICATE_SENSOR").
   - Type fences: float and bool rejected -> raises AllosteryRefusal("NOT_EXACT_RATIONAL").
   - Negative signal and sensor count limits (>4096) -> raises AllosteryRefusal("SIGNAL_OUT_OF_RANGE").
   - minimal_quorum calculation under varied Hill parameters and uncapped gate.
3. Provisional Promotion & MIS Support (U16):
   - ObservationSupportPolicyV1:
     - 0, 1, 2 independent observations -> support < 3, eligible=False.
     - 5-clique K_5 of correlated observations -> MIS = 1, eligible=False.
     - 5-cycle C_5 of pairwise conflicting observations -> MIS = 2, eligible=False.
     - Star graph K_{1,3} -> MIS = 3, eligible=True.
     - 3 disjoint edges 3 K_2 -> MIS = 3, eligible=True.
     - 3 completely independent observations -> MIS = 3, eligible=True.
     - Deduplication of same occurrence_id and identical 4-tuples.
     - Propagated references rejected with PROPAGATED_REFERENCE_CANNOT_BE_OBSERVATION.
     - Graph budget ceiling >32 nodes -> SUPPORT_BUDGET_EXHAUSTED, eligible=False.
   - ProvisionalPromotionEngineV1:
     - support < 3 -> Candidate, review_queued=False.
     - support >= 3 -> Provisional, review_queued=True.
     - Placeholder / defect prefix -> Placeholder refuses promotion, review_queued=False.
4. Prompt Ecology Evaporation & Decay:
   - ClonalSelectionEngine:
     - Linear idle counter increment on apply_decay.
     - Deactivation when runs_idle >= half_life_runs.
     - Stimulation resets runs_idle=0 and increments affinity_score.
     - filter_active_repertoire strips deactivated rules.
   - ClonalSelectorV1:
     - Float affinity boost rejected with TypeError("EXACT_RATIONAL_REQUIRED").
     - GuardInstance autonomous decay rejected with PermissionError("EXTERNAL_EPOCH_DECISION_REQUIRED").
   - Exact rational exponential half-life verification comparing kinetics.
"""

from __future__ import annotations

from fractions import Fraction
import pytest

from eis.domain.danger_gate import (
    DangerDecision,
    DangerSeverity,
    GuardDisposition,
    ImmuneEvaluationEngineV1,
    Signal1Match,
    Signal2Danger,
    TwoSignalCollapseError,
    TwoSignalDangerGate,
)
from eis.domain.danger_signals import (
    SignalIndependenceRefusal,
    assert_signals_independent,
    signal1_digest,
)
from eis.domain.allostery import (
    AllostericConsensusGate,
    AllostericDecision,
    DEFAULT_PARAMETERS,
    minimal_quorum,
)
from eis.domain.value_objects import (
    AllosteryRefusal,
    DetectorRule,
    HillParameters,
)
from eis.domain.provisional_promotion import (
    ObservationSupportPolicyV1,
    PromotionResult,
    ProvisionalPromotionEngineV1,
    RawObservationV1,
    SupportResult,
)
from eis.domain.clonal_selection import (
    ClonalSelectionEngine,
    ClonalSelectorV1,
    GuardInstance,
)


# ==============================================================================
# 1. TWO-SIGNAL INDEPENDENCE (F-IMMUNE-04)
# ==============================================================================

class TestTwoSignalIndependenceStress:
    """Empirical verification of F-IMMUNE-04: strict requirement of both signals."""

    @pytest.fixture
    def match(self) -> Signal1Match:
        return Signal1Match("model-verdict", "verified", 1.0, 0)

    @pytest.fixture
    def danger_high(self) -> Signal2Danger:
        return Signal2Danger(
            danger_type="PROTECTED_FIELD_VIOLATION",
            severity=DangerSeverity.HIGH,
            defect_count=1,
            evidence_digest="sha256:" + "a" * 64,
            observer_id="host-protected-field-check",
        )

    def test_case0_neither_signal_tolerated(self) -> None:
        """Neither Signal 1 nor Signal 2 -> TOLERATED, is_suppressed=False."""
        result = TwoSignalDangerGate.evaluate([], None)
        assert result.decision == DangerDecision.TOLERATED
        assert result.is_suppressed is False
        assert result.signal1_count == 0
        assert result.signal2_severity is None

    def test_case1_signal1_alone_is_diagnostic_only(self, match: Signal1Match) -> None:
        """Signal 1 alone (without Signal 2) -> DIAGNOSTIC_ONLY, is_suppressed=False."""
        # 1 match
        result1 = TwoSignalDangerGate.evaluate([match], None)
        assert result1.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert result1.is_suppressed is False
        assert result1.signal1_count == 1
        assert result1.signal2_severity is None

        # 5 matches
        matches = [Signal1Match("model-verdict", f"pattern_{i}", 1.0, i * 10) for i in range(5)]
        result5 = TwoSignalDangerGate.evaluate(matches, None)
        assert result5.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert result5.is_suppressed is False
        assert result5.signal1_count == 5

        # Danger with 0 defect count is treated as absent Signal 2
        empty_danger = Signal2Danger(
            danger_type="PROTECTED_FIELD_VIOLATION",
            severity=DangerSeverity.CRITICAL,
            defect_count=0,
            evidence_digest="sha256:" + "b" * 64,
            observer_id="host-check",
        )
        result_empty_d = TwoSignalDangerGate.evaluate(matches, empty_danger)
        assert result_empty_d.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert result_empty_d.is_suppressed is False

    @pytest.mark.parametrize("severity", list(DangerSeverity))
    def test_case2_signal2_alone_never_suppresses(self, severity: DangerSeverity) -> None:
        """Signal 2 alone across ALL severities (LOW, MEDIUM, HIGH, CRITICAL) -> DIAGNOSTIC_ONLY, is_suppressed=False."""
        danger = Signal2Danger(
            danger_type="HOST_STRUCTURAL_DEFECT",
            severity=severity,
            defect_count=10,
            evidence_digest="sha256:" + "c" * 64,
            observer_id="host-syntax-verifier",
        )
        result = TwoSignalDangerGate.evaluate([], danger)
        assert result.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert result.is_suppressed is False
        assert result.signal2_severity == severity
        assert result.signal1_count == 0

    def test_case3_both_signals_strictly_required_for_suppression(
        self, match: Signal1Match
    ) -> None:
        """Both Signal 1 and Signal 2 present -> suppression engaged."""
        # LOW severity -> DEFENSIVE_LOCKDOWN, is_suppressed=True
        d_low = Signal2Danger("DEFECT", DangerSeverity.LOW, 1, "sha256:" + "0" * 64, "host")
        res_low = TwoSignalDangerGate.evaluate([match], d_low)
        assert res_low.decision == DangerDecision.DEFENSIVE_LOCKDOWN
        assert res_low.is_suppressed is True

        # MEDIUM severity -> DEFENSIVE_LOCKDOWN, is_suppressed=True
        d_med = Signal2Danger("DEFECT", DangerSeverity.MEDIUM, 1, "sha256:" + "0" * 64, "host")
        res_med = TwoSignalDangerGate.evaluate([match], d_med)
        assert res_med.decision == DangerDecision.DEFENSIVE_LOCKDOWN
        assert res_med.is_suppressed is True

        # HIGH severity -> QUARANTINED, is_suppressed=True
        d_high = Signal2Danger("DEFECT", DangerSeverity.HIGH, 1, "sha256:" + "0" * 64, "host")
        res_high = TwoSignalDangerGate.evaluate([match], d_high)
        assert res_high.decision == DangerDecision.QUARANTINED
        assert res_high.is_suppressed is True

        # CRITICAL severity -> QUARANTINED, is_suppressed=True
        d_crit = Signal2Danger("DEFECT", DangerSeverity.CRITICAL, 1, "sha256:" + "0" * 64, "host")
        res_crit = TwoSignalDangerGate.evaluate([match], d_crit)
        assert res_crit.decision == DangerDecision.QUARANTINED
        assert res_crit.is_suppressed is True

    def test_evaluate_conjunction_truth_table(self) -> None:
        """Evaluate conjunction method truth table."""
        gate = TwoSignalDangerGate()
        assert gate.evaluate_conjunction(None, None) == GuardDisposition.NO_ACTIVATION
        assert gate.evaluate_conjunction("signal1_present", None) == GuardDisposition.FINDING
        assert gate.evaluate_conjunction(None, "signal2_present") == GuardDisposition.NO_ACTIVATION
        assert gate.evaluate_conjunction("signal1_present", "signal2_present") == GuardDisposition.REFUSE

    def test_two_signal_collapse_derived_signal2(self) -> None:
        """Signal 2 derived from Signal 1 raises TwoSignalCollapseError in conjunction."""
        gate = TwoSignalDangerGate()

        class DerivedDanger:
            is_derived = True
            source = "MATCHER"

        with pytest.raises(TwoSignalCollapseError, match="TWO_SIGNAL_COLLAPSE"):
            gate.evaluate_conjunction("signal1", DerivedDanger())

    def test_two_signal_collapse_model_authored_signal2(self) -> None:
        """Model-authored Signal 2 returns TWO_SIGNAL_COLLAPSE."""
        gate = TwoSignalDangerGate()

        class ModelDanger:
            source = "MODEL"

        assert gate.evaluate_conjunction("signal1", ModelDanger()) == GuardDisposition.TWO_SIGNAL_COLLAPSE

    def test_evaluate_independent_refuses_derived_or_same_digest(self, match: Signal1Match) -> None:
        """assert_signals_independent and evaluate_independent refuse non-independent Signal 2."""
        # 1. Same evidence digest as Signal 1
        d_same_digest = Signal2Danger(
            "PROTECTED_FIELD_VIOLATION",
            DangerSeverity.HIGH,
            1,
            evidence_digest=signal1_digest([match]),
            observer_id="host-check",
        )
        with pytest.raises(SignalIndependenceRefusal) as exc:
            TwoSignalDangerGate.evaluate_independent(
                [match],
                d_same_digest,
                detector_id="regex",
                detector_predicates=frozenset(),
                offsets_are_content=False,
            )
        assert exc.value.code == "TWO_SIGNAL_COLLAPSE"

        # 2. Observer is same as detector
        d_same_observer = Signal2Danger(
            "PROTECTED_FIELD_VIOLATION",
            DangerSeverity.HIGH,
            1,
            evidence_digest="sha256:" + "d" * 64,
            observer_id="regex",
        )
        with pytest.raises(SignalIndependenceRefusal) as exc2:
            TwoSignalDangerGate.evaluate_independent(
                [match],
                d_same_observer,
                detector_id="regex",
                detector_predicates=frozenset(),
                offsets_are_content=False,
            )
        assert exc2.value.code == "TWO_SIGNAL_COLLAPSE"

    def test_immune_evaluation_engine_custody_tiers(self) -> None:
        """ImmuneEvaluationEngineV1 requires both signals and proper custody for REFUSE."""
        engine = ImmuneEvaluationEngineV1()

        # Admitted + both signals -> REFUSE
        assert engine.evaluate(
            custody="admitted",
            target_scope="math",
            admitted_scope=["math"],
            detector_match=True,
            independent_danger=True,
        ) == GuardDisposition.REFUSE

        # Admitted + detector_match only (Signal 1 only) -> FINDING (not REFUSE)
        assert engine.evaluate(
            custody="admitted",
            target_scope="math",
            admitted_scope=["math"],
            detector_match=True,
            independent_danger=False,
        ) == GuardDisposition.FINDING

        # Admitted + independent_danger only (no detector_match) -> NO_ACTIVATION
        assert engine.evaluate(
            custody="admitted",
            target_scope="math",
            admitted_scope=["math"],
            detector_match=False,
            independent_danger=True,
        ) == GuardDisposition.NO_ACTIVATION

        # Provisional custody + both signals -> FINDING (provisional cannot refuse yet)
        assert engine.evaluate(
            custody="provisional",
            target_scope="math",
            admitted_scope=["math"],
            detector_match=True,
            independent_danger=True,
        ) == GuardDisposition.FINDING

        # Candidate custody -> NO_ACTIVATION
        assert engine.evaluate(
            custody="candidate",
            target_scope="math",
            admitted_scope=["math"],
            detector_match=True,
            independent_danger=True,
        ) == GuardDisposition.NO_ACTIVATION


# ==============================================================================
# 2. ALLOSTERIC QUORUM & HILL COOPERATIVITY
# ==============================================================================

class TestAllostericConsensusStress:
    """Stress-test AllostericConsensusGate across edge cases, caps, sub-threshold, and quorum."""

    def test_edge_silence_and_zero_signals(self) -> None:
        """Empty signal mapping or all-zero signals cannot activate."""
        gate = AllostericConsensusGate()

        # Empty signals
        dec_empty = gate.evaluate_quorum({})
        assert dec_empty.is_activated is False
        assert dec_empty.aggregate_signal == Fraction(0)
        assert dec_empty.positive_sensors == 0
        assert dec_empty.hill_value == Fraction(0)

        # Non-empty with zero values
        dec_zeros = gate.evaluate_quorum({"sensor1": 0, "sensor2": 0})
        assert dec_zeros.is_activated is False
        assert dec_zeros.aggregate_signal == Fraction(0)
        assert dec_zeros.positive_sensors == 0
        assert dec_zeros.hill_value == Fraction(0)

    def test_edge_sensor_cap_exceeded(self) -> None:
        """Individual sensor exceeding per_sensor_cap is strictly refused."""
        gate = AllostericConsensusGate(per_sensor_cap=Fraction(1))
        with pytest.raises(AllosteryRefusal) as exc:
            gate.evaluate_quorum({"rogue_sensor": Fraction(3, 2)})
        assert exc.value.code == "SIGNAL_ABOVE_SENSOR_CAP"

    def test_edge_case_insensitive_duplicate_sensors(self) -> None:
        """Sensors that differ only in casing cannot sneak through."""
        gate = AllostericConsensusGate()
        with pytest.raises(AllosteryRefusal) as exc:
            gate.evaluate_quorum({"SensorA": Fraction(1), "sensora": Fraction(1)})
        assert exc.value.code == "DUPLICATE_SENSOR"

    def test_edge_type_fences_floats_and_bools_rejected(self) -> None:
        """Floats and booleans must be refused with NOT_EXACT."""
        gate = AllostericConsensusGate()
        with pytest.raises(AllosteryRefusal) as exc_float:
            gate.evaluate_quorum({"sensor1": 0.75})
        assert exc_float.value.code == "NOT_EXACT"

        with pytest.raises(AllosteryRefusal) as exc_bool:
            gate.evaluate_quorum({"sensor1": True})
        assert exc_bool.value.code == "NOT_EXACT"

    def test_edge_negative_signal_and_empty_id(self) -> None:
        """Negative signal or invalid sensor id is refused."""
        gate = AllostericConsensusGate()
        with pytest.raises(AllosteryRefusal) as exc_neg:
            gate.evaluate_quorum({"sensor1": -1})
        assert exc_neg.value.code == "SIGNAL_OUT_OF_RANGE"

        with pytest.raises(AllosteryRefusal) as exc_id:
            gate.evaluate_quorum({"": 1})
        assert exc_id.value.code == "BAD_SENSOR_ID"

    def test_sub_threshold_single_sensor_cannot_activate(self) -> None:
        """Default gate (n=2, K=2, t=1/2, cap=1): single sensor at max cap S=1 gives H(1)=1/5 < 1/2."""
        gate = AllostericConsensusGate(
            parameters=DEFAULT_PARAMETERS,
            activation_threshold=Fraction(1, 2),
            per_sensor_cap=Fraction(1),
        )
        assert gate.quorum_size == 2

        # 1 sensor with max value 1
        dec = gate.evaluate_quorum({"sensor1": 1})
        assert dec.aggregate_signal == Fraction(1)
        assert dec.positive_sensors == 1
        assert dec.hill_value == Fraction(1, 5)  # 1^2 / (2^2 + 1^2) = 1/5
        assert dec.is_activated is False

    def test_sub_threshold_multiple_sensors_sum_below_threshold(self) -> None:
        """Three weak sensors summing to S=3/2 < 2 cannot activate."""
        gate = AllostericConsensusGate(
            parameters=DEFAULT_PARAMETERS,
            activation_threshold=Fraction(1, 2),
            per_sensor_cap=Fraction(1),
        )
        dec = gate.evaluate_quorum({
            "s1": Fraction(1, 2),
            "s2": Fraction(1, 2),
            "s3": Fraction(1, 2),
        })
        assert dec.aggregate_signal == Fraction(3, 2)
        assert dec.positive_sensors == 3
        # H(3/2) = (9/4) / (4 + 9/4) = (9/4) / (25/4) = 9/25 = 0.36 < 0.50
        assert dec.hill_value == Fraction(9, 25)
        assert dec.is_activated is False

    def test_cooperative_quorum_activation(self) -> None:
        """Two sensors at cap (S=2) reach H(2)=1/2 and activate quorum."""
        gate = AllostericConsensusGate(
            parameters=DEFAULT_PARAMETERS,
            activation_threshold=Fraction(1, 2),
            per_sensor_cap=Fraction(1),
        )
        dec = gate.evaluate_quorum({"model_a": 1, "model_b": 1})
        assert dec.aggregate_signal == Fraction(2)
        assert dec.positive_sensors == 2
        # H(2) = 4 / (4 + 4) = 1/2
        assert dec.hill_value == Fraction(1, 2)
        assert dec.is_activated is True

    def test_cooperative_high_hill_coefficient_sigmoidal_switch(self) -> None:
        """High Hill coefficient n=4, K=2 produces ultra-sharp sigmoidal transition."""
        params = HillParameters(hill_coefficient=4, half_maximal_constant=Fraction(2))
        gate = AllostericConsensusGate(
            parameters=params,
            activation_threshold=Fraction(1, 2),
            per_sensor_cap=Fraction(1),
        )
        # minimal quorum: m*1 >= 2 -> quorum_size = 2
        assert gate.quorum_size == 2

        # S=1: H(1) = 1 / (16 + 1) = 1/17 ~ 0.0588 (strongly suppressed)
        dec1 = gate.evaluate_quorum({"s1": 1})
        assert dec1.hill_value == Fraction(1, 17)
        assert dec1.is_activated is False

        # S=2: H(2) = 16 / (16 + 16) = 1/2 = 0.50 (exact transition)
        dec2 = gate.evaluate_quorum({"s1": 1, "s2": 1})
        assert dec2.hill_value == Fraction(1, 2)
        assert dec2.is_activated is True

        # S=3: H(3) = 81 / (16 + 81) = 81/97 ~ 0.8351 (strong activation)
        dec3 = gate.evaluate_quorum({"s1": 1, "s2": 1, "s3": 1})
        assert dec3.hill_value == Fraction(81, 97)
        assert dec3.is_activated is True

    def test_minimal_quorum_scaling(self) -> None:
        """Verify minimal_quorum computation with various thresholds and caps."""
        p2 = HillParameters(hill_coefficient=2, half_maximal_constant=Fraction(2))
        # cap = 1, t = 1/2 -> quorum = 2
        assert minimal_quorum(p2, Fraction(1, 2), Fraction(1)) == 2
        # cap = 1/2, t = 1/2 -> quorum = 4
        assert minimal_quorum(p2, Fraction(1, 2), Fraction(1, 2)) == 4
        # cap = 1/4, t = 1/2 -> quorum = 8
        assert minimal_quorum(p2, Fraction(1, 2), Fraction(1, 4)) == 8

    def test_uncapped_gate_behavior(self) -> None:
        """Uncapped gate (per_sensor_cap=None) allows single sensor to reach sum threshold."""
        gate = AllostericConsensusGate(per_sensor_cap=None)
        assert gate.quorum_size is None

        # Single sensor with value 2 reaches threshold
        dec = gate.evaluate_quorum({"super_sensor": 2})
        assert dec.is_activated is True
        assert dec.positive_sensors == 1
        assert dec.quorum_size is None


# ==============================================================================
# 3. PROVISIONAL PROMOTION & MIS SUPPORT (U16)
# ==============================================================================

class TestProvisionalPromotionStress:
    """Stress-test ObservationSupportPolicyV1 and ProvisionalPromotionEngineV1."""

    def test_fewer_than_3_observations_fails_promotion(self) -> None:
        """Graphs with fewer than 3 independent observations must fail promotion."""
        policy = ObservationSupportPolicyV1()
        engine = ProvisionalPromotionEngineV1()

        # 0 observations
        res0 = policy.compute_support([])
        assert res0.support_count == 0
        assert res0.eligible_for_provisional is False
        prom0 = engine.promote_candidate_if_eligible("cand_0", res0.support_count, ["math"])
        assert prom0.new_custody == "Candidate"
        assert prom0.review_queued is False

        # 1 observation
        obs1 = [RawObservationV1("occ_1", "model_1", "scaff_1", "prec_1", "root_1")]
        res1 = policy.compute_support(obs1)
        assert res1.support_count == 1
        assert res1.eligible_for_provisional is False
        prom1 = engine.promote_candidate_if_eligible("cand_1", res1.support_count, ["math"])
        assert prom1.new_custody == "Candidate"
        assert prom1.review_queued is False

        # 2 independent observations
        obs2 = [
            RawObservationV1("occ_1", "model_1", "scaff_1", "prec_1", "root_1"),
            RawObservationV1("occ_2", "model_2", "scaff_2", "prec_2", "root_2"),
        ]
        res2 = policy.compute_support(obs2)
        assert res2.support_count == 2
        assert res2.eligible_for_provisional is False
        prom2 = engine.promote_candidate_if_eligible("cand_2", res2.support_count, ["math"])
        assert prom2.new_custody == "Candidate"
        assert prom2.review_queued is False

    def test_correlated_clique_k5_fails_promotion(self) -> None:
        """5 observations sharing the same model_id form a 5-clique K_5 -> MIS = 1 < 3."""
        policy = ObservationSupportPolicyV1()
        engine = ProvisionalPromotionEngineV1()

        clique_obs = [
            RawObservationV1(f"occ_{i}", "shared_model", f"scaff_{i}", f"prec_{i}", f"root_{i}")
            for i in range(5)
        ]
        res = policy.compute_support(clique_obs)
        assert res.support_count == 1  # only 1 node in maximum independent set
        assert res.eligible_for_provisional is False
        prom = engine.promote_candidate_if_eligible("cand_k5", res.support_count, ["math"])
        assert prom.new_custody == "Candidate"
        assert prom.review_queued is False

    def test_correlated_cycle_c5_fails_promotion(self) -> None:
        """5 observations with pairwise cyclical conflicts form exact C_5 -> MIS = floor(5/2) = 2 < 3."""
        policy = ObservationSupportPolicyV1()
        engine = ProvisionalPromotionEngineV1()

        # Build an exact chordless 5-cycle: (0-1), (1-2), (2-3), (3-4), (4-0)
        # Node 0: model=m40, scaff=s01, prec=p0, root=r0
        # Node 1: model=m1,  scaff=s01, prec=p12, root=r1  (edge 0-1 via scaff)
        # Node 2: model=m23, scaff=s2,  prec=p12, root=r2  (edge 1-2 via prec)
        # Node 3: model=m23, scaff=s3,  prec=p3,  root=r34 (edge 2-3 via model)
        # Node 4: model=m40, scaff=s4,  prec=p4,  root=r34 (edge 3-4 via root, edge 4-0 via model)
        cycle_obs = [
            RawObservationV1("occ_0", generating_model_id="m40", scaffold_digest="s01", precedent_set_digest="p0", inheritance_root="r0"),
            RawObservationV1("occ_1", generating_model_id="m1",  scaffold_digest="s01", precedent_set_digest="p12", inheritance_root="r1"),
            RawObservationV1("occ_2", generating_model_id="m23", scaffold_digest="s2",  precedent_set_digest="p12", inheritance_root="r2"),
            RawObservationV1("occ_3", generating_model_id="m23", scaffold_digest="s3",  precedent_set_digest="p3",  inheritance_root="r34"),
            RawObservationV1("occ_4", generating_model_id="m40", scaffold_digest="s4",  precedent_set_digest="p4",  inheritance_root="r34"),
        ]
        res = policy.compute_support(cycle_obs)
        assert res.support_count == 2
        assert res.eligible_for_provisional is False
        prom = engine.promote_candidate_if_eligible("cand_c5", res.support_count, ["math"])
        assert prom.new_custody == "Candidate"
        assert prom.review_queued is False

    def test_three_independent_observations_succeeds_promotion(self) -> None:
        """3 completely independent observations -> MIS = 3 -> Provisional promotion succeeds."""
        policy = ObservationSupportPolicyV1()
        engine = ProvisionalPromotionEngineV1()

        indep_obs = [
            RawObservationV1("occ_1", "model_1", "scaff_1", "prec_1", "root_1"),
            RawObservationV1("occ_2", "model_2", "scaff_2", "prec_2", "root_2"),
            RawObservationV1("occ_3", "model_3", "scaff_3", "prec_3", "root_3"),
        ]
        res = policy.compute_support(indep_obs)
        assert res.support_count == 3
        assert res.eligible_for_provisional is True
        prom = engine.promote_candidate_if_eligible("cand_indep3", res.support_count, ["math"])
        assert prom.new_custody == "Provisional"
        assert prom.review_queued is True
        assert prom.enforcement_authorized is False

    def test_disjoint_pairs_reach_quorum(self) -> None:
        """6 observations in 3 disjoint conflicting pairs (3 K_2) -> MIS = 3 -> succeeds."""
        policy = ObservationSupportPolicyV1()
        engine = ProvisionalPromotionEngineV1()

        obs = [
            # Pair 1 (conflicts on model)
            RawObservationV1("occ_1a", generating_model_id="model_A"),
            RawObservationV1("occ_1b", generating_model_id="model_A"),
            # Pair 2 (conflicts on scaffold)
            RawObservationV1("occ_2a", scaffold_digest="scaff_B"),
            RawObservationV1("occ_2b", scaffold_digest="scaff_B"),
            # Pair 3 (conflicts on precedent)
            RawObservationV1("occ_3a", precedent_set_digest="prec_C"),
            RawObservationV1("occ_3b", precedent_set_digest="prec_C"),
        ]
        res = policy.compute_support(obs)
        assert res.support_count == 3
        assert res.eligible_for_provisional is True
        prom = engine.promote_candidate_if_eligible("cand_3k2", res.support_count, ["math"])
        assert prom.new_custody == "Provisional"
        assert prom.review_queued is True

    def test_deduplication_of_duplicate_occurrences(self) -> None:
        """Duplicate occurrence_id or identical 4-tuples are deduplicated before MIS."""
        policy = ObservationSupportPolicyV1()

        dup_obs = [
            RawObservationV1("occ_1", "model_1", "scaff_1", "prec_1", "root_1"),
            RawObservationV1("occ_1", "model_1", "scaff_1", "prec_1", "root_1"),  # duplicate occ_id
            RawObservationV1("occ_2", "model_1", "scaff_1", "prec_1", "root_1"),  # identical tuple
            RawObservationV1("occ_3", "model_2", "scaff_2", "prec_2", "root_2"),
        ]
        res = policy.compute_support(dup_obs)
        assert res.support_count == 2
        assert res.eligible_for_provisional is False

    def test_propagated_reference_strictly_rejected(self) -> None:
        """is_propagated_reference=True raises ValueError on registration and computation."""
        policy = ObservationSupportPolicyV1()
        prop_obs = RawObservationV1("occ_p", "model_p", is_propagated_reference=True)

        with pytest.raises(ValueError, match="PROPAGATED_REFERENCE_CANNOT_BE_OBSERVATION"):
            policy.register_observation(prop_obs)

        with pytest.raises(ValueError, match="PROPAGATED_REFERENCE_CANNOT_BE_OBSERVATION"):
            policy.compute_support([prop_obs])

    def test_placeholder_candidate_refuses_promotion(self) -> None:
        """Candidate with placeholder ID or defect:defect: prefix refuses promotion regardless of support."""
        engine = ProvisionalPromotionEngineV1()

        res1 = engine.promote_candidate_if_eligible("placeholder:anti_pattern_1", 5, ["math"])
        assert res1.new_custody == "Placeholder refuses promotion"
        assert res1.review_queued is False

        res2 = engine.promote_candidate_if_eligible("defect:defect:double_prefix", 10, ["math"])
        assert res2.new_custody == "Placeholder refuses promotion"
        assert res2.review_queued is False

    def test_budget_exhaustion_over_32_nodes(self) -> None:
        """More than 32 unique observations triggers SUPPORT_BUDGET_EXHAUSTED."""
        policy = ObservationSupportPolicyV1()
        nodes = [
            RawObservationV1(f"occ_{i}", f"model_{i}", f"scaff_{i}", f"prec_{i}", f"root_{i}")
            for i in range(35)
        ]
        res = policy.compute_support(nodes)
        assert "SUPPORT_BUDGET_EXHAUSTED" in str(res.support_count)
        assert res.eligible_for_provisional is False


# ==============================================================================
# 4. PROMPT ECOLOGY EVAPORATION & DECAY
# ==============================================================================

class TestPromptEcologyDecayStress:
    """Stress-test idle decay, stimulation, and half-life kinetics."""

    def test_clonal_selection_engine_decay_and_deactivation(self) -> None:
        """Rule idle count increments on decay and deactivates at half_life_runs."""
        rule = DetectorRule(
            rule_id="r_decay",
            target_epitope="fake_verdict",
            match_pattern=r"fake\s+verdict",
            generation=1,
            affinity_score=1.0,
            half_life_runs=3,
            runs_idle=0,
            is_active=True,
        )

        # Run 1: idle = 1 < 3 -> still active
        r1 = ClonalSelectionEngine.apply_decay(rule)
        assert r1.runs_idle == 1
        assert r1.is_active is True

        # Run 2: idle = 2 < 3 -> still active
        r2 = ClonalSelectionEngine.apply_decay(r1)
        assert r2.runs_idle == 2
        assert r2.is_active is True

        # Run 3: idle = 3 >= 3 -> evaporated / deactivated!
        r3 = ClonalSelectionEngine.apply_decay(r2)
        assert r3.runs_idle == 3
        assert r3.is_active is False

        # filter_active_repertoire strips r3
        active = ClonalSelectionEngine.filter_active_repertoire([rule, r1, r2, r3])
        assert r3 not in active
        assert len(active) == 3

    def test_clonal_selection_engine_stimulation_resets_idle(self) -> None:
        """Stimulation on match resets runs_idle to 0 and increments affinity_score."""
        stale_rule = DetectorRule(
            rule_id="r_stale",
            target_epitope="fake_verdict",
            match_pattern=r"fake\s+verdict",
            generation=1,
            affinity_score=2.0,
            half_life_runs=5,
            runs_idle=4,
            is_active=True,
        )
        stimulated = ClonalSelectionEngine.stimulate(stale_rule, affinity_boost=1.5)
        assert stimulated.runs_idle == 0
        assert stimulated.is_active is True
        assert stimulated.affinity_score == 3.5

    def test_clonal_selector_v1_type_fences_and_autonomous_decay(self) -> None:
        """ClonalSelectorV1 rejects float affinity boosts and autonomous guard decay."""
        selector = ClonalSelectorV1()

        # Float affinity boost rejected
        with pytest.raises(TypeError, match="EXACT_RATIONAL_REQUIRED"):
            selector.stimulate(affinity_boost=1.5, rule=None)

        # Exact int or rational allowed
        rule_obj = {"id": "dummy"}
        assert selector.stimulate(affinity_boost=2, rule=rule_obj) is rule_obj

        # GuardInstance cannot apply autonomous decay without external epoch decision
        guard = selector.create_guard(initial_active=True)
        with pytest.raises(PermissionError, match="EXTERNAL_EPOCH_DECISION_REQUIRED"):
            guard.apply_autonomous_decay(elapsed_cycles=10)

    def test_exponential_half_life_exact_kinetics(self) -> None:
        """Model the exact rational exponential decay factor (1/2)^k over elapsed generations."""
        # Half life H = 10 generations, base affinity = 100
        # Generations elapsed: 0, 10, 20, 30
        h = 10
        base = Fraction(100)

        def decayed_affinity(elapsed: int) -> Fraction:
            halving_steps = elapsed // h
            decay_factor = Fraction(1, 2 ** halving_steps)
            return base * decay_factor

        assert decayed_affinity(0) == Fraction(100)
        assert decayed_affinity(5) == Fraction(100)   # sub-half-life remains at step 0
        assert decayed_affinity(10) == Fraction(50)   # 1 half-life: halved
        assert decayed_affinity(20) == Fraction(25)   # 2 half-lives: quartered
        assert decayed_affinity(30) == Fraction(25, 2)  # 3 half-lives: 12.5

        # Worked example from Rust test_f_bio_04_evaporation_worked_example:
        # Prior decayed weight at 8 half-lives = 25/256
        # Plus 1 new use at current epoch = 1 = 256/256 -> Total = 281/256
        prior = Fraction(25, 256)
        new_use = Fraction(1)
        total = prior + new_use
        assert total == Fraction(281, 256)
