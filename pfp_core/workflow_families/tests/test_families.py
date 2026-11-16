"""One parametrized suite for every registered workflow family."""
from __future__ import annotations

import hashlib
import json

import pytest

from pfp_core import REPO_ROOT
from pfp_core.workflow_families import base, load
from pfp_core.workflow_families.base import (
    POSITIVE,
    REFUSED,
    FixtureProposer,
    Proposal,
    SealedLeakError,
    Usage,
    WorkflowFamilySpecV1,
    new_budget,
    run_fixture,
)

REGISTRY = load()
TARGET = {f'WF{n}' for n in range(6, 50)} | {'WF51', 'WF55', 'WF56', 'WF57'}
CASES = [(wf_id, name, expected) for wf_id, cls in REGISTRY.items()
         for name, (_bundle, expected) in cls().fixtures().items()]


@pytest.fixture(scope='module')
def audit_nodes():
    audit = json.loads((REPO_ROOT / 'dag' / 'reviews' / 'workflows_audit.json').read_text(encoding='utf-8'))
    return {n['id']: n for n in audit['registry']['family_nodes']}


def test_registry_covers_wf6_to_wf49_wf51_and_wf55_to_wf57_exactly():
    assert set(REGISTRY) == TARGET


@pytest.mark.parametrize('wf_id', sorted(REGISTRY))
def test_spec_matches_the_dag_node(wf_id, audit_nodes):
    spec, node = REGISTRY[wf_id].spec, audit_nodes[wf_id]
    assert (spec.name, spec.layer, list(spec.depends_on), spec.merge_into, spec.folder) == (
        node['name'], node['layer'], node['depends_on'], node['merge_into'], node['path'])
    assert spec.authority_effect == 'None'
    assert (REPO_ROOT / spec.folder).is_dir()


@pytest.mark.parametrize('wf_id', sorted(REGISTRY))
def test_every_family_has_a_positive_and_an_adversarial_fixture(wf_id):
    expected = [e for _b, e in REGISTRY[wf_id]().fixtures().values()]
    assert any(e in POSITIVE for e in expected)
    assert REFUSED in expected


@pytest.mark.parametrize(('wf_id', 'name', 'expected'), CASES)
def test_fixture_verdict(wf_id, name, expected):
    family = REGISTRY[wf_id]()
    first = run_fixture(family, name)
    again = run_fixture(family, name)
    assert first.verdict == expected, (first.code, first.detail, first.host)
    assert first.receipt_sha256 == again.receipt_sha256
    assert first.budget['spent_microusd'] == 0
    assert first.authority_effect == 'None'
    if expected in POSITIVE and first.host['certified_predicates']:
        assert not [k for k, v in first.host['certified_predicates'].items() if not v]


LAYER4_RESULTS = {
    ('WF6', 'all_dialects_accepted'): (
        'SWEEP_GRADED',
        {'acceptance': {'plain': 1, 'swapped': 1},
         'flips_vs_first': [],
         'items': {'i1': {'plain': True, 'swapped': True}, 'i2': {'plain': True, 'swapped': True}}},
    ),
    ('WF6', 'one_dialect_fails_item_by_item'): (
        'SWEEP_GRADED',
        {'acceptance': {'plain': 1, 'swapped': '1/2'},
         'flips_vs_first': [['i1', 'swapped']],
         'items': {'i1': {'plain': True, 'swapped': False}, 'i2': {'plain': True, 'swapped': True}}},
    ),
    ('WF6', 'dialect_zeroes_a_row'): (
        'DIALECT_CHANGES_QUERY',
        {'broken': [['i1', 'zero_row'], ['i2', 'zero_row']]},
    ),
    ('WF6', 'dialect_shifts_rhs'): (
        'DIALECT_CHANGES_QUERY',
        {'broken': [['i1', 'shifted']]},
    ),
    ('WF6', 'incomplete_sweep'): (
        'INCOMPLETE_SWEEP',
        {'missing': [['i2', 'swapped']]},
    ),
    ('WF8', 'three_sealed_stages'): (
        'SEALED_PIPELINE',
        {'stages': 3},
    ),
    ('WF8', 'packet_edited_after_seal'): (
        'SEAL_MISMATCH',
        {'sealed_stages': 1, 'stage': 'solve'},
    ),
    ('WF8', 'chain_link_broken'): (
        'CHAIN_BROKEN',
        {'sealed_stages': 1, 'stage': 'solve'},
    ),
    ('WF8', 'fence_dropped_from_packet'): (
        'FENCE_VIOLATED',
        {'sealed_stages': 1, 'stage': 'solve'},
    ),
    ('WF8', 'sealed_but_wrong_stage'): (
        'STAGE_RECOMPUTE_MISMATCH',
        {'sealed_stages': 1, 'stage': 'solve'},
    ),
    ('WF16', 'one_crosswalk_preserves'): (
        'CROSSWALK_PRESERVED',
        {'choices': [{'flipped_edges': [1, 2]}], 'differ_on_vertices': [], 'verdict': 'exact'},
    ),
    ('WF16', 'two_crosswalks_non_unique'): (
        'CROSSWALK_PRESERVED',
        {'choices': [{'flipped_edges': [1, 2]}, {'flipped_edges': [0, 3]}],
         'differ_on_vertices': [['a', 'b', 'c', 'd']],
         'verdict': 'exact'},
    ),
    ('WF16', 'orientation_sign_dropped'): (
        'CROSSWALK0:RELATIONS_PRESERVED',
        {'choices': [{'flipped_edges': [1]}],
         'differ_on_vertices': [],
         'failed': ['crosswalk0:relations_preserved', 'crosswalk0:data_transported'],
         'verdict': 'exact'},
    ),
    ('WF16', 'two_vertices_one_column'): (
        'CROSSWALK0:BIJECTIVE',
        {'choices': [],
         'differ_on_vertices': [],
         'failed': ['crosswalk0:bijective'],
         'verdict': 'exact'},
    ),
    ('WF16', 'target_data_not_transported'): (
        'VERDICTS_IDENTICAL',
        {'choices': [{'flipped_edges': [1, 2]}],
         'differ_on_vertices': [],
         'failed': ['verdicts_identical', 'crosswalk0:data_transported'],
         'verdict': 'exact'},
    ),
    ('WF17', 'difference_and_equivalence_witnessed'): (
        'CLAIMS_WITNESSED',
        {'claims': 2},
    ),
    ('WF17', 'unwitnessed_difference'): (
        'CLAIM0:WITNESSED',
        {'claims': 2, 'failed': ['claim0:witnessed']},
    ),
    ('WF17', 'formula_does_not_separate'): (
        'CLAIM0:SEPARATES',
        {'claims': 1, 'failed': ['claim0:separates']},
    ),
    ('WF17', 'trace_equivalent_is_not_bisimilar'): (
        'CLAIM0:BISIMULATION',
        {'claims': 1, 'failed': ['claim0:bisimulation']},
    ),
    ('WF17', 'claims_name_undeclared_states'): (
        'CLAIM0:STATES_DECLARED',
        {'claims': 2, 'failed': ['claim0:states_declared', 'claim1:states_declared']},
    ),
    ('WF21', 'rewrite_outside_fences_solved'): (
        'REWRITE_CERTIFIED',
        {},
    ),
    ('WF21', 'edit_inside_question_fence'): (
        'EDIT_INSIDE_FENCE',
        {},
    ),
    ('WF21', 'rewrite_leaks_answer_key'): (
        'ANSWER_KEY_LEAK',
        {},
    ),
    ('WF21', 'overlapping_matches'): (
        'OVERLAPPING_MATCHES',
        {},
    ),
    ('WF21', 'question_duplicated_outside_fence'): (
        'QUESTION_NOT_PRESERVED',
        {'violations': ['question']},
    ),
    ('WF23', 'clean_custody'): (
        'CUSTODY_INTACT',
        {'forged_lines': 0, 'leaked_files': []},
    ),
    ('WF23', 'answer_in_participant_bytes'): (
        'ANSWER_NOT_DERIVABLE',
        {'failed': ['answer_not_derivable'], 'forged_lines': 0, 'leaked_files': ['notes.txt']},
    ),
    ('WF23', 'answer_base64_encoded'): (
        'ANSWER_NOT_DERIVABLE',
        {'failed': ['answer_not_derivable'], 'forged_lines': 0, 'leaked_files': ['notes.txt']},
    ),
    ('WF23', 'forged_stdout_line'): (
        'STDOUT_LINES_AUTHENTIC',
        {'failed': ['stdout_lines_authentic'], 'forged_lines': 1, 'leaked_files': []},
    ),
    ('WF23', 'stale_checker_executed'): (
        'EXECUTED_CHECKER_IS_RECORDED',
        {'failed': ['executed_checker_is_recorded'], 'forged_lines': 0, 'leaked_files': []},
    ),
    ('WF23', 'file_edited_after_manifest'): (
        'FILE_HASHES_MATCH',
        {'failed': ['file_hashes_match'], 'forged_lines': 0, 'leaked_files': []},
    ),
    ('WF23', 'edited_file_with_self_computed_manifest'): (
        'FILE_HASHES_MATCH',
        {'failed': ['file_hashes_match'], 'forged_lines': 0, 'leaked_files': []},
    ),
    ('WF29', 'sound_checker_kills_all'): (
        'CHECKER_ACCEPTED',
        {'false_rejections': 0, 'kill_rate': 1, 'mutants': 5},
    ),
    ('WF29', 'root_gauge_falsely_rejects'): (
        'NO_FALSE_REJECTION',
        {'failed': ['no_false_rejection'], 'false_rejections': 2, 'kill_rate': 1, 'mutants': 5},
    ),
    ('WF29', 'cycle_only_checker_too_weak'): (
        'KILL_RATE_MEETS_BAR',
        {'failed': ['kill_rate_meets_bar'], 'false_rejections': 0, 'kill_rate': '2/5', 'mutants': 5},
    ),
    ('WF29', 'model_code_not_executed'): (
        'MALFORMED_CANDIDATE',
        {'reason': 'unknown predicate "lambda case: True"'},
    ),
    ('WF44', 'coboundary_potential_valid'): (
        'CERTIFICATE_VALID',
        {'schema': 'coboundary_potential'},
    ),
    ('WF44', 'l1_dual_pair_optimal'): (
        'CERTIFICATE_VALID',
        {'schema': 'l1_dual_circulation'},
    ),
    ('WF44', 'canonical_rational_solution'): (
        'CERTIFICATE_VALID',
        {'schema': 'canonical_rational'},
    ),
    ('WF44', 'non_canonical_rational'): (
        'CANONICAL_FORM',
        {'failed': ['canonical_form'], 'schema': 'canonical_rational'},
    ),
    ('WF44', 'dual_not_a_circulation'): (
        'DUAL_IS_CIRCULATION',
        {'failed': ['dual_is_circulation'], 'schema': 'l1_dual_circulation'},
    ),
    ('WF44', 'ill_typed_short_dual'): (
        'ILL_TYPED',
        {},
    ),
    ('WF44', 'float_in_certificate'): (
        'FLOAT_IN_CERTIFICATE',
        {},
    ),
    ('WF44', 'wrong_schema_named'): (
        'ILL_TYPED',
        {},
    ),
}


LAYER5_RESULTS = {
    ('WF12', 'gauge_shifted_ranks_certified'): (
        'ARMS_COMPARED',
        {'gauge_fixed_ranks': {'baseline': 0, 'mechanism': 2, 'null_control': -1, 'random_control': 1},
         'paired_totals': {'baseline->mechanism': 2,
                           'baseline->null_control': -1,
                           'null_control->mechanism': 3,
                           'random_control->mechanism': 1},
         'residual': [0, 0, 0, 0]},
    ),
    ('WF12', 'inflated_mechanism_effect'): (
        'RANK_DIFFERENCES_MATCH_PAIRED_TOTALS',
        {'failed': ['rank_differences_match_paired_totals'],
         'gauge_fixed_ranks': {'baseline': 0, 'mechanism': 4, 'null_control': -1, 'random_control': 1},
         'paired_totals': {'baseline->mechanism': 2,
                           'baseline->null_control': -1,
                           'null_control->mechanism': 3,
                           'random_control->mechanism': 1},
         'residual': [-2, -2, -2, 0]},
    ),
    ('WF12', 'random_control_norm_differs'): (
        'CONTROLS_UNMATCHED',
        {'failed': ['random_norm_matches_mechanism'],
         'squared_norms': {'mechanism': 25, 'random_control': 3}},
    ),
    ('WF12', 'arm_on_different_items'): (
        'MALFORMED_CANDIDATE',
        {'reason': 'every arm must answer the same items'},
    ),
    ('WF36', 'materialised_first_try'): (
        'MATERIALISED',
        {'residual': [0, 0, 0, 0, 0], 'syndromes': [[0, 0]]},
    ),
    ('WF36', 'repaired_from_shared_syndrome'): (
        'MATERIALISED_AFTER_RETRY',
        {'residual': [0, 0, 0, 0, 0], 'syndromes': [[0, 1], [0, 0]]},
    ),
    ('WF36', 'abstain_on_closed_nonexact_cycle'): (
        'ABSTAIN_NOT_MATERIALISABLE',
        {'rank_S_slots': 1, 'rank_augmented': 2},
    ),
    ('WF36', 'partial_guard_false_green'): (
        'PARTIAL_GUARD',
        {'full_syndrome': [0, 1], 'guard_syndrome': [0], 'kernel_witness': [0, 0, 0, 1, 0]},
    ),
    ('WF36', 'lazy_false_abstention'): (
        'FALSE_ABSTENTION',
        {'rank_S_slots': 2, 'rank_augmented': 2},
    ),
    ('WF36', 'guard_red_after_retry'): (
        'GUARD_RED_AFTER_RETRY',
        {'syndromes': [[0, 1], [0, 1]]},
    ),
    ('WF36', 'stage2_drifts_from_slots'): (
        'STAGE2_POTENTIAL_EXPLAINS_SLOTS',
        {'failed': ['stage2_potential_explains_slots'],
         'residual': [0, 0, 0, -1, 1],
         'syndromes': [[0, 0]]},
    ),
    ('WF39', 'all_guards_pass'): (
        'ALL_GUARDS_PASS',
        {'residual_evidence': []},
    ),
    ('WF39', 'self_certifying_receipt'): (
        'AUTHORITY_ESCALATION',
        {'escalating_fields': ['verdict'], 'residual_evidence': ['authority']},
    ),
    ('WF39', 'authority_escalation'): (
        'AUTHORITY_ESCALATION',
        {'escalating_fields': [], 'residual_evidence': ['authority']},
    ),
    ('WF39', 'stale_nonce'): (
        'FRESH_NONCE',
        {'failed': ['fresh_nonce'], 'residual_evidence': ['fresh_nonce']},
    ),
    ('WF39', 'truthful_nonzero_defect'): (
        'ZERO_DEFECT',
        {'failed': ['zero_defect'], 'residual_evidence': ['zero_defect']},
    ),
    ('WF39', 'trivial_self_chosen_payload'): (
        'PAYLOAD_NOT_BOUND_TO_TASK',
        {'residual_evidence': ['payload_bound_to_task']},
    ),
    ('WF39', 'witness_bound_to_other_payload'): (
        'WITNESS_BOUND_TO_PAYLOAD',
        {'failed': ['witness_bound_to_payload', 'replay_match', 'zero_defect'],
         'residual_evidence': ['witness_bound_to_payload', 'replay_match', 'zero_defect']},
    ),
    ('WF42', 'consistent_trace'): (
        'TRACE_VALID',
        {'Phi': 0, 'dual': [0, 0]},
    ),
    ('WF42', 'three_claim_cycle_obstructed'): (
        'TRACE_OBSTRUCTED',
        {'Phi': 1, 'dual': [1, 1, 1]},
    ),
    ('WF42', 'conclusion_contradicts_steps'): (
        'CONCLUSION_MATCHES_STEPS',
        {'Phi': 0, 'dual': [0, 0], 'failed': ['conclusion_matches_steps']},
    ),
    ('WF42', 'hidden_obstruction'): (
        'HIDDEN_OBSTRUCTION',
        {'Phi': 1, 'dual': [1, 1, 1]},
    ),
    ('WF42', 'non_minimal_correction'): (
        'PRIMAL_EQUALS_DUAL',
        {'Phi': 1, 'dual': [1, 1, 1], 'failed': ['primal_equals_dual']},
    ),
    ('WF42', 'unextractable_step'): (
        'MALFORMED_CANDIDATE',
        {'reason': 'extractor cannot parse step "b exceeds a by one"'},
    ),
    ('WF43', 'honest_gate'): (
        'GATE_HONEST',
        {'leaked': {}, 'probes': 11},
    ),
    ('WF43', 'keyword_adjudication'): (
        'NO_ANSWER_FREE_REPLY_PASSES',
        {'failed': ['no_answer_free_reply_passes', 'accepts_true_solution', 'gate_verifies_task'],
         'leaked': {'constant_verdict': ['keyword'],
                    'keyword_bait': ['keyword'],
                    'templated_receipt': ['keyword']},
         'probes': 11},
    ),
    ('WF43', 'receipt_or_answer'): (
        'NO_ANSWER_FREE_REPLY_PASSES',
        {'failed': ['no_answer_free_reply_passes', 'gate_verifies_task'],
         'leaked': {'templated_receipt': ['has_field']},
         'probes': 11},
    ),
    ('WF43', 'input_replacement_gate'): (
        'NO_ANSWER_FREE_REPLY_PASSES',
        {'failed': ['no_answer_free_reply_passes', 'accepts_true_solution', 'gate_verifies_task'],
         'leaked': {'input_replacement': ['solves_own']},
         'probes': 11},
    ),
    ('WF43', 'constant_reject_gate'): (
        'ACCEPTS_TRUE_SOLUTION',
        {'failed': ['accepts_true_solution', 'gate_verifies_task'], 'leaked': {}, 'probes': 11},
    ),
    ('WF43', 'slash_keyword_gate'): (
        'NO_ANSWER_FREE_REPLY_PASSES',
        {'failed': ['no_answer_free_reply_passes', 'gate_verifies_task'],
         'leaked': {'wrong_answer_0': ['has_field', 'keyword'],
                    'wrong_answer_1': ['has_field', 'keyword'],
                    'wrong_answer_2': ['has_field', 'keyword'],
                    'wrong_answer_3': ['has_field', 'keyword'],
                    'wrong_answer_4': ['has_field', 'keyword']},
         'probes': 11},
    ),
    ('WF48', 'committed_and_both_checkers_kill'): (
        'COMMIT_REVEAL_CERTIFIED',
        {'kills': {'residual.v1': '12/12', 'tree_integration.v1': '12/12'}},
    ),
    ('WF48', 'artifact_changed_after_commit'): (
        'ARTIFACT_CHANGED_AFTER_COMMIT',
        {},
    ),
    ('WF48', 'weak_checker_lets_mutant_survive'): (
        'LENGTH_ONLY.V1:KILLS_EVERY_MUTANT',
        {'failed': ['length_only.v1:kills_every_mutant'],
         'kills': {'length_only.v1': '1/12', 'residual.v1': '12/12'}},
    ),
    ('WF48', 'committed_wrong_artifact'): (
        'RESIDUAL.V1:ACCEPTS_ARTIFACT_AND_GAUGE',
        {'failed': ['residual.v1:accepts_artifact_and_gauge',
                    'residual.v1:kills_every_mutant',
                    'tree_integration.v1:accepts_artifact_and_gauge',
                    'tree_integration.v1:kills_every_mutant'],
         'kills': {'residual.v1': '11/12', 'tree_integration.v1': '11/12'}},
    ),
    ('WF48', 'manifest_swapped_after_commit'): (
        'MANIFEST_COMMITMENT_MATCHES',
        {'failed': ['manifest_commitment_matches']},
    ),
}


LAYER6_RESULTS = {
    ('WF18', 'replay_reproduces_every_grade'): (
        'REPLAY_REPRODUCED',
        {'cells': 3, 'mismatched': []},
    ),
    ('WF18', 'reply_byte_drifted'): (
        'STORED_BYTES_DRIFTED',
        {'drift': ['c1:raw_reply']},
    ),
    ('WF18', 'grade_not_reproduced'): (
        'EVERY_GRADE_REPRODUCES',
        {'cells': 3, 'failed': ['every_grade_reproduces'], 'mismatched': ['c2']},
    ),
    ('WF18', 'grader_pin_drifted'): (
        'SOURCE_PIN_DRIFT',
        {},
    ),
    ('WF18', 'parallel_edge_violation_recorded_certified'): (
        'EVERY_GRADE_REPRODUCES',
        {'cells': 4, 'failed': ['every_grade_reproduces'], 'mismatched': ['c4']},
    ),
    ('WF35', 'channels_compared_on_one_checker'): (
        'CHANNELS_COMPARED',
        {'accepts': {'grammar_mask': 2, 'prompt': 1}, 'discordant': {'first_only': 0, 'second_only': 1}},
    ),
    ('WF35', 'arms_used_different_checkers'): (
        'ARMS_NOT_MATCHED',
        {},
    ),
    ('WF35', 'arms_used_different_budgets'): (
        'ARMS_NOT_MATCHED',
        {},
    ),
    ('WF35', 'channel_label_claims_acceptance'): (
        'ACCEPT_SET_DEPENDS_ONLY_ON_BYTES',
        {'accepts': {'grammar_mask': 1, 'prompt': 1}, 'discordant': {'first_only': 0, 'second_only': 0},
         'failed': ['accept_set_depends_only_on_bytes']},
    ),
    ('WF35', 'grammar_mask_accepts_parallel_edge_violation'): (
        'ACCEPT_SET_DEPENDS_ONLY_ON_BYTES',
        {'accepts': {'grammar_mask': 0, 'prompt': 0}, 'discordant': {'first_only': 0, 'second_only': 0},
         'failed': ['accept_set_depends_only_on_bytes']},
    ),
}


def _findings(detail):
    """What a verdict found, without the hashes in it."""
    return {key: value for key, value in detail.items() if 'sha256' not in key and key != 'head'}


def test_the_layer_4_results_name_every_fixture_of_the_layer_4_families():
    families = {wf_id for wf_id, _name in LAYER4_RESULTS}
    assert families == {'WF6', 'WF8', 'WF16', 'WF17', 'WF21', 'WF23', 'WF29', 'WF44'}
    assert set(LAYER4_RESULTS) == {(wf_id, name) for wf_id in families for name in REGISTRY[wf_id]().fixtures()}


@pytest.mark.parametrize(('wf_id', 'name'), sorted(LAYER4_RESULTS))
def test_a_layer_4_fixture_ends_with_the_code_and_the_findings_its_name_says(wf_id, name):
    result = run_fixture(REGISTRY[wf_id](), name)
    assert (result.code, _findings(result.detail)) == LAYER4_RESULTS[(wf_id, name)]


def test_the_layer_5_results_name_every_fixture_of_the_layer_5_families():
    families = {wf_id for wf_id, _name in LAYER5_RESULTS}
    assert families == {'WF12', 'WF36', 'WF39', 'WF42', 'WF43', 'WF48'}
    assert set(LAYER5_RESULTS) == {(wf_id, name) for wf_id in families for name in REGISTRY[wf_id]().fixtures()}


@pytest.mark.parametrize(('wf_id', 'name'), sorted(LAYER5_RESULTS))
def test_a_layer_5_fixture_ends_with_the_code_and_the_findings_its_name_says(wf_id, name):
    result = run_fixture(REGISTRY[wf_id](), name)
    assert (result.code, _findings(result.detail)) == LAYER5_RESULTS[(wf_id, name)]


def test_the_layer_6_results_name_every_fixture_of_the_layer_6_families():
    families = {wf_id for wf_id, _name in LAYER6_RESULTS}
    assert families == {'WF18', 'WF35'}
    assert set(LAYER6_RESULTS) == {(wf_id, name) for wf_id in families for name in REGISTRY[wf_id]().fixtures()}


@pytest.mark.parametrize(('wf_id', 'name'), sorted(LAYER6_RESULTS))
def test_a_layer_6_fixture_ends_with_the_code_and_the_findings_its_name_says(wf_id, name):
    result = run_fixture(REGISTRY[wf_id](), name)
    assert (result.code, _findings(result.detail)) == LAYER6_RESULTS[(wf_id, name)]


def test_the_duality_pin_is_the_rust_source():
    from pfp_core.workflow_families import layer6
    source = REPO_ROOT / 'code' / 'rust' / 'pfp_operads' / 'src' / 'families' / 'duality.rs'
    text = source.read_bytes().decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    assert hashlib.sha256(text.encode('utf-8')).hexdigest() == layer6.GRADER_PIN


def test_authority_escalation_is_refused():
    with pytest.raises(ValueError, match='AUTHORITY_ESCALATION'):
        WorkflowFamilySpecV1('WF7', 'x', 1, (), None, 'c', 'workflows/wf07_typed_refusal', authority_effect='Host')


def test_a_prompt_carrying_a_sealed_literal_never_dispatches():
    family = REGISTRY['WF7']()
    bundle = {'task': {'statement': 'secret 98765', 'A': [[1]], 'b': [1]}, 'sealed': {'expected': 98765},
              'replies': [{'answer': [1]}]}
    budget = new_budget('leak', bundle['task'])
    with pytest.raises(SealedLeakError):
        family.execute(bundle, budget=budget)
    assert budget.summary()['calls'] == 0


def test_a_priced_reply_is_refused_by_the_zero_spend_budget():
    family = REGISTRY['WF7']()
    bundle, _ = family.fixtures()['solvable_answered']
    priced = FixtureProposer([Proposal({'answer': [2, 1]}, Usage(quote_microusd=50, actual_microusd=40))])
    out = family.execute(bundle, budget=new_budget('priced', bundle['task']), proposer=priced)
    assert out.verdict == REFUSED and out.budget['spent_microusd'] == 0
    assert out.transcript[-1]['reply'] == 'BUDGET_REFUSED'


def test_canonical_rejects_floats_as_fractions():
    with pytest.raises(base.MalformedCandidateError):
        base.as_fraction('0.5', 'x')
    assert base.as_fraction('1/2', 'x') == base.Fraction(1, 2)


def test_readme_blocks_and_dag_records_are_current():
    from pfp_core.workflow_families import docs
    assert docs.build(check=True) == []


def test_a_private_name_in_a_source_field_is_refused():
    from pfp_core.workflow_families import docs
    private = 'run it on the ' + 'om' + 'ega' + '_engine host'
    with pytest.raises(ValueError, match=r"WF7: field 'process'"):
        docs.guard('WF7', 'process', private)
    with pytest.raises(ValueError, match='readme'):
        docs.guard('WF7', 'readme block', 'see the ' + 'wo' + 'land gate')
    # The Greek letter as a math symbol is not a name.
    sym = 'om' + 'ega'
    math = f'\\{sym}_1 and {sym}_2 and {sym}1'
    assert docs.guard('WF7', 'math', math) == math


def test_a_readme_without_the_generated_markers_is_refused():
    from pfp_core.workflow_families import docs
    block = docs.render_readme_block(REGISTRY['WF7'])
    with pytest.raises(ValueError, match='WF7: README lacks'):
        docs.splice_readme('WF7', '# WF7: Typed refusal\n\nhand-written\n', block)
    spliced = docs.splice_readme('WF7', f'# WF7\n\n{docs.README_BEGIN}\nold\n{docs.README_END}\n\nkept\n', block)
    assert spliced == f'# WF7\n\n{block}\n\nkept\n'


def test_every_generated_readme_block_is_current_and_says_runnable_offline():
    from pfp_core.workflow_families import docs
    for wf_id in sorted(docs.README_BLOCK_IDS):
        cls = REGISTRY[wf_id]
        text = (REPO_ROOT / cls.spec.folder / 'README.md').read_text(encoding='utf-8')
        assert docs.render_readme_block(cls) in text.replace('\r\n', '\n'), wf_id
        assert 'no runner and no run yet' not in text, wf_id


def test_drift_in_the_index_or_the_dag_status_is_reported():
    from pfp_core.workflow_families import docs
    reg = {'WF7': REGISTRY['WF7']}
    index = '| WF | Workflow | Status |\n| --- | --- | --- |\n| 7 | [Typed refusal](x) | runnable offline |\n'
    dag = {'nodes': [{'id': 'WF7', 'status': docs.DAG_STATUS}]}
    assert docs.drift(reg, index, dag) == []
    assert docs.drift(reg, index.replace('runnable offline', 'proposal'), dag) == [
        "workflows/README.md#WF7: status 'proposal', expected 'runnable offline'"]
    assert docs.drift(reg, index, {'nodes': [{'id': 'WF7', 'status': 'proposal'}]}) == [
        "workflows/dag/workflow_dag.json#WF7: status 'proposal', expected 'implemented_offline'"]


def test_an_unaffordable_call_is_never_dispatched():
    from pfp_core.workflow_families.base import CallableProposer
    calls = []

    def fn(prompt):
        calls.append(prompt)
        return {'answer': [2, 1]}, Usage(actual_microusd=900)
    family = REGISTRY['WF7']()
    bundle, _ = family.fixtures()['solvable_answered']
    out = family.execute(bundle, budget=new_budget('dear', bundle['task']),
                         proposer=CallableProposer(fn, quote_microusd=1_000_000))
    assert calls == [] and out.verdict == REFUSED and out.budget['spent_microusd'] == 0


def test_a_short_sealed_answer_is_caught_as_a_whole_token():
    family = REGISTRY['WF7']()
    bundle = {'task': {'statement': 'the answer is 42', 'A': [[1]], 'b': [1]}, 'sealed': {'answer': 42},
              'replies': [{'answer': [1]}]}
    with pytest.raises(SealedLeakError):
        family.execute(bundle, budget=new_budget('short', bundle['task']))
    bundle['task']['statement'] = 'the answer is 421'
    assert family.execute(bundle, budget=new_budget('ok', bundle['task'])).verdict == 'HOST_CERTIFIED'


HOSTED = {wf_id: cls for wf_id, cls in REGISTRY.items() if issubclass(cls, base.HostedFamily)}


def test_the_rust_host_lists_every_hosted_family_under_the_registry_s_names():
    from pfp.infrastructure import operad_host
    listed = operad_host.result(operad_host.call(('family', 'list')))['families']
    assert listed == [{'workflow': wf_id, 'name': cls.spec.name, 'host_check': cls.spec.host_check_id}
                      for wf_id, cls in HOSTED.items()]
    assert set(HOSTED) == {'WF6', 'WF7', 'WF8', 'WF9', 'WF10', 'WF11', 'WF12', 'WF13', 'WF16', 'WF17', 'WF18',
                           'WF20', 'WF21', 'WF23', 'WF24', 'WF25', 'WF26', 'WF27', 'WF29', 'WF30', 'WF31', 'WF32',
                           'WF33', 'WF35', 'WF36', 'WF38', 'WF39', 'WF40', 'WF42', 'WF43', 'WF44', 'WF45', 'WF46',
                           'WF47', 'WF48'}


@pytest.mark.parametrize('wf_id', sorted(HOSTED))
def test_a_hosted_family_holds_no_check_of_its_own(wf_id):
    cls = HOSTED[wf_id]
    for name in ('validate', 'check', 'run', 'prompt', 'execute', '_host', '_verdict'):
        assert name not in vars(cls), f'{wf_id} overrides {name}'
    assert set(vars(cls)) - {'__module__', '__doc__', '__qualname__', '__firstlineno__', '__static_attributes__',
                             '__annotations__'} <= {'spec', 'fixtures'}


def test_a_hosted_family_refuses_a_malformed_task_before_any_proposal():
    from pfp_core.workflow_families.base import CallableProposer
    calls = []

    def fn(prompt):
        calls.append(prompt)
        return {'answer': [1]}, Usage()
    family = REGISTRY['WF7']()
    bundle = {'task': {'A': [[1, 2], [3]], 'b': [1, 2]}}
    budget = new_budget('WF7:ragged', bundle['task'])
    with pytest.raises(base.MalformedCandidateError, match='rectangular'):
        family.execute(bundle, budget=budget, proposer=CallableProposer(fn, quote_microusd=0))
    assert calls == [] and budget.summary()['calls'] == 0


def test_a_hosted_family_asks_exactly_what_the_host_wrote():
    from pfp_core.workflow_families.base import CallableProposer
    prompts = []

    def fn(prompt):
        prompts.append(prompt)
        return {'coefficients': [1, 0, 2]}, Usage()
    family = REGISTRY['WF31']()
    bundle, _ = family.fixtures()['held_out_winner']
    out = family.execute(bundle, budget=new_budget('WF31:host', bundle['task']),
                         proposer=CallableProposer(fn, quote_microusd=0))
    assert out.verdict == 'HOST_CERTIFIED' and out.code == 'WINNER_SELECTED'
    assert [t['stage'] for t in out.transcript] == ['proposer:0', 'proposer:1', 'proposer:2']
    assert len(set(prompts)) == 1 and prompts[0].startswith('WF31 Multi-agent tournament')
    assert 'held_out' not in prompts[0]
    assert {t['request_sha256'] for t in out.transcript} == {base.sha256_hex(prompts[0])}
    assert out.host['certified_predicates'] == {'splits_disjoint': True, 'winner_beats_baseline': True}
    assert out.host['final_output_certified'] is True


def test_what_the_host_leaves_unchecked_keeps_the_run_from_being_fully_certified():
    family = REGISTRY['WF32']()
    scoped = run_fixture(family, 'checked_claims_admitted_rest_open')
    assert (scoped.verdict, scoped.code) == ('HOST_CERTIFIED', 'CLAIM_SCOPED')
    assert scoped.host['uncertified_obligations'] == ['c3', 'c4']
    assert scoped.host['final_output_certified'] is False
    full = run_fixture(family, 'every_claim_checked')
    assert (full.verdict, full.code) == ('HOST_CERTIFIED', 'ALL_CLAIMS_ADMITTED')
    assert full.host['uncertified_obligations'] == [] and full.host['final_output_certified'] is True


def test_a_battery_asks_one_capsule_at_a_time_and_counts_a_missing_reply():
    family = REGISTRY['WF13']()
    out = run_fixture(family, 'dropped_capsule_keeps_denominator')
    assert [t['stage'] for t in out.transcript] == ['capsule:stab5', 'capsule:stab3', 'capsule:anom', 'capsule:comm',
                                                    'capsule:refuse']
    assert out.verdict == 'REFUSED' and out.detail['denominator'] == 5
    assert out.host['certified_predicates']['capsule:refuse'] is False


def test_a_sealed_value_in_a_hosted_task_is_refused_by_the_host_and_never_dispatched():
    family = REGISTRY['WF31']()
    bundle, _ = family.fixtures()['held_out_winner']
    leaky = {**bundle, 'task': {**bundle['task'], 'statement': 'One held-out value is 51.'},
             'sealed': {'held_out': bundle['sealed']['held_out'], 'answer': 51}}
    budget = new_budget('WF31:leak', leaky['task'])
    with pytest.raises(SealedLeakError, match='proposer:0'):
        family.execute(leaky, budget=budget)
    assert budget.summary()['calls'] == 0


def test_the_python_guard_of_the_unported_families_reads_a_closing_mark_as_the_host_does():
    assert base.prompt_leaks('The total is 42.', {'answer': 42})
    assert base.prompt_leaks('Is it 42?', {'answer': 42})
    assert not base.prompt_leaks('p = .42 and 42.5', {'answer': 42})
    assert not base.prompt_leaks('The total is 42.', {'note': 42})
    assert base.prompt_leaks('choose a.?', {'answer': 'a.'})
    assert not base.prompt_leaks('choose a', {'answer': 'a.'})


XOR_FAMILIES = ['WF9', 'WF20', 'WF27', 'WF33']


@pytest.mark.parametrize('wf_id', XOR_FAMILIES)
@pytest.mark.parametrize('label', [0.9, 0.0, 1.0, '0', '1', True, False, 2, -1, None])
def test_a_non_binary_edge_label_is_refused_before_any_proposal(wf_id, label):
    # Regression: int(x) % 2 read 0.9 as 0 and certified the empty repair of a different task.
    from pfp_core.workflow_families.base import CallableProposer
    calls = []

    def fn(prompt):
        calls.append(prompt)
        return {'flip': []}, Usage()
    family = REGISTRY[wf_id]()
    bundle = {'task': {'statement': 'Flip the fewest labels.', 'edges': [[0, 1], [1, 2], [2, 0]],
                       'labels': [label, 0, 0], 'fuel': 9}, 'replies': [{'flip': []}]}
    budget = new_budget(f'{wf_id}:label', bundle['task'])
    with pytest.raises(base.MalformedCandidateError, match='exact integer 0 or 1'):
        family.execute(bundle, budget=budget, proposer=CallableProposer(fn, quote_microusd=0))
    assert calls == [] and budget.summary()['calls'] == 0


@pytest.mark.parametrize('label', [float('nan'), float('inf')])
def test_a_label_that_is_not_json_never_reaches_the_host(label):
    family = REGISTRY['WF9']()
    bundle = {'task': {'edges': [[0, 1], [1, 2], [2, 0]], 'labels': [label, 0, 0]}, 'replies': [{'flip': []}]}
    budget = new_budget('WF9:nan', bundle['task'])
    with pytest.raises(ValueError, match='not JSON compliant'):
        family.execute(bundle, budget=budget)
    assert budget.summary()['calls'] == 0


@pytest.mark.parametrize('edges', [[[0, 1], [1, 2], [2, 0, 5]], [[0, 1], [1, 2], 'ab']])
def test_a_malformed_edge_is_refused_before_any_proposal(edges):
    family = REGISTRY['WF9']()
    bundle = {'task': {'edges': edges, 'labels': [1, 0, 0]}, 'replies': [{'flip': []}]}
    with pytest.raises(base.MalformedCandidateError, match='each edge is a pair'):
        family.execute(bundle, budget=new_budget('WF9:edge', bundle['task']))


@pytest.mark.parametrize('wf_id', XOR_FAMILIES)
def test_exact_binary_labels_are_still_admitted(wf_id):
    family = REGISTRY[wf_id]()
    task = {'edges': [[0, 1], [1, 2], [2, 0]], 'labels': [1, 0, 0], 'fuel': 9}
    assert family.validate(task) is task


def test_docs_main_prints_the_result_and_exits_by_it(monkeypatch, capsys):
    from pfp_core.workflow_families import docs
    monkeypatch.setattr(docs, 'build', lambda check: [])
    assert docs.main(['--check']) == 0
    assert capsys.readouterr().out == '{\n  "stale": []\n}\n'
    monkeypatch.setattr(docs, 'build', lambda check: ['README.md'])
    assert docs.main([]) == 1
    assert capsys.readouterr().out == '{\n  "drift": [\n    "README.md"\n  ]\n}\n'


def test_docs_build_writes_only_without_check(monkeypatch):
    from pathlib import Path

    from pfp_core.workflow_families import docs
    written = []
    monkeypatch.setattr(Path, 'write_bytes', lambda self, data: written.append(self))
    assert docs.build(check=True) == []
    assert written == []
    assert docs.build(check=False) == []
    assert docs.AUDIT in written and len(written) == 45
    monkeypatch.setattr(docs, '_encode', lambda path, text: b'changed')
    stale = docs.build(check=True)
    assert len(stale) == 45 and 'dag/reviews/workflows_audit.json' in stale


def test_docs_a_missing_host_file_is_refused(monkeypatch, tmp_path):
    from pfp_core.workflow_families import docs
    assert docs.host_files(REGISTRY['WF7']) is not None
    monkeypatch.setattr(docs, 'REPO_ROOT', tmp_path)
    with pytest.raises(ValueError, match=r'WF7: the host file code/rust/pfp_operads/src/families/wf07\.rs is missing'):
        docs.host_files(REGISTRY['WF7'])


def test_docs_drift_reads_only_numbered_rows_with_a_status_cell():
    from pfp_core.workflow_families import docs
    one = {'WF7': REGISTRY['WF7']}
    dag = {'nodes': [{'id': 'WF7', 'status': 'implemented_offline'}]}
    assert docs.drift(one, '| 7 |\n| WF | Workflow | Status |\n| 7 | Typed refusal | runnable offline |\n', dag) == []
    assert docs.drift(one, '| 7 | Typed refusal | design |\n', dag) == [
        "workflows/README.md#WF7: status 'design', expected 'runnable offline'"]
    assert docs.drift(one, '| 7 | Typed refusal | runnable offline |\n', {'nodes': []}) == [
        "workflows/dag/workflow_dag.json#WF7: status None, expected 'implemented_offline'"]


def test_docs_readme_block_ids_are_wf6_to_wf49():
    from pfp_core.workflow_families import docs
    assert len(docs.README_BLOCK_IDS) == 44
    assert 'WF6' in docs.README_BLOCK_IDS and 'WF49' in docs.README_BLOCK_IDS
    assert 'WF5' not in docs.README_BLOCK_IDS and 'WF50' not in docs.README_BLOCK_IDS


def test_docs_docstring_head_drops_only_the_id_prefix():
    from types import SimpleNamespace

    from pfp_core.workflow_families import docs

    class Fake:
        """WF7. Typed refusal. It refuses.

        Body line.
        """
        spec = SimpleNamespace(wf_id='WF7')
    assert docs._docstring(Fake) == ('Typed refusal. It refuses.', 'Body line.')


def test_docs_encode_keeps_crlf_only_when_seen_in_the_first_4096_bytes(tmp_path):
    from pfp_core.workflow_families import docs
    early, late = tmp_path / 'early', tmp_path / 'late'
    early.write_bytes(b'a' * 4094 + b'\r\n')
    late.write_bytes(b'a' * 4095 + b'\r\n')
    assert docs._encode(early, 'x\ny\n') == b'x\r\ny\r\n'
    assert docs._encode(late, 'x\ny\n') == b'x\ny\n'
    assert docs._encode(tmp_path / 'absent', 'x\n') == b'x\n'


def test_docs_guard_names_the_whole_match():
    from pfp_core.workflow_families import docs
    with pytest.raises(ValueError, match=r"WF7: field 'name' carries a private name \('Symbol Game'\)"):
        docs.guard('WF7', 'name', 'the Symbol Game rules')
