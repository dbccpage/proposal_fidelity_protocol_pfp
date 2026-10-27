"""Closed-Loop "Fugu" Autophagous Cemetery & Antibody Blocking Integration Test.

Implements the closed-loop autophagous cycle across Adversary, the city, and Prompt Civilization:
1. Generation g=1: A candidate with a deliberate fatal defect (Clean Architecture layer violation)
   is proposed, critiqued by Defect Hunter with DISPOSITION="KILL", and buried in the cemetery
   as a CemeteryHeadstoneV1. Act VI records the failure, and PharmacySeeder farms the defect
   into an active candidate antibody in the pharmacy catalog.
2. Generation g=2: An identical defective candidate is presented to a fresh runtime.
   At the Act IV Primal Dual Sandbox gate, the candidate payload SHA-256 matches the buried
   cemetery headstone from g=1. Act IV actively blocks and refuses the candidate with
   code "REGRESSION_AGAINST_CEMETERY_REFUSED" before critique turns and token spend occur.
3. Generation g=3: A mutated variant carrying the same forbidden defect pattern is presented.
   Act IV Sandbox gate detects the armed pharmacy antibody and blocks with
   code "REGRESSION_AGAINST_ANTIBODY_REFUSED".
4. Generation g=4: A clean candidate without defects passes Act IV Sandbox gate.
5. Generation g=5: Ablation testing with `no_cemetery_defense=True` confirms that without the
   cemetery fence, the candidate bypasses Act IV Sandbox, establishing causal isolation.

Governance & Rules:
- AuthorityEffect: Strictly "None".
- Zero-Float Law: Exact rational arithmetic (fractions.Fraction).
- OpenRouter Budget Protection: 100% hermetic local execution (0 live API calls, $0.00 spend).
- Claim Discipline: Defensible claims supported by verified execution receipts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pfp.domain.value_objects.seat_turn import SeatTurnReplyV1
from adversary.infrastructure.native import DefaultNativeOperationPort
from adversary.profile.profile_loader import load_adversary_council_profile
from adversary.runtime import build_adversary_runtime
from adversary.stage.domain import (
    AUTHORITY_EFFECT_NONE,
    CemeteryHeadstoneV1,
    WorkPacketV1,
)
from adversary.stage.domain.immune.seeder import PharmacySeeder
from adversary.stage.infrastructure.default_adapters import (
    FileCemeteryAdapter,
    FixtureAgentTurnAdapter,
)
from adversary.stage.infrastructure.pharmacy_writer import (
    filesystem_catalog_text,
    filesystem_text_writer,
)
from adversary.use_cases.bout_service import execute_7act_adversary_bout

DEFECTIVE_CODE = (
    "class OrderDomainService:\n"
    "    from infrastructure import RawSocketDatabase  # DIRECT_LAYER_VIOLATION\n"
    "    def process(self):\n"
    "        return RawSocketDatabase().query()\n"
)
DEFECTIVE_BYTES = DEFECTIVE_CODE.encode("utf-8")
DEFECTIVE_SHA256 = "sha256:" + hashlib.sha256(DEFECTIVE_BYTES).hexdigest()

CLEAN_CODE = (
    "class OrderDomainService:\n"
    "    def __init__(self, repository_port):\n"
    "        self._repo = repository_port\n"
    "    def process(self):\n"
    "        return self._repo.find_all()\n"
)
CLEAN_BYTES = CLEAN_CODE.encode("utf-8")


def _make_packet(task_key: str, objective: str) -> WorkPacketV1:
    return WorkPacketV1(
        task_key=task_key,
        scene_id="act1_perception",
        objective=objective,
        input_artifact_refs=(),
        acceptance_criteria=("Zero architectural regressions",),
        budget_units=50,
        evaluator_epoch_id="sha256:" + hashlib.sha256(task_key.encode("utf-8")).hexdigest(),
    )


def test_fugu_closed_loop_cemetery_and_antibody_blocking(tmp_path: Path) -> None:
    """Full closed-loop test: g=1 kills & buries defect, g=2 blocks identical candidate before token spend."""
    out_dir = tmp_path / "_intelligence" / "_adversary"
    _, _, profile, _, _ = load_adversary_council_profile()

    # =========================================================================
    # GENERATION g=1: Deliberate Defect Injected, Killed, and Buried
    # =========================================================================
    rt_g1 = build_adversary_runtime(output_dir=tmp_path / "_intelligence", fixture_mode=False)

    canned_g1 = {
        # Gauge Breaker proposes the defective code in Act III
        ("act2_panel_debate", "seat_gauge_breaker"): SeatTurnReplyV1(
            reply_text=DEFECTIVE_CODE,
            machine_fields={"AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=DEFECTIVE_BYTES,
        ),
        # Primal Dual uninhibited in g=1 (cemetery is initially empty)
        ("act4_sandbox", "seat_primal_dual"): SeatTurnReplyV1(
            reply_text="Primal Dual initial audit: candidate syntax valid.",
            machine_fields={"DISPOSITION": "PASS", "AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=b"primal_dual_initial_pass",
        ),
        # Defect Hunter identifies fatal architecture defect and kills candidate in Act V
        ("act2_panel_debate", "seat_defect_hunter"): SeatTurnReplyV1(
            reply_text=(
                "Fatal clean architecture defect: domain layer imports infrastructure directly.\n"
                "```critique\n"
                '{"blocking": true, "challenge_kind": "FatalDefect", "counterexample": "OrderDomainService directly imports RawSocketDatabase"}\n'
                "```"
            ),
            machine_fields={"DISPOSITION": "KILL", "AUTHORITY_EFFECT": "None"},
            residual_colour="Red",
            authority_effect="None",
            raw_bytes=b"defect_hunter_kill_g1",
        ),
    }

    turn_adapter_g1 = FixtureAgentTurnAdapter(canned_replies=canned_g1)
    object.__setattr__(rt_g1, "seat_port", turn_adapter_g1)

    packet_g1 = _make_packet("fugu_g1_run", "Refactor OrderDomainService with pure domain isolation")
    res_g1 = execute_7act_adversary_bout(profile, rt_g1, packet_g1, output_dir=out_dir, native_support=DefaultNativeOperationPort())

    # Bout completes with zero surviving candidates (candidate was killed by Defect Hunter)
    assert res_g1.is_ok, f"Expected bout to complete without crash: {res_g1.unwrap_err()}"
    receipt_g1 = res_g1.unwrap()
    assert receipt_g1.authority_effect == AUTHORITY_EFFECT_NONE

    # Verify headstone was recorded in cemetery
    cemetery_dir = rt_g1.emitters.cemetery.cemetery_dir
    assert cemetery_dir.exists(), "Cemetery directory must exist after candidate kill"
    headstones = list(cemetery_dir.glob("*.headstone.json"))
    assert len(headstones) >= 1, "At least one headstone must be buried in cemetery"

    # Verify headstone content matches the killed defective payload
    headstone_data = json.loads(headstones[0].read_text(encoding="utf-8"))
    hs_obj = CemeteryHeadstoneV1.from_dict(headstone_data)
    assert hs_obj.candidate_payload_sha256 == DEFECTIVE_SHA256
    assert "KILLED_BY_DEFECT_HUNTER" in hs_obj.cause_of_death

    # Farm defect into armed candidate antibody via PharmacySeeder
    seeder = PharmacySeeder(repo_root=tmp_path, text_writer=filesystem_text_writer, text_source=filesystem_catalog_text)
    farmed_antibodies = seeder.farm_antibodies_from_defects(
        ["clean_arch_violation: OrderDomainService directly imports RawSocketDatabase"],
        run_id="fugu_g1_run",
        task_id="task_fugu_g1",
    )
    assert len(farmed_antibodies) == 1
    assert farmed_antibodies[0].constraint_type == "ProjectOut"

    catalog_file = seeder.catalog_repo.catalog_file
    assert catalog_file.exists(), "Pharmacy catalog must be persisted on disk"
    catalog_data = json.loads(catalog_file.read_text(encoding="utf-8"))
    assert len(catalog_data.get("antibodies", {})) >= 1

    # =========================================================================
    # GENERATION g=2: Identical Defect Blocked at Act IV Primal Dual Sandbox Gate
    # =========================================================================
    # Fresh runtime instantiated — cemetery contains g=1 headstone
    rt_g2 = build_adversary_runtime(output_dir=tmp_path / "_intelligence", fixture_mode=False)

    canned_g2 = {
        # Gauge Breaker proposes the IDENTICAL defective payload in generation g=2
        ("act2_panel_debate", "seat_gauge_breaker"): SeatTurnReplyV1(
            reply_text=DEFECTIVE_CODE,
            machine_fields={"AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=DEFECTIVE_BYTES,
        ),
        # If Primal Dual or Defect Hunter are called, they would log, but Act IV gate must block before them
        ("act4_sandbox", "seat_primal_dual"): SeatTurnReplyV1(
            reply_text="Primal Dual should not be reached for regression.",
            machine_fields={"DISPOSITION": "PASS", "AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=b"primal_dual_should_not_run",
        ),
        ("act2_panel_debate", "seat_defect_hunter"): SeatTurnReplyV1(
            reply_text="Defect Hunter should not be reached for regression.",
            machine_fields={"DISPOSITION": "PASS", "AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=b"defect_hunter_should_not_run",
        ),
    }

    turn_adapter_g2 = FixtureAgentTurnAdapter(canned_replies=canned_g2)
    object.__setattr__(rt_g2, "seat_port", turn_adapter_g2)

    packet_g2 = _make_packet("fugu_g2_run", "Refactor OrderDomainService with pure domain isolation")
    res_g2 = execute_7act_adversary_bout(profile, rt_g2, packet_g2, output_dir=out_dir, native_support=DefaultNativeOperationPort())

    # In g=2, the bout must be REFUSED at the Act IV Sandbox gate
    assert res_g2.is_err, "Expected bout to be refused due to cemetery regression"
    refusal_g2 = res_g2.unwrap_err()

    # Verify refusal code and message
    assert refusal_g2.code == "REGRESSION_AGAINST_CEMETERY_REFUSED"
    assert "matches headstone" in refusal_g2.message
    assert hs_obj.headstone_id in refusal_g2.message

    # Verify Defect Hunter critique was NEVER invoked in g=2 (zero critique token spend)
    defect_hunter_calls = [
        req for req in turn_adapter_g2.invocation_log
        if req.seat_id == "seat_defect_hunter"
    ]
    assert len(defect_hunter_calls) == 0, "Defect Hunter must NOT be invoked when candidate is blocked at sandbox"

    # Verify Primal Dual sandbox turn was not executed because the cemetery fence fired first
    primal_dual_calls = [
        req for req in turn_adapter_g2.invocation_log
        if req.seat_id == "seat_primal_dual"
    ]
    assert len(primal_dual_calls) == 0, "Primal Dual turn must NOT execute when cemetery fence blocks regression"

    # Verify refusal bundle was persisted under _intelligence/_adversary/runs/
    refusal_bundle_path_str = dict(refusal_g2.details).get("refusal_bundle", "")
    assert refusal_bundle_path_str, "Refusal bundle path must be recorded in refusal details"
    refusal_bundle_dir = Path(refusal_bundle_path_str)
    assert refusal_bundle_dir.exists(), f"Refusal bundle directory must exist at {refusal_bundle_dir}"
    summary_json = refusal_bundle_dir / "summary.json"
    assert summary_json.exists(), "summary.json must exist in refusal bundle"
    refusal_payload = json.loads(summary_json.read_text(encoding="utf-8"))
    assert refusal_payload.get("status") == "REFUSED"
    assert refusal_payload.get("act_reached") == "SANDBOX"


def test_fugu_armed_antibody_blocking_mutation(tmp_path: Path) -> None:
    """Tests that a mutated variant carrying the farmed antibody pattern is blocked in Act IV."""
    out_dir = tmp_path / "_intelligence" / "_adversary"
    _, _, profile, _, _ = load_adversary_council_profile()

    # 1. Pre-seed an antibody via PharmacySeeder
    seeder = PharmacySeeder(repo_root=tmp_path, text_writer=filesystem_text_writer, text_source=filesystem_catalog_text)
    farmed = seeder.farm_antibodies_from_defects(
        ["fatal_memory_leak_defect"],
        run_id="preseed_run",
        task_id="task_preseed",
    )
    assert len(farmed) == 1
    assert farmed[0].target_pattern == "fatal_memory_leak_defect"

    catalog_file = seeder.catalog_repo.catalog_file
    catalog_payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    for entry in catalog_payload.get("antibodies", {}).values():
        entry["pharmacy_status"] = "admitted"
    catalog_file.write_text(json.dumps(catalog_payload), encoding="utf-8")

    # 2. Mutated candidate code: different structure, but contains forbidden antibody pattern
    mutated_code = (
        "class CustomerService:\n"
        "    # Triggering: fatal_memory_leak_defect\n"
        "    def fetch(self): pass\n"
    )
    mutated_bytes = mutated_code.encode("utf-8")

    rt = build_adversary_runtime(output_dir=tmp_path / "_intelligence", fixture_mode=False)

    canned = {
        ("act2_panel_debate", "seat_gauge_breaker"): SeatTurnReplyV1(
            reply_text=mutated_code,
            machine_fields={"AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=mutated_bytes,
        ),
    }
    turn_adapter = FixtureAgentTurnAdapter(canned_replies=canned)
    object.__setattr__(rt, "seat_port", turn_adapter)

    from adversary.infrastructure.estates.oeeis_immune import OeeisImmuneAdapter

    packet = _make_packet("fugu_g3_run", "Refactor CustomerService")
    res = execute_7act_adversary_bout(
        profile,
        rt,
        packet,
        output_dir=out_dir,
        repo_root=tmp_path,
        admitted_antibody_reader=OeeisImmuneAdapter.admitted_regression_antibodies,
        native_support=DefaultNativeOperationPort(),
    )

    assert res.is_err, "Expected mutated candidate with forbidden pattern to be refused"
    refusal = res.unwrap_err()
    assert refusal.code == "REGRESSION_AGAINST_ANTIBODY_REFUSED"
    assert "matches admitted antibody" in refusal.message


def test_fugu_clean_candidate_passes_sandbox_gate(tmp_path: Path) -> None:
    """Tests that a clean candidate without defects passes Act IV Sandbox gate cleanly."""
    out_dir = tmp_path / "_intelligence" / "_adversary"
    _, _, profile, _, _ = load_adversary_council_profile()

    # Pre-seed cemetery with an unrelated headstone
    cemetery_adapter = FileCemeteryAdapter(out_dir / "cemetery")
    dummy_hs = CemeteryHeadstoneV1(
        candidate_id="unrelated_dead",
        run_key="old_run",
        scene_id="act2_panel_debate",
        cause_of_death="KILLED_BY_DEFECT_HUNTER: syntax error",
        killing_seat_id="seat_defect_hunter",
        evidence_refs=(),
        candidate_payload_sha256="sha256:" + hashlib.sha256(b"completely_different_code").hexdigest(),
    )
    assert cemetery_adapter.record_headstone(dummy_hs).is_ok

    rt = build_adversary_runtime(output_dir=tmp_path / "_intelligence", fixture_mode=False)

    canned = {
        ("act2_panel_debate", "seat_gauge_breaker"): SeatTurnReplyV1(
            reply_text=CLEAN_CODE,
            machine_fields={"AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=CLEAN_BYTES,
        ),
        ("act4_sandbox", "seat_primal_dual"): SeatTurnReplyV1(
            reply_text="Primal Dual audit passed: pure dependency injection.",
            machine_fields={"DISPOSITION": "PASS", "AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=b"primal_dual_pass",
        ),
        ("act2_panel_debate", "seat_defect_hunter"): SeatTurnReplyV1(
            reply_text=(
                "Non-blocking review: clean decoupled architecture.\n"
                '```critique\n{"blocking": false, "counterexample": null}\n```'
            ),
            machine_fields={"DISPOSITION": "PASS", "AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=b"defect_hunter_pass",
        ),
    }
    turn_adapter = FixtureAgentTurnAdapter(canned_replies=canned)
    object.__setattr__(rt, "seat_port", turn_adapter)

    packet = _make_packet("fugu_clean_run", "Decoupled Clean Architecture implementation")
    res = execute_7act_adversary_bout(profile, rt, packet, output_dir=out_dir, native_support=DefaultNativeOperationPort())

    assert res.is_ok, f"Expected clean candidate to pass all 7 acts: {res.unwrap_err()}"
    receipt = res.unwrap()
    assert receipt.authority_effect == AUTHORITY_EFFECT_NONE
    assert receipt.final_state.terminal_status == "COMPLETED"


def test_fugu_cemetery_defense_ablation(tmp_path: Path) -> None:
    """Ablation test: with no_cemetery_defense=True, the candidate bypasses Act IV Sandbox."""
    out_dir = tmp_path / "_intelligence" / "_adversary"
    _, _, profile, _, _ = load_adversary_council_profile()

    # Pre-seed cemetery with headstone matching DEFECTIVE_BYTES
    cemetery_adapter = FileCemeteryAdapter(out_dir / "cemetery")
    hs = CemeteryHeadstoneV1(
        candidate_id="dead_cand_1",
        run_key="prior_run",
        scene_id="act2_panel_debate",
        cause_of_death="KILLED_BY_DEFECT_HUNTER: direct import",
        killing_seat_id="seat_defect_hunter",
        evidence_refs=(),
        candidate_payload_sha256=DEFECTIVE_SHA256,
    )
    assert cemetery_adapter.record_headstone(hs).is_ok

    rt = build_adversary_runtime(output_dir=tmp_path / "_intelligence", fixture_mode=False)

    canned = {
        ("act2_panel_debate", "seat_gauge_breaker"): SeatTurnReplyV1(
            reply_text=DEFECTIVE_CODE,
            machine_fields={"AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=DEFECTIVE_BYTES,
        ),
        ("act4_sandbox", "seat_primal_dual"): SeatTurnReplyV1(
            reply_text="Primal Dual audit run because cemetery defense was ablated.",
            machine_fields={"DISPOSITION": "PASS", "AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=b"primal_dual_pass_ablated",
        ),
        ("act2_panel_debate", "seat_defect_hunter"): SeatTurnReplyV1(
            reply_text=(
                "Non-blocking critique for test.\n"
                '```critique\n{"blocking": false, "counterexample": null}\n```'
            ),
            machine_fields={"DISPOSITION": "PASS", "AUTHORITY_EFFECT": "None"},
            residual_colour="Open",
            authority_effect="None",
            raw_bytes=b"defect_hunter_pass",
        ),
    }
    turn_adapter = FixtureAgentTurnAdapter(canned_replies=canned)
    object.__setattr__(rt, "seat_port", turn_adapter)

    packet = _make_packet("fugu_ablation_run", "Ablation test run")
    res = execute_7act_adversary_bout(
        profile,
        rt,
        packet,
        output_dir=out_dir,
        ablation_flags={"no_cemetery_defense": True},
        native_support=DefaultNativeOperationPort(),
    )

    # When ablated, the candidate is NOT blocked at Act IV Sandbox
    assert res.is_ok, f"Expected bout to proceed through Act IV when ablated: {res.unwrap_err()}"
    primal_dual_calls = [
        req for req in turn_adapter.invocation_log
        if req.seat_id == "seat_primal_dual"
    ]
    assert len(primal_dual_calls) == 1, "Primal Dual must be invoked when cemetery defense is ablated"
