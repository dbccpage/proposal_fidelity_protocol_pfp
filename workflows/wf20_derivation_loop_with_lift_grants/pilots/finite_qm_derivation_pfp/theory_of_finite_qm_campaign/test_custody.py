"""Synthetic custody protocol fixtures, not mathematical evidence or expected answers."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from custody import Custody, SCHEMA, blob, rewrite, sha


class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.snapshot = 'dag/results/custody/fixture/snapshots'
        self.expected = {}
        entries = []
        cases = [
            ('prompt', 'dag/prompts/FINITE_QM__FQ-TEST.yaml',
             'dag/prompts/finite_qm_fq_test.yaml',
             b'operad_record: ../operads/FQ-TEST.yaml\nuser_prompt: Open FQ-TEST.yaml. Weight=14/5\n',
             {'FQ-TEST.yaml': 'fq_test.yaml'}, ['FQ-TEST']),
            ('paper', 'dag/derivations/fixture/TFQ-1_source.md',
             'dag/derivations/fixture/tfq_1_source.md',
             b'See [TFQ-2](TFQ-2_target.md). Weight=14/5.\n',
             {'TFQ-2_target.md': 'tfq_2_target.md'}, ['FQ-TEST', 'FQ-SECOND']),
        ]
        for kind, old, path, before, aliases, uses in cases:
            after = rewrite(before, aliases)
            a, b = self.snapshot+'/before/'+old, self.snapshot+'/after/'+path
            self.put(a, before); self.put(b, after); self.put(path, after)
            self.expected[kind] = sha(before)
            entries.append(dict(kind=kind, path=path, historical_path=old,
                                historical_sha256=sha(before), historical_git_blob=blob(before),
                                historical_snapshot=a, current_sha256=sha(after),
                                current_git_blob=blob(after), current_snapshot=b,
                                filename_renames=aliases, line_endings='preserve', uses=uses))
        audit = json.dumps({'scope': 'Synthetic historical custody fixture'}).encode()
        self.put('dag/pfp/prompt_audit.json', audit)
        self.data = dict(schema_id=SCHEMA, authority_effect='None', snapshot_root=self.snapshot,
                         historical_audit_sha256=sha(audit), artifacts=entries)
        self.save()

    def put(self, path, data):
        p=self.root/path; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)

    def save(self):
        self.put('dag/pfp/filename_custody.json', json.dumps(self.data).encode())

    def consume(self, custody):
        for entry in self.data['artifacts']:
            for node in entry['uses']:
                self.assertTrue(custody.matches(entry['kind'], entry['path'],
                                                 self.expected[entry['kind']], node))
        custody.finish()

    def test_valid_filename_only_successors(self):
        self.consume(Custody(self.root))

    def test_whole_filename_and_sentence_boundaries(self):
        before=b'FQ-TEST.yaml. [x](dir/FQ-TEST.yaml#anchor) FQ-TEST.yaml.bak FQ-TEST.yaml_extra AFQ-TEST.yaml'
        after=b'fq_test.yaml. [x](dir/fq_test.yaml#anchor) FQ-TEST.yaml.bak FQ-TEST.yaml_extra AFQ-TEST.yaml'
        self.assertEqual(rewrite(before, {'FQ-TEST.yaml':'fq_test.yaml'}), after)

    def test_explicit_crlf_conversion_preserves_the_historical_bytes(self):
        entry=self.data['artifacts'][1]
        before=(self.root/entry['historical_snapshot']).read_bytes().replace(b'\n',b'\r\n')
        self.put(entry['historical_snapshot'],before)
        entry['historical_sha256']=self.expected['paper']=sha(before)
        entry['historical_git_blob']=blob(before);entry['line_endings']='crlf_to_lf';self.save()
        self.consume(Custody(self.root))
        self.assertIn(b'\r\n',(self.root/entry['historical_snapshot']).read_bytes())
        entry['line_endings']='lf_to_crlf';self.save()
        with self.assertRaisesRegex(ValueError,'line_endings'):Custody(self.root)

    def test_live_content_edit_is_rejected(self):
        entry=self.data['artifacts'][0]
        self.put(entry['path'], (self.root/entry['path']).read_bytes().replace(b'14/5', b'15/5'))
        with self.assertRaisesRegex(ValueError, 'current_bytes'): Custody(self.root)

    def test_mutation_after_loading_is_rejected(self):
        c=Custody(self.root);entry=self.data['artifacts'][0];self.put(entry['path'], b'forged')
        self.assertFalse(c.matches('prompt',entry['path'],self.expected['prompt'],'FQ-TEST'))

    def test_forged_current_hash_cannot_authorize_mathematics_change(self):
        entry=self.data['artifacts'][0]
        forged=(self.root/entry['path']).read_bytes().replace(b'14/5',b'15/5')
        self.put(entry['path'],forged);self.put(entry['current_snapshot'],forged)
        entry['current_sha256']=sha(forged);entry['current_git_blob']=blob(forged);self.save()
        with self.assertRaisesRegex(ValueError,'not_filename_only'): Custody(self.root)

    def test_forging_both_snapshots_cannot_replace_the_historical_pin(self):
        entry=self.data['artifacts'][0]
        for side in ['historical','current']:
            forged=(self.root/entry[side+'_snapshot']).read_bytes().replace(b'14/5',b'15/5')
            self.put(entry[side+'_snapshot'],forged)
            entry[side+'_sha256']=sha(forged);entry[side+'_git_blob']=blob(forged)
            if side=='current':self.put(entry['path'],forged)
        self.save();c=Custody(self.root)
        with self.assertRaisesRegex(ValueError,'historical_binding'):
            c.matches('prompt',entry['path'],self.expected['prompt'],'FQ-TEST')

    def test_historical_rollback_cannot_bypass_the_current_pin(self):
        entry=self.data['artifacts'][0]
        self.put(entry['path'],(self.root/entry['historical_snapshot']).read_bytes())
        with self.assertRaisesRegex(ValueError,'current_bytes'): Custody(self.root)

    def test_missing_entry_does_not_waive_a_changed_pin(self):
        removed=self.data['artifacts'].pop();self.save();c=Custody(self.root)
        self.assertFalse(c.matches('paper',removed['path'],self.expected['paper'],'FQ-TEST'))

    def test_missing_snapshot_is_rejected(self):
        (self.root/self.data['artifacts'][0]['historical_snapshot']).unlink()
        with self.assertRaises(OSError): Custody(self.root)

    def test_duplicate_artifact_is_rejected(self):
        self.data['artifacts'].append(copy.deepcopy(self.data['artifacts'][0]));self.save()
        with self.assertRaisesRegex(ValueError,'duplicate_artifact'): Custody(self.root)

    def test_use_coverage_and_task_binding_are_required(self):
        c=Custody(self.root);entry=self.data['artifacts'][0]
        with self.assertRaisesRegex(ValueError,'historical_binding'):
            c.matches('prompt',entry['path'],self.expected['prompt'],'WRONG-TASK')
        with self.assertRaises(ValueError):c.finish()
        self.data['artifacts'][0]['uses'].append('PHANTOM');self.save();c=Custody(self.root)
        for e in self.data['artifacts']:
            for node in e['uses']:
                if node!='PHANTOM':c.matches(e['kind'],e['path'],self.expected[e['kind']],node)
        with self.assertRaisesRegex(ValueError,'use_coverage'): c.finish()

    def test_duplicate_uses_are_rejected(self):
        self.data['artifacts'][0]['uses'].append('FQ-TEST');self.save()
        with self.assertRaisesRegex(ValueError,'uses'): Custody(self.root)

    def test_snapshot_path_escape_is_rejected(self):
        self.data['artifacts'][0]['historical_snapshot']=self.snapshot+'/../outside';self.save()
        with self.assertRaisesRegex(ValueError,'path_escape'): Custody(self.root)

    def test_noncanonical_text_substitutions_are_rejected(self):
        self.data['artifacts'][0]['filename_renames']={'14/5':'15/5'};self.save()
        with self.assertRaisesRegex(ValueError,'filename'): Custody(self.root)

    def test_historical_audit_changes_are_rejected(self):
        self.put('dag/pfp/prompt_audit.json', b'{"forged":true}')
        with self.assertRaisesRegex(ValueError,'historical_audit_changed'): Custody(self.root)

    def test_boolean_digest_and_extra_oracle_fields_are_rejected(self):
        entry=self.data['artifacts'][0];entry['historical_sha256']=True;self.save()
        with self.assertRaises(ValueError):Custody(self.root)
        entry['historical_sha256']=self.expected['prompt'];entry['expected_answer']=0;self.save()
        with self.assertRaisesRegex(ValueError,'entry_shape'):Custody(self.root)

    def test_duplicate_keys_and_floats_are_rejected(self):
        raw=json.dumps(self.data)
        for bad in ['{"schema_id":"forged",'+raw[1:],raw.replace('"artifacts":','"float":1.0,"artifacts":',1)]:
            self.put('dag/pfp/filename_custody.json',bad.encode())
            with self.assertRaises(ValueError):Custody(self.root)


if __name__=='__main__':unittest.main()
