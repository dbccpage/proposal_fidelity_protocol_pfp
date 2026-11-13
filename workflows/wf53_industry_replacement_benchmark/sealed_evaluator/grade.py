"""Post-freeze sealed grading. Imported only by the harness after deliveries freeze.

The child process (jailed, see ``tasks/sandbox.py``) receives the candidate
and the scenario *operations* only. It returns one observation per
operation. This module, in the parent, holds the expectations and builds the
verdict, so code in the candidate's process cannot write a verdict: the most
it can do is report its own observations, which is what an implementation
does anyway. A refusal (no delivery) scores zero and is reported separately
from a delivered wrong answer.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from tasks.common import extract_code, prewarm, run_isolated  # noqa: E402

from .scenario import judge, ops_only  # noqa: E402

SEALED = {
    't1_api_refactor_under_contract': 't1_sealed',
    't2_sql_security_and_analytics_migration': 't2_sealed',
    't3_bloated_skill_repository_triage': 't3_sealed',
    't4_stateful_protocol_synthesis': 't4_sealed',
}

DRIVER = r'''
import json, sqlite3
from decimal import Decimal
try:
    import candidate
except BaseException as exc:
    emit({"import_error": type(exc).__name__})
    raise SystemExit(0)

DDL = ("CREATE TABLE orders(id INTEGER PRIMARY KEY, customer TEXT NOT NULL, region TEXT, "
       "amount_cents INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);")


class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


class Sender:
    def __init__(self, fail_on):
        self.calls, self.fail_on = [], fail_on

    def __call__(self, msg_id, payload):
        self.calls.append([msg_id, payload])
        if msg_id == self.fail_on:
            raise ConnectionError("down")


def norm(v, depth=0):
    if depth > 20:
        return {"type": "too_deep"}
    if v is None or type(v) in (bool, int, float, str):
        return v
    if type(v) is Decimal:
        return {"decimal": str(v)}
    if type(v) in (list, tuple):
        return [norm(x, depth + 1) for x in v]
    if type(v) is dict:
        return {str(k): norm(x, depth + 1) for k, x in v.items()}
    return {"type": type(v).__name__}


def resolve(a, env):
    if type(a) is dict and set(a) == {"$"}:
        return env[a["$"]]
    if type(a) is list:
        return [resolve(x, env) for x in a]
    if type(a) is dict:
        return {k: resolve(x, env) for k, x in a.items()}
    return a


def make(kind, p, env):
    if kind == "clock":
        return Clock(p["t"])
    if kind == "sender":
        return Sender(p["fail_on"])
    if kind == "dict":
        return {}
    if kind == "db":
        conn = sqlite3.connect(":memory:")
        conn.executescript(DDL)
        conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", p["rows"])
        return conn
    if kind == "count":
        return env[p["db"]].execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    raise KeyError(kind)


out = {}
for name, ops in json.load(open("scenarios.json", encoding="utf-8")).items():
    env, obs = {}, []
    for op in ops:
        try:
            kind = op["op"]
            if kind == "call":
                target = getattr(env[op["obj"]], op["fn"]) if op["obj"] else getattr(candidate, op["fn"])
                value = target(*resolve(op["args"], env), **resolve(op["kwargs"], env))
            elif kind == "get":
                value = getattr(env[op["obj"]], op["attr"])
            elif kind == "echo":
                value = env[op["obj"]]
            elif kind == "let":
                value = op["value"]
            elif kind == "make":
                value = make(op["kind"], op["params"], env)
            elif kind == "tick":
                env[op["obj"]].t += op["dt"]
                value = None
            elif kind == "sent":
                value = env[op["obj"]].calls
            if op.get("as"):
                env[op["as"]] = value
            obs.append({"ok": norm(value)})
        except BaseException as exc:
            obs.append({"exc": type(exc).__name__, "code": norm(getattr(exc, "code", None))})
    out[name] = obs
emit({"scenarios": out})
'''


def scenarios(task_id: str) -> dict:
    return importlib.import_module(f'sealed_evaluator.{SEALED[task_id]}').SCENARIOS


def _valid(result, names) -> bool:
    if not isinstance(result, dict):
        return False
    if set(result) == {'import_error'}:
        return True
    obs = result.get('scenarios')
    return (set(result) == {'scenarios'} and isinstance(obs, dict) and set(obs) == set(names)
            and all(isinstance(v, list) and all(isinstance(o, dict) for o in v) for v in obs.values()))


def _files(task_id):
    return {'scenarios.json': json.dumps(ops_only(scenarios(task_id)))}


SEALED_TIMEOUT = 20


def grade(task_id: str, delivered_text: str | None) -> dict:
    if delivered_text is None:
        return {'delivered': False, 'correct': False, 'passed': 0, 'total': None}
    scen = scenarios(task_id)
    out = run_isolated(extract_code(delivered_text), DRIVER, _files(task_id), timeout=SEALED_TIMEOUT,
                       validate=lambda r: _valid(r, scen))
    result = out.get('result') or {}
    if 'scenarios' not in result:
        return {'delivered': True, 'correct': False, 'passed': 0, 'total': len(scen),
                'failed': [result.get('import_error') or out.get('error', 'unknown')]}
    failed = sorted(n for n, steps in scen.items() if not judge(steps, result['scenarios'][n]))
    return {'delivered': True, 'correct': not failed, 'passed': len(scen) - len(failed), 'total': len(scen),
            'failed': failed}


def prewarm_offline(task_id: str, texts: list[str]) -> None:
    """Grade many fixtures in parallel, each in its own fresh process (cache warm-up only).

    Uses the same timeout grade() will use, so the warmed cache entries share grade()'s key
    (the timeout is part of the cache key); a shorter prewarm would be discarded and re-run.
    """
    prewarm([extract_code(t) for t in texts], DRIVER, _files(task_id), timeout=SEALED_TIMEOUT)
