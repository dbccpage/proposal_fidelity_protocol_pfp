"""Executable countermodels for "report-fibre separation is necessary, not sufficient"."""
import json
from pathlib import Path

import reproducer_ablation as ra

RESULTS = Path(ra.__file__).with_name('reproducer_ablation_results.json')


def test_shared_misdiagnosis_separates_base_from_patch_and_still_fails_sealed():
    task = next(t for t in ra.TASKS if t.task_id == 'mean_empty')
    cand = next(c for c in task.candidates if c.name == 'shared_misdiagnosis')
    assert ra.run_tests(task.base, cand.aligned_test) in ra.BEHAVIOURAL_FAILURES
    assert ra.run_tests(cand.patch, cand.aligned_test) == ra.PASS
    assert ra.run_tests(cand.patch, task.sealed) != ra.PASS


def test_literal_overfit_separates_and_still_fails_sealed():
    task = next(t for t in ra.TASKS if t.task_id == 'parse_bool_case')
    cand = next(c for c in task.candidates if c.name == 'literal_overfit')
    assert ra.run_tests(task.base, cand.aligned_test) == ra.ASSERTION_FAIL
    assert ra.run_tests(cand.patch, cand.aligned_test) == ra.PASS
    assert ra.run_tests(cand.patch, task.sealed) != ra.PASS


def test_collection_error_is_never_a_separation():
    task = next(t for t in ra.TASKS if t.task_id == 'slug_spaces')
    cand = next(c for c in task.candidates if c.name == 'broken_syntax_reproducer')
    assert ra.run_tests(task.base, cand.aligned_test) == ra.COLLECTION_ERROR
    assert ra._run(task, cand, 'reproducer_aligned')['separated'] is False


def test_fenced_reproducer_edit_is_refused_and_not_submitted():
    task = next(t for t in ra.TASKS if t.task_id == 'mean_empty')
    cand = next(c for c in task.candidates if c.name == 'fenced_test_tamper')
    row = ra._run(task, cand, 'reproducer_blind_fenced_broad')
    assert row['refusal'] == 'PROTECTED_REPRODUCER_EDIT' and row['submitted'] is False


def test_every_blind_reproducer_fails_on_base_behaviourally():
    for task in ra.TASKS:
        for test in (task.blind_broad, task.blind_narrow):
            assert ra.run_tests(task.base, test) in ra.BEHAVIOURAL_FAILURES, task.task_id


def test_committed_results_regenerate_byte_identically():
    fresh = (json.dumps(ra.run_ablation(), indent=1, sort_keys=True) + '\n').encode('utf-8')
    assert RESULTS.read_bytes() == fresh


def test_declared_fixture_outcomes():
    arms = ra.run_ablation()['arms']
    assert arms['reproducer_aligned']['false_separation_rate'] == '7/10'
    assert arms['reproducer_blind_fenced_broad']['false_separation_rate'] == '0/4'
    assert arms['reproducer_blind_fenced_narrow']['false_separation_rate'] == '4/8'
    assert len({a['precision_forced_submit'] for a in arms.values()}) == 1
