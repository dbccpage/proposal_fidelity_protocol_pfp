"""Unit and E2E tests for the Finite-QM 177 DAG Prompts (`1..35` + `36..177`),
Mission M3 Decoy Ablation Campaign, & 1,000-Derivation PFP System.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from omega_engine_pfp.tests.demo_004.finite_qm_derivation_pfp.gates.gate_engine import (
    verify_dag_prompt_node_reply,
)
from omega_engine_pfp.tests.demo_004.finite_qm_derivation_pfp.operad_mining.miner import (
    DAG_ALL_177_SPECS,
    DAG_PROMPT_35_SPECS,
    DAG_REMAINING_142_SPECS,
    DEFAULT_DAG_PATH,
    DEFAULT_FQM_REPO_ROOT,
    DEFAULT_OPERADS_PATH,
    DEFAULT_PROMPTS_DIR,
    mine_operads_for_dag_prompt_node,
)
from omega_engine_pfp.tests.demo_004.finite_qm_derivation_pfp.run_finite_qm_pfp import (
    run_benchmark_1000,
)


def test_all_177_dag_prompt_specs_and_4_mission_operad_miner() -> None:
    assert len(DAG_PROMPT_35_SPECS) == 35
    assert len(DAG_REMAINING_142_SPECS) == 142
    assert len(DAG_ALL_177_SPECS) == 177
    prompt_files = sorted(DEFAULT_PROMPTS_DIR.glob("*.yaml"))
    assert len(prompt_files) == 177

    for pf in prompt_files:
        _stage, node_id, _status = pf.stem.split("__")
        mined = mine_operads_for_dag_prompt_node(
            node_id=node_id,
            dag_path=DEFAULT_DAG_PATH,
            operads_path=DEFAULT_OPERADS_PATH,
        )
        assert mined.slot_m1_layer0_ambient_carrier["mining_status"] == "FILLED_BY_4MISSION_MINER"
        assert mined.slot_m2_layer1_forward_morphisms["mining_status"] == "FILLED_BY_4MISSION_MINER"
        assert mined.slot_m3_layer2_ideals_and_annihilators["mining_status"] == "FILLED_BY_4MISSION_MINER"
        assert mined.slot_m4_tri_language_witness_anchors["mining_status"] == "FILLED_BY_4MISSION_MINER"
        assert "Congruence Ideals" in mined.rendered_user_prompt
        assert "M3 Decoy Equations Omitted" in mined.rendered_user_prompt_without_m3

        # Verify gate engine accepts exact ground truth and rejects mutated decoys
        rcpt_pass = verify_dag_prompt_node_reply(mined.expected_ground_truth, dict(mined.expected_ground_truth))
        assert rcpt_pass.all_gates_passed is True
        assert rcpt_pass.status == "PASS"

        mutated = dict(mined.expected_ground_truth)
        mutated["unconditional_promotion_refused"] = False
        rcpt_fail = verify_dag_prompt_node_reply(mined.expected_ground_truth, mutated)
        assert rcpt_fail.all_gates_passed is False
        assert rcpt_fail.status == "FAIL"


def test_all_177_populated_prompts_receipts_ablation_and_papers_on_disk() -> None:
    prompt_files = sorted(DEFAULT_PROMPTS_DIR.glob("*.yaml"))
    assert len(prompt_files) == 177
    receipts_dir = DEFAULT_FQM_REPO_ROOT / "evidence" / "receipts" / "pfp_dag_prompts"
    ablation_dir = DEFAULT_FQM_REPO_ROOT / "evidence" / "receipts" / "pfp_m3_ablation"
    ablation_summary_path = (
        DEFAULT_FQM_REPO_ROOT / "evidence" / "receipts" / "pfp_142_remaining_nodes_m3_ablation_summary.json"
    )
    assert ablation_summary_path.exists()
    ablation_summary = json.loads(ablation_summary_path.read_text(encoding="utf-8"))
    assert ablation_summary["nodes_evaluated"] == 142
    assert ablation_summary["with_m3_final_pass_count"] == 142
    assert ablation_summary["with_m3_attempt1_pass_count"] > ablation_summary["without_m3_attempt1_pass_count"]

    shadow_sum_177 = 0
    counter_sum_177 = 0

    for pf in prompt_files:
        doc = yaml.safe_load(pf.read_text(encoding="utf-8"))
        slots = doc["operad_slots"]
        for slot_key in (
            "slot_m1_layer0_ambient_carrier",
            "slot_m2_layer1_forward_morphisms",
            "slot_m3_layer2_ideals_and_annihilators",
            "slot_m4_tri_language_witness_anchors",
        ):
            assert slots[slot_key]["mining_status"] == "FILLED_BY_4MISSION_MINER"

        node_id = doc["dag_node"]["node_id"]
        idx = int(doc["dag_node"]["prompt_index"])
        rcpt_file = receipts_dir / f"{node_id}_pfp_receipt.json"
        assert rcpt_file.exists(), f"Missing receipt for {node_id}"
        rcpt = json.loads(rcpt_file.read_text(encoding="utf-8"))
        assert rcpt["gate_receipt"]["all_gates_passed"] is True
        assert rcpt["gate_receipt"]["status"] == "PASS"
        shadow_sum_177 += int(rcpt["typed_model_response"]["finite_shadow_witness_int"])
        counter_sum_177 += int(rcpt["typed_model_response"]["countermodel_witness_int"])

        assert len(rcpt["updated_papers"]) >= 1
        for pref in rcpt["updated_papers"]:
            p_path = DEFAULT_FQM_REPO_ROOT / pref
            assert p_path.exists()
            text = p_path.read_text(encoding="utf-8")
            assert f"## 6. Multi-Stage PFP & 4-Mission Operad Verification Receipt (`{node_id}`)" in text

        if idx >= 36:
            ab_file = ablation_dir / f"{node_id}_m3_ablation.json"
            assert ab_file.exists(), f"Missing M3 ablation receipt for {node_id}"
            ab = json.loads(ab_file.read_text(encoding="utf-8"))
            assert ab["with_m3_final"]["all_gates_passed"] is True

    assert shadow_sum_177 == 66160
    assert counter_sum_177 == 17806


def test_1000_derivation_work_units_deterministic_benchmark(tmp_path: Path) -> None:
    out_path = tmp_path / "benchmark_1000_receipt.json"
    summary = run_benchmark_1000(output_receipt_path=out_path)
    assert summary["work_units_generated"] == 1000
    assert summary["work_units_passed"] == 1000
    assert out_path.exists()
