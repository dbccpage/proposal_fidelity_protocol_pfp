"""Reproducibility and invariant tests for the 5-seam LLM mechanism showcase."""
from __future__ import annotations

import json

from benchmarks.llm_mechanisms.run_five_seam_showcase import (
    RESULTS_PATH,
    build_five_seam_showcase_report,
)


def test_five_seam_showcase_results_file_matches_deterministic_run() -> None:
    assert RESULTS_PATH.exists(), 'five_seam_showcase_results.json must exist'
    stored = json.loads(RESULTS_PATH.read_text(encoding='utf-8'))
    fresh = build_five_seam_showcase_report()
    assert stored == fresh
    assert stored['live_api_spend_usd'] == '0.000000'
    assert stored['authority_effect'] == 'None'


def test_five_seam_showcase_all_seams_and_negative_controls_pass() -> None:
    report = build_five_seam_showcase_report()
    seams = report['seams']
    assert set(seams) == {
        'seam_1_sampling_parameters',
        'seam_2_logit_and_grammar_decode',
        'seam_3_host_controlled_scratchpad',
        'seam_4_attention_heads_kv_and_residual_steering',
        'seam_5_weights_finetune_on_antibodies_from_receipts',
    }

    # Seam 1 assertions
    s1 = seams['seam_1_sampling_parameters']
    assert s1['quotient_collapse']['t0_n5_has_redundant_replicates'] is True
    assert s1['quotient_collapse']['t0_n5_effective_draws'] == 1
    assert s1['selection_rule_comparison']['majority_vote']['status'] == 'DELIVERED_UNCERTIFIED'
    assert s1['selection_rule_comparison']['certificate_first']['status'] == 'HOST_CERTIFIED'
    assert s1['all_uncertified_negative_control']['status'] == 'NO_CERTIFIED_SAMPLE'

    # Seam 2 assertions
    s2 = seams['seam_2_logit_and_grammar_decode']
    assert s2['decode_receipt_verifier_matrix'] == {
        'honored_json_schema': 'PASS',
        'carrier_violation_refusal': 'CARRIER_CONSTRAINT_VIOLATED',
        'extreme_logit_bias_refusal': 'LOGIT_BIAS_EXCEEDS_CEILING',
        'missing_grammar_hash_refusal': 'MISSING_GRAMMAR_HASH',
        'non_none_authority_refusal': 'AUTHORITY_EFFECT_NON_NONE',
    }
    sep = s2['layer2_vs_layer3_separation']
    assert sep['unconstrained_noncanonical']['wire_syntax_valid'] is False
    assert sep['trie_constrained_wrong_math']['wire_syntax_valid'] is True
    assert sep['trie_constrained_wrong_math']['semantically_certified'] is False
    assert sep['trie_constrained_certified']['semantically_certified'] is True

    # Seam 3 assertions
    s3 = seams['seam_3_host_controlled_scratchpad']
    assert s3['free_form_cot_stationary_arm']['terminal_refusal'] == 'SURVIVOR_OBSTRUCTION'
    assert s3['host_scratch_ledger_c006_arm']['certified_terminal'] == 'ACCEPTED_ZERO_DEFECT'
    assert s3['host_scratch_ledger_c006_arm']['final_turn_4_tokens_saved_vs_cot'] > 0
    assert s3['treg_circuit_breaker_control']['treg_suspended'] is True
    assert s3['treg_circuit_breaker_control']['escalate_after_treg'] is False

    # Seam 4 assertions
    s4 = seams['seam_4_attention_heads_kv_and_residual_steering']
    for arch in ('llama_qwen_model_layers', 'gemma4_language_model_layers'):
        a = s4['architectures_verified'][arch]
        assert a['attention_delta0_max_abs_diff'] == 0.0
        assert a['attention_delta6_max_abs_diff'] > 0.0
        assert a['head_alpha1_max_abs_diff'] == 0.0
        assert a['head_ablation_changed_norm'] > 0.0
        assert a['head_patch_changed_norm'] > 0.0
        assert a['steering_vs_random_norm_diff'] < 1e-5
        assert abs(a['steering_vs_random_dot_product']) < 1e-4
        assert a['kv_cache_token_exact'] is True
    gate = s4['eis_two_signal_attention_gate']
    assert gate['self_authorizing_observer_control']['refusal_code'] == 'TWO_SIGNAL_COLLAPSE'
    assert gate['signal1_only_without_host_danger_control']['authorize_mask'] is False
    assert gate['two_signal_host_authorized']['authorize_mask'] is True

    # Seam 5 assertions
    s5 = seams['seam_5_weights_finetune_on_antibodies_from_receipts']
    assert s5['dataset_causal_witness_verified'] is True
    assert s5['negative_controls_and_refusals'] == {
        'holdout_prompt_overlap': 'HOLDOUT_CONTAMINATION_REFUSAL',
        'holdout_task_id_overlap': 'HOLDOUT_CONTAMINATION_REFUSAL',
        'tainted_pciv_lineage': 'TAINTED_LINEAGE_RECEIPT_REFUSED',
        'uncertified_chosen_proposal': 'UNCERTIFIED_CHOSEN_PROPOSAL_REFUSED',
        'protected_contract_fence_violation': 'CHOSEN_PROTECTED_FENCE_VIOLATION',
        'thymus_admitted_guard_match': 'CHOSEN_FAILED_ADMITTED_GUARD',
        'alternative_valid_witness_in_rejected': 'ALTERNATIVE_VALID_WITNESS_NOT_REJECTED',
    }
    eval_dpo = s5['dpo_lora_training_and_holdout_evaluation']
    assert eval_dpo['base_model_param_max_drift'] == 0.0
    assert eval_dpo['dpo_margin_improved'] is True
    assert eval_dpo['frobenius_norm_diff'] < 1e-5
    assert eval_dpo['trained_beats_random_on_holdout'] is True
    assert eval_dpo['trained_beats_base_on_holdout'] is True
    assert s5['weight_adapter_receipt']['authority_effect'] == 'None'
