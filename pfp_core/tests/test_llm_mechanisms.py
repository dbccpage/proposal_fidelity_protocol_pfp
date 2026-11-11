"""Unit and adversarial falsification tests for all 5 LLM intervention seams (`pfp_core.llm_mechanisms`)."""
from __future__ import annotations

import json
from dataclasses import replace
from fractions import Fraction

import pytest
import torch

from eis.domain.value_objects import DetectorRule
from pciv.domain.causal_witness import seal_causal_witness
from pfp.domain.ports.decode_control_port import ControlKind, DecodeControlReceipt
from pfp_core.civilization import Lineage
from pfp_core.fidelity import HostOracleContext, ProtectedContract
from pfp_core.llm_mechanisms import (
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
from pfp_core.operad_pipe import quotient_workflows

# ============================================================================
# SEAM 1 TESTS: Sampling Parameters & WholeRunBudget
# ============================================================================


def test_seam1_zero_float_law_and_bounds() -> None:
    with pytest.raises(TypeError, match='ZERO_FLOAT_LAW'):
        SamplingConfigV1(temperature=0.7)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match='ZERO_FLOAT_LAW'):
        SamplingConfigV1(top_p=0.95)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match='ZERO_FLOAT_LAW'):
        SamplingConfigV1(temperature=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match='BOUNDED_TEMPERATURE_REQUIRED'):
        SamplingConfigV1(temperature=Fraction(5, 2))
    with pytest.raises(ValueError, match='BOUNDED_TOP_P_REQUIRED'):
        SamplingConfigV1(top_p=Fraction(0))
    with pytest.raises(ValueError, match='BOUNDED_N_SAMPLES_REQUIRED'):
        SamplingConfigV1(n_samples=0)
    with pytest.raises(ValueError, match='UNKNOWN_SELECTION_RULE'):
        SamplingConfigV1(selection_rule='blind_trust')


def test_seam1_zero_temp_replicate_quotient_collapse() -> None:
    cfg_1 = SamplingConfigV1(temperature=Fraction(0), n_samples=1, selection_rule='certificate_first')
    cfg_5 = SamplingConfigV1(temperature=Fraction(0), n_samples=5, selection_rule='certificate_first')
    assert not cfg_1.has_redundant_zero_temp_replicates
    assert cfg_5.has_redundant_zero_temp_replicates
    assert cfg_5.effective_draws == 1

    classes = quotient_workflows(
        {
            't0_n1': cfg_1.as_typed_ops('seed_digest_1'),
            't0_n5': cfg_5.as_typed_ops('seed_digest_1'),
        }
    )
    assert len(classes) == 1
    assert next(iter(classes.values())) == ['t0_n1', 't0_n5']


def test_seam1_certificate_first_beats_uncertified_majority_mode() -> None:
    draws = [
        ('{"answer":"2/4"}', 10, 20, 8),  # draw 0: uncanonical (modal error)
        ('{"answer":"2/4"}', 10, 20, 8),  # draw 1: uncanonical (modal error)
        ('{"answer":"2/4"}', 10, 20, 8),  # draw 2: uncanonical (modal error)
        ('{"answer":"1/2"}', 10, 20, 8),  # draw 3: canonical & host-certified
    ]

    def _sampler(idx: int, _temp: Fraction, _seed: int) -> tuple[str, int, int, int]:
        return draws[idx]

    def _checker(reply: str) -> HostOracleContext:
        ctx = HostOracleContext()
        ctx.record('canonical_rational', reply == '{"answer":"1/2"}', reply)
        return ctx

    maj_cfg = SamplingConfigV1(
        temperature=Fraction(7, 10),
        top_p=Fraction(9, 10),
        n_samples=4,
        seed=11,
        selection_rule='majority_vote',
    )
    cert_cfg = SamplingConfigV1(
        temperature=Fraction(7, 10),
        top_p=Fraction(9, 10),
        n_samples=4,
        seed=11,
        selection_rule='certificate_first',
    )

    maj_out = evaluate_sampling_seam(
        maj_cfg, task_id='t_rat', prompt_text='reduce 2/4', sampler=_sampler, host_checker=_checker
    )
    cert_out = evaluate_sampling_seam(
        cert_cfg, task_id='t_rat', prompt_text='reduce 2/4', sampler=_sampler, host_checker=_checker
    )

    assert maj_out.status == 'DELIVERED_UNCERTIFIED'
    assert maj_out.selected_reply == '{"answer":"2/4"}'
    assert not maj_out.majority_is_certified

    assert cert_out.status == 'HOST_CERTIFIED'
    assert cert_out.selected_reply == '{"answer":"1/2"}'
    assert cert_out.selected_index == 3
    assert cert_out.certified_draw_indices == (3,)
    assert cert_out.budget_summary['spent_microusd'] == 40
    assert cert_out.authority_effect == 'None'


def test_seam1_refuses_when_no_draw_certified_or_budget_exceeded() -> None:
    def _bad_sampler(_idx: int, _temp: Fraction, _seed: int) -> tuple[str, int, int, int]:
        return ('{"answer":"wrong"}', 30, 15, 5)

    def _checker(reply: str) -> HostOracleContext:
        ctx = HostOracleContext()
        ctx.record('exact_match', reply == '{"answer":"right"}', reply)
        return ctx

    cfg = SamplingConfigV1(temperature=Fraction(1, 2), n_samples=3, selection_rule='certificate_first')
    no_cert = evaluate_sampling_seam(
        cfg, task_id='t_none', prompt_text='prompt', sampler=_bad_sampler, host_checker=_checker, cap_microusd=500
    )
    assert no_cert.status == 'NO_CERTIFIED_SAMPLE'
    assert no_cert.selected_reply is None

    budget_refused = evaluate_sampling_seam(
        cfg, task_id='t_cap', prompt_text='prompt', sampler=_bad_sampler, host_checker=_checker, cap_microusd=50
    )
    assert budget_refused.status == 'BUDGET_REFUSED'
    assert budget_refused.draws_executed == 1


# ============================================================================
# SEAM 2 TESTS: Logit & Grammar-Constrained Decoding (Layer 2 vs Layer 3)
# ============================================================================


def test_seam2_verify_decode_receipt_exact_refusal_modes() -> None:
    valid_carrier = DecodeControlReceipt(
        receipt_id='r1',
        case_id='c1',
        control_kind=ControlKind.CARRIER_MASK.value,
        output_tokens=(3, 4, 5),
        allowed_tokens=(3, 4, 5, 6),
        honored=True,
    )
    assert verify_decode_receipt_exact(valid_carrier)['status'] == 'PASS'

    violated_carrier = replace(valid_carrier, output_tokens=(3, 99))
    res_viol = verify_decode_receipt_exact(violated_carrier)
    assert res_viol['status'] == 'REFUSAL'
    assert res_viol['refusal_code'] == 'CARRIER_CONSTRAINT_VIOLATED'

    extreme_bias = DecodeControlReceipt(
        receipt_id='r2',
        case_id='c1',
        control_kind=ControlKind.LOGIT_BIAS.value,
        output_tokens=(3,),
        logit_biases=((3, 1500),),
    )
    res_bias = verify_decode_receipt_exact(extreme_bias)
    assert res_bias['status'] == 'REFUSAL'
    assert res_bias['refusal_code'] == 'LOGIT_BIAS_EXCEEDS_CEILING'

    missing_hash = DecodeControlReceipt(
        receipt_id='r3',
        case_id='c1',
        control_kind=ControlKind.JSON_SCHEMA.value,
        output_tokens=(3,),
        grammar_sha256=None,
    )
    assert verify_decode_receipt_exact(missing_hash)['refusal_code'] == 'MISSING_GRAMMAR_HASH'

    bad_hash = replace(missing_hash, grammar_sha256='not_a_64_char_hex_hash')
    assert verify_decode_receipt_exact(bad_hash)['refusal_code'] == 'INVALID_GRAMMAR_HASH'

    bad_auth = replace(valid_carrier, authority_effect='Elevated')
    assert verify_decode_receipt_exact(bad_auth)['refusal_code'] == 'AUTHORITY_EFFECT_NON_NONE'


def test_seam2_layer2_trie_eliminates_syntax_errors_but_layer3_catches_wrong_math() -> None:
    tokenizer = FastOffsetTokenizer()
    right_reply = '{"status":"SOLVED","kind":"product_sign","answer":{"sign":"-1","negative_count":"3"}}'
    wrong_on_grammar_reply = '{"status":"SOLVED","kind":"product_sign","answer":{"sign":"+1","negative_count":"2"}}'
    allowed_language = [right_reply, wrong_on_grammar_reply]

    controller = LogitGrammarControllerV1(allowed_language, tokenizer)

    def _host_checker(decoded: str) -> tuple[HostOracleContext, bool]:
        ctx = HostOracleContext()
        try:
            obj = json.loads(decoded)
            wire_ok = isinstance(obj, dict) and obj.get('status') == 'SOLVED'
        except json.JSONDecodeError:
            obj = {}
            wire_ok = False
        ctx.record('wire_json_valid', wire_ok, decoded)
        ctx.record(
            'exact_product_sign',
            bool(wire_ok and obj.get('answer') == {'sign': '-1', 'negative_count': '3'}),
            decoded,
        )
        return ctx, wire_ok

    # On-grammar but mathematically wrong candidate: passes Layer 2 & wire check, refused by Layer 3!
    wrong_tokens = tokenizer.encode(wrong_on_grammar_reply, add_special_tokens=False)
    eval_wrong = controller.evaluate_candidate(
        case_id='ps_wrong',
        request_text='factors: - + - -',
        output_tokens=wrong_tokens,
        control_kind=ControlKind.JSON_SCHEMA,
        host_checker=_host_checker,
    )
    assert eval_wrong.layer2_verdict['status'] == 'PASS'
    assert eval_wrong.wire_syntax_valid is True
    assert eval_wrong.semantically_certified is False
    assert eval_wrong.layer3_oracle['certified_predicates']['exact_product_sign'] is False

    # On-grammar and mathematically right candidate: passes both Layer 2 and Layer 3
    right_tokens = tokenizer.encode(right_reply, add_special_tokens=False)
    eval_right = controller.evaluate_candidate(
        case_id='ps_right',
        request_text='factors: - + - -',
        output_tokens=right_tokens,
        control_kind=ControlKind.JSON_SCHEMA,
        host_checker=_host_checker,
    )
    assert eval_right.layer2_verdict['status'] == 'PASS'
    assert eval_right.wire_syntax_valid is True
    assert eval_right.semantically_certified is True


# ============================================================================
# SEAM 3 TESTS: Host-Controlled Scratchpad (U12 Ledger + AM-4 + Treg)
# ============================================================================


def test_seam3_am4_stationary_attractor_and_treg_circuit_breaker() -> None:
    # 1. Round-5 K4 witness: RepeatedCut on turn 11 matching turn 9 (state_A, move_X)
    cut_history = [
        ScratchTurnRecordV1(
            turn=9,
            host_state_digest='state_A',
            canonical_move_digest='move_X',
            move_kind='CUT',
            outcome='IdempotentStationary',
        ),
        ScratchTurnRecordV1(
            turn=10,
            host_state_digest='state_A',
            canonical_move_digest='move_Y',
            move_kind='VERIFY',
            outcome='IdempotentStationary',
        ),
        ScratchTurnRecordV1(
            turn=11,
            host_state_digest='state_A',
            canonical_move_digest='move_X',
            move_kind='CUT',
            outcome='IdempotentStationary',
        ),
    ]
    rep_cut = detect_stationary_attractor_exact(cut_history)
    assert rep_cut.escalate is True
    assert rep_cut.detected_attractor == 'RepeatedCut'
    assert rep_cut.findings[0]['prior_turn'] == 9
    assert rep_cut.findings[0]['current_turn'] == 11

    # 2. RepeatedSettledAssert resets on AdmittedDescent
    assert_history = [
        ScratchTurnRecordV1(
            turn=1,
            host_state_digest='s0',
            canonical_move_digest='m1',
            move_kind='ASSERT',
            target_variable='a->b',
            outcome='IdempotentStationary',
        ),
        ScratchTurnRecordV1(
            turn=2,
            host_state_digest='s0',
            canonical_move_digest='m1',
            move_kind='ASSERT',
            target_variable='a->b',
            outcome='IdempotentStationary',
        ),
        ScratchTurnRecordV1(
            turn=3, host_state_digest='s0', canonical_move_digest='m2', move_kind='CUT', outcome='AdmittedDescent'
        ),
        ScratchTurnRecordV1(
            turn=4,
            host_state_digest='s1',
            canonical_move_digest='m1',
            move_kind='ASSERT',
            target_variable='a->b',
            outcome='IdempotentStationary',
        ),
    ]
    rep_reset = detect_stationary_attractor_exact(assert_history)
    assert rep_reset.escalate is False

    # 3. Treg suspends escalation when findings exceed treg_firing_ceiling
    noisy_history = [
        ScratchTurnRecordV1(
            turn=t, host_state_digest='s0', canonical_move_digest='m1', move_kind='CUT', outcome='IdempotentStationary'
        )
        for t in range(1, 7)
    ]
    rep_treg = detect_stationary_attractor_exact(noisy_history, treg_firing_ceiling=3)
    assert len(rep_treg.findings) == 5
    assert rep_treg.treg_suspended is True
    assert rep_treg.escalate is False


def test_seam3_k4_coboundary_repair_and_bounded_prompt_size() -> None:
    edges = [('a', 'b'), ('b', 'c'), ('c', 'a'), ('a', 'd'), ('b', 'd'), ('c', 'd')]
    initial_claims = {'a->b': 1, 'b->c': 2, 'c->a': 0, 'a->d': -2, 'b->d': 0, 'c->d': -3}
    cycles = {
        'c1': [('a', 'b', 1), ('b', 'c', 1), ('c', 'a', 1)],
        'c2': [('a', 'b', 1), ('b', 'd', 1), ('a', 'd', -1)],
        'c3': [('b', 'c', 1), ('c', 'd', 1), ('b', 'd', -1)],
    }
    chords = ['c->a', 'b->d', 'c->d']

    session = HostScratchSessionV1(
        board_id='k4_b1_3',
        edges=edges,
        initial_claims=initial_claims,
        fundamental_cycles=cycles,
        chords=chords,
        fuel=10,
    )
    assert session.compute_phi1() == 7  # |3| + |3| + |-1| = 7

    # Stationary move twice triggers AM-4 escalation
    s1 = session.apply_cut(initial_claims, rationale='thinking step 1 with long chain of thought' * 4)
    s2 = session.apply_cut(initial_claims, rationale='thinking step 2 with long chain of thought' * 4)
    assert s1['am4_escalate'] is False
    assert s2['am4_escalate'] is True
    assert s2['am4_detected'] == 'RepeatedCut'

    # Now descend across the 3 chords: c->a = -3, b->d = -3, c->d = -5
    step1 = dict(initial_claims, **{'c->a': -3})
    r1 = session.apply_cut(step1, rationale='repair chord c->a to -3' * 4)
    assert r1['outcome'] == 'AdmittedDescent'
    assert r1['phi1'] == 4

    step2 = dict(step1, **{'b->d': -3, 'c->d': -6})
    r2 = session.apply_cut(step2, rationale='repair chord b->d to -3 and adjust c->d' * 4)
    assert r2['outcome'] == 'AdmittedDescent'
    assert r2['phi1'] == 1

    step3 = dict(step2, **{'c->d': -5})
    r3 = session.apply_cut(step3, rationale='repair chord c->d to -5 for zero defect' * 4)
    assert r3['outcome'] == 'AdmittedDescent'
    assert r3['phi1'] == 0

    # Verify bounded ledger prompt vs growing CoT prompt
    ledger_json = json.loads(session.render_ledger_prompt())
    assert len(ledger_json['last_two_turns']) == 2
    assert len(session.render_ledger_prompt()) < len(session.render_cot_prompt())

    #Mutated potential is refused; exact potential is certified
    bad_verdict = session.verify_zero_defect({'a': 0, 'b': 1, 'c': 3, 'd': 99})
    assert bad_verdict['status'] == 'REFUSED'
    assert bad_verdict['refusal'] == 'POTENTIAL_COBOUNDARY_MISMATCH'

    good_verdict = session.verify_zero_defect({'a': 0, 'b': 1, 'c': 3, 'd': -2})
    assert good_verdict['status'] == 'SOLVED'
    assert good_verdict['terminal'] == 'ACCEPTED_ZERO_DEFECT'


# ============================================================================
# SEAM 4 TESTS: Open-Weight Attention / Heads / Residual / KV (Llama + Gemma 4)
# ============================================================================


@pytest.mark.parametrize('gemma4_layout', [False, True])
def test_seam4_open_weight_interventions_across_llama_and_gemma4_layouts(gemma4_layout: bool) -> None:
    tokenizer = FastOffsetTokenizer()
    model = PinnedEagerMicroCausalLM(tokenizer.vocab_size, gemma4_layout=gemma4_layout, seed=13)
    rev = 'a' * 40
    runner = OpenWeightMechanismRunnerV1(
        model,
        tokenizer,
        model_id='google/gemma-4-9b-it' if gemma4_layout else 'Qwen/Qwen2.5-7B-Instruct',
        revision=rev,
    )
    text = 'factors : - + - fluff noise'
    fluff_start = text.index('fluff')
    carrier_pos = runner.carrier_positions(text, [(0, fluff_start)])
    assert len(carrier_pos) >= 3

    base_logits, readouts0 = runner.forward(text)
    assert readouts0 == []

    # 1. Attention 4D mask intervention: delta=0 identity, delta=6 shifts logits & cleans up
    null_attn_logits, attn_r0 = runner.forward(text, attention={'layers': [0, 1], 'positions': carrier_pos, 'delta': 0})
    assert torch.allclose(base_logits, null_attn_logits, atol=1e-6)
    assert all(r['changed_entries'] == 0 for r in attn_r0)

    shifted_attn_logits, attn_r1 = runner.forward(
        text, attention={'layers': [0, 1], 'positions': carrier_pos, 'delta': 6}
    )
    assert not torch.allclose(base_logits, shifted_attn_logits)
    assert all(r['changed_entries'] > 0 for r in attn_r1)

    # 2. Head scaling/ablation + hook cleanup on exception
    null_head_logits, _ = runner.forward(text, heads={'layer': 0, 'heads': [0], 'alpha': 1.0})
    assert torch.allclose(base_logits, null_head_logits, atol=1e-6)

    ablated_head_logits, head_r1 = runner.forward(text, heads={'layer': 0, 'heads': [0], 'alpha': 0.0})
    assert not torch.allclose(base_logits, ablated_head_logits)
    assert head_r1[0]['changed_norm'] > 0.0

    with (
        pytest.raises(RuntimeError, match='simulated_abort'),
        runner.interventions(heads={'layer': 0, 'heads': [0], 'alpha': 0.0}),
    ):
        raise RuntimeError('simulated_abort')
    after_abort_logits, _ = runner.forward(text)
    assert torch.allclose(base_logits, after_abort_logits, atol=1e-6)

    # 3. Clean-to-corrupted head patching
    clean_text = 'factors : - + -'
    clean_head = runner.capture(clean_text, layer=1, kind='head', head=0)
    patched_logits, patch_r = runner.forward(text, patch={'layer': 1, 'head': 0, 'value': clean_head})
    assert not torch.allclose(base_logits, patched_logits)
    assert patch_r[0]['changed_norm'] > 0.0

    # 4. Contrastive residual steering vs equal-norm orthogonal random vector control
    r_clean = runner.capture(clean_text, layer=1, kind='residual')[0]
    r_noisy = runner.capture(text, layer=1, kind='residual')[0]
    steer_vec = r_clean - r_noisy
    rand_vec = runner.build_equal_norm_random_vector(steer_vec, seed=99)
    assert abs(float(steer_vec.norm().item()) - float(rand_vec.norm().item())) < 1e-5
    assert abs(float(torch.dot(steer_vec, rand_vec).item())) < 1e-4

    steered_logits, _ = runner.forward(text, residual={'layer': 1, 'vector': steer_vec, 'alpha': 1.5})
    random_logits, _ = runner.forward(text, residual={'layer': 1, 'vector': rand_vec, 'alpha': 1.5})
    assert not torch.allclose(steered_logits, random_logits)

    # 5. KV cache parity: incremental cache matches full recomputation token-for-token
    parity_full = runner.cache_parity(text, steps=4)
    assert parity_full['token_exact'] is True
    parity_pruned = runner.cache_parity(text, steps=4, keep_positions=list(carrier_pos))
    assert parity_pruned['kept_positions'] == list(carrier_pos)


def test_seam4_eis_two_signal_gate_prevents_self_authorizing_attention_mask() -> None:
    # Self-authorizing observer ('attention_probe') must be refused with TWO_SIGNAL_COLLAPSE
    collapsed = evaluate_attention_intervention_gate(
        distractor_mass=Fraction(3, 10),
        danger_tau=Fraction(1, 20),
        host_refusal_on_unmasked=True,
        host_observer_id='attention_probe',
    )
    assert collapsed['refusal_code'] == 'TWO_SIGNAL_COLLAPSE'
    assert collapsed['authorize_mask'] is False

    # Signal 1 only (high distractor mass, no host refusal on unmasked turn) -> diagnostic only
    s1_only = evaluate_attention_intervention_gate(
        distractor_mass=Fraction(3, 10),
        danger_tau=Fraction(1, 20),
        host_refusal_on_unmasked=False,
        host_observer_id='host.public_smoke',
    )
    assert s1_only['disposition'] == 'DIAGNOSTIC_OR_NORMALIZE'
    assert s1_only['authorize_mask'] is False

    # Signal 1 + independent Host Signal 2 -> HOLD_OR_REPAIR (mask authorized)
    both = evaluate_attention_intervention_gate(
        distractor_mass=Fraction(3, 10),
        danger_tau=Fraction(1, 20),
        host_refusal_on_unmasked=True,
        host_observer_id='host.public_smoke',
    )
    assert both['disposition'] == 'HOLD_OR_REPAIR'
    assert both['refusal_code'] is None
    assert both['authorize_mask'] is True


# ============================================================================
# SEAM 5 TESTS: Weights (`finetune_on_antibodies` from PFP Verified Receipts)
# ============================================================================


def _make_oracle(passed: bool, pred_name: str, evidence_text: str) -> HostOracleContext:
    ctx = HostOracleContext()
    ctx.record(pred_name, passed, evidence_text)
    return ctx


def test_seam5_refuses_holdout_contamination_tainted_lineage_and_multiplicity_violation() -> None:
    lineage = Lineage()
    lineage.add('seed_bad')
    lineage.add('genome_tainted')
    lineage.derive('seed_bad', 'genome_tainted', 'mut_1')
    lineage.add('seed_good')
    lineage.add('genome_clean')
    lineage.derive('seed_good', 'genome_clean', 'mut_2')
    thymus_rule = DetectorRule(rule_id='r_todo', target_epitope='code', match_pattern='TODO_HACK')

    pipeline = ReceiptToWeightPipelineV1(
        lineage=lineage,
        tainted_seeds={'seed_bad'},
        thymus_rules=[thymus_rule],
        self_panel=['clean_code_sample'],
    )

    good_chosen = CandidateRunReceiptV1(
        receipt_id='rcpt_w1',
        task_id='train_1',
        prompt_text='factors : - + -',
        candidate_text='{"sign":"-1"}',
        genome_id='genome_clean',
        oracle=_make_oracle(True, 'exact_sign', '{"sign":"-1"}'),
        contract=ProtectedContract.fence_markers('{"sign":"-1"}', '{"sign":', '}'),
    )
    good_rejected = CandidateRunReceiptV1(
        receipt_id='rcpt_l1',
        task_id='train_1',
        prompt_text='factors : - + -',
        candidate_text='{"sign":"+1"}',
        genome_id='genome_clean',
        oracle=_make_oracle(False, 'exact_sign', '{"sign":"+1"}'),
        refusal_code='SIGN_MISMATCH',
    )

    # 1. Hold-out prompt contamination refusal
    with pytest.raises(ValueError, match='HOLDOUT_CONTAMINATION_REFUSAL'):
        pipeline.extract_verified_triples(
            [(good_chosen, good_rejected)],
            holdout_prompts=['factors : - + -'],
        )

    # 2. Hold-out task_id contamination refusal
    with pytest.raises(ValueError, match='HOLDOUT_CONTAMINATION_REFUSAL'):
        pipeline.extract_verified_triples(
            [(good_chosen, good_rejected)],
            holdout_prompts=['factors : + + -'],
            holdout_task_ids=['train_1'],
        )

    # 3. Tainted lineage refusal
    tainted_chosen = replace(good_chosen, genome_id='genome_tainted')
    with pytest.raises(ValueError, match='TAINTED_LINEAGE_RECEIPT_REFUSED'):
        pipeline.extract_verified_triples(
            [(tainted_chosen, good_rejected)],
            holdout_prompts=['factors : + + -'],
        )

    # 4. Uncertified chosen proposal refusal
    uncert_chosen = replace(good_chosen, oracle=_make_oracle(False, 'exact_sign', '{"sign":"-1"}'))
    with pytest.raises(ValueError, match='UNCERTIFIED_CHOSEN_PROPOSAL_REFUSED'):
        pipeline.extract_verified_triples(
            [(uncert_chosen, good_rejected)],
            holdout_prompts=['factors : + + -'],
        )

    # 4b. ProtectedContract fence violation on chosen
    fence_broken_chosen = replace(good_chosen, candidate_text='{"wrong_key":"-1"}')
    with pytest.raises(ValueError, match='CHOSEN_PROTECTED_FENCE_VIOLATION'):
        pipeline.extract_verified_triples(
            [(fence_broken_chosen, good_rejected)],
            holdout_prompts=['factors : + + -'],
        )

    # 5. Thymus guard failure on chosen
    guard_chosen = replace(good_chosen, candidate_text='{"sign":"-1"} // TODO_HACK')
    with pytest.raises(ValueError, match='CHOSEN_FAILED_ADMITTED_GUARD'):
        pipeline.extract_verified_triples(
            [(guard_chosen, good_rejected)],
            holdout_prompts=['factors : + + -'],
        )

    # 6. Witness multiplicity guard: alternative valid witness MUST NOT be rejected!
    alt_valid_rejected = replace(
        good_rejected,
        candidate_text='{"sign":"-1","equivalent":true}',
        oracle=_make_oracle(True, 'exact_sign', '{"sign":"-1","equivalent":true}'),
    )
    with pytest.raises(ValueError, match='ALTERNATIVE_VALID_WITNESS_NOT_REJECTED'):
        pipeline.extract_verified_triples(
            [(good_chosen, alt_valid_rejected)],
            holdout_prompts=['factors : + + -'],
        )


def test_seam5_end_to_end_dpo_lora_training_freezes_base_and_beats_random_adapter() -> None:
    tokenizer = FastOffsetTokenizer()
    model = PinnedEagerMicroCausalLM(tokenizer.vocab_size, gemma4_layout=True, seed=21)
    rev = 'b' * 40

    # Snapshot every base model parameter before training
    base_snapshot = {name: param.detach().clone() for name, param in model.named_parameters()}

    pipeline = ReceiptToWeightPipelineV1()
    train_pairs = [
        (
            CandidateRunReceiptV1(
                receipt_id='rcpt_w1',
                task_id='train_sign_1',
                prompt_text='factors : - + -',
                candidate_text='{"sign":"-1"}',
                genome_id='g_clean',
                oracle=_make_oracle(True, 'exact_sign', '{"sign":"-1"}'),
            ),
            CandidateRunReceiptV1(
                receipt_id='rcpt_l1',
                task_id='train_sign_1',
                prompt_text='factors : - + -',
                candidate_text='{"sign":"+1"}',
                genome_id='g_clean',
                oracle=_make_oracle(False, 'exact_sign', '{"sign":"+1"}'),
                refusal_code='SIGN_MISMATCH',
            ),
        ),
        (
            CandidateRunReceiptV1(
                receipt_id='rcpt_w2',
                task_id='train_rat_2',
                prompt_text='claims : "2/4"',
                candidate_text='{"answer":"1/2"}',
                genome_id='g_clean',
                oracle=_make_oracle(True, 'canonical_rational', '{"answer":"1/2"}'),
            ),
            CandidateRunReceiptV1(
                receipt_id='rcpt_l2',
                task_id='train_rat_2',
                prompt_text='claims : "2/4"',
                candidate_text='{"answer":"2/4"}',
                genome_id='g_clean',
                oracle=_make_oracle(False, 'canonical_rational', '{"answer":"2/4"}'),
                refusal_code='RATIONAL_NONCANONICAL',
            ),
        ),
    ]
    holdout_prompts = ['factors : - - -', 'claims : "1/2"']

    triples, holdout_sha = pipeline.extract_verified_triples(
        train_pairs,
        holdout_prompts=holdout_prompts,
        holdout_task_ids=['holdout_sign_1', 'holdout_rat_1'],
    )
    dataset = pipeline.compile_dataset(triples, holdout_manifest_sha256=holdout_sha)
    assert verify_causal_witness(dataset.causal_witness) is True

    # Tampered causal witness (bound to a different dataset_sha256) must be rejected by trainer
    tampered_dataset = replace(
        dataset,
        causal_witness=seal_causal_witness({'dataset_sha256': '0' * 64}),
    )
    with pytest.raises(ValueError, match='INVALID_DATASET_CAUSAL_WITNESS'):
        pipeline.train_dpo_lora_on_receipts(
            model,
            tokenizer,
            tampered_dataset,
            target_linear=model.lm_head,
            base_model_id='google/gemma-4-9b-it',
            base_model_revision=rev,
        )

    adapter, receipt = pipeline.train_dpo_lora_on_receipts(
        model,
        tokenizer,
        dataset,
        target_linear=model.lm_head,
        base_model_id='google/gemma-4-9b-it',
        base_model_revision=rev,
        rank=4,
        alpha=Fraction(8),
        lr=0.2,
        steps=30,
        seed=42,
    )

    # 1. Base model weights must have 0.0 parameter drift
    for name, param in model.named_parameters():
        assert torch.equal(param, base_snapshot[name]), f'Base parameter {name} mutated!'

    # 2. DPO preference margin must strictly increase
    margin_before = float(receipt.mean_dpo_margin_before)
    margin_after = float(receipt.mean_dpo_margin_after)
    assert margin_after > margin_before
    assert receipt.authority_effect == 'None'

    # 3. Equal-Frobenius-norm random adapter control must match norm and lose to receipt-trained adapter
    random_ctrl = adapter.build_equal_norm_random_control(seed=77)
    assert abs(adapter.frobenius_norm() - random_ctrl.frobenius_norm()) < 1e-5

    def _holdout_margin(active_adapter: LowRankWeightAdapterV1) -> float:
        p_ids = torch.tensor([tokenizer.encode('factors : - - -', add_special_tokens=False)], dtype=torch.long)
        w_ids = tokenizer.encode('{"sign":"-1"}', add_special_tokens=False)
        l_ids = tokenizer.encode('{"sign":"+1"}', add_special_tokens=False)
        with torch.no_grad(), active_adapter.attached_to(model.lm_head):
            full_w = torch.cat([p_ids, torch.tensor([w_ids], dtype=torch.long)], dim=1)
            full_l = torch.cat([p_ids, torch.tensor([l_ids], dtype=torch.long)], dim=1)
            lp_w = torch.log_softmax(model(full_w).logits, dim=-1)
            lp_l = torch.log_softmax(model(full_l).logits, dim=-1)
            p_len = p_ids.shape[1]
            score_w = sum(float(lp_w[0, p_len - 1 + i, tid].item()) for i, tid in enumerate(w_ids))
            score_l = sum(float(lp_l[0, p_len - 1 + i, tid].item()) for i, tid in enumerate(l_ids))
            return score_w - score_l

    assert _holdout_margin(adapter) > _holdout_margin(random_ctrl)
