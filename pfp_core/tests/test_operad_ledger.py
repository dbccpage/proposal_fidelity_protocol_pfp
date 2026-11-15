"""Tests for operad failure ledger wiring, lifecycle, refusal semantics, and headstone conversion."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from pciv.domain.models import CemeteryHeadstoneV1
from pfp_core.exclusions import (
    FRONTIER,
    REFUTED,
    SURVIVED_TEST,
    UNCORROBORATED,
    HeadstoneExclusionPolicyV1,
    plan_retests,
    settle,
)
from pfp_core.operad_ledger import (
    CANONICAL_ANTI_SKILL_FAILURE_CLASSES,
    CANONICAL_FAILURE_CLASSES,
    CANONICAL_PHARMACY_FAILURE_CLASSES,
    OperadLedgerAdapter,
    OperadLedgerError,
    admitted,
    headstone_to_exclusion_hypothesis,
    is_valid_ddc_trace,
    is_valid_evidence_sha256,
    propose_candidate,
    record_admission,
    record_failure,
    record_headstone,
    record_retirement,
    record_trial,
    resolve_failure_class,
    verify,
)

SAMPLE_SHA256 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


@pytest.fixture
def ledger_file(tmp_path: Path) -> Path:
    return tmp_path / "test_ledger.jsonl"


def test_canonical_class_taxonomies():
    assert len(CANONICAL_PHARMACY_FAILURE_CLASSES) == 12
    assert len(CANONICAL_ANTI_SKILL_FAILURE_CLASSES) == 12
    assert len(CANONICAL_FAILURE_CLASSES) == 24
    assert CANONICAL_PHARMACY_FAILURE_CLASSES.isdisjoint(CANONICAL_ANTI_SKILL_FAILURE_CLASSES)


def test_module_level_retirement_and_admitted(ledger_file: Path):
    # Test module-level record_failure, propose_candidate, record_trial, record_admission, record_retirement, admitted
    record_failure(
        ledger_file,
        failure_id="task_fail@run_mod",
        workflow="WF55",
        run="run_mod",
        failure_class="SCHEMA_SEMANTIC_LAUNDERING",
        ddc_trace="CRM",
        evidence_sha256=SAMPLE_SHA256,
    )
    propose_candidate(
        ledger_file,
        candidate_id="cand_semantic",
        capability_kind="antibody",
        constraint="semantic checking",
        derived_from=["task_fail@run_mod"],
    )
    t = record_trial(
        ledger_file,
        candidate_id="cand_semantic",
        held_out=["held_out_case@run_1"],
        baseline_correct=0,
        treated_correct=1,
        clean_panel_hits=0,
    )
    assert t.get("status") == "PASS"
    trial_seq = t["result"]["seq"]

    assert admitted(ledger_file) == []
    adm = record_admission(ledger_file, candidate_id="cand_semantic", trial_seq=trial_seq)
    assert adm.get("status") == "PASS"

    adm_rules = admitted(ledger_file)
    assert len(adm_rules) == 1
    assert adm_rules[0]["id"] == "cand_semantic"

    ret = record_retirement(ledger_file, candidate_id="cand_semantic", reason="retired by test")
    assert ret.get("status") == "PASS"
    assert admitted(ledger_file) == []
    assert is_valid_evidence_sha256(SAMPLE_SHA256) is True
    assert is_valid_evidence_sha256(SAMPLE_SHA256.upper()) is False
    assert is_valid_evidence_sha256("sha256:" + SAMPLE_SHA256) is False
    assert is_valid_evidence_sha256("short") is False
    assert is_valid_evidence_sha256(123) is False


def test_is_valid_ddc_trace():
    assert is_valid_ddc_trace("E") is True
    assert is_valid_ddc_trace("CRM") is True
    assert is_valid_ddc_trace("EΛDMT") is True
    assert is_valid_ddc_trace("") is False
    assert is_valid_ddc_trace("INVALID") is False


def test_resolve_failure_class():
    assert resolve_failure_class("SELF_CERTIFICATION") == "SELF_CERTIFICATION"
    assert resolve_failure_class("SemanticHallucination") == "SemanticHallucination"
    assert resolve_failure_class("REFUSED_FLATTERY_CONTEXT_SMUGGLE") == "SycophanticAgreement"
    assert resolve_failure_class("SYNTAX_ERROR") == "StructuralNonFit"
    assert resolve_failure_class("KILLED_BY_DEFECT_HUNTER: direct import") == "BoundaryLeakage"


def test_record_failure_appends_valid_record(ledger_file: Path):
    res = record_failure(
        ledger_file,
        failure_id="fail_001@run_1",
        workflow="WF14",
        run="run_1",
        failure_class="SELF_CERTIFICATION",
        ddc_trace="CRM",
        evidence_sha256=SAMPLE_SHA256,
    )
    assert res.get("status") == "PASS"
    entry = res.get("result", {})
    assert entry.get("seq") == 0
    assert entry.get("prev") == "0000000000000000000000000000000000000000000000000000000000000000"
    assert entry["record"]["kind"] == "failure"
    assert entry["record"]["id"] == "fail_001@run_1"

    v = verify(ledger_file)
    assert v.get("status") == "PASS"
    assert v.get("result", {}).get("entries") == 1


def test_record_failure_refuses_invalid_failure_class(ledger_file: Path):
    res = record_failure(
        ledger_file,
        failure_id="fail_bad_class",
        workflow="WF14",
        run="run_1",
        failure_class="NOT_A_CANON_CLASS",
        ddc_trace="CRM",
        evidence_sha256=SAMPLE_SHA256,
    )
    assert res.get("status") == "REFUSED"
    refusal = res.get("refusal", {})
    assert refusal.get("code") == "UNKNOWN_FAILURE_CLASS"


def test_record_failure_refuses_bad_ddc_trace(ledger_file: Path):
    res = record_failure(
        ledger_file,
        failure_id="fail_bad_ddc",
        workflow="WF14",
        run="run_1",
        failure_class="SELF_CERTIFICATION",
        ddc_trace="XYZ",
        evidence_sha256=SAMPLE_SHA256,
    )
    assert res.get("status") == "REFUSED"
    refusal = res.get("refusal", {})
    assert refusal.get("code") == "BAD_DDC_TRACE"


def test_record_failure_refuses_uppercase_sha256(ledger_file: Path):
    res = record_failure(
        ledger_file,
        failure_id="fail_bad_sha",
        workflow="WF14",
        run="run_1",
        failure_class="SELF_CERTIFICATION",
        ddc_trace="CRM",
        evidence_sha256=SAMPLE_SHA256.upper(),
    )
    assert res.get("status") == "REFUSED"
    refusal = res.get("refusal", {})
    assert refusal.get("code") == "BAD_EVIDENCE_HASH"


def test_record_headstone_with_cemetery_object(ledger_file: Path):
    raw_digest = "sha256:" + hashlib.sha256(b"payload").hexdigest()
    headstone = CemeteryHeadstoneV1(
        candidate_id="cand_clean_arch_01",
        run_key="run_alpha",
        scene_id="scene_audit",
        cause_of_death="CLEAN_ARCHITECTURE_VIOLATION",
        killing_seat_id="host_check",
        evidence_refs=(),
        candidate_payload_sha256=raw_digest,
    )

    res = record_headstone(ledger_file, headstone, workflow="WF14")
    assert res.get("status") == "PASS"
    entry = res.get("result", {})
    assert entry.get("seq") == 0
    record = entry.get("record", {})
    assert record.get("kind") == "failure"
    assert record.get("failure_class") == "BoundaryLeakage"
    assert record.get("evidence_sha256") == raw_digest.removeprefix("sha256:")
    assert record.get("id") == "cand_clean_arch_01@run_alpha"


def test_record_headstone_with_dict(ledger_file: Path):
    raw_digest = hashlib.sha256(b"dict_payload").hexdigest()
    hs_dict = {
        "candidate_id": "cand_flattery",
        "run_key": "run_beta",
        "scene_id": "scene_dialogue",
        "cause_of_death": "REFUSED_FLATTERY_CONTEXT_SMUGGLE",
        "killing_seat_id": "critic_seat",
        "candidate_payload_sha256": "sha256:" + raw_digest,
    }

    res = record_headstone(ledger_file, hs_dict, workflow="WF19")
    assert res.get("status") == "PASS"
    record = res.get("result", {}).get("record", {})
    assert record.get("failure_class") == "SycophanticAgreement"
    assert record.get("evidence_sha256") == raw_digest


def test_propose_candidate_valid_and_refusal(ledger_file: Path):
    # Proposing candidate before failure exists should be refused with UNKNOWN_FAILURE
    res_unknown = propose_candidate(
        ledger_file,
        candidate_id="rule_01",
        capability_kind="antibody",
        constraint="disallow direct imports",
        derived_from=["nonexistent_failure@run_1"],
    )
    assert res_unknown.get("status") == "REFUSED"
    assert res_unknown.get("refusal", {}).get("code") == "UNKNOWN_FAILURE"

    # Record the failure
    rec_fail = record_failure(
        ledger_file,
        failure_id="fail_arch@run_1",
        workflow="WF14",
        run="run_1",
        failure_class="BoundaryLeakage",
        ddc_trace="CRM",
        evidence_sha256=SAMPLE_SHA256,
    )
    assert rec_fail.get("status") == "PASS"

    # Now candidate with existing derived_from passes
    res_cand = propose_candidate(
        ledger_file,
        candidate_id="rule_01",
        capability_kind="antibody",
        constraint="disallow direct imports",
        derived_from=["fail_arch@run_1"],
    )
    assert res_cand.get("status") == "PASS"
    assert res_cand["result"]["record"]["kind"] == "candidate"


def test_trial_split_overlap_refusal(ledger_file: Path):
    # Setup failure and candidate
    record_failure(
        ledger_file,
        failure_id="case_10@run_1",
        workflow="WF14",
        run="run_1",
        failure_class="SELF_CERTIFICATION",
        ddc_trace="CRM",
        evidence_sha256=SAMPLE_SHA256,
    )
    propose_candidate(
        ledger_file,
        candidate_id="cand_self_cert",
        capability_kind="antibody",
        constraint="verify host check",
        derived_from=["case_10@run_1"],
    )

    # Trial with overlapping case name (case_10@run_2 shares base case_10)
    trial_overlap = record_trial(
        ledger_file,
        candidate_id="cand_self_cert",
        held_out=["case_10@run_2"],
        baseline_correct=0,
        treated_correct=1,
        clean_panel_hits=0,
    )
    assert trial_overlap.get("status") == "REFUSED"
    assert trial_overlap.get("refusal", {}).get("code") == "SPLIT_OVERLAP"


def test_trial_rejects_floats_and_invalid_u32(ledger_file: Path):
    with pytest.raises(OperadLedgerError, match="baseline_correct must be a non-negative 32-bit"):
        record_trial(
            ledger_file,
            candidate_id="rule_01",
            held_out=["case_held@run_2"],
            baseline_correct=1.5,  # float disallowed under Zero-Float law
            treated_correct=2,
            clean_panel_hits=0,
        )

    with pytest.raises(OperadLedgerError, match="clean_panel_hits must be a non-negative 32-bit"):
        record_trial(
            ledger_file,
            candidate_id="rule_01",
            held_out=["case_held@run_2"],
            baseline_correct=0,
            treated_correct=1,
            clean_panel_hits=-1,
        )


def test_admission_unearned_refusal(ledger_file: Path):
    record_failure(
        ledger_file,
        failure_id="case_a@run_1",
        workflow="WF14",
        run="run_1",
        failure_class="FAKE_RECEIPT",
        ddc_trace="CRM",
        evidence_sha256=SAMPLE_SHA256,
    )
    propose_candidate(
        ledger_file,
        candidate_id="cand_fake_receipt",
        capability_kind="rule",
        constraint="cryptographic check",
        derived_from=["case_a@run_1"],
    )

    # Attempt admission without a passing trial for sequence 999
    adm_no_trial = record_admission(
        ledger_file,
        candidate_id="cand_fake_receipt",
        trial_seq=999,
    )
    assert adm_no_trial.get("status") == "REFUSED"
    assert adm_no_trial.get("refusal", {}).get("code") == "NOT_EARNED"


def test_full_lifecycle_append_verify_and_load_admitted(ledger_file: Path):
    adapter = OperadLedgerAdapter(ledger_file)

    # 1. Failure
    f_res = adapter.record_failure(
        failure_id="task_fail@run_1",
        workflow="WF55",
        run="run_1",
        failure_class="OPTIMALITY_HALLUCINATION",
        ddc_trace="CRM",
        evidence_sha256=SAMPLE_SHA256,
    )
    assert f_res.get("status") == "PASS"
    assert f_res["result"]["seq"] == 0

    # 2. Candidate
    c_res = adapter.propose_candidate(
        candidate_id="rule_opt_bound",
        capability_kind="rule",
        constraint="provide measurable cost model",
        derived_from=["task_fail@run_1"],
    )
    assert c_res.get("status") == "PASS"
    assert c_res["result"]["seq"] == 1

    # 3. Trial (passing: treated > baseline and clean_panel_hits == 0)
    t_res = adapter.record_trial(
        candidate_id="rule_opt_bound",
        held_out=["disjoint_case_1@run_held", "disjoint_case_2@run_held"],
        baseline_correct=0,
        treated_correct=2,
        clean_panel_hits=0,
    )
    assert t_res.get("status") == "PASS"
    trial_seq = t_res["result"]["seq"]
    assert trial_seq == 2

    # Verify not admitted yet
    assert adapter.admitted() == []

    # 4. Admission
    a_res = adapter.record_admission(
        candidate_id="rule_opt_bound",
        trial_seq=trial_seq,
    )
    assert a_res.get("status") == "PASS"
    assert a_res["result"]["seq"] == 3

    # Now admitted rules contains rule_opt_bound
    adm_list = adapter.admitted()
    assert len(adm_list) == 1
    assert adm_list[0]["id"] == "rule_opt_bound"
    assert adm_list[0]["capability_kind"] == "rule"

    # Verify ledger integrity
    v_res = adapter.verify()
    assert v_res.get("status") == "PASS"
    assert v_res["result"]["entries"] == 4

    # 5. Retirement
    r_res = adapter.record_retirement(
        candidate_id="rule_opt_bound",
        reason="superseded by exact rational cost metric",
    )
    assert r_res.get("status") == "PASS"
    assert r_res["result"]["seq"] == 4

    # Now admitted rules is empty again
    assert adapter.admitted() == []

    # Final verify
    final_v = adapter.verify()
    assert final_v.get("status") == "PASS"
    assert final_v["result"]["entries"] == 5


def test_headstone_to_exclusion_hypothesis_and_retesting():
    policy = HeadstoneExclusionPolicyV1(
        host_seat_ids=frozenset({"host_check", "oracle"}),
        family_of={"critic_seat_a": "family_alpha", "critic_seat_b": "family_beta"},
    )

    # 1. Host kill stays buried (returns None)
    host_kill = SimpleNamespace(
        headstone_id="hs_host_01",
        candidate_id="cand_syntax_error",
        cause_of_death="SYNTAX_ERROR",
        killing_seat_id="host_check",
    )
    assert headstone_to_exclusion_hypothesis(host_kill, policy, falsifier="recompile", falsifier_cost=1) is None

    # 2. Model seat kill becomes an ExclusionHypothesisV1
    model_kill = {
        "headstone_id": "hs_model_01",
        "candidate_id": "cand_flattery",
        "cause_of_death": "REFUSED_FLATTERY_CONTEXT_SMUGGLE",
        "killing_seat_id": "critic_seat_a",
    }
    hyp = headstone_to_exclusion_hypothesis(model_kill, policy, falsifier="run_anti_flattery_probe", falsifier_cost=2)
    assert hyp is not None
    assert hyp.exclusion_id == "hs_model_01"
    assert hyp.branch == "cand_flattery"
    assert hyp.falsifier == "run_anti_flattery_probe"
    assert hyp.falsifier_cost == 2
    assert hyp.classify() == UNCORROBORATED
    assert FRONTIER not in (hyp.classify(),)

    # 3. Plan retests
    plan = plan_retests([hyp], budget=10, dead_floor=5)
    assert plan.order == ("hs_model_01",)
    assert plan.cost == 2

    # 4. Settle retest outcome (refuted -> branch reopens)
    settled = settle(plan, {"hs_model_01": True})
    assert settled["hs_model_01"] == REFUTED

    # Survived test (confirming defect)
    settled_dead = settle(plan, {"hs_model_01": False})
    assert settled_dead["hs_model_01"] == SURVIVED_TEST


@pytest.mark.parametrize("f_class", sorted(CANONICAL_FAILURE_CLASSES))
def test_all_24_canonical_classes_accepted(ledger_file: Path, f_class: str):
    res = record_failure(
        ledger_file,
        failure_id=f"fail_{f_class}@run_1",
        workflow="WF14",
        run="run_1",
        failure_class=f_class,
        ddc_trace="CRM",
        evidence_sha256=SAMPLE_SHA256,
    )
    assert res.get("status") == "PASS", f"Failure class {f_class} was refused: {res}"
