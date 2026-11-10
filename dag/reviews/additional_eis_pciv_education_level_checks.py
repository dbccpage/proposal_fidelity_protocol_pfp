"""Compare two fully read teaching cells with their written level policies."""
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
frozen = {row['path']: row for row in scope['files']}


def cell_namespace(path):
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == frozen[path]['sha256']
    namespace = {}
    for cell in json.loads(raw)['cells']:
        if cell['cell_type'] != 'code':
            continue
        tree = ast.parse(''.join(cell['source']))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name == 'math' for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module == 'fractions'
        with redirect_stdout(io.StringIO()):
            exec(compile(tree, path, 'exec'), namespace)
    return namespace


allocation = 'education/010_oepciv/curriculum/420_population_reserves_persistence/notebooks/lesson_420_07_ecological_reserves_and_population.ipynb'
decay = 'education/010_oepciv/curriculum/410_selection_ranking_retrieval/notebooks/lesson_410_06_precedent_retrieval_and_evaporation.ipynb'
allocate = cell_namespace(allocation)['allocate_reserves']
evaporate = cell_namespace(decay)['evaporate_weight']
actual = allocate(10)
quotas = [Q(3, 5)*10, Q(1, 4)*10, Q(3, 20)*10]
required = [q.numerator // q.denominator for q in quotas]
priority = sorted(range(3), key=lambda i: (-(quotas[i]-required[i]), i))
for i in priority[:10-sum(required)]:
    required[i] += 1
assert actual == [6, 2, 2] and required == [6, 3, 1]
continuous = evaporate(1, 5, half_life=10)
discrete = Q(1, 2)**(5//10)
assert continuous != discrete and discrete == 1
at_boundary = evaporate(1, 10, half_life=10)
assert at_boundary == Q(1, 2)**(10//10) == Q(1, 2)

result = {
    'status': 'complete_offline_teaching_policy_controls',
    'owner_pins': [{'path': p, 'sha256': frozen[p]['sha256']} for p in [allocation, decay]],
    'controls': [
        {'id': 'capacity10_tie_policy', 'notebook': actual, 'written_level_policy': required,
         'conclusion': 'A small exact tie differs; this is separate from the large-capacity float precision counterexample.'},
        {'id': 'half_life_midpoint', 'notebook_continuous': continuous, 'written_discrete': str(discrete),
         'positive_boundary_agreement': str(Q(1, 2)),
         'conclusion': 'The notebook and level specify different decay functions. Both can be policies, but the difference must be explicit.'}
    ],
    'limits': ['Only the two previously fully read standard-library teaching cells were run in isolated dictionaries.',
               'No production runtime, provider, source edit or private benchmark access; no statistical efficacy inference.']
}
(REV / 'additional_eis_pciv_education_level_checks.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result['controls']))
