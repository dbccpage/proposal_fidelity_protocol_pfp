"""Scenario language for sealed grading (audit finding F2, review finding 3).

A sealed test is a list of steps. Each step is an operation the untrusted
child process performs on the candidate (inputs only) paired with the
expectation the trusted parent holds back. The child returns one
observation per operation; the parent compares. Expected values never enter
the candidate's process, and the verdict is built only in the parent.
"""
from __future__ import annotations

ANY = '__any__'


def ref(name):
    return {'$': name}


def call(fn, *args, obj=None, as_=None, **kwargs):
    return {'op': 'call', 'fn': fn, 'obj': obj, 'args': list(args), 'kwargs': kwargs, 'as': as_}


def get(obj, attr):
    return {'op': 'get', 'obj': obj, 'attr': attr}


def echo(obj):
    return {'op': 'echo', 'obj': obj}


def let(as_, value):
    """Bind a JSON value once, so later steps can pass the same object (for mutation checks)."""
    return {'op': 'let', 'as': as_, 'value': value}


def make(kind, as_, **params):
    """Child-side helper objects: ``clock`` (t), ``db`` (rows), ``sender`` (fail_on)."""
    return {'op': 'make', 'kind': kind, 'as': as_, 'params': params}


def tick(obj, dt):
    return {'op': 'tick', 'obj': obj, 'dt': dt}


def ok(value):
    return {'ok': value}


def raises(name, code=ANY):
    return {'exc': name, 'code': code}


def matches(expected, observed) -> bool:
    if expected == ANY:
        return isinstance(observed, dict) and len(observed) >= 1
    if not isinstance(observed, dict):
        return False
    if 'ok' in expected:
        return set(observed) == {'ok'} and observed['ok'] == expected['ok']
    return (set(observed) == {'exc', 'code'} and observed['exc'] == expected['exc']
            and (expected['code'] == ANY or observed['code'] == expected['code']))


def judge(steps, observations) -> bool:
    return (isinstance(observations, list) and len(observations) == len(steps)
            and all(matches(exp, obs) for (_, exp), obs in zip(steps, observations)))


def ops_only(scenarios: dict) -> dict:
    """What the child receives: operations, never expectations."""
    return {name: [op for op, _ in steps] for name, steps in scenarios.items()}
