"""End-to-end tests of the batch toolkit on a tiny dummy node in a temporary tree.

No network, no Lean, no cargo, no Mathlib: the dummy node's gates are plain Python commands. The
tree is built from the real stage helpers (prepare_stage.py, workflow, contracts, exact_json.py,
scripts/contract_scores.py) and a three-node DAG whose prompts come from the real generator.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import challenge  # noqa: E402
import common  # noqa: E402
import companions  # noqa: E402
import finalize  # noqa: E402
import generate_prompts as gen  # noqa: E402
import integrate  # noqa: E402
import pfp_batch  # noqa: E402
import preflight  # noqa: E402
import publish  # noqa: E402
import review  # noqa: E402
import selection  # noqa: E402
import spec_builder  # noqa: E402
import stages  # noqa: E402
import verify_batch  # noqa: E402

FIXED_NOW = datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
STATEMENT = {'DUMMY-ADD': 'For integers a and b the exact sum a+b equals b+a on the listed cases.',
             'DUMMY-MUL': 'For integers a and b the exact product a*b equals b*a on the listed cases.',
             'DUMMY-NEG': 'For integers a the exact negation of the negation of a is a on the listed cases.'}

ADDITION = "def add(a, b):\n    return a + b\n"
TEST = ("import sys, unittest\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))\n"
        "from addition import add\n\nclass T(unittest.TestCase):\n    def test_commutes(self):\n        self.assertEqual(add(2, 3), add(3, 2))\n\n"
        "if __name__ == '__main__':\n    unittest.main()\n")
REPLAY = ("import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))\n"
          "from addition import add\nfor line in sys.stdin.read().splitlines():\n    kind, a, b = line.split('\\t')\n    print('\\t'.join([kind, a, b, str(add(int(a), int(b)))]))\n")
CHECKER = '''import json, sys
from pathlib import Path

def require(ok, message):
    if not ok:
        raise ValueError(message)

def check(request_path, candidate_path):
    try:
        request = json.loads(Path(request_path).read_bytes())
        candidate = json.loads(Path(candidate_path).read_bytes())
        public = json.loads((Path(__file__).parent / 'public_input.json').read_bytes())
        for key in ('task_id', 'stage_id', 'attempt_id', 'input_sha256'):
            require(candidate[key] == request[key], 'binding ' + key)
        records = candidate['data']['records']
        require([r['input'] for r in records] == public['cases'], 'inputs differ from the public cases')
        for record in records:
            a, b = record['input']
            require(all(type(x) is str for x in record['input'] + record['output']), 'strings only')
            require(record['output'] == [str(int(a) + int(b))], 'wrong sum')
        require(set(candidate['data']) == {'records'}, 'extra keys')
        return {'records_checked': len(records)}
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ValueError('malformed: ' + repr(error))

if __name__ == '__main__':
    print(json.dumps(check(sys.argv[1], sys.argv[2])))
'''
FORMAT = "def lines(data):\n    return ['\\t'.join(['add'] + r['input'] + r['output']) for r in data['records']]\n"
SEMANTIC = '''def semantic_mutants(data, profile):
    def subtract(d):
        d['records'][0]['input'][1] = str(-int(d['records'][0]['input'][1]))
    return [{'id': 'subtraction_for_addition', 'rationale': 'A plausible reading error: b negated, output kept.', 'mutate': subtract}]

def semantic_controls(data, profile):
    def swap(d):
        d['records'][0]['input'].reverse()
        d['records'][0]['input'].reverse()
        d['records'][1]['output'] = list(d['records'][1]['output'])
    return [{'id': 'identity_relabel', 'rationale': 'Valid rewrite of the same record.', 'mutate': swap}]
'''
CASES = [['2', '3'], ['-4', '4']]
DATA = {'records': [{'input': ['2', '3'], 'output': ['5']}, {'input': ['-4', '4'], 'output': ['0']}]}


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode('utf-8'))


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def build_tree(root: Path):
    for name in ('prepare_stage.py', 'workflow.yaml', 'mode.yaml', 'stage_contracts.yaml', 'prompt_template.yaml', 'exact_json.py'):
        (root / 'dag/pfp').mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / 'dag/pfp' / name, root / 'dag/pfp' / name)
    (root / 'scripts').mkdir()
    shutil.copyfile(REPO / 'scripts/contract_scores.py', root / 'scripts/contract_scores.py')
    write(root / 'dag/pfp/prompt_audit.json', json.dumps({'nodes': [], 'prompts_reviewed': 0}))
    write(root / 'dag/theory_of_finite_qm.jsonl', '')
    (root / 'dag/derivations').mkdir()
    (root / 'dag/prompts').mkdir()
    write(root / 'dag/operads/index.json', json.dumps({'schema_id': 'x', 'nodes': []}))
    nodes = [{'id': i, 'stage': 'FINITE_QM_CORE', 'status': 'COMPUTATIONALLY_CHECKED', 'source_status': 'toy', 'statement': s,
              'source': [], 'lean': [], 'rust': [], 'imported_structure': [], 'bottleneck': 'toy bottleneck', 'tags': []} for i, s in STATEMENT.items()]
    write(root / 'dag/derivation_dag.json', json.dumps({'source_commit': 'dummy', 'nodes': nodes}))
    write(root / 'lean4/lean-toolchain', 'leanprover/lean4:v9.9.9\n')
    write(root / 'src/addition.py', ADDITION)
    write(root / 'tests/test_dummy.py', TEST)
    write(root / 'tests/replay.py', REPLAY)
    write(root / 'dag/pfp/batch_tools/toolkit_marker.py', 'VERSION = 1\n')
    code = gen.run(root, False, True, list(STATEMENT), False, out=open(os.devnull, 'w'))
    assert code == 0
    git(root, 'init', '-q')
    git(root, 'config', 'user.email', 't@example.invalid')
    git(root, 'config', 'user.name', 'T')
    git(root, 'config', 'core.autocrlf', 'false')
    git(root, 'add', '-A')
    git(root, 'commit', '-q', '-m', 'base')


def spec_for(task, hook=True, second=False):
    boundary = {'supports': 'Exact addition on the two listed integer pairs commutes.',
                'does_not_support': 'Commutativity for all integers or any other ring.',
                'narrowest_claim': 'Two exact integer pairs.',
                'next_test': 'Prove commutativity of integer addition in the kernel for symbolic a and b.'}
    profile = {
        'source_review_status': 'semantics_reviewed_for_selected_step', 'source_scope_review': 'Toy scope review of ' + task + '.',
        'independent_predicates': ['Recompute each sum with exact integers.'], 'claim_boundary': boundary, 'carrier': 'Int', 'coefficient_ring': 'Z',
        'production_sources': ['src/addition.py', 'tests/test_dummy.py', 'tests/replay.py'], 'build_sources': ['lean4/lean-toolchain'],
        'challenge_plan': 'Edit every coordinate; add subtraction-for-addition near miss.', 'composition_tree': ['add(neg(a), b)'],
        'anchors': ['src/addition.py'], 'checker_id': 'dummy-integer-sum-v1', 'result_or_obstruction': boundary['supports'],
        'next_mathematical_step': boundary['next_test'], 'report': '# ' + task + '\n\nToy report.', 'construction': 'Sums computed with Python integers.',
        'colour_meanings': {'Int': 'Exact Python integers'}, 'dag_status_depends_on_result': second,
        'p2_gates': [{'id': 'python', 'argv': ['{python}', '-X', 'utf8', 'tests/test_dummy.py'], 'needs': None, 'cwd': '.'},
                     {'id': 'replay', 'argv': ['{python}', '-X', 'utf8', 'tests/replay.py'], 'needs': None, 'cwd': '.', 'stdin_file': 'public_input.tsv'}],
        'p2_checks': {'wire': {'gate': 'replay'}, 'tests': {'python': {'gate': 'python', 'stream': 'stderr'}}}}
    op = lambda i, ins: {'id': i, 'ordered_inputs': ins, 'output': 'Int', 'arity': len(ins), 'carrier': 'Int', 'coefficient_ring': 'Z',
                         'hypotheses': ['exact integers'], 'semantic_predicate': 'integer ' + i}
    delta = {'add_or_refine_generators': [op('add', ['Int', 'Int']), op('neg', ['Int'])],
             'add_or_refine_relations': [{'id': 'comm', 'equation_or_predicate': 'add(a,b)=add(b,a)', 'typing_conditions': 'Int',
                                          'evidence_status': 'P1 candidate', 'scope': 'listed cases'}],
             'checked_compositions': [{'outer_operation': 'add', 'input_slot': 0, 'inner_operation': 'neg', 'colour_match': 'Int -> Int',
                                       'hypothesis_match': 'same carrier', 'licensing_relations': ['comm'], 'evidence_status': 'toy'}],
             'failed_compositions': [], 'counterexamples': [], 'open_obligations': ['General commutativity is not established by two cases.']}
    spec = {'profile': profile, 'public_input': {'cases': CASES}, 'operad_delta': delta, 'checker': 'check_candidate.py',
            'format': 'format_certificate.py', 'candidate': {'data': DATA, 'public_tsv': ''.join('add\t%s\t%s\n' % tuple(c) for c in CASES)}}
    if hook:
        spec['semantic_mutants'] = 'semantic_mutants.py'
    return spec


def prepare_node(batch, task, hook=True, second=False, data=None, adjust=None):
    specs = batch.dir / 'specs'
    write(specs / 'check_candidate.py', CHECKER)
    write(specs / 'format_certificate.py', FORMAT)
    write(specs / 'semantic_mutants.py', SEMANTIC)
    spec = spec_for(task, hook, second)
    if adjust:
        adjust(spec)
    stages.p0_request(batch, task)
    # The checker reads public_input.json beside itself; p0_missions writes it to the run folder.
    stages.p0_missions(batch, task, spec, specs)
    stages.submit_candidate(batch, task, data or spec['candidate']['data'], spec['candidate']['public_tsv'])
    return spec


class Dummy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / 'tree'
        cls.root.mkdir()
        build_tree(cls.root)
        cls.ctx = common.Ctx(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class EndToEnd(Dummy):
    def test_full_batch_then_verify_then_tamper(self):
        ctx = self.ctx
        # --- init: ordered selection, refuses to move the start
        with self.assertRaisesRegex(ValueError, 'first un-run index position 1'):
            selection.select_batch(ctx, 1, start=2, now=FIXED_NOW)
        directory = selection.select_batch(ctx, 1, start=1, now=FIXED_NOW)
        self.assertEqual(directory.name, '20300102T030405Z_prompts_1_1')
        chosen = json.loads((directory / 'selection.json').read_bytes())
        self.assertEqual([r['node_id'] for r in chosen['nodes']], ['DUMMY-ADD'])
        self.assertEqual(chosen['lean_toolchain'], 'v9.9.9')
        self.assertEqual(chosen['base_commit'], git(self.root, 'rev-parse', 'HEAD'))
        with self.assertRaisesRegex(ValueError, 'Batch folder exists'):
            selection.select_batch(ctx, 1, now=FIXED_NOW)
        batch = stages.Batch(ctx, directory)
        # --- P0/P1
        prepare_node(batch, 'DUMMY-ADD')
        run = batch.run('DUMMY-ADD')
        self.assertTrue((run / 'p0/source_inventory.json').is_file() and (run / 'p1/candidate.json').is_file())
        with self.assertRaisesRegex(ValueError, 'Refusing overwrite'):
            stages.submit_candidate(batch, 'DUMMY-ADD', DATA)
        # --- P2/P4/P5 through the shared driver
        outcome = challenge.run_node(batch, 'DUMMY-ADD')
        self.assertEqual(outcome['accepted_attempt'], 'p1')
        counts = outcome['mutant_counts']
        self.assertGreater(counts['coordinate'], 8)
        self.assertEqual((counts['semantic'], counts['semantic_controls']), (1, 1))
        host = common.load_json(run / 'p2/host_check.json')
        self.assertEqual(host['status'], 'accepted_candidate_for_challenge')
        self.assertEqual(host['predicate_results']['test_counts'], {'python': 1})
        self.assertTrue(host['predicate_results']['exact_cross_language_full_output'])
        index = {r['node_id']: r for r in common.load_json(ctx.index_path)['nodes']}
        self.assertEqual(index['DUMMY-ADD']['current_stage'], 'P5_RECORD')
        # a run node is refused by the next selection, which starts at the first un-run row
        second = selection.select_batch(ctx, 1, now=datetime(2030, 1, 2, 3, 4, 6, tzinfo=timezone.utc))
        self.assertEqual(common.load_json(second / 'selection.json')['nodes'][0]['node_id'], 'DUMMY-MUL')
        self.assertEqual(common.load_json(second / 'selection.json')['first_position'], 2)
        shutil.rmtree(second)
        # --- review, companions, integrate, finalize
        results = review.review_all(batch, 'audit')
        self.assertEqual(results[0]['task'], 'DUMMY-ADD')
        summary = companions.write_companions(batch)
        self.assertGreaterEqual(summary['live_subjects'], 5)
        combined = [p for p in self.root.rglob('*.contract.score.yaml')]
        self.assertTrue(any(p.name == 'check_candidate.contract.score.yaml' for p in combined))
        write(batch.dir / 'integration_gates.json', json.dumps([{'id': 'dummy_tests', 'argv': ['{python}', '-X', 'utf8', 'tests/test_dummy.py'],
                                                                   'cwd': '.', 'needs': None, 'optimizable': True, 'count': stages.PYTHON_TESTS}]))
        integration = integrate.integrate(batch, modes=('normal', 'optimized'))
        self.assertEqual(integration['test_counts'], {'dummy_tests': 1, 'dummy_tests_optimized': 1})
        # another run committed since selection extends an unselected operad collection: preserved as updated, not as a failure
        other = next(r for r in ctx.index()['nodes'] if r['node_id'] == 'DUMMY-MUL')['operad_collection']
        with open(self.root / other, 'ab') as handle:
            handle.write(b'# extended by a later committed run\n')
        git(self.root, 'add', other)
        git(self.root, 'commit', '-q', '-m', 'later run')
        # the toolkit may be fixed while a batch runs: that must not break the preservation proof
        write(self.root / 'dag/pfp/batch_tools/toolkit_marker.py', 'VERSION = 2\n')
        sealed = finalize.finalize(batch, 'audit')
        write(self.root / 'dag/pfp/batch_tools/toolkit_marker.py', 'VERSION = 1\n')
        self.assertEqual(sealed['counts']['semantic_mutants'], 1)
        preserved = common.load_json(batch.dir / 'review/preservation.json')['files']
        self.assertEqual([e['path'] for e in preserved if e.get('updated_since_base_by_committed_work')], [other])
        self.assertGreater(sealed['sealed_files'], 30)
        git_status = subprocess.run(['git', 'status', '--porcelain'], cwd=self.root, capture_output=True, text=True).stdout
        self.assertIn('dag/results/', git_status)
        # --- verify, then tamper with sealed bytes and a mutant outcome
        report = verify_batch.verify(batch)
        self.assertEqual((report['runs'], report['verified_nodes'][0]['semantic_mutants']), (1, 1))
        self.assertGreater(report['companions_checked'], 3)
        self.assertGreater(report['preserved_files_checked'], 5)
        # a later batch rewrites other rows of the shared index: the replay must still pass
        index_copy = ctx.index_path.read_bytes()
        shared = json.loads(index_copy)
        shared['claim'] = 'later batches rewrite rows of this file'
        ctx.index_path.write_bytes((json.dumps(shared, indent=2) + '\n').encode('utf-8'))
        verify_batch.verify(batch)
        ctx.index_path.write_bytes(index_copy)
        mutant = next((run / 'p4/mutants').glob('semantic_*.json'))
        original = mutant.read_bytes()
        mutant.write_bytes(original.replace(b'"-3"', b'"3"'))
        with self.assertRaisesRegex(ValueError, 'sealed artifact changed'):
            verify_batch.verify(batch)
        mutant.write_bytes(original)
        verify_batch.verify(batch)
        # --- publish refuses unowned changes, then commits only the manifest
        write(self.root / 'stray.txt', 'x')
        with self.assertRaisesRegex(ValueError, 'Unowned change'):
            publish.publish(batch, 'batch')
        (self.root / 'stray.txt').unlink()
        committed = publish.publish(batch, 'Run dummy batch', trailer='Co-Authored-By: Test <t@example.invalid>')
        self.assertFalse(committed['pushed'])
        self.assertIn('Co-Authored-By', git(self.root, 'log', '-1', '--format=%B'))
        self.assertEqual(git(self.root, 'status', '--porcelain'), '')
        # the sealed batch still verifies after the commit and with the next batch's index changes
        verify_batch.verify(batch)


class Guards(Dummy):
    def make_batch(self, name):
        root = Path(tempfile.mkdtemp(dir=self.tmp.name)) / 'tree'
        shutil.copytree(self.root, root, ignore=shutil.ignore_patterns('.git'))
        git(root, 'init', '-q')
        git(root, 'config', 'user.email', 't@example.invalid')
        git(root, 'config', 'user.name', 'T')
        git(root, 'add', '-A')
        git(root, 'commit', '-q', '-m', 'base')
        # a fresh index: nothing has run in this copy
        ctx = common.Ctx(root)
        return ctx, stages.Batch(ctx, selection.select_batch(ctx, 1, now=FIXED_NOW))

    def test_semantic_hook_required_unless_waived(self):
        ctx, batch = self.make_batch('a')
        batch_dir = batch.dir
        stages.p0_request(batch, 'DUMMY-ADD')
        specs = batch_dir / 'specs'
        write(specs / 'check_candidate.py', CHECKER)
        write(specs / 'format_certificate.py', FORMAT)
        spec = spec_for('DUMMY-ADD', hook=False)
        stages.p0_missions(batch, 'DUMMY-ADD', spec, specs)
        stages.submit_candidate(batch, 'DUMMY-ADD', DATA, spec['candidate']['public_tsv'])
        stages.p2(batch, 'DUMMY-ADD')
        with self.assertRaisesRegex(ValueError, 'semantic near-miss hook'):
            challenge.p4(batch, 'DUMMY-ADD')
        shutil.rmtree(batch.run('DUMMY-ADD') / 'p4')
        with self.assertRaisesRegex(ValueError, 'semantic near-miss hook'):
            challenge.p4(batch, 'DUMMY-ADD', waive_semantic='too short')
        shutil.rmtree(batch.run('DUMMY-ADD') / 'p4')
        counts = challenge.p4(batch, 'DUMMY-ADD', waive_semantic='No semantic counterexample exists for this toy sum beyond the coordinate edits.')
        self.assertEqual(counts['semantic'], 0)

    def test_second_reviewer_required_when_status_depends_on_result(self):
        ctx, batch = self.make_batch('b')
        prepare_node(batch, 'DUMMY-ADD', second=True)
        challenge.run_node(batch, 'DUMMY-ADD')
        review.review_all(batch, 'audit')
        integrate.integrate(batch)
        with self.assertRaisesRegex(ValueError, 'Second, independent review required'):
            finalize.finalize(batch, 'audit')
        author = common.load_json(batch.dir / 'execution_policy.json')['researcher']
        shutil.rmtree(review.review_dir(batch, 'DUMMY-ADD', 'audit'))
        review.review_all(batch, 'audit', {'DUMMY-ADD': {'reviewer': author, 'verdict': 'agree'}})
        with self.assertRaisesRegex(ValueError, 'Second, independent review required'):
            finalize.finalize(batch, 'audit')
        shutil.rmtree(review.review_dir(batch, 'DUMMY-ADD', 'audit'))
        review.review_all(batch, 'audit', {'DUMMY-ADD': {'reviewer': 'a different reviewer', 'verdict': 'agree', 'notes': 'rechecked the sums'}})
        self.assertGreater(finalize.finalize(batch, 'audit')['sealed_files'], 20)
        self.assertEqual(verify_batch.verify(batch)['runs'], 1)

    def test_repair_attempt_needs_a_repairable_host_check(self):
        ctx, batch = self.make_batch('c')
        prepare_node(batch, 'DUMMY-ADD')
        stages.p2(batch, 'DUMMY-ADD')
        with self.assertRaisesRegex(ValueError, 'host_transition_not_authorized'):
            stages.p3_request(batch, 'DUMMY-ADD', 'p3a')

    def fake_lean(self, directory):
        directory.mkdir()
        if os.name == 'nt':
            write(directory / 'lean.cmd', "@echo off\r\necho Lean (version %FAKE_LEAN_VERSION%, fake)\r\necho 'Dummy.thm' depends on axioms: [propext]\r\n%FAKE_LEAN_EXTRA%\r\n")
        else:
            write(directory / 'lean', "#!/bin/sh\necho \"Lean (version $FAKE_LEAN_VERSION, fake)\"\necho \"'Dummy.thm' depends on axioms: [propext]\"\n$FAKE_LEAN_EXTRA\n")
            (directory / 'lean').chmod(0o755)

    def lean_spec(self, spec):
        spec['profile']['p2_gates'].append({'id': 'lean', 'argv': ['{lean}', '--version'], 'needs': 'lean', 'cwd': 'lean4'})
        spec['profile']['p2_checks']['lean'] = {'gate': 'lean', 'anchors': ['Dummy.thm']}

    def test_lean_gate_reads_the_version_from_the_toolchain_file(self):
        from unittest import mock
        fakes = Path(tempfile.mkdtemp(dir=self.tmp.name)) / 'bin'
        self.fake_lean(fakes)
        outcomes = {}
        for label, version, extra in (('match', '9.9.9', 'echo ok'), ('mismatch', '1.2.3', 'echo ok'), ('sorry', '9.9.9', "echo 'Dummy.thm' depends on axioms: [sorryAx]")):
            ctx, batch = self.make_batch(label)
            environment = {'PATH': str(fakes) + os.pathsep + os.environ['PATH'], 'FAKE_LEAN_VERSION': version, 'FAKE_LEAN_EXTRA': extra}
            with mock.patch.dict(os.environ, environment):
                prepare_node(batch, 'DUMMY-ADD', adjust=self.lean_spec)
                result = stages.p2(batch, 'DUMMY-ADD')
            outcomes[label] = (result['status'], result['predicate_results']['lean_version']['matches'], result['bounded_failure_codes'])
        self.assertEqual(outcomes['match'], ('accepted_candidate_for_challenge', True, []))
        self.assertEqual(outcomes['mismatch'], ('repairable_candidate_defect', False, ['G5_SCOPE']))
        self.assertEqual(outcomes['sorry'], ('repairable_candidate_defect', True, ['G5_SCOPE']))

    def test_cargo_gate_runs_behind_the_target_guard(self):
        from unittest import mock
        fakes = Path(tempfile.mkdtemp(dir=self.tmp.name)) / 'bin'
        fakes.mkdir()
        if os.name == 'nt':
            write(fakes / 'cargo.cmd', "@echo off\r\necho target=%CARGO_TARGET_DIR%\r\n")
        else:
            write(fakes / 'cargo', '#!/bin/sh\necho "target=$CARGO_TARGET_DIR"\n')
            (fakes / 'cargo').chmod(0o755)
        target = Path(tempfile.mkdtemp(dir=self.tmp.name)) / 'ct'
        (target / 'debug').mkdir(parents=True)
        (target / 'debug/big.bin').write_bytes(b'0' * 2048)
        ctx, batch = self.make_batch('cargo')
        with mock.patch.dict(os.environ, {'PATH': str(fakes) + os.pathsep + os.environ['PATH']}):
            prepare_node(batch, 'DUMMY-ADD', adjust=lambda s: s['profile']['p2_gates'].append(
                {'id': 'rust', 'argv': ['{cargo}', 'test'], 'needs': 'cargo', 'cwd': '.'}))
            result = stages.p2(batch, 'DUMMY-ADD', min_free_gb=0.0001, max_target_gb=1e-9, cargo_target=str(target), max_path_chars=400)
        self.assertEqual(result['status'], 'accepted_candidate_for_challenge')
        self.assertTrue(result['predicate_results']['cargo_guard']['cleared'])
        self.assertFalse((target / 'debug/big.bin').exists())
        run = batch.run('DUMMY-ADD')
        self.assertIn('target=' + str(target), (run / 'p2/native/rust.stdout.log').read_text())
        with mock.patch.dict(os.environ, {'PATH': str(fakes) + os.pathsep + os.environ['PATH']}):
            shutil.rmtree(run / 'p2')
            with self.assertRaises(common.DiskSpaceError):
                stages.p2(batch, 'DUMMY-ADD', min_free_gb=10 ** 9, cargo_target=str(target), max_path_chars=400)

    def test_failed_gate_is_retained_and_repair_is_a_new_attempt(self):
        ctx, batch = self.make_batch('d')
        bad = json.loads(json.dumps(DATA))
        bad['records'][0]['output'] = ['6']
        prepare_node(batch, 'DUMMY-ADD', data=bad)
        run = batch.run('DUMMY-ADD')
        # The checker rejects the wrong sum, so P2 must report a repairable defect and keep its receipts.
        result = stages.p2(batch, 'DUMMY-ADD')
        self.assertEqual((result['status'], result['bounded_failure_codes']), ('repairable_candidate_defect', ['G3_WITNESS']))
        self.assertNotEqual(result['predicate_results']['native_exit_codes']['certificate'], 0)
        with self.assertRaises(ValueError):
            challenge.run_node(batch, 'DUMMY-ADD')
        stages.p3_request(batch, 'DUMMY-ADD', 'p3a')
        stages.submit_candidate(batch, 'DUMMY-ADD', DATA, attempt='p3a')
        outcome = challenge.run_node(batch, 'DUMMY-ADD', attempt='p3a')
        self.assertEqual(outcome['accepted_attempt'], 'p3a')
        self.assertEqual(common.load_json(run / 'accepted.json')['failed_checkpoints'], ['p2'])
        self.assertTrue((run / 'p2/native/certificate_receipt.json').is_file())


BOUND_CHECKER = """import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'dag/pfp/prepare_stage.py').is_file())
sys.path.insert(0, str(ROOT / 'dag/pfp'))
import exact_json as E

def check(request, candidate):
    try:
        _, cand, public = E.bound(request, candidate, 'DUMMY-ADD')
        records = cand['data']['records']
        if [r['input'] for r in records] != public['cases']:
            raise ValueError('inputs differ')
        for r in records:
            a, b = r['input']
            if r['output'] != [str(int(a) + int(b))]:
                raise ValueError('wrong sum')
        if set(cand['data']) != {'records'}:
            raise ValueError('extra keys')
        return {'ok': True}
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ValueError('malformed ' + repr(error))
"""
LAZY_CHECKER = "def check(request, candidate):\n    return {'ok': True}\n"


class SpecBuilderAndPreflight(Dummy):
    def spec_dir(self, name, checker):
        folder = self.root / 'specs_pre' / name
        write(folder / 'check_candidate.py', checker)
        write(folder / 'format_certificate.py', FORMAT)
        write(folder / 'semantic_mutants.py', SEMANTIC)
        return folder

    def test_build_spec_declares_the_four_standard_gates_and_validates(self):
        boundary = {'supports': 's', 'does_not_support': 'general case of the thing',
                    'narrowest_claim': 'n', 'next_test': 'Prove the unnormalized statement for three sectors with a unitary mix.'}
        gen = {'id': 'op', 'ordered_inputs': ['A'], 'output': 'A', 'semantic_predicate': 'p', 'hypotheses': ['h']}
        spec = spec_builder.build_spec(
            node='X', short='x', lean='XMod', anchors=['XMod.t'], cases=[[1]], public_tsv='x\t1\n', data={'records': []}, scope_review='scope',
            predicates=['q'], boundary=boundary, generators=[gen], relations=[{'id': 'r', 'equation_or_predicate': 'e'}],
            compositions=[{'outer_operation': 'op', 'input_slot': 0, 'inner_operation': 'op'}], open_obligations=['o'], depends_on_result=True)
        gates = {g['id']: g for g in spec['profile']['p2_gates']}
        self.assertEqual(sorted(gates), ['lean', 'python', 'rust', 'rust_replay'])
        self.assertEqual((gates['rust']['needs'], gates['lean']['needs'], gates['python']['needs']), ('cargo', 'lean', None))
        self.assertEqual(gates['lean']['argv'][-1], 'XMod.lean')
        self.assertTrue(spec['profile']['dag_status_depends_on_result'])
        self.assertIn('lean4/XMod.lean', spec['profile']['production_sources'])
        stages.validate_spec(spec['profile'], spec['operad_delta'])
        self.assertEqual(spec['operad_delta']['add_or_refine_generators'][0]['arity'], 1)
        mismatched = spec_builder.build_spec(
            node='X', short='x', lean='XMod', anchors=['XMod.t'], cases=[[1]], public_tsv='x\t1\n', data={}, scope_review='scope', predicates=['q'], boundary=boundary,
            generators=[dict(gen, output='B'), dict(gen, id='op2', ordered_inputs=['B'], output='C')], relations=[{'id': 'r', 'equation_or_predicate': 'e'}],
            compositions=[{'outer_operation': 'op', 'input_slot': 0, 'inner_operation': 'op2'}], open_obligations=['o'])
        self.assertEqual(len(mismatched['operad_delta']['failed_compositions']), 1)
        self.assertIn('Colour mismatch', mismatched['operad_delta']['failed_compositions'][0]['reason'])
        self.assertEqual([(c['outer_operation'], c['inner_operation']) for c in mismatched['operad_delta']['checked_compositions']], [('op2', 'op')])
        bad = dict(spec['operad_delta'], add_or_refine_generators=[dict(gen, output='B', arity=1)])
        with self.assertRaisesRegex(ValueError, 'Graft colour mismatch'):
            stages.validate_spec(spec['profile'], bad)

    def test_preflight_runs_every_mutant_and_catches_a_lazy_checker(self):
        spec = spec_for('DUMMY-ADD')
        folder = self.spec_dir('good', BOUND_CHECKER)
        report = preflight.preflight(self.ctx, 'DUMMY-ADD', folder, spec=spec)
        self.assertGreater(report['coordinate_mutants'], 5)
        self.assertEqual((report['semantic_mutants'], report['semantic_controls']), (1, 1))
        lazy = self.spec_dir('lazy', LAZY_CHECKER)
        with self.assertRaisesRegex(ValueError, 'accepts coordinate mutants'):
            preflight.preflight(self.ctx, 'DUMMY-ADD', lazy, spec=spec)

    def test_preflight_rejects_wire_lines_with_empty_trailing_fields(self):
        spec = spec_for('DUMMY-ADD')
        folder = self.spec_dir('wire', BOUND_CHECKER)
        write(folder / 'format_certificate.py', "def lines(data):\n    return ['add\\t1\\t']\n")
        with self.assertRaisesRegex(ValueError, 'non-empty single lines'):
            preflight.preflight(self.ctx, 'DUMMY-ADD', folder, spec=spec)


class Units(unittest.TestCase):
    def test_historical_version_accepts_only_committed_versions_of_a_build_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git(root, 'init', '-q')
            git(root, 'config', 'user.email', 't@example.invalid')
            git(root, 'config', 'user.name', 'T')
            write(root / 'Cargo.toml', 'a = 1\n')
            git(root, 'add', '.')
            git(root, 'commit', '-q', '-m', 'one')
            write(root / 'Cargo.toml', 'a = 2\n')
            git(root, 'commit', '-q', '-am', 'two')
            digest = lambda text: hashlib.sha256(text.encode('utf-8')).hexdigest()
            self.assertTrue(verify_batch.historical_version(root, 'Cargo.toml', digest('a = 1\n')))
            self.assertTrue(verify_batch.historical_version(root, 'Cargo.toml', digest('a = 2\n')))
            self.assertFalse(verify_batch.historical_version(root, 'Cargo.toml', digest('a = 3\n')))

    def test_coordinate_mutants_cover_leaves_tails_and_keys(self):
        names = [n for n, _ in challenge.coordinate_mutants(DATA)]
        self.assertIn('coordinate_records/0/input/0', names)
        self.assertIn('drop_last_records', names)
        self.assertIn('delete_(root)/records', names)
        self.assertIn('drop_last_records/1/input', names)
        for name, mutate in challenge.coordinate_mutants(DATA):
            copy = json.loads(json.dumps(DATA))
            mutate(copy)
            self.assertNotEqual(copy, DATA, name)
        self.assertEqual(challenge.perturbed('2'), '3')
        self.assertEqual(challenge.perturbed('1/2'), '3/2')
        self.assertEqual(challenge.perturbed(True), False)
        self.assertEqual(challenge.perturbed('abc'), 'abc~')

    def test_boilerplate_next_test_is_refused(self):
        spec = spec_for('X')
        profile, delta = spec['profile'], spec['operad_delta']
        stages.validate_spec(profile, delta)
        for text in ('Challenge every output coordinate and strict custody/type boundary, then address the explicit unpaid mathematical bridge.',
                     'TBD', profile['claim_boundary']['does_not_support']):
            bad = json.loads(json.dumps(profile))
            bad['claim_boundary']['next_test'] = text
            with self.assertRaisesRegex(ValueError, 'next_test'):
                stages.validate_spec(bad, delta)

    def test_lean_version_is_read_from_the_toolchain_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'dag/pfp').mkdir(parents=True)
            (root / 'dag/pfp/prepare_stage.py').write_text('')
            ctx = common.Ctx(root)
            with self.assertRaises(ValueError):
                common.lean_toolchain(ctx)
            write(root / 'lean4/lean-toolchain', 'leanprover/lean4:v4.35.0\n')
            self.assertEqual(common.lean_toolchain(ctx), 'v4.35.0')
            self.assertTrue(common.check_lean_version(ctx, 'Lean (version 4.35.0, x86_64-w64-windows-gnu, Release)'))
            self.assertFalse(common.check_lean_version(ctx, 'Lean (version 4.33.1, x86_64)'))
            write(root / 'lean4/lean-toolchain', 'leanprover/lean4:v4.99.0-rc1\n')
            self.assertEqual(common.lean_toolchain(ctx), 'v4.99.0-rc1')
        for path in HERE.glob('*.py'):
            self.assertNotRegex(path.read_text(encoding='utf-8').replace('4.33.1', '').replace('4.35.0', '').replace('4.99.0', '').replace('9.9.9', ''),
                                r'lean4:v\d', path.name)

    def test_disk_precheck_and_cargo_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(common.DiskSpaceError):
                common.disk_precheck(tmp, 10 ** 9, 'test build')
            self.assertGreater(common.disk_precheck(tmp, 0.0001, 'test build'), 0)
            target = Path(tmp) / 'ct'
            (target / 'debug').mkdir(parents=True)
            (target / 'debug/big.bin').write_bytes(b'0' * 4096)
            kept = common.cargo_target_guard(target, min_free_gb=0.0001, max_target_gb=1.0, max_path_chars=400)
            self.assertFalse(kept['report']['cleared'])
            self.assertTrue((target / 'debug/big.bin').is_file())
            cleared = common.cargo_target_guard(target, min_free_gb=0.0001, max_target_gb=1e-9, max_path_chars=400)
            self.assertTrue(cleared['report']['cleared'])
            self.assertFalse((target / 'debug/big.bin').exists())
            self.assertEqual(cleared['env']['CARGO_TARGET_DIR'], str(target))
            with self.assertRaises(common.DiskSpaceError):
                common.cargo_target_guard(target, min_free_gb=10 ** 9, max_path_chars=400)
            if os.name == 'nt':
                with self.assertRaisesRegex(ValueError, 'too long'):
                    common.cargo_target_guard(Path(tmp) / ('x' * 80), min_free_gb=0.0001)

    def test_cli_toolchain_reads_the_real_toolchain_file(self):
        import io
        from contextlib import redirect_stdout
        stream = io.StringIO()
        with redirect_stdout(stream):
            pfp_batch.main(['--root', str(REPO), 'toolchain'])
        expected = (REPO / 'lean4/lean-toolchain').read_text(encoding='utf-8').split(':v')[-1].strip()
        self.assertEqual(json.loads(stream.getvalue())['lean_toolchain'], 'v' + expected)


if __name__ == '__main__':
    unittest.main()
