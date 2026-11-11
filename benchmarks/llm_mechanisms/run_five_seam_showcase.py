"""Deterministic 5-Seam LLM Intervention & Receipt-to-Weight Showcase Runner.

Executes all five physical LLM intervention seams (`Sampling`, `Logit/Grammar`,
`Host Scratchpad`, `Attention/KV/Residual`, and `Weights/LoRA from Verified
Receipt Triples`) with their paired negative controls and writes
`benchmarks/llm_mechanisms/five_seam_showcase_results.json`.

Live API spend: USD 0.000000.
AuthorityEffect: None.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import torch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eis.domain.value_objects import DetectorRule  # noqa: E402
from pfp.domain.ports.decode_control_port import ControlKind, DecodeControlReceipt  # noqa: E402
from pfp_core.civilization import Lineage  # noqa: E402
from pfp_core.fidelity import HostOracleContext, ProtectedContract  # noqa: E402
from pfp_core.llm_mechanisms import (  # noqa: E402
    CandidateRunReceiptV1,
    FastOffsetTokenizer,
    HostScratchSessionV1,
    LogitGrammarControllerV1,
    LowRankWeightAdapterV1,
    OpenWeightMechanismRunnerV1,
    PinnedEagerMicroCausalLM,
    ReceiptToWeightPipelineV1,
    SamplingConfigV1,
    ScratchTurnRecordV1,
    detect_stationary_attractor_exact,
    evaluate_attention_intervention_gate,
    evaluate_sampling_seam,
    verify_causal_witness,
    verify_decode_receipt_exact,
)
from pfp_core.operad_pipe import quotient_workflows  # noqa: E402

RESULTS_PATH = Path(__file__).resolve().parent / 'five_seam_showcase_results.json'


def _oracle_single(name: str, passed: bool, evidence: str) -> HostOracleContext:
    ctx = HostOracleContext()
    ctx.record(name, passed, evidence)
    return ctx


def _run_seam1_showcase() -> dict[str, Any]:
    cfg_t0_n1 = SamplingConfigV1(temperature=Fraction(0), n_samples=1, selection_rule='certificate_first')
    cfg_t0_n5 = SamplingConfigV1(temperature=Fraction(0), n_samples=5, selection_rule='certificate_first')
    q_classes = quotient_workflows(
        {
            'arm_t0_n1': cfg_t0_n1.as_typed_ops('prompt_charpoly_3x3'),
            'arm_t0_n5': cfg_t0_n5.as_typed_ops('prompt_charpoly_3x3'),
        }
    )

    draws = [
        ('{"answer":"2/4"}', 12, 24, 8),
        ('{"answer":"2/4"}', 12, 24, 8),
        ('{"answer":"2/4"}', 12, 24, 8),
        ('{"answer":"1/2"}', 12, 24, 8),
    ]

    def _sampler(idx: int, _temp: Fraction, _seed: int) -> tuple[str, int, int, int]:
        return draws[idx]

    def _checker(reply: str) -> HostOracleContext:
        return _oracle_single('canonical_rational_reduced', reply == '{"answer":"1/2"}', reply)

    outcomes: dict[str, Any] = {}
    for rule in ('greedy_first', 'majority_vote', 'certificate_first'):
        cfg = SamplingConfigV1(
            temperature=Fraction(7, 10),
            top_p=Fraction(9, 10),
            n_samples=4,
            seed=19,
            selection_rule=rule,
        )
        out = evaluate_sampling_seam(
            cfg,
            task_id=f'canonical_rational_{rule}',
            prompt_text='Reduce 2/4 to canonical rational JSON.',
            sampler=_sampler,
            host_checker=_checker,
        )
        outcomes[rule] = {
            'status': out.status,
            'selected_reply': out.selected_reply,
            'selected_index': out.selected_index,
            'certified_draw_indices': list(out.certified_draw_indices),
            'majority_reply': out.majority_reply,
            'majority_is_certified': out.majority_is_certified,
            'spent_microusd': out.budget_summary['spent_microusd'],
            'total_tokens': out.budget_summary['total_tokens'],
            'authority_effect': out.authority_effect,
        }

    # Control: when 0/4 draws are certified, certificate_first returns NO_CERTIFIED_SAMPLE
    all_bad_out = evaluate_sampling_seam(
        SamplingConfigV1(temperature=Fraction(7, 10), n_samples=4, seed=19, selection_rule='certificate_first'),
        task_id='canonical_rational_none',
        prompt_text='Reduce 2/4 to canonical rational JSON.',
        sampler=lambda _i, _t, _s: ('{"answer":"2/4"}', 12, 24, 8),
        host_checker=_checker,
    )

    return {
        'seam_id': 'seam_1_sampling_parameters',
        'quotient_collapse': {
            'input_arms': ['arm_t0_n1', 'arm_t0_n5'],
            'equivalence_classes': list(q_classes.values()),
            't0_n5_has_redundant_replicates': cfg_t0_n5.has_redundant_zero_temp_replicates,
            't0_n5_effective_draws': cfg_t0_n5.effective_draws,
            'redundant_draw_reduction_ratio': '4/5',
        },
        'selection_rule_comparison': outcomes,
        'all_uncertified_negative_control': {
            'status': all_bad_out.status,
            'selected_reply': all_bad_out.selected_reply,
            'spent_microusd': all_bad_out.budget_summary['spent_microusd'],
        },
        'authority_effect': 'None',
    }


def _run_seam2_showcase(tokenizer: FastOffsetTokenizer) -> dict[str, Any]:
    right_reply = '{"status":"SOLVED","kind":"product_sign","answer":{"sign":"-1","negative_count":"3"}}'
    wrong_on_grammar_reply = '{"status":"SOLVED","kind":"product_sign","answer":{"sign":"+1","negative_count":"2"}}'
    noncanonical_reply = '{"status":"SOLVED","answer":"2/4"}'

    controller = LogitGrammarControllerV1([right_reply, wrong_on_grammar_reply], tokenizer)

    def _host_checker(decoded: str) -> tuple[HostOracleContext, bool]:
        ctx = HostOracleContext()
        try:
            obj = json.loads(decoded)
            wire_ok = (
                isinstance(obj, dict)
                and obj.get('status') == 'SOLVED'
                and obj.get('kind') == 'product_sign'
                and isinstance(obj.get('answer'), dict)
            )
        except json.JSONDecodeError:
            obj = {}
            wire_ok = False
        ctx.record('wire_schema_valid', wire_ok, decoded)
        ctx.record(
            'exact_product_sign_oracle',
            bool(wire_ok and obj.get('answer') == {'sign': '-1', 'negative_count': '3'}),
            decoded,
        )
        return ctx, wire_ok

    eval_unconstrained = controller.evaluate_candidate(
        case_id='call1_unconstrained_noncanonical',
        request_text='factors: - + - -',
        output_tokens=tokenizer.encode(noncanonical_reply, add_special_tokens=False),
        control_kind=ControlKind.CARRIER_MASK,
        host_checker=_host_checker,
    )
    eval_wrong_math = controller.evaluate_candidate(
        case_id='call1_trie_wrong_math',
        request_text='factors: - + - -',
        output_tokens=tokenizer.encode(wrong_on_grammar_reply, add_special_tokens=False),
        control_kind=ControlKind.JSON_SCHEMA,
        host_checker=_host_checker,
    )
    eval_certified = controller.evaluate_candidate(
        case_id='call1_trie_certified',
        request_text='factors: - + - -',
        output_tokens=tokenizer.encode(right_reply, add_special_tokens=False),
        control_kind=ControlKind.JSON_SCHEMA,
        host_checker=_host_checker,
    )

    # Receipt verifier refusal matrix
    base_rcpt = eval_certified.decode_receipt
    verifier_matrix = {
        'honored_json_schema': verify_decode_receipt_exact(base_rcpt)['status'],
        'carrier_violation_refusal': verify_decode_receipt_exact(
            DecodeControlReceipt(
                receipt_id='rcpt_bad_carrier',
                case_id='c_carrier',
                control_kind=ControlKind.CARRIER_MASK.value,
                output_tokens=(999,),
                allowed_tokens=(1, 2, 3),
            )
        )['refusal_code'],
        'extreme_logit_bias_refusal': verify_decode_receipt_exact(
            DecodeControlReceipt(
                receipt_id='rcpt_bad_bias',
                case_id='c_bias',
                control_kind=ControlKind.LOGIT_BIAS.value,
                output_tokens=(1,),
                logit_biases=((1, 2000),),
            )
        )['refusal_code'],
        'missing_grammar_hash_refusal': verify_decode_receipt_exact(
            replace(base_rcpt, grammar_sha256=None)
        )['refusal_code'],
        'non_none_authority_refusal': verify_decode_receipt_exact(
            replace(base_rcpt, authority_effect='BypassHost')
        )['refusal_code'],
    }

    return {
        'seam_id': 'seam_2_logit_and_grammar_decode',
        'language_sha256': controller.language_sha256,
        'carrier_token_count': len(controller.carrier_mask.allowed_tokens),
        'decode_receipt_verifier_matrix': verifier_matrix,
        'layer2_vs_layer3_separation': {
            'unconstrained_noncanonical': {
                'layer2_status': eval_unconstrained.layer2_verdict['status'],
                'layer2_refusal_code': eval_unconstrained.layer2_verdict.get('refusal_code'),
                'wire_syntax_valid': eval_unconstrained.wire_syntax_valid,
                'semantically_certified': eval_unconstrained.semantically_certified,
            },
            'trie_constrained_wrong_math': {
                'layer2_status': eval_wrong_math.layer2_verdict['status'],
                'wire_syntax_valid': eval_wrong_math.wire_syntax_valid,
                'semantically_certified': eval_wrong_math.semantically_certified,
                'failed_host_predicates': [
                    k for k, v in eval_wrong_math.layer3_oracle['certified_predicates'].items() if not v
                ],
            },
            'trie_constrained_certified': {
                'layer2_status': eval_certified.layer2_verdict['status'],
                'wire_syntax_valid': eval_certified.wire_syntax_valid,
                'semantically_certified': eval_certified.semantically_certified,
            },
        },
        'authority_effect': 'None',
    }


def _run_seam3_showcase() -> dict[str, Any]:
    edges = [('a', 'b'), ('b', 'c'), ('c', 'a'), ('a', 'd'), ('b', 'd'), ('c', 'd')]
    initial_claims = {'a->b': 1, 'b->c': 2, 'c->a': 0, 'a->d': -2, 'b->d': 0, 'c->d': -3}
    cycles = {
        'c1': [('a', 'b', 1), ('b', 'c', 1), ('c', 'a', 1)],
        'c2': [('a', 'b', 1), ('b', 'd', 1), ('a', 'd', -1)],
        'c3': [('b', 'c', 1), ('c', 'd', 1), ('b', 'd', -1)],
    }
    chords = ['c->a', 'b->d', 'c->d']

    # Arm A: Free-form CoT stationary loop (repeats stationary cut 4 times)
    cot_session = HostScratchSessionV1(
        board_id='k4_cot_stationary',
        edges=edges,
        initial_claims=initial_claims,
        fundamental_cycles=cycles,
        chords=chords,
        fuel=6,
    )
    cot_token_trajectory: list[int] = []
    for t in range(4):
        step = cot_session.apply_cut(
            initial_claims,
            mode='cot',
            rationale=(
                f'Turn {t + 1}: re-evaluating cycle equations in free-form '
                'chain-of-thought without host ledger compaction.'
            ),
        )
        cot_token_trajectory.append(step['prompt_tokens_estimated'])
    cot_terminal = cot_session.verify_zero_defect({'a': 0, 'b': 1, 'c': 3, 'd': -2})

    # Arm B: Host-Controlled Scratch Ledger (C006) with chord-guided descent
    ledger_session = HostScratchSessionV1(
        board_id='k4_host_ledger_c006',
        edges=edges,
        initial_claims=initial_claims,
        fundamental_cycles=cycles,
        chords=chords,
        fuel=6,
    )
    phi1_initial = ledger_session.compute_phi1()
    descent_moves = [
        dict(initial_claims, **{'c->a': -3}),
        dict(initial_claims, **{'c->a': -3, 'b->d': -3, 'c->d': -6}),
        dict(initial_claims, **{'c->a': -3, 'b->d': -3, 'c->d': -5}),
        dict(initial_claims, **{'c->a': -3, 'b->d': -3, 'c->d': -5}),  # 4th turn to compare prompt token bound
    ]
    ledger_token_trajectory: list[int] = []
    phi1_trajectory: list[int] = [phi1_initial]
    for idx, move in enumerate(descent_moves):
        step = ledger_session.apply_cut(
            move,
            mode='ledger',
            rationale=f'Turn {idx + 1}: chord update on open fundamental cycle.',
        )
        ledger_token_trajectory.append(step['prompt_tokens_estimated'])
        phi1_trajectory.append(step['phi1'])

    mutated_potential_verdict = ledger_session.verify_zero_defect({'a': 0, 'b': 1, 'c': 3, 'd': 5})
    certified_verdict = ledger_session.verify_zero_defect({'a': 0, 'b': 1, 'c': 3, 'd': -2})

    # Treg circuit-breaker check
    noisy_turns = [
        ScratchTurnRecordV1(
            turn=i,
            host_state_digest='s_fixed',
            canonical_move_digest='m_fixed',
            move_kind='CUT',
            outcome='IdempotentStationary',
        )
        for i in range(1, 7)
    ]
    treg_report = detect_stationary_attractor_exact(noisy_turns, treg_firing_ceiling=3)

    return {
        'seam_id': 'seam_3_host_controlled_scratchpad',
        'board_id': 'k4_b1_3',
        'initial_phi1': phi1_initial,
        'free_form_cot_stationary_arm': {
            'prompt_tokens_by_turn': cot_token_trajectory,
            'am4_escalate_triggered': cot_session.history[-1].turn >= 2,
            'terminal_status': cot_terminal['status'],
            'terminal_refusal': cot_terminal['refusal'],
            'final_phi1': cot_terminal['phi1_final'],
        },
        'host_scratch_ledger_c006_arm': {
            'prompt_tokens_by_turn': ledger_token_trajectory,
            'phi1_trajectory': phi1_trajectory,
            'final_turn_4_tokens_saved_vs_cot': cot_token_trajectory[-1] - ledger_token_trajectory[-1],
            'mutated_potential_refusal': mutated_potential_verdict['refusal'],
            'certified_terminal': certified_verdict['terminal'],
            'certified_potential': certified_verdict['potential'],
        },
        'treg_circuit_breaker_control': {
            'findings_count': len(treg_report.findings),
            'treg_firing_ceiling': 3,
            'treg_suspended': treg_report.treg_suspended,
            'escalate_after_treg': treg_report.escalate,
        },
        'authority_effect': 'None',
    }


def _run_seam4_showcase(tokenizer: FastOffsetTokenizer) -> dict[str, Any]:
    rev = 'c' * 40
    layouts: dict[str, Any] = {}
    text = 'factors : - + - fluff noise'
    clean_text = 'factors : - + -'
    fluff_idx = text.index('fluff')

    for layout_name, is_gemma4, model_id in (
        ('llama_qwen_model_layers', False, 'Qwen/Qwen2.5-7B-Instruct'),
        ('gemma4_language_model_layers', True, 'google/gemma-4-9b-it'),
    ):
        model = PinnedEagerMicroCausalLM(tokenizer.vocab_size, gemma4_layout=is_gemma4, seed=17)
        runner = OpenWeightMechanismRunnerV1(model, tokenizer, model_id=model_id, revision=rev)
        carrier_pos = runner.carrier_positions(text, [(0, fluff_idx)])

        base_logits, _ = runner.forward(text)
        null_attn_logits, _ = runner.forward(
            text, attention={'layers': [0, 1], 'positions': carrier_pos, 'delta': 0}
        )
        active_attn_logits, attn_readouts = runner.forward(
            text, attention={'layers': [0, 1], 'positions': carrier_pos, 'delta': 6}
        )

        null_head_logits, _ = runner.forward(text, heads={'layer': 0, 'heads': [0], 'alpha': 1.0})
        ablated_head_logits, head_readouts = runner.forward(
            text, heads={'layer': 0, 'heads': [0], 'alpha': 0.0}
        )

        clean_head = runner.capture(clean_text, layer=1, kind='head', head=0)
        patched_logits, patch_readouts = runner.forward(
            text, patch={'layer': 1, 'head': 0, 'value': clean_head}
        )

        r_clean = runner.capture(clean_text, layer=1, kind='residual')[0]
        r_noisy = runner.capture(text, layer=1, kind='residual')[0]
        steer_vec = r_clean - r_noisy
        rand_vec = runner.build_equal_norm_random_vector(steer_vec, seed=101)
        steered_logits, _ = runner.forward(text, residual={'layer': 1, 'vector': steer_vec, 'alpha': 1.5})
        rand_logits, _ = runner.forward(text, residual={'layer': 1, 'vector': rand_vec, 'alpha': 1.5})

        kv_parity = runner.cache_parity(text, steps=4)

        layouts[layout_name] = {
            'model_id': model_id,
            'architecture_layers': runner.pipeline['architecture_layers'],
            'carrier_positions': list(carrier_pos),
            'attention_delta0_max_abs_diff': float((base_logits - null_attn_logits).abs().max().item()),
            'attention_delta6_max_abs_diff': float((base_logits - active_attn_logits).abs().max().item()),
            'attention_delta6_changed_entries': sum(r['changed_entries'] for r in attn_readouts),
            'head_alpha1_max_abs_diff': float((base_logits - null_head_logits).abs().max().item()),
            'head_ablation_changed_norm': round(head_readouts[0]['changed_norm'], 6),
            'head_patch_changed_norm': round(patch_readouts[0]['changed_norm'], 6),
            'head_patch_logit_shift_l2': round(float((base_logits - patched_logits).norm().item()), 6),
            'steering_vs_random_norm_diff': round(
                abs(float(steer_vec.norm().item()) - float(rand_vec.norm().item())), 8
            ),
            'steering_vs_random_dot_product': round(float(torch.dot(steer_vec, rand_vec).item()), 8),
            'steered_vs_random_logit_l2_diff': round(float((steered_logits - rand_logits).norm().item()), 6),
            'kv_cache_token_exact': kv_parity['token_exact'],
        }

    gate_collapsed = evaluate_attention_intervention_gate(
        distractor_mass=Fraction(7, 20),
        danger_tau=Fraction(1, 20),
        host_refusal_on_unmasked=True,
        host_observer_id='attention_probe',
    )
    gate_s1_only = evaluate_attention_intervention_gate(
        distractor_mass=Fraction(7, 20),
        danger_tau=Fraction(1, 20),
        host_refusal_on_unmasked=False,
        host_observer_id='host.public_smoke',
    )
    gate_authorized = evaluate_attention_intervention_gate(
        distractor_mass=Fraction(7, 20),
        danger_tau=Fraction(1, 20),
        host_refusal_on_unmasked=True,
        host_observer_id='host.public_smoke',
        danger_kind='REPLAY_FAILURE',
    )

    return {
        'seam_id': 'seam_4_attention_heads_kv_and_residual_steering',
        'architectures_verified': layouts,
        'eis_two_signal_attention_gate': {
            'self_authorizing_observer_control': gate_collapsed,
            'signal1_only_without_host_danger_control': gate_s1_only,
            'two_signal_host_authorized': gate_authorized,
        },
        'authority_effect': 'None',
    }


def _run_seam5_showcase(tokenizer: FastOffsetTokenizer) -> dict[str, Any]:
    lineage = Lineage()
    lineage.add('seed_compromised')
    lineage.add('genome_tainted_v1')
    lineage.derive('seed_compromised', 'genome_tainted_v1', 'bad_mutation')
    lineage.add('seed_verified')
    lineage.add('genome_clean_v1')
    lineage.derive('seed_verified', 'genome_clean_v1', 'verified_mutation')

    thymus_rule = DetectorRule(rule_id='guard_no_todo_stub', target_epitope='code', match_pattern='TODO_STUB')
    pipeline = ReceiptToWeightPipelineV1(
        lineage=lineage,
        tainted_seeds={'seed_compromised'},
        thymus_rules=[thymus_rule],
        self_panel=['{"sign":"-1"}', '{"answer":"1/2"}'],
    )

    w1 = CandidateRunReceiptV1(
        receipt_id='rcpt_chosen_01',
        task_id='train_sign_01',
        prompt_text='factors : - + -',
        candidate_text='{"sign":"-1"}',
        genome_id='genome_clean_v1',
        oracle=_oracle_single('exact_sign', True, '{"sign":"-1"}'),
        contract=ProtectedContract.fence_markers('{"sign":"-1"}', '{"sign":', '}'),
    )
    l1 = CandidateRunReceiptV1(
        receipt_id='rcpt_rejected_01',
        task_id='train_sign_01',
        prompt_text='factors : - + -',
        candidate_text='{"sign":"+1"}',
        genome_id='genome_clean_v1',
        oracle=_oracle_single('exact_sign', False, '{"sign":"+1"}'),
        refusal_code='SIGN_PARITY_REFUSAL',
    )
    w2 = CandidateRunReceiptV1(
        receipt_id='rcpt_chosen_02',
        task_id='train_rat_02',
        prompt_text='claims : "2/4"',
        candidate_text='{"answer":"1/2"}',
        genome_id='genome_clean_v1',
        oracle=_oracle_single('canonical_rational', True, '{"answer":"1/2"}'),
        contract=ProtectedContract.fence_markers('{"answer":"1/2"}', '{"answer":', '}'),
    )
    l2 = CandidateRunReceiptV1(
        receipt_id='rcpt_rejected_02',
        task_id='train_rat_02',
        prompt_text='claims : "2/4"',
        candidate_text='{"answer":"2/4"}',
        genome_id='genome_clean_v1',
        oracle=_oracle_single('canonical_rational', False, '{"answer":"2/4"}'),
        refusal_code='RATIONAL_NONCANONICAL',
    )

    holdout_prompts = ['factors : - - -', 'claims : "1/2"']
    holdout_task_ids = ['holdout_sign_01', 'holdout_rat_01']

    # Record negative control refusals
    refusal_controls: dict[str, str] = {}
    negative_cases = [
        (
            'holdout_prompt_overlap',
            [(w1, l1)],
            ['factors : - + -'],
            holdout_task_ids,
        ),
        (
            'holdout_task_id_overlap',
            [(w1, l1)],
            holdout_prompts,
            ['train_sign_01'],
        ),
        (
            'tainted_pciv_lineage',
            [(replace(w1, genome_id='genome_tainted_v1'), l1)],
            holdout_prompts,
            holdout_task_ids,
        ),
        (
            'uncertified_chosen_proposal',
            [(replace(w1, oracle=_oracle_single('exact_sign', False, '{"sign":"-1"}')), l1)],
            holdout_prompts,
            holdout_task_ids,
        ),
        (
            'protected_contract_fence_violation',
            [(replace(w1, candidate_text='{"other":"-1"}'), l1)],
            holdout_prompts,
            holdout_task_ids,
        ),
        (
            'thymus_admitted_guard_match',
            [(replace(w1, candidate_text='{"sign":"-1"} // TODO_STUB'), l1)],
            holdout_prompts,
            holdout_task_ids,
        ),
        (
            'alternative_valid_witness_in_rejected',
            [(w1, replace(l1, oracle=_oracle_single('exact_sign', True, '{"sign":"-1"}')))],
            holdout_prompts,
            holdout_task_ids,
        ),
    ]
    for label, pairs_arg, hp_arg, htid_arg in negative_cases:
        try:
            pipeline.extract_verified_triples(pairs_arg, holdout_prompts=hp_arg, holdout_task_ids=htid_arg)
            refusal_controls[label] = 'UNEXPECTED_PASS'
        except ValueError as exc:
            refusal_controls[label] = str(exc).split(':')[0]

    triples, holdout_sha = pipeline.extract_verified_triples(
        [(w1, l1), (w2, l2)],
        holdout_prompts=holdout_prompts,
        holdout_task_ids=holdout_task_ids,
    )
    dataset = pipeline.compile_dataset(triples, holdout_manifest_sha256=holdout_sha)

    model = PinnedEagerMicroCausalLM(tokenizer.vocab_size, gemma4_layout=True, seed=21)
    rev = 'd' * 40
    base_snapshot = {name: param.detach().clone() for name, param in model.named_parameters()}

    adapter, receipt = pipeline.train_dpo_lora_on_receipts(
        model,
        tokenizer,
        dataset,
        target_linear=model.lm_head,
        target_module_name='lm_head',
        base_model_id='google/gemma-4-9b-it',
        base_model_revision=rev,
        rank=4,
        alpha=Fraction(8),
        lr=0.2,
        steps=30,
        seed=42,
    )

    base_drift = sum(
        float((param.detach() - base_snapshot[name]).abs().max().item())
        for name, param in model.named_parameters()
    )
    random_ctrl = adapter.build_equal_norm_random_control(seed=77)

    def _eval_holdout_margin(active_adapter: LowRankWeightAdapterV1 | None) -> float:
        p_ids = torch.tensor([tokenizer.encode('factors : - - -', add_special_tokens=False)], dtype=torch.long)
        w_ids = tokenizer.encode('{"sign":"-1"}', add_special_tokens=False)
        l_ids = tokenizer.encode('{"sign":"+1"}', add_special_tokens=False)
        full_w = torch.cat([p_ids, torch.tensor([w_ids], dtype=torch.long)], dim=1)
        full_l = torch.cat([p_ids, torch.tensor([l_ids], dtype=torch.long)], dim=1)
        p_len = p_ids.shape[1]
        with torch.no_grad():
            if active_adapter is None:
                lp_w = torch.log_softmax(model(full_w).logits, dim=-1)
                lp_l = torch.log_softmax(model(full_l).logits, dim=-1)
            else:
                with active_adapter.attached_to(model.lm_head):
                    lp_w = torch.log_softmax(model(full_w).logits, dim=-1)
                    lp_l = torch.log_softmax(model(full_l).logits, dim=-1)
            score_w = sum(float(lp_w[0, p_len - 1 + i, tid].item()) for i, tid in enumerate(w_ids))
            score_l = sum(float(lp_l[0, p_len - 1 + i, tid].item()) for i, tid in enumerate(l_ids))
            return score_w - score_l

    holdout_base = _eval_holdout_margin(None)
    holdout_trained = _eval_holdout_margin(adapter)
    holdout_random = _eval_holdout_margin(random_ctrl)

    return {
        'seam_id': 'seam_5_weights_finetune_on_antibodies_from_receipts',
        'verified_triple_count': len(triples),
        'dataset_sha256': dataset.dataset_sha256,
        'holdout_manifest_sha256': dataset.holdout_manifest_sha256,
        'dataset_causal_witness_verified': verify_causal_witness(
            dataset.causal_witness, expected_dataset_sha256=dataset.dataset_sha256
        ),
        'negative_controls_and_refusals': refusal_controls,
        'dpo_lora_training_and_holdout_evaluation': {
            'base_model_param_max_drift': base_drift,
            'mean_dpo_margin_before': receipt.mean_dpo_margin_before,
            'mean_dpo_margin_after': receipt.mean_dpo_margin_after,
            'dpo_margin_improved': float(receipt.mean_dpo_margin_after) > float(receipt.mean_dpo_margin_before),
            'trained_lora_frobenius_norm': round(adapter.frobenius_norm(), 6),
            'random_control_lora_frobenius_norm': round(random_ctrl.frobenius_norm(), 6),
            'frobenius_norm_diff': round(abs(adapter.frobenius_norm() - random_ctrl.frobenius_norm()), 8),
            'holdout_margin_base': f'{holdout_base:.6f}',
            'holdout_margin_trained_lora': f'{holdout_trained:.6f}',
            'holdout_margin_equal_norm_random_lora': f'{holdout_random:.6f}',
            'trained_beats_random_on_holdout': holdout_trained > holdout_random,
            'trained_beats_base_on_holdout': holdout_trained > holdout_base,
        },
        'weight_adapter_receipt': receipt.to_dict(),
        'authority_effect': 'None',
    }


def build_five_seam_showcase_report() -> dict[str, Any]:
    tokenizer = FastOffsetTokenizer()
    seam1 = _run_seam1_showcase()
    seam2 = _run_seam2_showcase(tokenizer)
    seam3 = _run_seam3_showcase()
    seam4 = _run_seam4_showcase(tokenizer)
    seam5 = _run_seam5_showcase(tokenizer)

    return {
        'schema_version': 'pfp.benchmarks.five_seam_llm_mechanisms_showcase.v1',
        'status': 'offline_deterministic_open_weight_and_mechanism_showcase_not_live_frontier_campaign',
        'live_api_spend_usd': '0.000000',
        'authority_effect': 'None',
        'seams': {
            'seam_1_sampling_parameters': seam1,
            'seam_2_logit_and_grammar_decode': seam2,
            'seam_3_host_controlled_scratchpad': seam3,
            'seam_4_attention_heads_kv_and_residual_steering': seam4,
            'seam_5_weights_finetune_on_antibodies_from_receipts': seam5,
        },
        'claim_hygiene': {
            'supports': (
                'Deterministic execution, cryptographic receipt verification, and paired negative-control '
                'ablation across all five LLM intervention seams (sampling parameters, token-trie logit masking, '
                'C006 host scratchpad with AM-4/Treg loop breaking, eager 4D attention/head/KV/residual hooks '
                'across Llama/Qwen and Gemma 4 layouts, and DPO LoRA weight updates from verified PFP receipt '
                'triples) in this repository setting.'
            ),
            'does_not_support': (
                'Claims of universal accuracy gains on live frontier or open-weight checkpoints without a '
                'pinned held-out live campaign, or any claim that internal model interventions replace '
                'external Layer-3 HostOracleContext verification.'
            ),
            'narrowest_defensible_claim': (
                'Each of the five intervention seams is executable under AuthorityEffect: None with exact '
                'negative controls (certificate_first vs majority_vote, Layer-2 trie vs Layer-3 semantic check, '
                'bounded C006 ledger vs growing CoT, EIS two-signal attention gate + equal-norm random steering '
                'vector, and holdout-disjoint receipt-to-LoRA vs equal-Frobenius-norm random LoRA) checked by '
                'this test suite at USD 0.00 live API spend.'
            ),
            'next_test_needed': (
                'Run the 5-seam runner on a pinned local Gemma 4 checkpoint (e.g., google/gemma-4-9b-it in '
                'eager mode) over the 3-family algebraic pilot and the 4-task industry replacement suite '
                'under a pre-authorized WholeRunBudget.'
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=RESULTS_PATH, help='Output JSON path.')
    args = parser.parse_args(argv)

    report = build_five_seam_showcase_report()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(f'Wrote 5-seam showcase report to {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
