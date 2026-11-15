"""WF57: what the workflow hands to the Rust host and reports back. Needs the ``pfp_operad`` binary."""
from __future__ import annotations

import hashlib
import json
import sys

from pfp.infrastructure import operad_host
from pfp_core import REPO_ROOT
from pfp_core.workflow_families.base import FixtureProposer, new_budget, run_fixture
from pfp_core.workflow_families.learning import EXAMPLE_LEDGER, lines
from pfp_core.workflow_families.repair import EXAMPLE, FOLDER, TASK_FIELDS, HostTestedPatchRepair

FAMILY = HostTestedPatchRepair()
ADJUST = 'def adjust(n):\n    if n < 0:\n        return n\n    return n - 1\n'
FAILED_BEFORE = [('operation', 1), ('answer', 0)]


def exits(rows):
    return [(row['check_id'], row['code']) for row in rows]


def last_record(out):
    return json.loads(out.detail['ledger'][-1])['record']


def test_the_verdict_and_the_record_are_the_hosts():
    out = run_fixture(FAMILY, 'patch_repairs_the_refused_operation')
    record = out.detail['record']
    assert (out.verdict, out.code) == ('HOST_CERTIFIED', 'REPAIRED')
    assert (exits(record['baseline']), exits(record['after'])) == (FAILED_BEFORE, [('operation', 0), ('answer', 0)])
    assert (record['trace'], record['changed_paths'], record['source_intact']) == ('CREIMT', ['operation.json'], True)
    assert (record['failure'], out.detail['ledger']) == (None, [])
    assert out.host['certified_predicates'] == {'patch_repairs_the_working_copy': True}


def test_refusals_carry_the_hosts_code():
    codes = {name: run_fixture(FAMILY, name).code for name, (_bundle, expected) in FAMILY.fixtures().items()
             if expected == 'REFUSED'}
    assert codes == {
        'patch_that_leaves_the_check_failing': 'INEFFECTIVE',
        'failed_patch_joins_an_existing_ledger': 'INEFFECTIVE',
        'patch_that_breaks_the_passing_check': 'REGRESSION',
        'patch_outside_the_write_set': 'PATCH_SCOPE_REFUSED',
        'reply_that_widens_its_own_write_set': 'PATCH_SCOPE_REFUSED',
        'patch_that_does_not_fit_the_file': 'PATCH_REFUSED',
        'reply_in_words_instead_of_a_patch': 'PATCH_REFUSED',
        'reply_that_declares_itself_repaired': 'BAD_REQUEST',
        'reply_without_a_patch': 'BAD_REQUEST',
        'file_that_differs_from_its_declared_hash': 'SOURCE_CHANGED',
        'check_whose_program_is_missing': 'CHECK_UNAVAILABLE',
        'nothing_to_repair': 'NO_REPAIR_NEEDED',
    }


def test_a_tested_patch_that_did_not_repair_is_a_failure_in_the_ledger():
    classes = {}
    for name in ('patch_that_leaves_the_check_failing', 'patch_that_breaks_the_passing_check',
                 'patch_outside_the_write_set'):
        out = run_fixture(FAMILY, name)
        kept = last_record(out)
        assert kept == out.detail['record']['failure']
        assert (kept['kind'], kept['workflow'], kept['id']) == (
            'failure', 'WF57', f"{out.detail['record']['case']}@wf57-example-1")
        assert out.host['certified_predicates'] == {
            'patch_repairs_the_working_copy': False, 'failed_patch_recorded': True}
        classes[name] = kept['failure_class']
    assert classes == {'patch_that_leaves_the_check_failing': 'CounterfeitExactness',
                       'patch_that_breaks_the_passing_check': 'BoundaryLeakage',
                       'patch_outside_the_write_set': 'StructuralNonFit'}


def test_a_run_that_tested_no_patch_blames_none():
    for name in ('file_that_differs_from_its_declared_hash', 'check_whose_program_is_missing',
                 'nothing_to_repair', 'reply_without_a_patch'):
        out = run_fixture(FAMILY, name)
        assert out.detail['ledger'] == [], name
        assert out.host['certified_predicates'] == {'patch_repairs_the_working_copy': False}


def test_the_failure_joins_the_ledger_wf55_reads(tmp_path):
    out = run_fixture(FAMILY, 'failed_patch_joins_an_existing_ledger')
    before = lines(EXAMPLE_LEDGER)
    assert out.detail['ledger'][:-1] == before
    assert last_record(out)['failure_class'] == 'CounterfeitExactness'
    book = tmp_path / 'ledger.jsonl'
    book.write_text(''.join(line + '\n' for line in out.detail['ledger']), encoding='utf-8')
    verified = operad_host.ledger('verify', book)
    assert (verified['status'], verified['result']['entries']) == ('PASS', len(before) + 1)


def test_the_tasks_write_set_wins_over_the_replys():
    out = run_fixture(FAMILY, 'reply_that_widens_its_own_write_set')
    refusal = out.detail['record']['refusal']
    assert (refusal['stage'], refusal['message']) == ('E', 'answer.json is not in the write set')
    assert out.detail['record']['changed_paths'] == []


def test_the_prompt_shows_the_write_set_and_the_checks_and_no_hash():
    bundle, _expected = FAMILY.fixtures()['patch_repairs_the_refused_operation']
    task = bundle['task']
    prompt = FAMILY.prompt(task)
    assert '\\"body\\": \\"product\\"' in prompt and '"argv":["pfp_operad","run","operation.json"]' in prompt
    assert '"write_paths":["operation.json"]' in prompt
    assert '\\"total\\"' not in prompt, 'a file outside the write set is not shown'
    assert not [digest for digest in task['sources'].values() if digest in prompt]


def test_no_reply_and_a_reply_that_is_not_an_object_are_refused():
    bundle, _expected = FAMILY.fixtures()['patch_repairs_the_refused_operation']

    def run(replies):
        budget = new_budget('WF57:replies', bundle['task'])
        try:
            return FAMILY.execute(bundle, budget=budget, proposer=FixtureProposer(replies))
        finally:
            budget.close()
    assert run([]).code == 'NO_ADMISSIBLE_REPLY'
    assert run(['change product to sum']).code == 'BAD_REQUEST'


def test_the_shipped_example_is_the_fixture_request_and_the_host_repairs_it(tmp_path):
    request = json.loads((EXAMPLE / 'request.json').read_text(encoding='utf-8'))
    bundle, _expected = FAMILY.fixtures()['patch_repairs_the_refused_operation']
    assert {key: request[key] for key in TASK_FIELDS} == {key: bundle['task'][key] for key in TASK_FIELDS}
    assert bundle['replies'] == [{'candidate_patch': request['candidate_patch']}]
    before = (EXAMPLE / 'source' / 'operation.json').read_bytes()
    outcome = operad_host.call(('repair', str(EXAMPLE / 'source'), str(tmp_path / 'run')), request)
    assert (outcome['status'], outcome['result']['outcome']) == ('PASS', 'REPAIRED')
    assert '"body": "sum"' in (tmp_path / 'run' / 'workspace' / 'operation.json').read_text(encoding='utf-8')
    assert (EXAMPLE / 'source' / 'operation.json').read_bytes() == before
    assert sorted(path.name for path in (tmp_path / 'run').iterdir()) == [
        'candidate.patch', 'record.json', 'request.json', 'workspace']


def test_the_archived_papers_worked_example_reproduces(tmp_path):
    """Paper 018, section 4: check exits [1, 0] before the patch and [0, 0] after; the source is untouched.

    The file under repair is the paper's four-line Python function and the two checks are its own
    asserts. The host runs them as commands and reads their exit codes; every decision is the host's.
    """
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'adjust.py').write_bytes(ADJUST.encode('utf-8'))

    def asserts(check_id, claim):
        return {'check_id': check_id, 'argv': [sys.executable, '-c', f'from adjust import adjust; assert {claim}']}
    request = {
        'run_key': 'paper-example-1', 'objective': 'adjust(2) must be 3 and adjust(-2) must stay -2.',
        'sources': {'adjust.py': hashlib.sha256(ADJUST.encode('utf-8')).hexdigest()}, 'write_paths': ['adjust.py'],
        'checks': [asserts('positive', 'adjust(2) == 3'), asserts('control', 'adjust(-2) == -2')],
        'candidate_patch': '--- a/adjust.py\n+++ b/adjust.py\n@@ -4 +4 @@\n-    return n - 1\n+    return n + 1\n',
    }
    outcome = operad_host.call(('repair', str(source), str(tmp_path / 'run')), request)
    record = outcome['result']
    assert (outcome['status'], record['outcome'], record['trace']) == ('PASS', 'REPAIRED', 'CREIMT')
    assert (exits(record['baseline']), exits(record['after'])) == (
        [('positive', 1), ('control', 0)], [('positive', 0), ('control', 0)])
    assert (source / 'adjust.py').read_bytes() == ADJUST.encode('utf-8')
    assert sorted(path.name for path in source.iterdir()) == ['adjust.py']
    assert sorted(path.name for path in (tmp_path / 'run' / 'workspace').iterdir()) == ['adjust.py']
    assert 'return n + 1' in (tmp_path / 'run' / 'workspace' / 'adjust.py').read_text(encoding='utf-8')
