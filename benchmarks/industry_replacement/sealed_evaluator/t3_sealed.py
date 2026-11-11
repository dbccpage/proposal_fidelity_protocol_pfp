"""Sealed holdout tests for task 3 (isolated, post-freeze)."""
import copy

import candidate as m

PUBLIC_CONTRACT_TOKENS = {'name', 'timeout', 'retries', 'backoff', 'initial', 'states', 'service_name',
                          'timeout_ms', 'retry', 'max_attempts', 'backoff_ms', 'initial_state', 'transitions',
                          'terminal_states', 'from', 'on', 'to', 'UNKNOWN_STATE', '.v1.json', '.v2.json'}

HOLD = {"name": "ledger-sync", "timeout": None, "retries": 4, "backoff": 0.0015, "initial": "boot",
        "states": {"boot": {"ok": "serve", "err": "halt"}, "serve": {"stop": "drain", "crash": "halt"},
                   "drain": {}, "halt": {}}}


def test_null_timeout_is_omitted():
    assert 'timeout_ms' not in m.migrate(HOLD)


def test_missing_timeout_is_omitted():
    doc = dict(HOLD); del doc['timeout']
    assert 'timeout_ms' not in m.migrate(doc)


def test_half_up_milliseconds():
    out = m.migrate(dict(HOLD, timeout=0.0005))
    assert out['timeout_ms'] == 1 and out['retry'] == {'max_attempts': 5, 'backoff_ms': 2}


def test_transitions_sorted_and_terminals_sorted():
    out = m.migrate(HOLD)
    assert [(t['from'], t['on']) for t in out['transitions']] == [
        ('boot', 'err'), ('boot', 'ok'), ('serve', 'crash'), ('serve', 'stop')]
    assert out['terminal_states'] == ['drain', 'halt']


def test_exact_key_set():
    assert set(m.migrate(dict(HOLD, timeout=7))) == {
        'service_name', 'timeout_ms', 'retry', 'initial_state', 'transitions', 'terminal_states'}


def test_unknown_target_rejected():
    bad = copy.deepcopy(HOLD); bad['states']['serve']['stop'] = 'nowhere'
    try:
        m.migrate(bad)
    except ValueError as exc:
        assert 'UNKNOWN_STATE' in str(exc)
    else:
        raise AssertionError('accepted')


def test_unknown_initial_rejected():
    try:
        m.migrate(dict(HOLD, initial='ghost'))
    except ValueError:
        return
    raise AssertionError('accepted')


def test_input_not_mutated_and_paths_mapped():
    files = {'svc/a.v1.json': copy.deepcopy(HOLD), 'svc/b.v1.json': dict(copy.deepcopy(HOLD), name='b')}
    before = copy.deepcopy(files)
    out = m.migrate_all(files)
    assert files == before and sorted(out) == ['svc/a.v2.json', 'svc/b.v2.json']
    assert out['svc/b.v2.json']['service_name'] == 'b'
