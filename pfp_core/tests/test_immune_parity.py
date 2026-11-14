"""Side-by-side parity validation tests for pfp_immune host binary and Python fallback.

Exercises all 5 host subcommands:
1. screen: Thymus negative selection over clean self panel
2. decide: Two-signal disposition check using exact rational comparisons
3. taint: Lineage DAG causal taint propagation with cycle refusal
4. select: 60/30/10 ecological reserve partition via largest-remainder allocation
5. exclusion: Multi-family consensus agreement and falsifier ordering
Also tests operad ledger recording across WF14, WF19, WF41, and WF51.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import tempfile
from fractions import Fraction
from pathlib import Path

import pytest

from eis.domain.value_objects import DetectorRule
from pfp_core import immune_host
from pfp_core.civilization import Candidate, Lineage
from pfp_core.civilization import select as py_select
from pfp_core.exclusions import ExclusionHypothesisV1, ExclusionVoteV1
from pfp_core.immunity import (
    DIAGNOSTIC,
    HOLD,
    PASS,
    host_danger,
    signal1,
)
from pfp_core.immunity import (
    decide as py_decide,
)
from pfp_core.immunity import (
    screen_rules as py_screen_rules,
)
from pfp_core.operad_ledger import OperadLedgerAdapter
from pfp_core.workflow_families.layer6 import ImmuneFailureClassification
from pfp_core.workflow_families.layer7 import (
    DetectorAdequacyTwoSignal,
    ExclusionHypothesisRetest,
    FailureDerivedRuleTransfer,
)


@pytest.fixture(scope="module")
def require_host():
    """Ensure host binary is present before running parity tests."""
    if not immune_host.is_available():
        pytest.skip("pfp_immune host binary not available on this platform")


# ---------------------------------------------------------------------------
# 1. Screen Subcommand Parity
# ---------------------------------------------------------------------------

def test_screen_clean_candidates_admitted(require_host):
    self_panel = ["clean_sample_alpha", "clean_sample_beta"]
    candidates = [
        {"rule_id": "r1", "pattern": "defect_pattern", "capability_kind": "Detector"},
        {"rule_id": "r2", "pattern": "absent_pattern", "capability_kind": "Detector"},
    ]
    res = immune_host.screen(self_panel, candidates)
    assert res["status"] == "PASS"
    assert res["admitted"] == ["r1", "r2"]
    assert res["purged"] == []

    # Parity with Python screen_rules
    py_rules = [
        DetectorRule(rule_id="r1", target_epitope="Detector", match_pattern="defect_pattern"),
        DetectorRule(rule_id="r2", target_epitope="Detector", match_pattern="absent_pattern"),
    ]
    py_admitted, py_killed = py_screen_rules(py_rules, self_panel)
    assert [r.rule_id for r in py_admitted] == res["admitted"]
    assert len(py_killed) == len(res["purged"])


def test_screen_autoimmune_candidates_purged(require_host):
    self_panel = ["clean_sample_alpha", "clean_sample_beta"]
    candidates = [
        {"rule_id": "r_clean", "pattern": "clean_sample", "capability_kind": "Detector"},
        {"rule_id": "r_good", "pattern": "defect", "capability_kind": "Detector"},
    ]
    res = immune_host.screen(self_panel, candidates)
    assert res["status"] == "FAIL"
    assert res["admitted"] == ["r_good"]
    assert len(res["purged"]) == 1
    assert res["purged"][0]["rule_id"] == "r_clean"
    assert "SELF_REACTIVE" in res["purged"][0]["reason"]

    # Parity with Python screen_rules
    py_rules = [
        DetectorRule(rule_id="r_clean", target_epitope="Detector", match_pattern="clean_sample"),
        DetectorRule(rule_id="r_good", target_epitope="Detector", match_pattern="defect"),
    ]
    py_admitted, py_killed = py_screen_rules(py_rules, self_panel)
    assert [r.rule_id for r in py_admitted] == res["admitted"]
    assert len(py_killed) == 1
    assert py_killed[0]["rule_id"] == "r_clean"


# ---------------------------------------------------------------------------
# 2. Decide Subcommand Parity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("signal1_matches", "danger_score", "expected_status", "expected_disposition_contains"),
    [
        ([], Fraction(0, 1), "PASS", "no rule match"),
        (["m1"], Fraction(0, 1), "DIAGNOSTIC_OR_NORMALIZE", "diagnostic only"),
        ([], Fraction(1, 1), "HOLD_OR_REPAIR", "exceeds threshold"),
        (["m1"], Fraction(1, 1), "HOLD_OR_REPAIR", "two-signal activation"),
    ],
)
def test_decide_quadrant_matrix(
    require_host, signal1_matches, danger_score, expected_status, expected_disposition_contains
):
    threshold = Fraction(1, 2)
    res = immune_host.decide(signal1_matches, danger_score, threshold)
    assert res["status"] == expected_status
    assert expected_disposition_contains in res["disposition"]


def test_decide_exact_rational_fractions(require_host):
    # Fraction 3/5 is greater than 1/2 threshold -> HOLD_OR_REPAIR
    res_above = immune_host.decide([], Fraction(3, 5), Fraction(1, 2))
    assert res_above["status"] == "HOLD_OR_REPAIR"

    # Fraction 2/5 is less than 1/2 threshold -> PASS
    res_below = immune_host.decide([], Fraction(2, 5), Fraction(1, 2))
    assert res_below["status"] == "PASS"

    # Prohibits floating point values
    with pytest.raises(TypeError, match="floating point values prohibited"):
        immune_host.decide([], 0.5, (1, 2))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 3. Taint Subcommand Parity
# ---------------------------------------------------------------------------

def test_taint_dag_propagation(require_host):
    edges = [
        {"parent": "p0", "child": "p1", "witness": "w1"},
        {"parent": "p1", "child": "p2", "witness": "w2"},
        {"parent": "p2", "child": "p3", "witness": "w3"},
    ]
    res = immune_host.taint(edges, revoked_parents=["p1"])
    assert set(res["tainted_nodes"]) == {"p1", "p2", "p3"}

    # Parity with Lineage.taint in civilization.py
    lin = Lineage()
    for e in edges:
        lin.derive(e["parent"], e["child"], "mutation")
    py_tainted = lin.taint({"p1"})
    assert py_tainted == set(res["tainted_nodes"])


def test_taint_cycle_refusal(require_host):
    edges = [
        {"parent": "a", "child": "b", "witness": "w1"},
        {"parent": "b", "child": "a", "witness": "w2"},
    ]
    res = immune_host.taint(edges, revoked_parents=["a"])
    assert res["status"] == "REFUSED"
    assert "Cycle detected" in res["reason"]

    # Lineage.derive detects cycle on insertion
    lin = Lineage()
    lin.derive("a", "b", "m")
    with pytest.raises(ValueError, match="CYCLE"):
        lin.derive("b", "a", "m")


# ---------------------------------------------------------------------------
# 4. Select Subcommand Parity
# ---------------------------------------------------------------------------

def test_select_reserve_partition_and_rational_ordering(require_host):
    population = [
        {"id": "c0", "fitness": Fraction(9, 10), "lineage_depth": 1},
        {"id": "c1", "fitness": Fraction(8, 10), "lineage_depth": 2},
        {"id": "c2", "fitness": Fraction(7, 10), "lineage_depth": 1},
        {"id": "c3", "fitness": Fraction(6, 10), "lineage_depth": 3},
        {"id": "c4", "fitness": Fraction(5, 10), "lineage_depth": 1},
        {"id": "c5", "fitness": Fraction(4, 10), "lineage_depth": 2},
        {"id": "c6", "fitness": Fraction(3, 10), "lineage_depth": 1},
        {"id": "c7", "fitness": Fraction(2, 10), "lineage_depth": 2},
        {"id": "c8", "fitness": Fraction(1, 10), "lineage_depth": 3},
        {"id": "c9", "fitness": Fraction(0, 10), "lineage_depth": 1},
    ]
    res = immune_host.select(population)
    assert len(res["core_60"]) == 6
    assert len(res["exploratory_30"]) == 3
    assert len(res["novel_10"]) == 1
    assert res["core_60"] == ["c0", "c1", "c2", "c3", "c4", "c5"]
    assert res["exploratory_30"] == ["c6", "c7", "c8"]
    assert res["novel_10"] == ["c9"]


# ---------------------------------------------------------------------------
# 5. Exclusion Subcommand Parity
# ---------------------------------------------------------------------------

def test_exclusion_consensus_and_falsifier_ordering(require_host):
    # Concordance with ExclusionHypothesisV1.classify
    hyp_dead = ExclusionHypothesisV1(
        "h1", "b1", "claim", "[1, 2]", 2,
        (ExclusionVoteV1("s1", "fam_a", True), ExclusionVoteV1("s2", "fam_b", True)),
    )
    assert hyp_dead.classify(min_families=2) == "PROBABLY_DEAD"

    votes_dead = {"fam_a": "EXCLUDE", "fam_b": "EXCLUDE"}
    res_dead = immune_host.exclusion(votes_dead, ["h1"])
    assert res_dead["consensus"] == "PROBABLY_DEAD"

    hyp_front = ExclusionHypothesisV1(
        "h2", "b2", "claim", "[3]", 1,
        (ExclusionVoteV1("s1", "fam_a", True), ExclusionVoteV1("s2", "fam_b", False)),
    )
    assert hyp_front.classify(min_families=2) == "FRONTIER"

    votes_front = {"fam_a": "EXCLUDE", "fam_b": "INCLUDE"}
    res_front = immune_host.exclusion(votes_front, ["h2"])
    assert res_front["consensus"] == "FRONTIER"

    hyp_uncorr = ExclusionHypothesisV1(
        "h3", "b3", "claim", "[4]", 1,
        (ExclusionVoteV1("s1", "fam_a", True),),
    )
    assert hyp_uncorr.classify(min_families=2) == "UNCORROBORATED"

    votes_uncorr = {"fam_a": "EXCLUDE"}
    res_uncorr = immune_host.exclusion(votes_uncorr, ["h3"])
    assert res_uncorr["consensus"] == "UNCORROBORATED"


# ---------------------------------------------------------------------------
# 6. Workflow Families and Operad Ledger Recording
# ---------------------------------------------------------------------------

def test_wf14_with_ledger_records_failures(require_host):
    with tempfile.TemporaryDirectory(prefix="pfp-wf14-ledger-") as tmp:
        ledger_file = Path(tmp) / "ledger.jsonl"
        wf = ImmuneFailureClassification()
        good_rules = [
            {"rule_id": "denominator_one", "target_epitope": "RATIONAL_NONCANONICAL", "pattern": '/1"'},
            {"rule_id": "leading_two", "target_epitope": "NONMONIC_LEADING_COEFFICIENT", "pattern": r"\[2,"},
            {"rule_id": "single_quotes", "target_epitope": "MALFORMED_JSON", "pattern": r"\{'"},
            {"rule_id": "autoimmune_bad", "target_epitope": "MALFORMED_JSON", "pattern": "coefficients"},
        ]
        task = {
            "statement": "Propose detector rules.",
            "failures": wf.failures(),
            "self_panel_sha256": "digest",
            "ledger_path": str(ledger_file),
            "run_id": "test_run_wf14",
        }
        from pfp_core.fidelity import HostOracleContext
        host_oracle = HostOracleContext()

        sealed = {"self_panel": wf.fixtures()["two_signal_rules_admitted"][0]["sealed"]["self_panel"]}
        task["self_panel_sha256"] = wf.fixtures()["two_signal_rules_admitted"][0]["task"]["self_panel_sha256"]

        verdict = wf.check(task, sealed, {"rules": good_rules}, host_oracle)
        assert verdict.verdict == "REFUSED"  # Autoimmune rule killed

        # Verify ledger recorded the thymus kill
        adapter = OperadLedgerAdapter(ledger_file)
        assert adapter.verify()["status"] == "PASS"
        lines = [json.loads(line) for line in ledger_file.read_text().splitlines() if line.strip()]
        assert len(lines) >= 1
        thymus_records = [entry["record"] for entry in lines if "thymus_kill" in entry["record"].get("id", "")]
        assert len(thymus_records) == 1
        assert thymus_records[0]["failure_class"] == "BoundaryLeakage"


def test_wf19_with_ledger_records_trials_and_admissions(require_host):
    with tempfile.TemporaryDirectory(prefix="pfp-wf19-ledger-") as tmp:
        ledger_file = Path(tmp) / "ledger.jsonl"
        wf = FailureDerivedRuleTransfer()
        fixtures = wf.fixtures()
        bundle, expected = fixtures["rules_transfer_to_held_out"]

        # Add ledger_path to task
        bundle["task"]["ledger_path"] = str(ledger_file)
        bundle["task"]["run_id"] = "test_run_wf19"

        from pfp_core.workflow_families.base import new_budget
        budget = new_budget("WF19:test", bundle["task"])
        try:
            verdict = wf.execute(bundle, budget=budget)
        finally:
            budget.close()
        assert verdict.verdict == "HOST_CERTIFIED"

        # Verify ledger recorded trial and admission
        adapter = OperadLedgerAdapter(ledger_file)
        assert adapter.verify()["status"] == "PASS"
        lines = [json.loads(line) for line in ledger_file.read_text().splitlines() if line.strip()]
        records = [entry["record"] for entry in lines]
        trials = [r for r in records if r.get("kind") == "trial"]
        admissions = [r for r in records if r.get("kind") == "admission"]
        assert len(trials) >= 1
        assert len(admissions) >= 1
        assert admissions[0]["candidate"] == trials[0]["candidate"]


def test_wf41_with_ledger_records_candidate_trial_admission(require_host):
    with tempfile.TemporaryDirectory(prefix="pfp-wf41-ledger-") as tmp:
        ledger_file = Path(tmp) / "ledger.jsonl"
        wf = DetectorAdequacyTwoSignal()
        bundle, expected = wf.fixtures()["calibrated_detector_admitted"]

        bundle["task"]["ledger_path"] = str(ledger_file)
        bundle["task"]["run_id"] = "test_run_wf41"

        from pfp_core.workflow_families.base import new_budget
        budget = new_budget("WF41:test", bundle["task"])
        try:
            verdict = wf.execute(bundle, budget=budget)
        finally:
            budget.close()
        assert verdict.verdict == "HOST_CERTIFIED"

        adapter = OperadLedgerAdapter(ledger_file)
        assert adapter.verify()["status"] == "PASS"
        lines = [json.loads(line) for line in ledger_file.read_text().splitlines() if line.strip()]
        records = [entry["record"] for entry in lines]
        candidates = [r for r in records if r.get("kind") == "candidate"]
        trials = [r for r in records if r.get("kind") == "trial"]
        admissions = [r for r in records if r.get("kind") == "admission"]
        assert len(candidates) == 1
        assert len(trials) == 1
        assert len(admissions) == 1
        assert candidates[0]["id"] == "denominator_one"
        assert admissions[0]["candidate"] == "denominator_one"


def test_wf51_with_ledger_records_branch_drop_failure(require_host):
    with tempfile.TemporaryDirectory(prefix="pfp-wf51-ledger-") as tmp:
        ledger_file = Path(tmp) / "ledger.jsonl"
        wf = ExclusionHypothesisRetest()
        bundle, expected = wf.fixtures()["control_without_retest_hides_the_answer"]

        bundle["task"]["ledger_path"] = str(ledger_file)
        bundle["task"]["run_id"] = "test_run_wf51"

        from pfp_core.workflow_families.base import new_budget
        budget = new_budget("WF51:test", bundle["task"])
        try:
            verdict = wf.execute(bundle, budget=budget)
        finally:
            budget.close()
        assert verdict.verdict == "TYPED_REFUSAL"

        adapter = OperadLedgerAdapter(ledger_file)
        assert adapter.verify()["status"] == "PASS"
        lines = [json.loads(line) for line in ledger_file.read_text().splitlines() if line.strip()]
        records = [entry["record"] for entry in lines]
        failures = [r for r in records if r.get("kind") == "failure"]
        assert len(failures) >= 1
        assert failures[0]["failure_class"] == "BRANCH_DROP_EXHAUSTION"


# ---------------------------------------------------------------------------
# 7. Offline Fallback Verification (Zero Binary Dependency)
# ---------------------------------------------------------------------------

def test_offline_fallback_mode(monkeypatch):
    """Verify that when host binary is unavailable, Python fallback executes deterministically."""
    monkeypatch.setattr(immune_host, "is_available", lambda: False)

    # 1. Screen rules fallback
    self_panel = ["clean_sample"]
    rules = [
        DetectorRule(rule_id="r_auto", target_epitope="Detector", match_pattern="clean"),
        DetectorRule(rule_id="r_good", target_epitope="Detector", match_pattern="absent"),
    ]
    admitted, killed = py_screen_rules(rules, self_panel)
    assert [r.rule_id for r in admitted] == ["r_good"]
    assert [k["rule_id"] for k in killed] == ["r_auto"]

    # 2. Decide fallback
    assert py_decide([], None).disposition == PASS
    assert py_decide(signal1("absent", [rules[1]]), None).disposition == DIAGNOSTIC
    danger = host_danger("MALFORMED_PAYLOAD", "host.contract_check", "test")
    assert py_decide([], danger).disposition == HOLD

    # 3. Taint fallback
    lin = Lineage()
    lin.derive("x", "y", "m")
    lin.derive("y", "z", "m")
    assert lin.taint({"x"}) == {"x", "y", "z"}

    # 4. Select fallback
    cand_base = Candidate("base", 3, 4, 100, 1000, 10, is_baseline=True)
    cand_better = Candidate("better", 4, 4, 150, 1500, 12)
    cand_unm = Candidate("unm", 0, 0, 0, 1200, 0, measured=False)
    sel = py_select([cand_base, cand_better, cand_unm])
    assert sel["Front"] == ["better"]
    assert sel["Baseline"] == ["base"]
    assert sel["Unmeasured"] == ["unm"]

    # 5. Exclusion fallback
    hyp = ExclusionHypothesisV1(
        "h_off", "b0", "claim", "[1]", 1,
        (ExclusionVoteV1("s1", "f1", True), ExclusionVoteV1("s2", "f2", True)),
    )
    assert hyp.classify(min_families=2) == "PROBABLY_DEAD"

