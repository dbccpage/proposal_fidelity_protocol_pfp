"""Release-surface checks for the v1.0rc funnel, seams, and zero-spend replay.

AuthorityEffect: None.
"""

from __future__ import annotations

import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_ddc_parser_imports_canon_letters_and_refuses_unknown_colour() -> None:
    from operads.canon import DDC_LETTER
    from operads.skill_operad.ddc_operad_parser import DDC_CANONICAL_LETTERS, require_operad_colour

    assert DDC_CANONICAL_LETTERS == DDC_LETTER
    assert require_operad_colour("State").value == "State"
    with pytest.raises(ValueError, match="OPERAD_COLOUR_REFUSED"):
        require_operad_colour("NotAColour")


def test_pciv_rejects_a_mutation_with_no_gain_and_no_cost_drop() -> None:
    from pfp_core.release_surface_v1rc import pciv_strict_pareto_admits

    assert pciv_strict_pareto_admits(Fraction(1, 2), Fraction(1, 2), 10, 10, 2, 2) is False
    assert pciv_strict_pareto_admits(Fraction(1, 2), Fraction(2, 3), 10, 12, 2, 2) is True
    assert pciv_strict_pareto_admits(Fraction(1, 2), Fraction(1, 2), 10, 8, 2, 2) is True


def test_clean_self_panel_has_zero_false_refusals() -> None:
    from pfp_core.release_surface_v1rc import clean_panel_false_refusals

    assert clean_panel_false_refusals() == 0


def test_holdout_overlap_is_refused() -> None:
    from pfp_core.release_surface_v1rc import assert_holdout_disjoint

    with pytest.raises(ValueError, match="HOLDOUT_CONTAMINATION_REFUSAL"):
        assert_holdout_disjoint(("C011",), ("C011",), ("train-prompt-c011",), ("train-prompt-c011",))


def test_tier1_batch_quotients_and_rejects_at_zero_usd() -> None:
    from pfp_core.release_surface_v1rc import run_tier1_release_batch

    batch = run_tier1_release_batch(target_count=1000)
    assert batch["total_generated"] >= 1000
    assert batch["lean4_candidates"] >= 1
    assert 0 < batch["unique_quotient_classes"] < batch["total_generated"]
    assert batch["usd_reject_total"] == "0"
    assert set(batch["reject_reasons"]) == {"port_mismatch", "budget_exceeded", "self_intolerant"}
    assert "HOLDOUT_CONTAMINATION_REFUSAL" in batch["holdout_refusal"]
    assert batch["provider_calls"] == 0
    again = run_tier1_release_batch(target_count=1000)
    assert again["digest"] == batch["digest"]


def test_six_arm_receipt_keeps_the_null_and_uses_exact_fractions() -> None:
    from pfp_core.release_surface_v1rc import run_six_arm_offline_campaign

    report = run_six_arm_offline_campaign()
    paired = report["comparisons"]["arm6_minus_arm3"]
    assert paired["accuracy_delta"] == "0"
    Fraction(paired["raw_mcnemar_p"])
    Fraction(paired["holm_adjusted_p"])
    assert any("is 0" in item for item in report["null_findings"])
    assert report["false_refusal_rate"] == "0"
    assert report["provider_calls"] == 0
    for key in ("supports", "does_not_support", "narrowest_claim", "negative_controls"):
        assert report["claim_hygiene"][key]
    second = run_six_arm_offline_campaign()
    assert second["digest"] == report["digest"]


def test_showcase_replay_performs_no_provider_call() -> None:
    from pfp_core.release_surface_v1rc import replay_guest_showcase

    replay = replay_guest_showcase()
    assert replay["mode"] == "zero-spend-replay"
    assert replay["provider_calls"] == 0
    assert replay["false_refusal_rate"] == "0"


def test_showcase_markup_is_static_and_keeps_the_brand_out() -> None:
    html = (REPO / "pfp_lab" / "web" / "static" / "index.html").read_text(encoding="utf-8")
    script = (REPO / "pfp_lab" / "web" / "static" / "app.js").read_text(encoding="utf-8")
    for tab in ("lab", "funnel", "strand"):
        assert f'data-tab="{tab}"' in html
    for move in ("ASSERT", "CUT", "VERIFY", "RETRACT"):
        assert move in html
    assert "zero-spend" in html
    assert 'id="invite"' in html
    assert "require(" not in script
    assert "module.exports" not in script
    blob = (html + script).lower()
    assert "om" + "ega" not in blob


_PINNED_RED_FENCE = """\
operads/skill_operad/skill_compiler/tests/test_skill_listing.py::test_the_live_tree_passes
operads/skill_operad/skill_compiler/tests/test_skill_listing.py::test_every_live_ext_stub_is_hidden_from_the_model
operads/skill_operad/tests/test_dispatch_resolution.py::DispatchResolutionTests::test_declared_license_with_reconciled_colours_resolves
operads/skill_operad/tests/test_domain_clean_arch.py::UseCaseIntegrationTests::test_validate_operad_use_case
operads/skill_operad/tests/test_honesty.py::ResidualHonestyLive::test_live_repo_classifies_legacy_rows_without_upgrading_them
operads/skill_operad/tests/test_honesty.py::HighTrafficSpoe::test_meta_chain_typed
operads/skill_operad/tests/test_span_operands_and_composition_judging.py::test_composition_gate1_colour_type_soundness
operads/skill_operad/tests/test_span_operands_and_composition_judging.py::test_composition_gate2_arity_and_slot_bounds
operads/skill_operad/tests/test_span_operands_and_composition_judging.py::test_composition_gate5_agent_capability_slice_licensing
operads/tests/architecture/test_clean_architecture_ast_boundaries.py::CleanArchitectureBoundaryTests::test_cross_context_imports_are_caught_in_source
operads/tests/ddc_execution/test_operad_composition_fail_open.py::test_the_validator_passes_on_the_real_registry
operads/tests/ddc_execution/test_operad_composition_fail_open.py::test_a_refused_composition_fails_the_gate
operads/tests/ddc_execution/test_operad_composition_fail_open.py::test_an_unmodified_copy_still_passes
operads/tests/integration/test_benchmark_burst_load.py::TestBenchmarkBurstLoad::test_sustained_100_plus_request_burst_load
operads/tests/integration/test_outbox_transaction_atomicity.py::TestOutboxTransactionAtomicity::test_handler_refuses_an_unreadable_skill_instead_of_skipping_it
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_actual_native_persistence_is_fully_measured_and_hash_bound
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_native_persisted_missing_terminal_binding_is_held_not_satisfied[phi_1]
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_native_persisted_missing_terminal_binding_is_held_not_satisfied[gamma_2]
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_native_persisted_missing_terminal_binding_is_held_not_satisfied[lean4_proof_hash]
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_native_persisted_missing_terminal_binding_is_held_not_satisfied[terminal_verdict]
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_native_non_pass_verdict_remains_not_applicable
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_cross_run_receipt_transplant_cannot_bind_another_candidate
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_native_single_ddc_and_uts_are_required_and_bound[missing]
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_native_single_ddc_and_uts_are_required_and_bound[changed_bytes]
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_native_single_ddc_and_uts_are_required_and_bound[changed_uts_bytes]
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_native_duplicate_terminal_token_is_malformed_not_satisfied
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_observed_failure_feedback_stays_candidate_and_correlates_to_source_run
operads/tests/integration/test_structurebench_production_bundle_contract.py::test_historical_ddc_copy_with_matching_changed_digest_still_refuses
operads/tests/unit/test_governance_digest.py::GovernanceDigestTests::test_checked_in_repairs_match_a_stored_fingerprint
operads/tests/unit/test_governance_digest.py::GovernanceDigestTests::test_missing_repair_target_fails_closed_as_anchor_changed
operads/tests/unit/test_governance_digest_refactor_branches.py::GovernanceDigestRefactorBranchTests::test_owner_coverage_separates_table_gap_registered_repair_and_unknown_language
eis/tests/unit/test_immune_system.py::TestEpistemicImmuneSystem::test_antimorphism_immune_bench_and_phagocytic_regenerator
eis/tests/unit/test_pharmacy_candidate_by_default.py::test_each_retired_id_is_reproduced_by_its_recorded_defect
eis/tests/unit/test_pharmacy_candidate_by_default.py::test_the_three_phantoms_cannot_be_farmed_again
eis/tests/unit/test_thymus_evaluation_error.py::test_invalid_pattern_surfaces_evaluation_error
"""


def _pytest_commands(workflow_text: str) -> list[str]:
    return [line for line in workflow_text.splitlines() if "-m pytest" in line]


def test_v1rc_gates_pytest_runs_operads_eis_and_pciv() -> None:
    text = (REPO / ".github" / "workflows" / "pfp_v1rc_gates.yml").read_text(encoding="utf-8")
    trees = {"operads", "eis", "pciv"}
    assert any(trees <= set(command.split()) for command in _pytest_commands(text))
    assert "The rest of eis/" not in text
    assert "historical receipt scripts" not in text


def test_v1rc_gates_deselect_pinned_red_operads_and_eis_nodes() -> None:
    text = (REPO / ".github" / "workflows" / "pfp_v1rc_gates.yml").read_text(encoding="utf-8")
    fence = REPO / ".github" / "pfp_v1rc_pinned_red_nodes.txt"
    assert ".github/pfp_v1rc_pinned_red_nodes.txt" in text
    assert "--deselect" in text
    listed = [
        line.strip()
        for line in fence.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    expected = [line for line in _PINNED_RED_FENCE.splitlines() if line]
    assert listed == expected
    assert len(listed) == 35
    assert all(node.startswith(("operads/", "eis/")) for node in listed)


def test_editable_install_imports_pfp_core_without_a_path_hack() -> None:
    if sys.platform == "win32":
        python = REPO / ".venv" / "Scripts" / "python.exe"
    else:
        python = REPO / ".venv" / "bin" / "python"
    if not python.is_file():
        pytest.fail(f"venv python missing at {python}")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [str(python), "-B", "-X", "utf8", "-c", "import pfp_core, pfp_core.release_surface_v1rc"],
        cwd=Path.home(),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
