"""Tests for the prompt generator and the corpus-derived validator count.

Every test that writes works on a throwaway copy of the files the validator reads, never on the
repository tree. The copy holds the sealed corpus (prompts, operads, audit, custody snapshots,
derivation papers and the Lean/Rust files the source bindings pin).
"""
import copy
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import generate_prompts as gen  # noqa: E402
import validate_prompts  # noqa: E402

COPY_DIRS = ['dag/pfp', 'dag/prompts', 'dag/operads', 'dag/derivations', 'dag/results/custody']
COPY_FILES = ['dag/derivation_dag.json', 'dag/theory_of_finite_qm.jsonl', 'dag/fragments/pregenesis_to_wdp.json',
              'scripts/contract_scores.py',
              'evidence/contract_score_migration/index.json']
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc')


def link_or_copy(source, target):
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def rewrite(path: Path, data: bytes):
    """Replace a file without touching other hard links to its old bytes."""
    path = Path(path)
    path.unlink()
    path.write_bytes(data)


def strip_generated(destination: Path):
    """Return the copy to the sealed corpus: drop every generated prompt, operad, audit row and index row.

    Once the repository holds the generated prompts, no node is missing; these tests need a tree in which
    some are, so they run on the sealed 177 whatever the repository now carries."""
    extension = destination / gen.EXTENSION_PATH
    if not extension.is_file():
        return
    generated = json.loads(extension.read_bytes())['nodes']
    for row in generated:
        (destination / row['prompt']).unlink()
        (destination / row['operad_collection']).unlink()
    extension.unlink()
    sealed = {row['node_id'] for row in json.loads((destination / 'dag/pfp/prompt_audit.json').read_bytes())['nodes']}
    index_path = destination / 'dag/operads/index.json'
    index = json.loads(index_path.read_bytes())
    index['nodes'] = [row for row in index['nodes'] if row['node_id'] in sealed]
    rewrite(index_path, gen.dump_json(index))


def build_overlay(destination: Path):
    """Copy what the validator and generator read; pinned source files come from the operad records."""
    for name in COPY_DIRS:
        shutil.copytree(REPO / name, destination / name, ignore=IGNORE, copy_function=link_or_copy)
    strip_generated(destination)
    for name in COPY_FILES:
        if (REPO / name).is_file():
            (destination / name).parent.mkdir(parents=True, exist_ok=True)
            link_or_copy(REPO / name, destination / name)
    pinned = set()
    for record in (destination / 'dag/operads').glob('*.yaml'):
        data = gen.load_yaml(record.read_bytes())
        pinned.update(b['path'] for b in data['source_bindings'] if b['availability'] == 'local')
    for name in sorted(pinned) + [p.relative_to(REPO).as_posix() for p in (REPO / 'lean4').glob('*.lean')]:
        source, target = REPO / name, destination / name
        if source.is_file() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            link_or_copy(source, target)


def sample_nodes(corpus):
    """One missing node per tier, preferring nodes with scanned candidates; deterministic."""
    chosen = {}
    for node in corpus.missing():
        tier = gen.tier_of(node['status'])
        built = gen.build_node(corpus, node)
        score = built['audit']['operation_candidates'] + built['audit']['relation_candidates']
        if tier not in chosen or (score and not chosen[tier][1]):
            chosen[tier] = (node['id'], score)
        if len(chosen) == 3 and all(s for _, s in chosen.values()):
            break
    return [chosen[t][0] for t in 'ABC']


class Overlay(unittest.TestCase):
    base = None

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.tmp.name) / 'base'
        build_overlay(cls.base)
        corpus = gen.Corpus(cls.base)
        cls.ids = sample_nodes(corpus)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def fresh(self):
        directory = Path(tempfile.mkdtemp(dir=self.tmp.name))
        shutil.copytree(self.base, directory / 'tree', copy_function=link_or_copy)
        return directory / 'tree'

    def write(self, root, ids=None, extra=()):
        out = io.StringIO()
        code = gen.run(root, False, True, list(ids or self.ids), False, out=out)
        self.assertEqual(code, 0, out.getvalue())
        return out.getvalue()

    def check(self, root, ids=None, all_missing=False):
        out = io.StringIO()
        code = gen.run(root, True, False, ids, all_missing, out=out)
        return code, json.loads(out.getvalue())


class SyncOwnedPapers(Overlay):
    def test_papers_the_pregenesis_sync_writes_are_never_pinned(self):
        corpus = gen.Corpus(self.base)
        self.assertTrue(corpus.sync_owned)
        owned = [path for tfq in corpus.sync_owned for path in corpus.papers.get(tfq, [])]
        self.assertTrue(owned)
        owned_rel = {corpus.rel(path) for path in owned}
        touched = 0
        for node in corpus.nodes:
            if any(rec in corpus.sync_owned for rec in corpus.records.get(node['id'], [])):
                touched += 1
            self.assertFalse(owned_rel & {pin['path'] for pin in gen.paper_pins(corpus, node['id'])}, node['id'])
        self.assertGreater(touched, 0)


class SampleGeneration(Overlay):
    def test_three_tiers_validate_and_counts_follow_the_corpus(self):
        root = self.fresh()
        before = validate_prompts.validate(root)
        self.assertEqual((before['errors'], before['prompts']), ([], 177))
        self.write(root)
        after = validate_prompts.validate(root)
        self.assertEqual(after['errors'], [])
        self.assertEqual((after['prompts'], after['collections']), (180, 180))
        extension = json.loads((root / gen.EXTENSION_PATH).read_bytes())
        self.assertEqual({r['tier'] for r in extension['nodes']}, {'A', 'B', 'C'})
        self.assertEqual(extension['prompts_reviewed'], 3)
        # The sealed audit is untouched.
        self.assertEqual((root / 'dag/pfp/prompt_audit.json').read_bytes(), (REPO / 'dag/pfp/prompt_audit.json').read_bytes())

    def test_statement_is_verbatim_and_names_follow_custody(self):
        root = self.fresh()
        self.write(root)
        corpus = gen.Corpus(root)
        for node_id in self.ids:
            node = corpus.by_id[node_id]
            path = root / corpus.ext_rows[node_id]['prompt']
            self.assertEqual(path.name, gen.canonical_filename('%s_%s_%s.yaml' % (node['stage'], node_id, node['status'])))
            prompt = gen.load_yaml(path.read_bytes())
            self.assertIn(node['statement'], prompt['user_prompt'])
            record = gen.load_yaml((path.parent / prompt['operad_record']).read_bytes())
            self.assertEqual(record['target']['source_statement'], node['statement'])
            self.assertEqual(record['presentation']['generators'], [])
            self.assertEqual(validate_prompts.check_presentation(record['presentation']), [])
            for pin in record['target']['paper_source_pins']:
                self.assertEqual(hashlib.sha256((root / pin['path']).read_bytes()).hexdigest(), pin['sha256'])
            self.assertTrue(path.read_bytes().endswith(b'\n') and b'\r' not in path.read_bytes())

    def test_idempotent_and_deterministic(self):
        first, second = self.fresh(), self.fresh()
        self.write(first)
        snapshot = {p: p.read_bytes() for p in (first / 'dag').rglob('*') if p.is_file() and 'results' not in p.parts}
        self.write(first)
        for path, data in snapshot.items():
            self.assertEqual(path.read_bytes(), data, path.name)
        self.write(second, list(reversed(self.ids)))
        for name in (gen.EXTENSION_PATH, 'dag/operads/index.json'):
            self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
        code, report = self.check(first, self.ids)
        self.assertEqual((code, report['current'], report['would_create'], report['stale']), (0, 3, 0, {}))

    def test_index_rows_follow_tier_order_after_the_sealed_head(self):
        root = self.fresh()
        self.write(root, list(reversed(self.ids)))
        rows = json.loads((root / 'dag/operads/index.json').read_bytes())['nodes']
        corpus = gen.Corpus(root)
        self.assertEqual([r['node_id'] for r in rows[:177]], gen.Corpus(self.base).base_ids)
        self.assertEqual([gen.tier_of(corpus.by_id[r['node_id']]['status']) for r in rows[177:]], ['A', 'B', 'C'])
        self.assertEqual(set(r['node_id'] for r in rows[177:]), set(self.ids))

    def test_statement_change_is_stale_and_regenerable(self):
        root = self.fresh()
        self.write(root)
        dag_path = root / 'dag/derivation_dag.json'
        dag = json.loads(dag_path.read_bytes())
        target = self.ids[1]
        for node in dag['nodes']:
            if node['id'] == target:
                node['statement'] += ' (Phase B narrowed statement.)'
        rewrite(dag_path, (json.dumps(dag, indent=2, ensure_ascii=False) + '\n').encode())
        code, report = self.check(root, self.ids)
        self.assertEqual(code, 1)
        self.assertEqual(list(report['stale']), [target])
        self.assertIn('statement_sha256', report['stale'][target])
        self.write(root)
        self.assertEqual(self.check(root, self.ids)[0], 0)
        self.assertEqual(validate_prompts.validate(root)['errors'], [])

    def test_changed_paper_pin_is_stale(self):
        root = self.fresh()
        self.write(root)
        corpus = gen.Corpus(root)
        pinned = [(n, corpus.ext_rows[n]['inputs']['paper_pins']) for n in self.ids if corpus.ext_rows[n]['inputs']['paper_pins']]
        node_id, pins = pinned[0]
        pinned_file = root / pins[0]['path']
        rewrite(pinned_file, pinned_file.read_bytes() + b'\nedited\n')
        code, report = self.check(root, self.ids)
        self.assertEqual(code, 1)
        self.assertIn('paper_pins', report['stale'][node_id])
        self.assertTrue(any('paper source pin changed' in e for e in validate_prompts.validate(root)['errors']))

    def test_executed_prompt_is_never_rewritten(self):
        root = self.fresh()
        self.write(root)
        index_path = root / 'dag/operads/index.json'
        index = json.loads(index_path.read_bytes())
        row = next(r for r in index['nodes'] if r['node_id'] == self.ids[0])
        row['latest_run'] = 'dag/results/x/runs/r'
        rewrite(index_path, (json.dumps(index, indent=2, ensure_ascii=False) + '\n').encode())
        dag_path = root / 'dag/derivation_dag.json'
        dag = json.loads(dag_path.read_bytes())
        for node in dag['nodes']:
            if node['id'] == self.ids[0]:
                node['statement'] += ' changed'
        rewrite(dag_path, (json.dumps(dag, indent=2, ensure_ascii=False) + '\n').encode())
        code, report = self.check(root, self.ids)
        self.assertEqual((code, list(report['executed_stale_needs_manual_delta'])), (1, [self.ids[0]]))
        prompt = root / gen.Corpus(root).ext_rows[self.ids[0]]['prompt']
        old = prompt.read_bytes()
        self.write(root)
        self.assertEqual(prompt.read_bytes(), old)
        kept = next(r for r in json.loads(index_path.read_bytes())['nodes'] if r['node_id'] == self.ids[0])
        self.assertEqual(kept['latest_run'], 'dag/results/x/runs/r')

    def test_status_change_keeps_the_prompt_file_name(self):
        root = self.fresh()
        self.write(root)
        corpus = gen.Corpus(root)
        name = corpus.ext_rows[self.ids[0]]['prompt']
        dag_path = root / 'dag/derivation_dag.json'
        dag = json.loads(dag_path.read_bytes())
        for node in dag['nodes']:
            if node['id'] == self.ids[0]:
                node['status'] = 'OPEN' if node['status'] != 'OPEN' else 'CONDITIONAL'
        rewrite(dag_path, (json.dumps(dag, indent=2, ensure_ascii=False) + '\n').encode())
        self.assertIn('status', self.check(root, self.ids)[1]['stale'][self.ids[0]])
        self.write(root)
        self.assertEqual(gen.Corpus(root).ext_rows[self.ids[0]]['prompt'], name)
        self.assertEqual(validate_prompts.validate(root)['errors'], [])


class ValidatorExtension(Overlay):
    def validate_after(self, mutate):
        root = self.fresh()
        self.write(root)
        mutate(root)
        return validate_prompts.validate(root)['errors']

    def test_row_missing_from_extension_is_an_identity_error(self):
        def drop(root):
            path = root / gen.EXTENSION_PATH
            data = json.loads(path.read_bytes())
            data['nodes'].pop()
            data['prompts_reviewed'] -= 1
            rewrite(path, json.dumps(data).encode())
        self.assertIn('corpus identity mismatch', self.validate_after(drop))

    def test_extra_prompt_without_row_is_an_identity_error(self):
        def extra(root):
            path = root / gen.EXTENSION_PATH
            data = json.loads(path.read_bytes())
            data['nodes'].pop()
            data['prompts_reviewed'] -= 1
            rewrite(path, json.dumps(data).encode())
            index_path = root / 'dag/operads/index.json'
            index = json.loads(index_path.read_bytes())
            index['nodes'].pop()
            rewrite(index_path, json.dumps(index).encode())
        errors = self.validate_after(extra)
        self.assertIn('corpus identity mismatch', errors)

    def test_tampered_prompt_fails_audit_hash(self):
        def tamper(root):
            path = root / gen.Corpus(root).ext_rows[self.ids[0]]['prompt']
            rewrite(path, path.read_bytes() + b'# edited\n')
        self.assertIn(self.ids[0] + ': audit hash mismatch', self.validate_after(tamper))

    def test_unbound_extension_is_rejected(self):
        def rebind(root):
            path = root / gen.EXTENSION_PATH
            data = json.loads(path.read_bytes())
            data['base_audit_sha256'] = '0' * 64
            rewrite(path, json.dumps(data).encode())
        self.assertIn('audit extension: not bound to the sealed audit', self.validate_after(rebind))

    def test_extension_may_not_repeat_a_sealed_node(self):
        def repeat(root):
            path = root / gen.EXTENSION_PATH
            data = json.loads(path.read_bytes())
            sealed = json.loads((root / 'dag/pfp/prompt_audit.json').read_bytes())['nodes'][0]
            data['nodes'].append(copy.deepcopy(sealed))
            data['prompts_reviewed'] += 1
            rewrite(path, json.dumps(data).encode())
        self.assertIn('extension repeats a sealed audit node', self.validate_after(repeat))

    def test_stale_local_source_pin_still_fails(self):
        def edit(root):
            record = gen.load_yaml((root / gen.Corpus(root).ext_rows[self.ids[0]]['operad_collection']).read_bytes())
            local = [b for b in record['source_bindings'] if b['availability'] == 'local']
            if not local:
                local = [b for b in gen.load_yaml((root / 'dag/operads/pg_wdp_growth_no_repair.yaml').read_bytes())['source_bindings']
                         if b['availability'] == 'local']
            source = root / local[0]['path']
            rewrite(source, source.read_bytes() + b'\n-- edited\n')
        self.assertTrue(any('local source pin changed' in e for e in self.validate_after(edit)))

    def test_missing_extension_equals_sealed_corpus(self):
        root = self.fresh()
        result = validate_prompts.validate(root)
        self.assertEqual((result['errors'], result['prompts']), ([], 177))


class ScanUnits(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'lean4').mkdir()
        (self.root / 'lean4/A.lean').write_text(
            'namespace Q\n'
            'structure Pt where\n  x : Nat\n\n'
            'def double (p : Pt) : Pt := Pt.mk (p.x + p.x)\n\n'
            'def helper (n : Nat) : Nat := n\n\n'
            'theorem double_x (p : Pt) : (double p).x = p.x + p.x := by\n  rfl\n\n'
            'theorem master_census_witness (n : Nat) : n = n := rfl\n'
            'end Q\n', encoding='utf-8')
        (self.root / 'dag/pfp').mkdir(parents=True)
        for name, content in (('dag/derivation_dag.json', json.dumps({'nodes': [], 'source_commit': 'c'})),
                              ('dag/theory_of_finite_qm.jsonl', ''),
                              ('dag/operads/index.json', json.dumps({'nodes': []})),
                              ('dag/pfp/prompt_audit.json', json.dumps({'nodes': [], 'prompts_reviewed': 0}))):
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text(content, encoding='utf-8')
        (self.root / 'dag/derivations').mkdir()
        (self.root / 'dag/prompts').mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_resolves_namespaced_declarations_and_follows_definitions(self):
        corpus = gen.Corpus(self.root)
        node = {'id': 'X-1', 'lean': ['lean4/quantum_mechanics/A.lean::Q.double_x', 'lean4/A.lean::Q.master_census_witness',
                                      'omega_engine/other.rs::fn_name', 'lean4/Missing.lean::Q.t'], 'rust': []}
        bindings, operations, relations, excluded, pins = gen.mine_node(corpus, node)
        self.assertEqual([r['name'] for r in relations], ['double_x'])
        self.assertEqual([o['name'] for o in operations], ['Pt', 'double'])
        self.assertEqual([e['name'] for e in excluded], ['master_census_witness'])
        self.assertEqual([b['availability'] for b in bindings], ['local', 'local', 'external', 'unavailable'])
        self.assertIsNone(bindings[2]['sha256'])
        self.assertEqual(list(pins), ['lean4/A.lean'])
        self.assertTrue(relations[0]['signature_excerpt'].startswith('theorem double_x'))
        self.assertNotIn(':=', relations[0]['signature_excerpt'])

    def test_tiers(self):
        self.assertEqual([gen.tier_of(s) for s in ('OPEN', 'REFUTED', 'PROVED_LEAN', 'DEFINITION', 'ADMITTED_PRIMITIVE')],
                         ['A', 'A', 'B', 'C', 'C'])
        with self.assertRaises(ValueError):
            gen.tier_of('INVENTED')


if __name__ == '__main__':
    unittest.main()
