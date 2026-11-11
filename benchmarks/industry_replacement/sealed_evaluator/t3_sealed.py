"""Sealed holdout scenarios for task 3. Judged in the parent after freeze."""
import copy

from .scenario import ANY, call, echo, let, ok, raises, ref

PUBLIC_CONTRACT_TOKENS = {'name', 'timeout', 'retries', 'backoff', 'initial', 'states', 'service_name',
                          'timeout_ms', 'retry', 'max_attempts', 'backoff_ms', 'initial_state', 'transitions',
                          'terminal_states', 'from', 'on', 'to', 'UNKNOWN_STATE', '.v1.json', '.v2.json',
                          'migrate', 'migrate_all', 'ValueError'}

HOLD = {"name": "ledger-sync", "timeout": None, "retries": 4, "backoff": 0.0015, "initial": "boot",
        "states": {"boot": {"ok": "serve", "err": "halt"}, "serve": {"stop": "drain", "crash": "halt"},
                   "drain": {}, "halt": {}}}
NO_TIMEOUT = {k: v for k, v in HOLD.items() if k != 'timeout'}
TRANSITIONS = [{'from': 'boot', 'on': 'err', 'to': 'halt'}, {'from': 'boot', 'on': 'ok', 'to': 'serve'},
               {'from': 'serve', 'on': 'crash', 'to': 'halt'}, {'from': 'serve', 'on': 'stop', 'to': 'drain'}]
EXPECTED = {'service_name': 'ledger-sync', 'retry': {'max_attempts': 5, 'backoff_ms': 2}, 'initial_state': 'boot',
            'transitions': TRANSITIONS, 'terminal_states': ['drain', 'halt']}
BAD_TARGET = copy.deepcopy(HOLD)
BAD_TARGET['states']['serve']['stop'] = 'nowhere'
FILES = {'svc/a.v1.json': HOLD, 'svc/b.v1.json': dict(HOLD, name='b')}

SCENARIOS = {
    'null_timeout_is_omitted': [(call('migrate', HOLD), ok(EXPECTED))],
    'missing_timeout_is_omitted': [(call('migrate', NO_TIMEOUT), ok(EXPECTED))],
    'half_up_milliseconds': [(call('migrate', dict(HOLD, timeout=0.0005)), ok(dict(EXPECTED, timeout_ms=1)))],
    'exact_key_set_with_timeout': [(call('migrate', dict(HOLD, timeout=7)), ok(dict(EXPECTED, timeout_ms=7000)))],
    'unknown_target_rejected': [(call('migrate', BAD_TARGET), raises('ValueError'))],
    'unknown_initial_rejected': [(call('migrate', dict(HOLD, initial='ghost')), raises('ValueError'))],
    'input_not_mutated_and_paths_mapped': [
        (let('files', FILES), ANY),
        (call('migrate_all', ref('files'), as_='out'),
         ok({'svc/a.v2.json': EXPECTED, 'svc/b.v2.json': dict(EXPECTED, service_name='b')})),
        (echo('files'), ok(FILES))],
}
