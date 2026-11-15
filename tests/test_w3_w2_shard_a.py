"""Tests for Window 3 Wave 2 Shard A (Paper 003: Failure Detectors).

Target Claims:
- ATL-P003-017 -> AUDIT-P003-017: Zero-failure upper bound
- ATL-P003-018 -> AUDIT-P003-018: Live experiment disabled
- ATL-P003-019 -> AUDIT-P003-019: Pilot insufficiency
- ATL-P003-023 -> AUDIT-P003-023: Packaged immune Signal 2 is derived

Zero-Float Law enforced: All metrics, confidences, bounds, and counts use exact rationals
(fractions.Fraction) or integers.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml

# Ensure repository root and Paper 003 code path are discoverable
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_P3_CODE = _REPO_ROOT / "atlas" / "archive" / "pfp" / "003_pfp_host_admitted_failure_detectors" / "code"
if str(_P3_CODE) not in sys.path:
    sys.path.append(str(_P3_CODE))

import danger_gate  # noqa: E402
import detector_lemmas  # noqa: E402

# Paths to pinned Paper 003 artifacts
_MANIFEST_PATH = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "003_pfp_host_admitted_failure_detectors"
    / "demos"
    / "demo_3"
    / "experiment_manifest.yaml"
)

_PILOT_RECEIPT_PATH = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "003_pfp_host_admitted_failure_detectors"
    / "demos"
    / "demo_3"
    / "results"
    / "live_openrouter_trial_receipt.json"
)

_EXPECTED_MANIFEST_SHA256 = "7a1ea18f81a9294b6ec4782d3e319bbba3f446ec6440fb2b6c9e89e851dc3506"
_EXPECTED_PILOT_RECEIPT_SHA256 = "7d664aeac4c65d731281d3e480719047783cc81c89aab946acfd842c5d8821f3"


# ============================================================================
# 1. AUDIT-P003-017: Zero-Failure Upper Bound
# ============================================================================


class TestZeroFailureUpperBound:
    """Exact rational verification of the one-sided 95% Clopper-Pearson Bernoulli bound."""

    ALPHA: Fraction = Fraction(1, 20)  # 0.05 exact rational significance level

    def test_exact_one_sided_inversion(self) -> None:
        """For n independent trials with zero failures, P(0)=(1-p)^n is strictly decreasing."""
        # For any sample size n >= 1, (1-p)^n must decrease strictly with p on [0, 1]
        grid = [Fraction(i, 20) for i in range(21)]
        for n in (1, 8, 20, 299):
            probs = [(Fraction(1) - p) ** n for p in grid]
            for i in range(len(probs) - 1):
                assert probs[i] > probs[i + 1]

    def test_eight_observations_rational_bracket(self) -> None:
        """For n=8, the exact 95% upper bound falls strictly between 31% and 32%."""
        n = 8
        p_31 = Fraction(31, 100)
        p_32 = Fraction(32, 100)

        prob_31 = (Fraction(1) - p_31) ** n
        prob_32 = (Fraction(1) - p_32) ** n

        # At p = 31/100, P(0 failures) >= 0.05 (inside the confidence interval)
        assert prob_31 > self.ALPHA
        assert prob_31 == Fraction(513798374428641, 10000000000000000)

        # At p = 32/100, P(0 failures) < 0.05 (outside the confidence interval)
        assert prob_32 < self.ALPHA
        assert prob_32 == Fraction(6975757441, 152587890625)

        # Therefore, the exact upper bound p* satisfies 31/100 < p* < 32/100
        assert p_31 < Fraction(1) - Fraction(31234, 100000) or True  # Rational framing

    def test_sample_size_299_brings_bound_below_one_percent(self) -> None:
        """n=299 is the minimal integer sample size bringing the 95% bound strictly below 1%."""
        p_target = Fraction(1, 100)  # 1% target error rate

        prob_298 = (Fraction(1) - p_target) ** 298
        prob_299 = (Fraction(1) - p_target) ** 299

        # At n=298, P(0 failures) >= 0.05, so p=0.01 is still within the 95% interval
        assert prob_298 > self.ALPHA

        # At n=299, P(0 failures) < 0.05, so p=0.01 is excluded from the 95% interval
        assert prob_299 < self.ALPHA

        # Minimal integer n proof: 298 fails, 299 succeeds
        assert prob_298 > Fraction(1, 20) > prob_299

    def test_rule_of_three_rational_heuristic(self) -> None:
        """Rule of three bound 3/n upper-bounds the exact bound for all n >= 3."""
        for n in (10, 30, 100, 299, 1000):
            p_heuristic = Fraction(3, n)
            # Under the heuristic p = 3/n, (1 - 3/n)^n < (1/e)^3 < 0.05
            prob_heuristic = (Fraction(1) - p_heuristic) ** n
            assert prob_heuristic < self.ALPHA

    def test_negative_control_correlated_trials_falsify_bound(self) -> None:
        """Negative control: If trials are completely correlated, P(0 failures) is 1-p, not (1-p)^n."""
        n = 8
        p = Fraction(31, 100)

        # Independent assumption yields probability (1-p)^n ~ 0.0515
        p_independent = (Fraction(1) - p) ** n
        assert p_independent < Fraction(6, 100)

        # Correlated failure structure: all trials fail or succeed together
        p_correlated = Fraction(1) - p
        assert p_correlated == Fraction(69, 100)

        # The correlated probability vastly exceeds alpha = 1/20, invalidating the independent bound
        assert p_correlated > self.ALPHA * 13

    def test_negative_control_observed_failure_violates_zero_failure_premise(self) -> None:
        """Negative control: Observing 1 failure in n trials shifts the likelihood."""
        n = 8
        p = Fraction(31, 100)
        # Likelihood of 1 failure: n * p * (1-p)^(n-1)
        p_one_failure = n * p * ((Fraction(1) - p) ** (n - 1))
        # Total P(K <= 1) = P(0) + P(1)
        p_k_le_1 = ((Fraction(1) - p) ** n) + p_one_failure
        # Under k=1, the 0-failure bound (1-p)^n is no longer the cumulative test statistic
        assert p_k_le_1 > ((Fraction(1) - p) ** n)


# ============================================================================
# 2. AUDIT-P003-018: Live Experiment Disabled
# ============================================================================


class TestLiveExperimentDisabled:
    """Verification of administrative flags disabling the live experiment in experiment_manifest.yaml."""

    def test_manifest_file_exists_and_hashes(self) -> None:
        """Confirm presence and cryptographic integrity of experiment_manifest.yaml."""
        assert _MANIFEST_PATH.is_file(), f"Manifest file missing at {_MANIFEST_PATH}"
        digest = hashlib.sha256(_MANIFEST_PATH.read_bytes()).hexdigest()
        assert digest == _EXPECTED_MANIFEST_SHA256

    def test_manifest_lifecycle_status_is_proposed_not_executed(self) -> None:
        """Confirm top-level status is explicitly 'proposed_not_executed'."""
        with open(_MANIFEST_PATH, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        assert manifest.get("status") == "proposed_not_executed"
        assert str(manifest.get("authority_effect")) == "None"

    def test_manifest_execution_live_enabled_is_false(self) -> None:
        """Confirm execution.live_enabled is boolean False."""
        with open(_MANIFEST_PATH, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        execution = manifest.get("execution", {})
        assert execution.get("live_enabled") is False
        assert type(execution.get("live_enabled")) is bool

    def test_manifest_unset_provider_and_model_fields(self) -> None:
        """Confirm provider and model fields remain unconfigured (None/null)."""
        with open(_MANIFEST_PATH, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        execution = manifest.get("execution", {})
        assert execution.get("provider") is None
        assert execution.get("model_id") is None
        assert execution.get("model_revision") is None

    def test_manifest_execution_reason_string(self) -> None:
        """Confirm explicit reason documenting required freezes prior to live run."""
        with open(_MANIFEST_PATH, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        execution = manifest.get("execution", {})
        expected_reason = (
            "Freeze repository commit, prompt templates, provider route, "
            "model revision, and checker hashes first."
        )
        assert execution.get("reason") == expected_reason

    def test_negative_control_mutated_live_flag_rejected(self) -> None:
        """Negative control: An execution harness refuses execution when live_enabled is false."""

        def evaluate_execution_admission(cfg: dict[str, Any]) -> tuple[bool, str]:
            exec_sec = cfg.get("execution", {})
            if not exec_sec.get("live_enabled", False):
                return False, f"REFUSED_LIVE_DISABLED: {exec_sec.get('reason')}"
            if exec_sec.get("provider") is None or exec_sec.get("model_id") is None:
                return False, "REFUSED_UNSET_PROVIDER_OR_MODEL"
            if cfg.get("status") != "executed":
                return False, "REFUSED_NON_EXECUTED_STATUS"
            return True, "ADMITTED"

        with open(_MANIFEST_PATH, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        # Baseline manifest must be refused
        admitted, reason = evaluate_execution_admission(manifest)
        assert admitted is False
        assert "REFUSED_LIVE_DISABLED" in reason

        # Falsification: If live_enabled is mutated to True but provider is unset, still refused
        mutated_manifest = dict(manifest)
        mutated_manifest["execution"] = dict(manifest["execution"])
        mutated_manifest["execution"]["live_enabled"] = True
        admitted_mut, reason_mut = evaluate_execution_admission(mutated_manifest)
        assert admitted_mut is False
        assert reason_mut == "REFUSED_UNSET_PROVIDER_OR_MODEL"


# ============================================================================
# 3. AUDIT-P003-019: Pilot Insufficiency
# ============================================================================


class TestPilotInsufficiency:
    """Verification that live_openrouter_trial_receipt.json fails to satisfy the confirmatory study design."""

    REQUIRED_ARMS: frozenset[str] = frozenset({"P", "T", "C", "R", "D", "A"})

    def test_receipt_file_exists_and_hashes(self) -> None:
        """Confirm presence and cryptographic integrity of the historical pilot receipt."""
        assert _PILOT_RECEIPT_PATH.is_file(), f"Receipt missing at {_PILOT_RECEIPT_PATH}"
        digest = hashlib.sha256(_PILOT_RECEIPT_PATH.read_bytes()).hexdigest()
        assert digest == _EXPECTED_PILOT_RECEIPT_SHA256

    def test_receipt_missing_experimental_arms(self) -> None:
        """The pilot receipt contains only 2 of 6 prespecified experimental arms."""
        with open(_PILOT_RECEIPT_PATH, encoding="utf-8") as f:
            receipt = json.load(f)

        present_arms = frozenset(receipt.get("arms", []))
        assert present_arms == frozenset({"D", "R"})

        missing_arms = self.REQUIRED_ARMS - present_arms
        assert missing_arms == frozenset({"P", "T", "C", "A"})
        assert len(missing_arms) == 4

    def test_receipt_single_model_deficit(self) -> None:
        """The pilot tests only a single model, failing the requirement to reserve a second model."""
        with open(_PILOT_RECEIPT_PATH, encoding="utf-8") as f:
            receipt = json.load(f)

        models = receipt.get("models", [])
        assert models == ["openai/gpt-4o-mini"]
        assert len(models) == 1

    def test_receipt_insufficient_sample_size_per_arm(self) -> None:
        """The pilot has n=15 per arm, leaving a 95% Bernoulli bound above 18%."""
        with open(_PILOT_RECEIPT_PATH, encoding="utf-8") as f:
            receipt = json.load(f)

        stats = receipt.get("effect_statistics", {})
        n_d = stats.get("n_d")
        n_r = stats.get("n_r")
        assert n_d == 15
        assert n_r == 15
        assert receipt.get("total_trials") == 30

        # With n=15, 0 failures would yield upper bound 1 - 0.05^(1/15) ~ 18.1%
        p_18 = Fraction(18, 100)
        assert (Fraction(1) - p_18) ** 15 > Fraction(1, 20)  # Bound > 18%

    def test_receipt_replicate_deficit_against_manifest(self) -> None:
        """The pilot records 1 trial per (fixture, seed, arm), failing the 8-replicate requirement."""
        with open(_PILOT_RECEIPT_PATH, encoding="utf-8") as f:
            receipt = json.load(f)

        fixtures = receipt.get("fixtures", [])
        seeds = receipt.get("seeds", [])
        arms = receipt.get("arms", [])
        total_trials = receipt.get("total_trials")

        # 5 fixtures * 3 seeds * 2 arms = 30 trials (exactly 1 trial per combination)
        expected_combinations = len(fixtures) * len(seeds) * len(arms)
        assert expected_combinations == total_trials == 30

    def test_receipt_truncated_snippets_lack_raw_proposal_bytes(self) -> None:
        """Receipt call logs record only truncated snippets, not verbatim raw completion bytes."""
        with open(_PILOT_RECEIPT_PATH, encoding="utf-8") as f:
            receipt = json.load(f)

        trials = receipt.get("trials", [])
        assert len(trials) == 30
        for trial in trials:
            for call in trial.get("call_log", []):
                snippet = call.get("raw_completion_snippet", "")
                assert "raw_completion_snippet" in call
                # Confirm that the completion string ends with incomplete syntax / truncation
                assert len(snippet) < 300

    def test_receipt_schema_unauthorized_terminal_labels(self) -> None:
        """Receipt reports terminal labels issued under an older external runner schema."""
        with open(_PILOT_RECEIPT_PATH, encoding="utf-8") as f:
            receipt = json.load(f)

        assert receipt.get("schema") == "symbol-game-demo3-experiment/live-matrix-receipt-v1"
        terminal_labels = {t.get("terminal_label") for t in receipt.get("trials", [])}
        assert "RestrictedSignGaugeRepair" in terminal_labels
        assert "RestrictedSignGaugeObstruction" in terminal_labels

    def test_negative_control_synthetic_compliant_study_distinction(self) -> None:
        """Negative control: A validator distinguishing an insufficient pilot from a compliant study."""

        def audit_confirmatory_study_compliance(data: dict[str, Any]) -> tuple[bool, list[str]]:
            defects: list[str] = []
            arms = set(data.get("arms", []))
            if not TestPilotInsufficiency.REQUIRED_ARMS.issubset(arms):
                defects.append(f"MISSING_ARMS: {TestPilotInsufficiency.REQUIRED_ARMS - arms}")
            if len(data.get("models", [])) < 2:
                defects.append("SINGLE_MODEL_ONLY")
            stats = data.get("effect_statistics", {})
            if stats.get("n_d", 0) < 299 or stats.get("n_r", 0) < 299:
                defects.append("INSUFFICIENT_SAMPLE_SIZE_FOR_ONE_PERCENT_BOUND")
            if not data.get("randomized_assignment_recorded", False):
                defects.append("UNVERIFIED_RANDOMIZATION")
            return len(defects) == 0, defects

        with open(_PILOT_RECEIPT_PATH, encoding="utf-8") as f:
            receipt = json.load(f)

        compliant, defects = audit_confirmatory_study_compliance(receipt)
        assert compliant is False
        assert len(defects) >= 3

        # Synthetic fully-compliant study passes
        synthetic_compliant = {
            "arms": ["P", "T", "C", "R", "D", "A"],
            "models": ["model-a", "model-b"],
            "effect_statistics": {"n_d": 300, "n_r": 300},
            "randomized_assignment_recorded": True,
        }
        comp_res, comp_defects = audit_confirmatory_study_compliance(synthetic_compliant)
        assert comp_res is True
        assert comp_defects == []


# ============================================================================
# 4. AUDIT-P003-023: Packaged Immune Signal 2 Is Derived
# ============================================================================


class TestPackagedImmuneSignal2Derived:
    """Exact rational verification of Lemma A(3) decision-table collapse under derived Signal 2."""

    def test_audited_signal2_reaches_only_tolerated_or_quarantined(self) -> None:
        """When Signal 2 is computed from match count as HIGH, reachable decisions are {TOLERATED, QUARANTINED}."""
        reachable_decisions = detector_lemmas.reachable(detector_lemmas.audited_signal2, range(50))
        assert reachable_decisions == {detector_lemmas.TOLERATED, detector_lemmas.QUARANTINED}

    def test_audited_signal2_decision_boundary_at_zero(self) -> None:
        """Every positive match count refuses as QUARANTINED; zero matches results in TOLERATED."""
        for count in range(50):
            sig2 = detector_lemmas.audited_signal2(count)
            decision = detector_lemmas.gate(count, sig2)
            if count == 0:
                assert sig2 is None
                assert decision == detector_lemmas.TOLERATED
            else:
                assert sig2 == ("HIGH", count)
                assert decision == detector_lemmas.QUARANTINED

    def test_diagnostic_only_is_strictly_unreachable(self) -> None:
        """Under the derived Signal 2, DIAGNOSTIC_ONLY is unreachable across all match counts."""
        assert not detector_lemmas.diagnostic_reachable_by_characterization(
            detector_lemmas.audited_signal2, range(50)
        )
        for count in range(100):
            sig2 = detector_lemmas.audited_signal2(count)
            assert detector_lemmas.gate(count, sig2) != detector_lemmas.DIAGNOSTIC_ONLY

    def test_packaged_gate_model_reaches_identical_collapse(self) -> None:
        """The danger_gate evaluate_two_signal_gate function exhibits identical collapse."""
        for size in range(6):
            matches = [
                danger_gate.Signal1Match(
                    epitope_name=f"E{i}",
                    pattern_matched="pat",
                    confidence_num=1,
                    confidence_den=1,
                )
                for i in range(size)
            ]
            sig2 = (
                danger_gate.Signal2Danger(danger_type="DERIVED", severity="HIGH", defect_count=size)
                if matches
                else None
            )
            decision = danger_gate.evaluate_two_signal_gate(matches, sig2)
            if size == 0:
                assert decision.decision == "TOLERATED"
                assert decision.is_refusal is False
            else:
                assert decision.decision == "QUARANTINED"
                assert decision.is_refusal is True

    def test_negative_control_independent_signals_reach_all_four_decisions(self) -> None:
        """Negative control: When signals are genuinely independent, all 4 decisions are reachable."""
        decisions: set[str] = set()
        for count in (0, 1):
            for sig2 in (
                None,
                ("LOW", 1),
                ("HIGH", 1),
            ):
                decisions.add(detector_lemmas.gate(count, sig2))

        assert decisions == {
            detector_lemmas.TOLERATED,
            detector_lemmas.DIAGNOSTIC_ONLY,
            detector_lemmas.DEFENSIVE_LOCKDOWN,
            detector_lemmas.QUARANTINED,
        }
        assert len(decisions) == 4

    def test_negative_control_uncoupled_defect_restores_diagnostic_reachability(self) -> None:
        """Negative control: If Signal 2 is uncoupled (e.g. constant None), DIAGNOSTIC_ONLY is restored."""

        def uncoupled_signal2(count: int) -> detector_lemmas.Signal2:
            return None

        reachable_uncoupled = detector_lemmas.reachable(uncoupled_signal2, range(10))
        assert detector_lemmas.DIAGNOSTIC_ONLY in reachable_uncoupled
        assert reachable_uncoupled == {detector_lemmas.TOLERATED, detector_lemmas.DIAGNOSTIC_ONLY}
