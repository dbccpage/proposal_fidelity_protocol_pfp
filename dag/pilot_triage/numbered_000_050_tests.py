"""Emit explicitly selected test bodies; this helper never executes pilot code."""
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'pilots/anomalon_woland'
LEDGER = Path(__file__).with_name('numbered_000_050_reads.json')
SELECT = {
26: ['test_all_rhs_against_independent_parity_and_assignments'],
27: ['test_dual_checks_not_just_objective_equality', 'test_trace_independent_3125_start_states'],
28: ['test_seeded_comparison_to_independent_ebnf', 'test_limits_are_not_grammar_refutations'],
29: ['test_scalar_finite_grid_against_independent_enumeration', 'test_false_kernel_certificate_not_just_one_boundary_witness'],
31: ['test_rational_global_phases_and_hadamard_matrix'],
32: ['test_999_weight_triples_and_positive_rescaling', 'test_assumption_is_operational_not_derived'],
33: ['test_independent_fraction_grid_and_sum_oracle', 'test_unknown_and_breach_are_persistent'],
34: ['test_exact_finite_projection_and_repair_oracle', 'test_false_residual_and_repair_witnesses'],
35: ['test_exact_predicate_against_independent_margin', 'test_observed_call_not_consensus', 'test_false_consensus'],
36: ['test_all_three_vertex_relations_against_matrix_oracle', 'test_complete_observations_against_independent_profiles'],
37: ['test_all_small_refinement_pairs_and_corrupted_witnesses'],
38: ['test_cutoff_counterexamples_and_declared_format'],
39: ['test_triangle_grid', 'test_unknown_angles_not_nonzero'],
41: ['test_transition_contract_and_replay'],
42: ['assert_math'],
43: ['oracle', 'test_complete_small_binary_path_oracle'],
44: ['test_false_betti_with_same_euler_is_rejected', 'test_exhaustive_small_graphs_exact_minors'],
46: ['test_all_62_augmented_basis_faces_unit_and_weighted'],
47: ['test_identity_and_associative_composition_exact_records', 'test_span_boundaries_source_locator_and_request_substitution'],
48: ['test_independent_hex_and_known_answer', 'test_group_laws_embedded_s3_and_three_keys', 'test_valid_comparison_and_exact_byte_controls'],
49: ['oracle', 'test_abstention_wrong_task_limit_and_sequence_end', 'test_tail_is_not_parsed_and_input_is_not_changed'],
50: ['expected', 'test_exact_one_pass_and_baseline'],
}

prior = json.loads(LEDGER.read_text())
for i in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
    found = []
    for path in sorted((BASE / f'pilot_{i:07d}' / 'tests').rglob('test*.py')):
        raw = path.read_bytes()
        lines = raw.decode('utf-8').splitlines()
        nodes = [n for n in ast.walk(ast.parse(raw)) if isinstance(n, ast.FunctionDef) and n.name in SELECT.get(i, [])]
        for n in nodes:
            found.append(n.name)
            print(f'FILE {path.relative_to(ROOT).as_posix()} FUNCTION {n.name}')
            print('\n'.join(f'{k+1}: {lines[k]}' for k in range(n.lineno-1, n.end_lineno)))
            entry = {'path': path.relative_to(ROOT).as_posix(), 'lines': [n.lineno,n.end_lineno], 'sha256': hashlib.sha256(raw).hexdigest(), 'review_level':'selected_test_body_emitted_for_review'}
            if entry not in prior:
                prior.append(entry)
    missing = set(SELECT.get(i, [])) - set(found)
    if missing:
        print('MISSING SELECTION', i, sorted(missing))
LEDGER.write_text(json.dumps(prior, indent=2)+'\n')
