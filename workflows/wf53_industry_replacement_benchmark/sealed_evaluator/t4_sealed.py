"""Sealed behaviour scenarios for task 4. Judged in the parent after freeze."""
from .scenario import ANY, call, get, make, ok, raises, ref, tick

PUBLIC_CONTRACT_TOKENS = {'cooldown_elapsed', 'probe_failure', 'probe_success', 'success', 'CLOSED', 'OPEN',
                          'HALF_OPEN', 'order', 'messages', 'payload', 'sent', 'Breaker', 'Outbox', 'allow',
                          'record_success', 'record_failure', 'state', 'enqueue', 'drain', 'next_state',
                          'ValueError', 'ConnectionError'}

B, C, S, T = ref('b'), ref('c'), ref('store'), ref('tx')


def breaker(threshold=2, cooldown=5.0):
    return [(make('clock', 'c', t=100.0), ANY), (call('Breaker', threshold, cooldown, C, as_='b'), ANY)]


def m(name, expected=ANY, *args):
    return (call(name, *args, obj='b'), expected)


def opened(threshold=2, cooldown=5.0):
    return breaker(threshold, cooldown) + [m('allow', ok(True)), m('record_failure')] * threshold


def state(value):
    return (get('b', 'state'), ok(value))


SCENARIOS = {
    'opens_at_threshold_and_success_resets': breaker(3) + [
        m('record_failure'), m('record_failure'), m('record_success'), m('record_failure'), m('record_failure'),
        state('CLOSED'), m('record_failure'), state('OPEN'), m('allow', ok(False))],
    'single_probe_in_half_open': opened() + [
        (tick('c', 5.0), ANY), m('allow', ok(True)), state('HALF_OPEN'), m('allow', ok(False)), m('allow', ok(False))],
    'probe_failure_restarts_cooldown': opened() + [
        (tick('c', 6.0), ANY), m('allow', ok(True)), m('record_failure'), state('OPEN'), m('allow', ok(False)),
        (tick('c', 4.9), ANY), m('allow', ok(False)), (tick('c', 0.2), ANY), m('allow', ok(True))],
    'backwards_clock_does_not_elapse_cooldown': opened() + [
        (tick('c', -50.0), ANY), m('allow', ok(False)), state('OPEN')],
    'probe_success_closes': opened() + [
        (tick('c', 5.0), ANY), m('allow', ok(True)), m('record_success'), state('CLOSED'),
        m('allow', ok(True)), m('allow', ok(True))],
    'outbox_crash_during_send_keeps_message_pending': [
        (make('dict', 'store'), ANY), (call('Outbox', S, as_='box'), ANY),
        (call('enqueue', 'a', 1, obj='box'), ANY), (call('enqueue', 'b', 2, obj='box'), ANY),
        (make('sender', 'tx', fail_on='b'), ANY), (call('drain', T, obj='box'), raises('ConnectionError')),
        (call('Outbox', S, as_='again'), ANY), (make('sender', 'tx2', fail_on=None), ANY),
        (call('drain', ref('tx2'), obj='again'), ANY),
        ({'op': 'sent', 'obj': 'tx'}, ok([['a', 1], ['b', 2]])), ({'op': 'sent', 'obj': 'tx2'}, ok([['b', 2]]))],
    'outbox_resume_never_resends': [
        (make('dict', 'store'), ANY), (call('Outbox', S, as_='box'), ANY),
        (call('enqueue', 'x', {'k': 1}, obj='box'), ANY), (make('sender', 'tx', fail_on=None), ANY),
        (call('drain', T, obj='box'), ANY), (call('Outbox', S, as_='again'), ANY),
        (make('sender', 'tx2', fail_on=None), ANY), (call('drain', ref('tx2'), obj='again'), ANY),
        ({'op': 'sent', 'obj': 'tx2'}, ok([]))],
    'outbox_idempotent_enqueue_and_conflict': [
        (make('dict', 'store'), ANY), (call('Outbox', S, as_='box'), ANY),
        (call('enqueue', 'x', 5, obj='box'), ANY), (call('enqueue', 'x', 5, obj='box'), ANY),
        (make('sender', 'tx', fail_on=None), ANY), (call('drain', T, obj='box'), ANY),
        ({'op': 'sent', 'obj': 'tx'}, ok([['x', 5]])), (call('enqueue', 'x', 6, obj='box'), raises('ValueError'))],
    'published_table_and_undefined_pairs': [
        (call('next_state', 'HALF_OPEN', 'probe_failure'), ok('OPEN')),
        (call('next_state', 'OPEN', 'cooldown_elapsed'), ok('HALF_OPEN'))] + [
        (call('next_state', s, e), raises('ValueError'))
        for s, e in (('OPEN', 'success'), ('CLOSED', 'probe_success'), ('HALF_OPEN', 'cooldown_elapsed'))],
}
