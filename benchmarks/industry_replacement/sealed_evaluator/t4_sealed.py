"""Sealed behaviour tests for task 4 (isolated, post-freeze)."""
import candidate as m

PUBLIC_CONTRACT_TOKENS = {'cooldown_elapsed', 'probe_failure', 'probe_success', 'success', 'CLOSED', 'OPEN', 'HALF_OPEN', 'order', 'messages', 'payload', 'sent'}


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def _opened(threshold=2, cooldown=5.0):
    c = Clock(); b = m.Breaker(threshold, cooldown, c)
    for _ in range(threshold):
        assert b.allow(); b.record_failure()
    return b, c


def test_opens_at_threshold_and_success_resets():
    c = Clock(); b = m.Breaker(3, 5.0, c)
    b.record_failure(); b.record_failure(); b.record_success(); b.record_failure(); b.record_failure()
    assert b.state == 'CLOSED'
    b.record_failure()
    assert b.state == 'OPEN' and not b.allow()


def test_single_probe_in_half_open():
    b, c = _opened()
    c.t += 5.0
    assert b.allow() and b.state == 'HALF_OPEN'
    assert not b.allow() and not b.allow()


def test_probe_failure_restarts_cooldown():
    b, c = _opened()
    c.t += 6
    assert b.allow(); b.record_failure()
    assert b.state == 'OPEN' and not b.allow()
    c.t += 4.9
    assert not b.allow()
    c.t += 0.2
    assert b.allow()


def test_backwards_clock_does_not_elapse_cooldown():
    b, c = _opened(cooldown=5.0)
    c.t -= 50
    assert not b.allow() and b.state == 'OPEN'


def test_probe_success_closes():
    b, c = _opened()
    c.t += 5
    assert b.allow(); b.record_success()
    assert b.state == 'CLOSED' and b.allow() and b.allow()


def test_outbox_crash_during_send_keeps_message_pending():
    store = {}; box = m.Outbox(store)
    box.enqueue('a', 1); box.enqueue('b', 2)
    seen = []

    def flaky(i, p):
        seen.append(i)
        if i == 'b':
            raise ConnectionError('down')
    try:
        box.drain(flaky)
    except ConnectionError:
        pass
    resumed = m.Outbox(store); sent = []
    resumed.drain(lambda i, p: sent.append((i, p)))
    assert seen == ['a', 'b'] and sent == [('b', 2)]


def test_outbox_resume_never_resends():
    store = {}; box = m.Outbox(store); box.enqueue('x', {'k': 1}); box.drain(lambda i, p: None)
    again = []
    m.Outbox(store).drain(lambda i, p: again.append(i))
    assert again == []


def test_outbox_idempotent_enqueue_and_conflict():
    box = m.Outbox({}); box.enqueue('x', 5); box.enqueue('x', 5)
    out = []; box.drain(lambda i, p: out.append(i))
    assert out == ['x']
    try:
        box.enqueue('x', 6)
    except ValueError:
        return
    raise AssertionError('conflict accepted')


def test_published_table_and_undefined_pairs():
    assert m.next_state('HALF_OPEN', 'probe_failure') == 'OPEN'
    assert m.next_state('OPEN', 'cooldown_elapsed') == 'HALF_OPEN'
    for pair in (('OPEN', 'success'), ('CLOSED', 'probe_success'), ('HALF_OPEN', 'cooldown_elapsed')):
        try:
            m.next_state(*pair)
        except ValueError:
            continue
        raise AssertionError('undefined pair accepted')
