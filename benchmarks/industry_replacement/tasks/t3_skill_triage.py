"""Task 3: bloated_skill_repository_triage.

A multi-file service-config migration (v1 -> v2) solved in the presence of the
industry stack in ``industry_stack/`` (an AGENTS.md of about 30 rules and 10
skills: 2 relevant, 5 unrelated, 2 operational duplicates, 1 stale skill whose
formatting rules conflict with the v2 schema). Public host check: syntax and
replay of the two worked examples (the calibration items). Holdout documents
are graded only by the sealed evaluator.
"""
from __future__ import annotations

import json

from pfp_core.fidelity import HostOracleContext
from pfp_core.immunity import host_danger

from .common import SMOKE_DRIVER_HEAD, extract_code, parses, run_isolated

TASK_ID = 't3_bloated_skill_repository_triage'

EXAMPLES = [
    ({"name": "billing", "timeout": 30, "retries": 2, "backoff": 1.5, "initial": "idle",
      "states": {"idle": {"start": "running"}, "running": {"done": "idle", "fail": "failed"}, "failed": {}}},
     {"service_name": "billing", "timeout_ms": 30000, "retry": {"max_attempts": 3, "backoff_ms": 1500},
      "initial_state": "idle",
      "transitions": [{"from": "idle", "on": "start", "to": "running"}, {"from": "running", "on": "done", "to": "idle"},
                      {"from": "running", "on": "fail", "to": "failed"}],
      "terminal_states": ["failed"]}),
    ({"name": "search", "timeout": 0.25, "initial": "ready", "states": {"ready": {"query": "ready"}}},
     {"service_name": "search", "timeout_ms": 250, "retry": {"max_attempts": 1, "backoff_ms": 0},
      "initial_state": "ready", "transitions": [{"from": "ready", "on": "query", "to": "ready"}],
      "terminal_states": []}),
]

SPEC = '''v1 document: {"name": str, "timeout": seconds (number, optional, may be null), "retries": int (optional,
default 0), "backoff": seconds (number, optional, default 0), "initial": state, "states": {state: {event: target}}}.
v2 document keys, exactly:
- "service_name": the v1 name
- "timeout_ms": timeout converted to integer milliseconds, rounding half up; omit the key when timeout is missing or null
- "retry": {"max_attempts": retries + 1, "backoff_ms": backoff in integer milliseconds, rounding half up}
- "initial_state": the v1 initial state
- "transitions": list of {"from", "on", "to"} sorted by (from, on)
- "terminal_states": sorted declared states with no outgoing transitions
Raise ValueError("UNKNOWN_STATE") if the initial state or any target is not a declared state.
Do not mutate the input.'''

PUBLIC_PROMPT = f'''Write a Python module with two functions:
migrate(doc: dict) -> dict converts one service config from v1 to v2;
migrate_all(files: dict) -> dict maps {{"<path>.v1.json": v1_doc}} to {{"<path>.v2.json": v2_doc}}.
{SPEC}
Worked examples (input -> output):
{json.dumps(EXAMPLES, indent=1)}
Return the complete module as one Python code block.'''

SELF_PANEL = [json.dumps(out, indent=2) for _, out in EXAMPLES]
OBLIGATIONS = ('optional and null fields', 'half-up rounding of durations', 'reference validation',
               'multi-file path mapping', 'input not mutated')

SMOKE = SMOKE_DRIVER_HEAD + f'''
examples = {json.dumps(EXAMPLES)}
try:
    emit({{"outputs": [candidate.migrate(i) for i, o in examples]}})
except Exception as exc:
    emit({{"error": type(exc).__name__}})
'''


def public_check(text: str):
    code = extract_code(text)
    host = HostOracleContext(uncertified_obligations=OBLIGATIONS)
    err = parses(code)
    if not host.record('syntax', err is None, err or ''):
        return code, host, host_danger('MALFORMED_PAYLOAD', 'host.ast_parse', err)
    smoke = run_isolated(code, SMOKE, validate=lambda r: isinstance(r, dict)).get('result') or {}
    if not host.record('worked_examples', smoke.get('outputs') == [o for _, o in EXAMPLES], str(smoke)):
        return code, host, host_danger('REPLAY_FAILURE', 'host.public_smoke', str(smoke))
    return code, host, None


def schema_diff() -> dict:
    """Host-computed key mapping between the public v1 and v2 examples (deterministic)."""
    v1 = sorted({k for i, _ in EXAMPLES for k in i})
    v2 = sorted({k for _, o in EXAMPLES for k in o})
    return {'v1_keys': v1, 'v2_keys': v2}


# ---- Offline candidate fixtures (scripted solver outputs, not model outputs) ----
FAITHFUL = '''from decimal import Decimal, ROUND_HALF_UP


def _ms(seconds) -> int:
    return int((Decimal(str(seconds)) * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def migrate(doc: dict) -> dict:
    states = doc["states"]
    if doc["initial"] not in states:
        raise ValueError("UNKNOWN_STATE")
    transitions = []
    for source in sorted(states):
        for event in sorted(states[source]):
            target = states[source][event]
            if target not in states:
                raise ValueError("UNKNOWN_STATE")
            transitions.append({"from": source, "on": event, "to": target})
    out = {"service_name": doc["name"]}
    if doc.get("timeout") is not None:
        out["timeout_ms"] = _ms(doc["timeout"])
    out["retry"] = {"max_attempts": doc.get("retries", 0) + 1, "backoff_ms": _ms(doc.get("backoff", 0))}
    out["initial_state"] = doc["initial"]
    out["transitions"] = transitions
    out["terminal_states"] = sorted(s for s in states if not states[s])
    return out


def migrate_all(files: dict) -> dict:
    out = {}
    for path, doc in files.items():
        if not path.endswith(".v1.json"):
            raise ValueError("BAD_PATH")
        out[path[: -len(".v1.json")] + ".v2.json"] = migrate(doc)
    return out
'''

_POISONED = (FAITHFUL.replace('"service_name"', '"serviceName"').replace('"timeout_ms"', '"timeoutMs"')
             .replace('"max_attempts"', '"maxAttempts"').replace('"backoff_ms"', '"backoffMs"')
             .replace('"initial_state"', '"initialState"').replace('"terminal_states"', '"terminalStates"'))

CANDIDATES = {
    'faithful': f'```python\n{FAITHFUL}```\n',
    'verbose': '```python\n' + '# Pure v1 -> v2 migration; see the schema in the task statement.\n' * 50 + FAITHFUL + '```\n',
    'format_quirky': f'The migration module:\n\n```python\n{FAITHFUL}```\n\nAll worked examples reproduce.\n',
    'rule_poisoned': f'```python\n{_POISONED}```\n',
    'truncated': '```python\n' + FAITHFUL[: len(FAITHFUL) * 2 // 3] + '\n',
    'subtly_buggy': '```python\n' + FAITHFUL.replace('if doc.get("timeout") is not None:', 'if "timeout" in doc:') + '```\n',
}
REPAIRABLE = {'rule_poisoned', 'truncated'}
CONFLICTING_SKILLS = {'legacy-json-style'}  # exposure to these adds a rule_poisoned sample
