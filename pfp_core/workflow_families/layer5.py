"""Layer 5 families: arm controls, staged guards, authority and gate audits, commit-reveal."""
from __future__ import annotations

from .base import HostedFamily, digest, spec_from
from .exact import commitment
from .registry import register

# ---------------------------------------------------------------- WF12

@register
class MechanismControlArms(HostedFamily):
    """WF12. Run a mechanism arm against matched null and random controls on the same items.

    Items are integer sums graded by the host. The paired effect is
    ``d_i = 1[pass(B, i)] - 1[pass(A, i)]``; the proposer's arm ranks are a
    potential on the arm-comparison graph, accepted iff its coboundary equals
    every paired total, which is invariant under ``r -> r + c``. Controls must be
    matched first: a zero null vector and a random vector with the mechanism's
    exact squared norm. The Rust host checks all of it.
    """
    spec = spec_from('WF12', 'Mechanism-control arms', 5, ['WF6', 'WF3'], 'Sweep',
                     'integer_rank_difference_certificate', 'wf12_mechanism_control_arms')

    def fixtures(self):
        task = {'statement': 'Sum each item. The arm note is the only thing that changes.',
                'items': [{'id': k, 'values': v} for k, v in enumerate([[1, 2], [3, 4], [5, 5], [2, 7]])],
                'mechanism_vector': [3, 4, 0], 'null_control_vector': [0, 0, 0], 'random_control_vector': [0, 0, 5]}
        arms = [{'answers': [3, 7, 0, 0]}, {'answers': [3, 7, 10, 9]}, {'answers': [3, 0, 0, 0]},
                {'answers': [3, 7, 10, 0]}]
        shifted = {'ranks': {'baseline': 12, 'mechanism': 14, 'null_control': 11, 'random_control': 13}}
        inflated = {'ranks': {'baseline': 2, 'mechanism': 6, 'null_control': 1, 'random_control': 3}}
        unmatched = {**task, 'random_control_vector': [1, 1, 1]}
        return {
            'gauge_shifted_ranks_certified': ({'task': task, 'replies': [*arms, shifted]}, 'HOST_CERTIFIED'),
            'inflated_mechanism_effect': ({'task': task, 'replies': [*arms, inflated]}, 'REFUSED'),
            'random_control_norm_differs': ({'task': unmatched, 'replies': [*arms, shifted]}, 'REFUSED'),
            'arm_on_different_items': ({'task': task, 'replies': [arms[0], {'answers': [3, 7, 10]}, *arms[2:],
                                                                  shifted]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF36

@register
class GuardedStagedSlotMaterialisation(HostedFamily):
    """WF36. Stage 1 fills typed cochain slots; a complete guard with one retry gates stage 2.

    Edge values on a graph are partly fixed, partly slots. The syndrome
    ``r = S c`` over the full cycle matrix is the single object used for the
    verdict, the retry prompt and the audit. Stage 2 must give a potential with
    ``delta phi = c``. Abstention is accepted only when the rank test shows no
    filling exists; a guard over a strict subset of cycles is refused with a
    false-green kernel witness. The Rust host checks all of it.
    """
    spec = spec_from('WF36', 'Guarded staged slot materialisation', 5, ['WF8'], 'WF8', 'exact_cochain_check',
                     'wf36_guarded_staged_slot_materialisation')

    def fixtures(self):
        base = {'statement': 'Fill the null edge slots so every cycle sums to zero, then give a potential.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], 'values': [1, 2, None, 1, None]}
        blocked = {**base, 'values': [1, 2, 0, None, None]}
        partial = {**base, 'guard_rows': [0]}
        good, near = {'slots': {'2': -3, '4': -4}}, {'slots': {'2': -3, '4': -3}}
        phi = {'potential': [0, 1, 3, 4]}
        return {
            'materialised_first_try': ({'task': base, 'replies': [good, phi]}, 'HOST_CERTIFIED'),
            'repaired_from_shared_syndrome': ({'task': base, 'replies': [near, good, phi]}, 'HOST_CERTIFIED'),
            'abstain_on_closed_nonexact_cycle': ({'task': blocked, 'replies': [{'abstain': True}]}, 'TYPED_REFUSAL'),
            'partial_guard_false_green': ({'task': partial, 'replies': []}, 'REFUSED'),
            'lazy_false_abstention': ({'task': base, 'replies': [{'abstain': True}]}, 'REFUSED'),
            'guard_red_after_retry': ({'task': base, 'replies': [near, near, phi]}, 'REFUSED'),
            'stage2_drifts_from_slots': ({'task': base, 'replies': [good, {'potential': [0, 1, 3, 5]}]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF39

@register
class AuthorityFirewallGate(HostedFamily):
    """WF39. Accept a reply only when every guard in the vector passes.

    The task fixes the public cochain; the reply supplies only the witness
    potential and a receipt. The host replays the registered verifier on the
    task's own edges and values and checks: payload bound to the task, authority effect 'None' with no
    extra fields, verifier registered, witness bound to the exact payload hash,
    replay hash, replay match, zero defect and a fresh nonce. A failed guard
    becomes residual evidence; self-certifying or escalating receipts are refused.
    The Rust host checks all of it.
    """
    spec = spec_from('WF39', 'Authority firewall gate', 5, ['WF1', 'WF23'], None, 'authority_guard_vector',
                     'wf39_authority_firewall_gate')

    def fixtures(self):
        good = {'edges': [[0, 1], [1, 2], [2, 0]], 'c': [1, 1, -2], 'phi': [0, 1, 2]}
        bad = {**good, 'phi': [0, 1, 3]}
        trivial = {'edges': [[0, 1]], 'c': [0], 'phi': [0, 0]}
        replays = {'good': {'residual': [0, 0, 0], 'defect': 0}, 'bad': {'residual': [0, -1, 1], 'defect': 2},
                   'trivial': {'residual': [0], 'defect': 0}}
        task = {'statement': 'Give a potential phi for the public cochain and a receipt from the registered verifier.',
                'nonce': 'run-0042', 'registered_verifiers': ['exact.cochain_residual.v1'],
                'edges': good['edges'], 'c': good['c']}

        def packet(payload, replay, bound=None, **over):
            receipt = {'authority_effect': 'None', 'verifier_id': 'exact.cochain_residual.v1',
                       'payload_sha256': digest(bound or payload), 'replay_sha256': digest(replay),
                       'claimed': replay, 'nonce': 'run-0042', **over}
            return {'task': task, 'replies': [{'payload': payload, 'receipt': receipt}]}
        return {
            'all_guards_pass': (packet(good, replays['good']), 'HOST_CERTIFIED'),
            'self_certifying_receipt': (packet(good, replays['good'], verifier_id='self', verdict='HOST_CERTIFIED'),
                                        'REFUSED'),
            'authority_escalation': (packet(good, replays['good'], authority_effect='Host'), 'REFUSED'),
            'stale_nonce': (packet(good, replays['good'], nonce='run-0041'), 'REFUSED'),
            'truthful_nonzero_defect': (packet(bad, replays['bad']), 'REFUSED'),
            'trivial_self_chosen_payload': (packet(trivial, replays['trivial']), 'REFUSED'),
            'witness_bound_to_other_payload': (packet(bad, replays['bad'], bound=good,
                                                      claimed={'residual': [0, 0, 0], 'defect': 0}), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF42

@register
class ReasoningTraceValidation(HostedFamily):
    """WF42. Extract a claim graph from a trace and certify it, or certify its obstruction.

    Each step 'u - v = k' is an edge cochain value. The host computes the
    obstruction ``Phi`` and a dual circulation. A consistent trace needs a
    potential explaining every step and a conclusion the steps force; an
    obstructed trace needs a correction with ``||r||_1 = Phi`` (primal = dual).
    Hidden obstructions and conclusions that contradict the steps are refused.
    The Rust host checks all of it.
    """
    spec = spec_from('WF42', 'Reasoning-trace validation', 5, ['WF10', 'WF21'], None,
                     'rational_lp_primal_dual_check', 'wf42_reasoning_trace_validation')

    def fixtures(self):
        task = {'statement': "Reason in steps of the form 'u - v = k', then state the conclusion."}
        chain = ['s1: b - a = 1', 's2: c - b = 1']
        cycle = ['s1: b - a = 1', 's2: c - b = 0', 's3: a - c = 0']
        pot = {'a': 0, 'b': 1, 'c': 2}

        def case(reply):
            return {'task': task, 'replies': [reply]}
        return {
            'consistent_trace': (case({'trace': chain, 'status': 'CONSISTENT', 'potential': pot,
                                       'conclusion': 'c - a = 2'}), 'HOST_CERTIFIED'),
            'three_claim_cycle_obstructed': (case({'trace': cycle, 'status': 'OBSTRUCTED', 'correction': [1, 0, 0]}),
                                             'TYPED_REFUSAL'),
            'conclusion_contradicts_steps': (case({'trace': chain, 'status': 'CONSISTENT', 'potential': pot,
                                                   'conclusion': 'c - a = 3'}), 'REFUSED'),
            'hidden_obstruction': (case({'trace': cycle, 'status': 'CONSISTENT', 'potential': pot,
                                         'conclusion': 'c - a = 1'}), 'REFUSED'),
            'non_minimal_correction': (case({'trace': cycle, 'status': 'OBSTRUCTED', 'correction': [2, -1, 0]}),
                                       'REFUSED'),
            'unextractable_step': (case({'trace': ['b exceeds a by one'], 'status': 'CONSISTENT'}), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF43

@register
class GateHonestyAudit(HostedFamily):
    """WF43. Replay answer-free probes against a proposed gate and refuse a gate that lets one pass.

    The proposer writes a gate in a small check language for the task
    ``A x = b``. The host replays an empty object, constant verdicts and
    refusals, a templated receipt, keyword bait, wrong answers in the same p/q
    form as the true one and an input replacement. Honest means the gate checks
    the task itself, no probe passes and the true solution does; every probe
    verdict is traced to the checks that produced it. The Rust host checks all of it.
    """
    spec = spec_from('WF43', 'Gate-honesty and answer-free leak audit', 5, ['WF23'], None,
                     'answer_free_probe_replay', 'wf43_gate_honesty_and_answer_free_leak_audit')

    def fixtures(self):
        task = {'statement': 'Write a gate that accepts a reply only if it solves A x = b.',
                'A': [[1, 1], [1, -1]], 'b': [3, 1]}

        def gate(mode, *checks):
            return {'task': task, 'replies': [{'gate': {'mode': mode, 'checks': [list(ch) for ch in checks]}}]}
        return {
            'honest_gate': (gate('all', ['has_field', 'answer'], ['solves_task']), 'HOST_CERTIFIED'),
            'keyword_adjudication': (gate('all', ['keyword', 'status', 'solved']), 'REFUSED'),
            'receipt_or_answer': (gate('any', ['solves_task'], ['has_field', 'receipt']), 'REFUSED'),
            'input_replacement_gate': (gate('all', ['solves_own']), 'REFUSED'),
            'constant_reject_gate': (gate('all', ['field_equals', 'status', 'never']), 'REFUSED'),
            'slash_keyword_gate': (gate('all', ['has_field', 'answer'], ['keyword', 'answer', '/']), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF48

@register
class CommitRevealMutationGate(HostedFamily):
    """WF48. Commit an artifact before reveal, then require two checkers to kill every mutant.

    The judge manifest names two registered checkers and is committed with a
    sealed salt. The proposer commits ``H(salt || potential)`` for a public
    cochain, then reveals. The host checks the commitment, both checkers accept
    the artifact and its gauge shift, and both reject every hostile mutant. A
    changed artifact after commit, or a surviving mutant, is refused. The Rust
    host checks all of it.
    """
    spec = spec_from('WF48', 'Commit-reveal with a hostile mutation gate', 5, ['WF11', 'WF23'], 'WF23',
                     'dual_checker_mutation_suite', 'wf48_commit_reveal_with_a_hostile_mutation_gate')

    def fixtures(self):
        manifest = {'checkers': ['residual.v1', 'tree_integration.v1']}
        weak = {'checkers': ['residual.v1', 'length_only.v1']}
        task = {'statement': 'Commit to a potential phi with delta phi = c, then reveal it.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3]], 'c': [1, 2, -3, 1], 'judge_manifest': manifest,
                'manifest_commitment': commitment('judge-salt-17', manifest)}
        weak_task = {**task, 'judge_manifest': weak, 'manifest_commitment': commitment('judge-salt-17', weak)}
        sealed = {'manifest_salt': 'judge-salt-17'}
        phi, other = [0, 1, 3, 4], [0, 1, 3, 5]

        def case(t, committed, revealed):
            return {'task': t, 'sealed': sealed, 'replies': [{'commitment': commitment('s4lt', committed)},
                                                            {'salt': 's4lt', 'artifact': revealed}]}
        return {
            'committed_and_both_checkers_kill': (case(task, phi, phi), 'HOST_CERTIFIED'),
            'artifact_changed_after_commit': (case(task, other, phi), 'REFUSED'),
            'weak_checker_lets_mutant_survive': (case(weak_task, phi, phi), 'REFUSED'),
            'committed_wrong_artifact': (case(task, other, other), 'REFUSED'),
            'manifest_swapped_after_commit': ({**case(task, phi, phi), 'task': {**task, 'judge_manifest': weak}},
                                              'REFUSED'),
        }
