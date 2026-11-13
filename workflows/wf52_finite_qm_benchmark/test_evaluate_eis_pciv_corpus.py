# ruff: noqa: S101
"""Unit and corpus-integrity tests for `dag/benchmark/evaluate_eis_pciv_corpus.py`.

Verifies:
1. Strict Stage A blind firewall isolation (zero access to `grades.json`,
   `results_summary.json`, `evaluator_rubric.json`, or non-null `accuracy_score`).
2. Complete denominator accounting across all 24 historical runs (`N = 24`),
   including refusals, validation failures, and admission failures.
3. EIS public-invariant screening, `charpoly_pilot_20261110` raw candidate call
   diagnostics, Thymus-screened `NormalizedMatcher` tolerance, conflict-graph MIS
   support, and PCIV 4-axis blind Pareto + transitive lineage taint.
4. Stage B read-only post-hoc validation, split-fibre semantic survivor detection
   (`DER-189` / `DER-110`), deterministic JSON serialization, strict
   `final_answer_certified is False`, and Claim Hygiene compliance.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _sys_path in (ROOT, HERE, ROOT / "ops"):
    if str(_sys_path) not in sys.path:
        sys.path.insert(0, str(_sys_path))

import evaluate_eis_pciv_corpus as evaluator  # noqa: E402

from eis.use_cases.two_signal_regulation import ThymusSelfPanelBuilder  # noqa: E402


def _write_pinned_run_receipt(run_dir: Path, payload: dict[str, Any]) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_bytes = (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    run_path = run_dir / "run.json"
    pin_path = run_dir / "run.sha256"
    run_path.write_bytes(raw_bytes)
    pin_path.write_text(f"{digest}\n", encoding="ascii")
    return run_path


def _make_synthetic_run_payload(
    *,
    run_id: str = "qm-synth-20261110:direct:000",
    plan: str = "direct",
    status: str = "completed",
    answer_text: str | None = "1. Spectrum\n2. Transition\n3. Reduced\n4. Thermal\n5. Consistency",
    accuracy_score: Any = None,
    spent_microusd: int = 500,
    input_tokens: int | None = 100,
    output_tokens: int | None = 200,
    finish_reason: str = "stop",
) -> dict[str, Any]:
    seed_sha = "a" * 64
    answer_sha = (
        hashlib.sha256(answer_text.encode("utf-8")).hexdigest()
        if answer_text is not None
        else None
    )
    return {
        "accuracy_score": accuracy_score,
        "answer_sha256": answer_sha,
        "answer_text": answer_text,
        "budget": {
            "available_microusd": 100000 - spent_microusd,
            "blocked": False,
            "cap_microusd": 100000,
            "held_microusd": 0,
            "run_id": run_id,
            "seed_sha256": seed_sha,
            "spent_microusd": spent_microusd,
        },
        "calls": [
            {
                "call_id": f"{run_id}:call:0",
                "finish_reason": finish_reason,
                "response_text": answer_text or "",
                "stage_id": "solve",
            }
        ],
        "host_checks": {"artifact_errors": {}, "claims": [], "stage_checks": []},
        "input_tokens": input_tokens,
        "offline": False,
        "output_tokens": output_tokens,
        "plan": plan,
        "provider": "openrouter:openai/gpt-4o-mini",
        "reasoning_tokens": 0,
        "run_id": run_id,
        "schema_version": "1.0",
        "seed_sha256": seed_sha,
        "status": status,
        "sum_provider_duration_seconds": 5.0,
        "wall_time_seconds": 5.25,
    }


def _collect_key_values(node: Any, target_key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k == target_key:
                found.append(v)
            found.extend(_collect_key_values(v, target_key))
    elif isinstance(node, list):
        for item in node:
            found.extend(_collect_key_values(item, target_key))
    return found


def test_stage_a_blind_firewall_never_opens_grades_rubric_or_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened_paths: list[str] = []
    real_open = builtins.open
    real_read_text = Path.read_text
    real_read_bytes = Path.read_bytes

    def _record_path(file_arg: Any) -> None:
        if isinstance(file_arg, (str, Path)):
            opened_paths.append(Path(file_arg).as_posix().lower())

    def _spy_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        _record_path(file)
        return real_open(file, *args, **kwargs)

    def _spy_read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        _record_path(self)
        return real_read_text(self, *args, **kwargs)

    def _spy_read_bytes(self: Path) -> bytes:
        _record_path(self)
        return real_read_bytes(self)

    monkeypatch.setattr(builtins, "open", _spy_open)
    monkeypatch.setattr(Path, "read_text", _spy_read_text)
    monkeypatch.setattr(Path, "read_bytes", _spy_read_bytes)

    stage_a = evaluator.run_blind_stage_a()

    forbidden_substrings = (
        "grades.json",
        "graded_results.json",
        "results_summary.json",
        "evaluator_rubric.json",
        "criterion_evidence.json",
        "evaluation_validation.json",
        "rubric",
    )
    bad_hits = [
        accessed
        for accessed in opened_paths
        if any(bad in accessed for bad in forbidden_substrings)
    ]
    assert bad_hits == []

    audit = stage_a["firewall_audit"]
    assert audit["grades_files_accessed"] == 0
    assert audit["results_summary_accessed"] is False
    assert audit["evaluator_rubric_accessed"] is False
    assert audit["all_run_accuracy_scores_null"] is True
    assert all(r["accuracy_score_in_run_json"] is None for r in stage_a["runs"])


@pytest.mark.parametrize(
    "bad_filename",
    [
        "grades.json",
        "results_summary.json",
        "evaluator_rubric.json",
        "graded_results.json",
        "criterion_evidence.json",
    ],
)
def test_stage_a_refuses_forbidden_file_paths(tmp_path: Path, bad_filename: str) -> None:
    forbidden = tmp_path / bad_filename
    forbidden.write_text("{}", encoding="utf-8")
    with pytest.raises(evaluator.BlindFirewallViolationError):
        evaluator.run_blind_stage_a([forbidden])


def test_stage_a_refuses_contaminated_run_json_with_score_or_grades(tmp_path: Path) -> None:
    scored_payload = _make_synthetic_run_payload(accuracy_score=88)
    scored_path = _write_pinned_run_receipt(tmp_path / "exp" / "runs" / "00_scored", scored_payload)
    with pytest.raises(evaluator.BlindFirewallViolationError, match="accuracy_score"):
        evaluator.run_blind_stage_a([scored_path])

    graded_payload = _make_synthetic_run_payload(accuracy_score=None)
    graded_payload["grades"] = {"points": 88}
    graded_path = _write_pinned_run_receipt(tmp_path / "exp" / "runs" / "01_graded", graded_payload)
    with pytest.raises(evaluator.BlindFirewallViolationError, match="forbidden key"):
        evaluator.run_blind_stage_a([graded_path])


def test_stage_b_refuses_private_rubric_path(tmp_path: Path) -> None:
    synth_path = _write_pinned_run_receipt(
        tmp_path / "exp" / "runs" / "00_clean",
        _make_synthetic_run_payload(),
    )
    stage_a = evaluator.run_blind_stage_a([synth_path])
    with pytest.raises(evaluator.BlindFirewallViolationError, match="STAGE_B_FIREWALL_REFUSAL"):
        evaluator.compare_post_hoc_stage_b(stage_a, tmp_path / "evaluator_rubric.json")


def test_all_24_historical_runs_accounted_in_denominators_and_resources() -> None:
    paths = evaluator.discover_historical_run_json_paths()
    assert len(paths) == 24

    stage_a = evaluator.run_blind_stage_a(paths)
    acct = stage_a["delivery_and_resource_accounting"]

    assert acct["assigned_run_count"] == 24
    assert len(stage_a["runs"]) == 24
    assert sum(acct["status_counts"].values()) == 24
    assert acct["status_counts"] == {
        "admission_failure": 1,
        "artifact_validation_failure": 4,
        "certificate_refused": 1,
        "completed": 15,
        "representation_refused": 3,
    }
    assert acct["delivered_answer_count"] == 19
    assert acct["delivered_answer_rate_exact"] == "19/24"
    assert acct["refused_or_admission_failed_count"] == 5
    assert acct["refused_or_admission_failed_rate_exact"] == "5/24"
    assert acct["completed_status_rate_exact"] == "5/8"
    assert acct["complete_5_section_non_truncated_count"] == 9
    assert acct["complete_5_section_non_truncated_rate_exact"] == "3/8"
    assert acct["truncated_run_count"] == 10
    assert acct["truncated_run_rate_exact"] == "5/12"

    assert acct["spent_microusd_total"] == 55614
    assert acct["spent_usd_total"] == "0.055614"
    assert acct["held_microusd_total"] == 0
    assert acct["runs_with_complete_token_cost_accounting"] == 23
    assert acct["runs_missing_token_usage_ids"] == ["qm-model-20261110:direct:000"]
    assert acct["sum_input_tokens_known"] == 52609
    assert acct["sum_output_tokens_known"] == 108914
    assert acct["sum_total_tokens_known"] == 161523

    undelivered = [r for r in stage_a["runs"] if not r["answer_delivered"]]
    assert len(undelivered) == 5
    assert all(r["blind_public_antibody_pass_count"] == 0 for r in undelivered)


def test_charpoly_raw_calls_and_thymus_normalizer() -> None:
    stage_a = evaluator.run_blind_stage_a()
    charpoly = stage_a["charpoly_pilot_raw_candidate_analysis"]
    assert charpoly["charpoly_checked_run_observed"] is True
    calls = {c["call_id"]: c for c in charpoly["frozen_call_diagnostics"]}

    call0 = calls["qm-charpoly-20261110:qm_charpoly_checked_v1:000:call:0"]
    assert call0["call_file_verified_against_run_json"] is True
    assert call0["parsed_as_json"] is True
    assert call0["has_duplicate_powers"] is False
    assert call0["has_unreduced_slash_one_rationals"] is True
    assert call0["sidecar_feedback"]["code"] == "RATIONAL_NONCANONICAL"
    assert call0["charpoly_wire_refusal_code"] == "NONMONIC_LEADING_COEFFICIENT"

    call1 = calls["qm-charpoly-20261110:qm_charpoly_checked_v1:000:call:1"]
    assert call1["call_file_verified_against_run_json"] is True
    assert call1["finish_reason"] == "length"
    assert call1["parsed_as_json"] is False
    assert call1["sidecar_feedback"]["code"] == "MALFORMED_JSON"
    assert call1["charpoly_wire_refusal_code"] == "MALFORMED_JSON"

    thymus_chk = charpoly["thymus_and_normalized_matcher_check"]
    assert thymus_chk["naive_regex_admitted_by_thymus"] is False
    assert thymus_chk["naive_regex_autoimmune_violations"] == 3
    assert thymus_chk["normalized_matcher_admitted_by_thymus"] is True
    assert thymus_chk["normalized_matcher_autoimmune_violations"] == 0
    assert thymus_chk["structural_defect_rule_admitted_by_thymus"] is True
    assert thymus_chk["monic_slash_one_probe_regulation_decision"] == "TOLERATED"
    assert thymus_chk["bad_degree_probe_regulation_decision"] == "QUARANTINED"


def test_mis_support_and_blind_pareto_lineage() -> None:
    stage_a = evaluator.run_blind_stage_a()
    mis = stage_a["eis_conflict_graph_mis_support"]
    assert mis["missing_thermal_or_consistency_ab06_ab10"]["mis_support_count"] == 4
    assert mis["missing_thermal_or_consistency_ab06_ab10"]["new_custody"] == "Provisional"
    assert mis["output_truncation"]["mis_support_count"] == 3
    assert mis["output_truncation"]["new_custody"] == "Provisional"
    assert mis["intermediate_encoding_or_gate_refusal"]["raw_occurrence_count"] == 4
    assert mis["intermediate_encoding_or_gate_refusal"]["mis_support_count"] == 2
    assert mis["intermediate_encoding_or_gate_refusal"]["new_custody"] == "Candidate"
    assert mis["rational_panel_schema_failure"]["raw_occurrence_count"] == 4
    assert mis["rational_panel_schema_failure"]["mis_support_count"] == 1
    assert mis["rational_panel_schema_failure"]["new_custody"] == "Candidate"

    pciv = stage_a["pciv_pareto_and_lineage"]
    assert pciv["eligible_run_count"] == 23
    assert pciv["blind_4d_pareto_front_run_ids"] == [
        "qm-hamiltonian-20261110:hamiltonian_host_matrix_v1:001",
        "qm-pilot-20261110:rational_fixed_panel_v1:000",
    ]
    assert "rational_fixed_panel_v2" in pciv["branch_transitive_tainted_plans"]
    assert "hamiltonian_host_matrix_v1" in pciv["branch_transitive_tainted_plans"]
    assert "qm_charpoly_ungated_v1" in pciv["branch_transitive_tainted_plans"]
    assert pciv["comparative_claim_holdout_refusal_code"] == "COMPARATIVE_CLAIM_HOLDOUT_REQUIRED"


def test_stage_b_post_hoc_validation_on_historical_corpus() -> None:
    report = evaluator.evaluate_historical_corpus()
    stage_a_before = json.dumps(report["stage_a_blind"], sort_keys=True)
    stage_b = evaluator.compare_post_hoc_stage_b(report["stage_a_blind"])
    assert json.dumps(report["stage_a_blind"], sort_keys=True) == stage_a_before

    strongest = stage_b["strongest_empirical_runs_audit"]
    rep83 = strongest["qm-model-repaired-20261110:direct:000"]
    assert rep83["post_hoc_score_out_of_100"] == 83
    assert rep83["retained_in_stage_a_top_public_obligation_tier"] is True
    assert rep83["retained_in_complete_5_section_non_truncated_cohort"] is True
    assert rep83["retained_on_stage_a_4d_pareto_front"] is False

    crit88 = strongest["qm-deepseek-critique-20261110:self_critique:000"]
    assert crit88["post_hoc_score_out_of_100"] == 88
    assert crit88["retained_in_stage_a_top_public_obligation_tier"] is False
    assert crit88["retained_in_complete_5_section_non_truncated_cohort"] is True
    assert crit88["retained_on_stage_a_4d_pareto_front"] is False

    cohorts = stage_b["blind_cohort_separation"]
    assert cohorts["truncated_incomplete_or_refused_union"]["count"] == 15
    assert cohorts["truncated_incomplete_or_refused_union"]["runs_scoring_ge_60_count"] == 0
    assert cohorts["complete_5_section_non_truncated"]["count"] == 9
    assert cohorts["complete_5_section_non_truncated"]["runs_scoring_ge_60_count"] == 3

    split_f = stage_b["split_fibre_blind_semantic_survivors"]
    assert split_f["passed_10_of_10_and_score_lt_100_count"] == 0
    assert split_f["passed_10_of_10_and_score_lt_100_run_ids"] == []
    assert split_f["top_observed_blind_tier_survivors_lt_100_count"] == 3


def test_stage_b_detects_synthetic_10_of_10_split_fibre_survivor(tmp_path: Path) -> None:
    clean_10_of_10_prose = ThymusSelfPanelBuilder.build_self_panel()[4]
    decoy_run_id = "qm-synth-split-fibre:direct:000"
    decoy_path = _write_pinned_run_receipt(
        tmp_path / "synth_exp" / "runs" / "00_decoy",
        _make_synthetic_run_payload(run_id=decoy_run_id, answer_text=clean_10_of_10_prose),
    )
    synth_summary_path = tmp_path / "results_summary.json"
    synth_summary_path.write_text(
        json.dumps(
            {
                "pareto_front_run_ids": [decoy_run_id],
                "raw_runs": [{"run_id": decoy_run_id, "score": 12}],
            }
        ),
        encoding="utf-8",
    )
    synth_a = evaluator.run_blind_stage_a([decoy_path])
    assert synth_a["eis_public_antibody_summary"]["passed_10_of_10_count"] == 1
    assert synth_a["final_answer_certified"] is False

    synth_b = evaluator.compare_post_hoc_stage_b(synth_a, synth_summary_path)
    synth_sf = synth_b["split_fibre_blind_semantic_survivors"]
    assert synth_sf["passed_10_of_10_and_score_lt_100_count"] == 1
    assert synth_sf["passed_10_of_10_and_score_lt_100_run_ids"] == [decoy_run_id]
    assert synth_sf["final_answer_certified"] is False


def test_deterministic_json_output_final_answer_uncertified_and_claim_hygiene() -> None:
    report_1 = evaluator.evaluate_historical_corpus()
    report_2 = evaluator.evaluate_historical_corpus()
    serialized_1 = evaluator.serialize_evaluation_report(report_1)
    serialized_2 = evaluator.serialize_evaluation_report(report_2)

    assert serialized_1 == serialized_2
    on_disk = evaluator.DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8")
    assert serialized_1 == on_disk

    certified_flags = _collect_key_values(report_1, "final_answer_certified")
    assert len(certified_flags) >= 28
    assert all(type(flag) is bool and flag is False for flag in certified_flags)

    ch = report_1["claim_hygiene"]
    assert isinstance(ch["supports"], list) and len(ch["supports"]) >= 1
    assert isinstance(ch["does_not_support"], list) and len(ch["does_not_support"]) >= 1
    assert isinstance(ch["narrowest_defensible_claim"], str) and ch["narrowest_defensible_claim"]
    assert isinstance(ch["next_test_needed"], str) and ch["next_test_needed"]

    # Check absence of disallowed unhedged wording in module source, test source, and JSON.
    disallowed_patterns = (
        r"\bpr[o]ves\b",
        r"\bmathematically\s+verif(?:ies|ied)\b",
        r"\bfundamenta[l]ly\b",
        r"\bfundamenta[l]\s+flaw\b",
        r"\btrue\s+inte[l]ligence\b",
        r"\bimpossib[l]e\b",
        r"\buniversa[l]\b",
        r"\bflaw[l]ess\b",
        r"\bperfect[l]y\b",
        r"\bclear[l]y\b",
        r"\bobvious[l]y\b",
        r"\bsimp[l]y\b",
        r"\bmere[l]y\b",
        r"\bweaponize[d]\b",
        r"\bguarantee[s](?!\s+under\s+the\s+declared\s+assumptions)\b",
    )
    evaluator_source = (HERE / "evaluate_eis_pciv_corpus.py").read_text(encoding="utf-8")
    test_source = (HERE / "test_evaluate_eis_pciv_corpus.py").read_text(encoding="utf-8")
    for target_name, text in (
        ("evaluate_eis_pciv_corpus.py", evaluator_source),
        ("test_evaluate_eis_pciv_corpus.py", test_source),
        ("eis_pciv_historical_evaluation.json", on_disk),
    ):
        violations = [
            m.group(0)
            for pat in disallowed_patterns
            if (m := re.search(pat, text, flags=re.IGNORECASE)) is not None
        ]
        assert violations == [], f"Claim hygiene violations in {target_name}: {violations}"
