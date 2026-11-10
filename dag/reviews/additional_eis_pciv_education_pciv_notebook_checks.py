"""Execute fully reviewed stdlib-only PCIV teaching cells on public toy inputs."""
import ast
from contextlib import redirect_stdout
from fractions import Fraction as Q
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
scope = json.loads((REV / 'additional_eis_pciv_education_remaining_scope.json').read_text())
states = {}
rows = []
for row in scope['files']:
    path = row['path']
    if not path.startswith('education/010_oepciv/curriculum/') or not path.endswith('.ipynb'):
        continue
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    notebook = json.loads(raw)
    ns = {}
    output = io.StringIO()
    for cell in notebook['cells']:
        if cell['cell_type'] != 'code':
            continue
        code = ''.join(cell['source'])
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(x.name in {'hashlib', 'json', 'math'} for x in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module == 'fractions'
        with redirect_stdout(output):
            exec(compile(tree, path, 'exec'), ns)
    states[Path(path).stem] = ns
    rows.append({'path': path, 'sha256': row['sha256'], 'stored_execution_counts': [c.get('execution_count') for c in notebook['cells'] if c['cell_type']=='code'],
                 'stored_output_count': sum(len(c.get('outputs', [])) for c in notebook['cells']),
                 'reviewed_cell_execution': 'pass', 'stdout': output.getvalue()})
assert len(rows) == 11

controls = []
topology = states['lesson_400_01_lineage_dag_and_causal_descent']['LineageTopology']()
topology.add_inheritance_edge('A', 'B', 'DirectMutation')
topology.add_inheritance_edge('B', 'A', 'Repair')
assert topology.inheritance_dag == {'B': ['A'], 'A': ['B']}
controls.append({'id': 'cycle', 'result': topology.inheritance_dag,
                 'conclusion': 'Separating reference edges does not enforce an acyclic inheritance graph.'})

mutate = states['lesson_400_02_mutation_operators_and_forge']['apply_mutation']
changed = mutate('ABC', 1, 1, '!', [(0, 3)])
assert changed == 'A!BC'
controls.append({'id': 'protected_internal_insertion', 'result': changed,
                 'conclusion': 'A zero-width insertion inside a protected interval bypasses the strict interval-overlap test.'})

dominates = states['lesson_410_04_pareto_selection_and_fitness']['dominates']
assert dominates((Q(1),), (Q(0), Q(99)))
assert dominates((0.9, 0.8), (0.7, 0.8))
controls.append({'id': 'pareto_shape_and_type', 'unequal_length_accepted': True, 'float_arguments_accepted': True,
                 'conclusion': 'zip truncates unequal vectors, and no rational-only input boundary is enforced.'})

allocate = states['lesson_420_07_ecological_reserves_and_population']['allocate_reserves']
capacity = 10**20 + 1
actual = allocate(capacity)
weights = [Q(3, 5), Q(1, 4), Q(3, 20)]
quotas = [w * capacity for w in weights]
expected = [q.numerator // q.denominator for q in quotas]
order = sorted(range(3), key=lambda i:(quotas[i] - expected[i], i), reverse=True)
for i in order[:capacity-sum(expected)]:
    expected[i] += 1
assert actual != expected and sum(actual) == sum(expected) == capacity
controls.append({'id': 'float_largest_remainder', 'capacity': capacity, 'recorded_algorithm': actual,
                 'exact_rational_algorithm_same_tie_policy': expected,
                 'conclusion': 'Float conversion erases the fractional priorities and assigns the last seat to the wrong reserve.'})

islands = states['lesson_420_10_open_horizons_and_multi_island_ecology']['IslandEcology'](2)
islands.islands[0].append('G')
try:
    islands.migrate(0, 7, 'G')
except IndexError:
    pass
else:
    raise AssertionError('expected invalid-target index error')
assert islands.islands == [[], []]
controls.append({'id': 'migration_validation_order', 'islands_after_invalid_target': islands.islands,
                 'conclusion': 'Source removal precedes target validation, losing the genome on an invalid target.'})

# A useful finite positive control: reachability agrees on all3-node digraphs.
reach = states['lesson_420_08_lineage_taint_and_custody_invalidation']['compute_forward_taint']
checks = 0
for bits in range(2**9):
    graph = {u:[v for v in range(3) if bits & (1 << (3*u+v))] for u in range(3)}
    for root in range(3):
        expected = {root}
        for _ in range(3):
            expected |= {v for u in list(expected) for v in graph[u]}
        assert reach(graph, root) == expected
        checks += 1
controls.append({'id': 'forward_taint_positive', 'finite_checks': checks,
                 'conclusion': 'The teaching reachability loop agrees with independent closure on all512three-vertex digraphs and allthree roots; no causal-truth claim follows.'})

out = {'status': 'complete_offline_reviewed_cell_controls', 'notebooks': rows, 'controls': controls,
       'limits': ['All11original notebook JSON bodies were fully read. Only their reviewed stdlib code cells ran, in isolated dictionaries; no Jupyter kernel or actual PCIV runtime was launched.',
                  'Stored notebook outputs were not rewritten. These toy findings are not automatically defects of the separately reviewed production classes.',
                  'No provider, native build, source rewrite or private benchmark access.']}
(REV / 'additional_eis_pciv_education_pciv_notebook_checks.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'notebooks': len(rows), 'controls': len(controls), 'positive_reachability_cases': checks, 'allocation_actual': actual, 'allocation_expected': expected if isinstance(expected,list) else 'see_control'}))
