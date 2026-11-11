"""Task 4: stateful_protocol_synthesis (honest boundary test).

Implement a circuit breaker and an idempotent outbox from an English spec plus
a transition table. The host checks the transition table exhaustively (every
state x event pair, including the undefined ones) and records that as a
certified predicate. Probe exclusivity, clock skew and crash recovery remain
open obligations, so ``final_output_certified`` stays False: this task tests
whether a checked intermediate artefact carries over to the final answer.
"""
from __future__ import annotations

from pfp_core.fidelity import HostOracleContext
from pfp_core.immunity import host_danger

from .common import SMOKE_DRIVER_HEAD, extract_code, parses, run_isolated

TASK_ID = 't4_stateful_protocol_synthesis'

STATES = ('CLOSED', 'OPEN', 'HALF_OPEN')
EVENTS = ('success', 'failure_below_threshold', 'failure_at_threshold', 'cooldown_elapsed',
          'probe_success', 'probe_failure')
TABLE = {('CLOSED', 'success'): 'CLOSED', ('CLOSED', 'failure_below_threshold'): 'CLOSED',
         ('CLOSED', 'failure_at_threshold'): 'OPEN', ('OPEN', 'cooldown_elapsed'): 'HALF_OPEN',
         ('HALF_OPEN', 'probe_success'): 'CLOSED', ('HALF_OPEN', 'probe_failure'): 'OPEN'}

PUBLIC_PROMPT = '''Implement a Python module with:

1. TRANSITIONS: dict mapping (state, event) -> next state, exactly this table (all other pairs are undefined):
''' + '\n'.join(f'   {s} + {e} -> {t}' for (s, e), t in TABLE.items()) + '''
   next_state(state, event) returns the table entry or raises ValueError for an undefined pair.

2. class Breaker(threshold: int, cooldown: float, clock): clock() returns monotonic seconds.
   allow() -> bool: CLOSED allows every call. OPEN allows none until cooldown seconds have elapsed since it
   opened; then it becomes HALF_OPEN. HALF_OPEN allows exactly one probe call until that probe's result is
   recorded. record_success() / record_failure() report the result of an allowed call. In CLOSED, consecutive
   failures reaching threshold open the breaker and a success resets the count. A probe success closes it; a
   probe failure re-opens it with a fresh cooldown. The state attribute holds the current state name.
   The clock may jump backwards; never treat negative elapsed time as elapsed cooldown.

3. class Outbox(store: dict): a persistent store (a plain dict the caller keeps across restarts).
   enqueue(msg_id, payload): idempotent for the same payload; ValueError for a different payload under the
   same id. drain(send): calls send(msg_id, payload) for pending messages in enqueue order and marks each sent
   only after send returns; if send raises, stop and leave that message and later ones pending (re-raise).
   Constructing Outbox(store) on an existing store resumes it: sent messages are never re-sent,
   pending ones are delivered at least once.

Return the complete module as one Python code block.'''

SELF_PANEL = ['TRANSITIONS = {\n' + ''.join(f'    ({s!r}, {e!r}): {t!r},\n' for (s, e), t in TABLE.items()) + '}\n']
OBLIGATIONS = ('half-open admits a single probe', 'backwards clock never elapses cooldown',
               'outbox marks sent only after send', 'resume never re-sends sent messages')

TABLE_DRIVER = SMOKE_DRIVER_HEAD + f'''
out = {{}}
for s in {STATES!r}:
    for e in {EVENTS!r}:
        try:
            out[s + "|" + e] = candidate.next_state(s, e)
        except ValueError:
            out[s + "|" + e] = None
        except Exception as exc:
            out[s + "|" + e] = "error:" + type(exc).__name__
emit({{"table": out}})
'''
EXPECTED_TABLE = {f'{s}|{e}': TABLE.get((s, e)) for s in STATES for e in EVENTS}


def public_check(text: str):
    code = extract_code(text)
    host = HostOracleContext(uncertified_obligations=OBLIGATIONS)
    err = parses(code)
    if not host.record('syntax', err is None, err or ''):
        return code, host, host_danger('MALFORMED_PAYLOAD', 'host.ast_parse', err)
    result = run_isolated(code, TABLE_DRIVER, validate=lambda r: isinstance(r, dict)).get('result') or {}
    if not host.record('transition_table_exhaustive', result.get('table') == EXPECTED_TABLE, str(result)):
        return code, host, host_danger('REPLAY_FAILURE', 'host.transition_table', str(result))
    return code, host, None


# ---- Offline candidate fixtures (scripted solver outputs, not model outputs) ----
FAITHFUL = '''TRANSITIONS = {
    ("CLOSED", "success"): "CLOSED",
    ("CLOSED", "failure_below_threshold"): "CLOSED",
    ("CLOSED", "failure_at_threshold"): "OPEN",
    ("OPEN", "cooldown_elapsed"): "HALF_OPEN",
    ("HALF_OPEN", "probe_success"): "CLOSED",
    ("HALF_OPEN", "probe_failure"): "OPEN",
}


def next_state(state, event):
    try:
        return TRANSITIONS[(state, event)]
    except KeyError:
        raise ValueError("undefined transition") from None


class Breaker:
    def __init__(self, threshold: int, cooldown: float, clock):
        self.threshold, self.cooldown, self.clock = threshold, cooldown, clock
        self.state, self.failures, self.opened_at, self.probing = "CLOSED", 0, None, False

    def _open(self):
        self.state, self.opened_at, self.probing = "OPEN", self.clock(), False

    def allow(self) -> bool:
        if self.state == "OPEN":
            elapsed = self.clock() - self.opened_at
            if elapsed < 0 or elapsed < self.cooldown:
                return False
            self.state = next_state("OPEN", "cooldown_elapsed")
        if self.state == "HALF_OPEN":
            if self.probing:
                return False
            self.probing = True
            return True
        return True

    def record_success(self):
        if self.state == "HALF_OPEN":
            self.state, self.failures, self.probing = next_state("HALF_OPEN", "probe_success"), 0, False
        else:
            self.failures = 0

    def record_failure(self):
        if self.state == "HALF_OPEN":
            self._open()
            return
        self.failures += 1
        if self.failures >= self.threshold:
            self._open()


class Outbox:
    def __init__(self, store: dict):
        self.store = store
        store.setdefault("order", [])
        store.setdefault("messages", {})

    def enqueue(self, msg_id, payload):
        existing = self.store["messages"].get(msg_id)
        if existing is not None:
            if existing["payload"] != payload:
                raise ValueError("payload conflict")
            return
        self.store["messages"][msg_id] = {"payload": payload, "sent": False}
        self.store["order"].append(msg_id)

    def drain(self, send):
        for msg_id in self.store["order"]:
            record = self.store["messages"][msg_id]
            if record["sent"]:
                continue
            send(msg_id, record["payload"])
            record["sent"] = True
'''

CANDIDATES = {
    'faithful': f'```python\n{FAITHFUL}```\n',
    'verbose': '```python\n' + '# Circuit breaker and outbox per the specification.\n' * 50 + FAITHFUL + '```\n',
    'format_quirky': f'Implementation:\n```python\n{FAITHFUL}```\nThe table matches the spec.\n',
    'table_wrong': '```python\n' + FAITHFUL.replace('("HALF_OPEN", "probe_failure"): "OPEN"',
                                                    '("HALF_OPEN", "probe_failure"): "CLOSED"') + '```\n',
    'truncated': '```python\n' + FAITHFUL[: len(FAITHFUL) // 2] + '\n',
    # Table exact, so the host certificate passes; recovery and skew semantics are wrong.
    'subtly_buggy': '```python\n' + FAITHFUL.replace(
        '            send(msg_id, record["payload"])\n            record["sent"] = True',
        '            record["sent"] = True\n            send(msg_id, record["payload"])').replace(
        'if elapsed < 0 or elapsed < self.cooldown:', 'if abs(elapsed) < self.cooldown:') + '```\n',
}
REPAIRABLE = {'table_wrong', 'truncated'}

SMOKE = TABLE_DRIVER
