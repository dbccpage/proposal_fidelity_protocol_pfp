"""Bounded controls of reviewed EIS teaching cells; no actual EIS runtime imported."""
import ast
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
scope = json.loads((REV / 'additional_eis_pciv_education_remaining_scope.json').read_text())
rows = []
states = {}
trees = {}
prediction_self_checks = 0
for row in scope['files']:
    path = row['path']
    if not path.startswith('education/009_oeeis/curriculum/') or not path.endswith('.ipynb'):
        continue
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    notebook = json.loads(raw)
    code_cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
    assert len(code_cells) == 4
    parsed = [ast.parse(''.join(c['source'])) for c in code_cells]
    for tree in parsed:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(x.name in {'sys', 'hashlib'} for x in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module == 'fractions'
    pred = parsed[2].body
    assert isinstance(pred[0], ast.Assign) and isinstance(pred[0].value, ast.Constant)
    assert isinstance(pred[1], ast.Assert) and isinstance(pred[1].test, ast.Compare)
    assert pred[0].targets[0].id == pred[1].test.left.id == 'prediction'
    assert pred[1].test.comparators[0].value == pred[0].value.value
    prediction_self_checks += 1
    ns = {}
    output = io.StringIO()
    with redirect_stdout(output):
        for tree in parsed:
            exec(compile(tree, path, 'exec'), ns)
    stem = Path(path).stem
    states[stem] = ns
    trees[stem] = parsed
    rows.append({'path': path, 'sha256': row['sha256'], 'reviewed_code_cells': len(parsed),
                 'stored_execution_counts': [c['execution_count'] for c in code_cells],
                 'stored_output_count': sum(len(c['outputs']) for c in code_cells),
                 'fresh_cell_completion': 'pass', 'stdout': output.getvalue(),
                 'prediction_comparison': 'literal_assigned_then_compared_with_same_literal'})
assert len(rows) == prediction_self_checks == 13

report = states['lesson_500_01_eis_architecture_overview']['report']
report.is_admitted = True
assert report.is_admitted is True


class RemoveConstructorGuards(ast.NodeTransformer):
    removed = 0

    def visit_ClassDef(self, node):
        if node.name == 'AntiSkillSpecV2':
            for method in node.body:
                if isinstance(method, ast.FunctionDef) and method.name == '__init__':
                    self.removed += sum(isinstance(x, ast.If) for x in method.body)
                    method.body = [x for x in method.body if not isinstance(x, ast.If)]
        return node


stem = 'lesson_520_01_component_role_partitioning'
mutant = RemoveConstructorGuards()
mutated_trees = [mutant.visit(ast.parse(ast.unparse(t))) for t in trees[stem]]
assert mutant.removed == 2
ns = {}
output = io.StringIO()
with redirect_stdout(output):
    for tree in mutated_trees:
        exec(compile(ast.fix_missing_locations(tree), 'in_memory_teaching_guard_mutant', 'exec'), ns)
assert isinstance(ns['invalid_spec'], ns['AntiSkillSpecV2'])
assert ns['prediction'] == 'SPEC_PURITY_HOLD'

out = {'status': 'complete_offline_teaching_cell_checks', 'notebooks': rows,
       'prediction_self_comparisons': prediction_self_checks,
       'controls': [
           {'id': 'mutable_report', 'is_admitted_after_assignment': report.is_admitted,
            'conclusion': 'The overview class permits the direct assignment its manually raised falsifier claims to intercept.'},
           {'id': 'negative_test_vacuity', 'guards_removed_in_memory': mutant.removed,
            'whole_notebook_cells_complete': True, 'invalid_spec_created': True,
            'stdout': output.getvalue(),
            'conclusion': 'The exception-only negative test has no failure assertion when the expected exception is absent; both constructor guards can be deleted while every notebook cell completes.'}],
       'limits': ['Only fully reviewed stdlib teaching cells ran, with one in-memory AST mutant. No original notebook was rewritten, no Jupyter kernel or actual EIS runtime launched.',
                  'Constant prediction checks and manual exception demonstrations are pedagogical patterns, not operational detector/custody evidence.',
                  'No provider, native/Lean build, external source or private benchmark access.']}
(REV / 'additional_eis_pciv_education_eis_notebook_checks.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'notebooks': len(rows), 'reviewed_code_cells': len(rows)*4, 'constant_prediction_self_checks': prediction_self_checks,
                  'mutated_constructor_guards': mutant.removed, 'mutant_cells_completed': True}))
