"""Finite table semantics; supplied resolution tables remain model assumptions.

World states change before reports are observed. Successful target beliefs stop
execution. Every cost of a reachable enabled action is an exact positive rational.
The immutable arena is reconstructed from the original input by the checker.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from itertools import chain

Belief = tuple[str, ...]


class ModelError(ValueError):
    """Invalid declared finite model, rather than a mathematical loss."""


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False).encode("utf-8")).hexdigest()


def fields(value: object, keys: set[str]) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise ModelError(f"expected exactly these fields: {sorted(keys)}")
    return value


def names(value: object, *, nonempty: bool = False) -> tuple[str, ...]:
    if type(value) is not list or any(type(x) is not str or not x for x in value):
        raise ModelError("expected a list of nonempty strings")
    if len(value) != len(set(value)) or (nonempty and not value):
        raise ModelError("duplicate names or empty required list")
    return tuple(sorted(value))


def belief(value: object, states: tuple[str, ...]) -> Belief:
    result = names(value, nonempty=True)
    if not set(result) <= set(states):
        raise ModelError("belief outside original carrier")
    return result


def rational(value: object, *, positive: bool = False) -> Fraction:
    if type(value) is not str:
        raise ModelError("rational values must be strings, never floats or booleans")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ModelError("invalid rational") from error
    if result < 0 or (positive and result == 0):
        raise ModelError("negative value or nonpositive action cost")
    return result


@dataclass(frozen=True)
class Arena:
    model_digest: str
    task_id: str
    assumptions: tuple[str, ...]
    authorization_json: str
    states: tuple[str, ...]
    initial: Belief
    targets: frozenset[Belief]
    reachable: tuple[Belief, ...]
    # Tuples prevent a caller from mutating a model after validation.
    edges: tuple[tuple[Belief, str, Fraction, tuple[Belief, ...]], ...]
    resolutions: tuple[tuple[Belief, tuple[str, ...]], ...]

    def moves(self, b: Belief) -> tuple[tuple[str, Fraction, tuple[Belief, ...]], ...]:
        return tuple((a, c, ys) for x, a, c, ys in self.edges if x == b)

    def valid_resolutions(self, b: Belief) -> tuple[str, ...]:
        return next((rs for x, rs in self.resolutions if x == b), ())


def compile_model(model: object) -> Arena:
    m = fields(model, {"schema", "task_id", "assumptions", "authorization", "states",
                       "actions", "enabled", "transitions", "reports", "initial",
                       "targets", "costs", "resolutions", "valid_resolutions", "emissions"})
    if m["schema"] != "wdp-finite-belief-model-v1" or type(m["task_id"]) is not str or not m["task_id"]:
        raise ModelError("unknown schema or missing task identity")
    assumptions = names(m["assumptions"])
    if not {"A2", "A4", "A5", "A6"} <= set(assumptions):
        raise ModelError("missing declared model assumptions")
    if type(m["authorization"]) is not dict:
        raise ModelError("authorization binding must be an object")
    states, actions = names(m["states"], nonempty=True), names(m["actions"])
    if type(m["enabled"]) is not dict or set(m["enabled"]) != set(states):
        raise ModelError("enablement must cover exactly the carrier")
    enabled = {s: names(m["enabled"][s]) for s in states}
    if any(not set(xs) <= set(actions) for xs in enabled.values()):
        raise ModelError("undeclared enabled action")
    required = {(s, a) for s in states for a in enabled[s]}
    transitions = {}
    if type(m["transitions"]) is not list:
        raise ModelError("transition table must be a list")
    for entry in m["transitions"]:
        row = fields(entry, {"state", "action", "successors"})
        key = (row["state"], row["action"])
        if key not in required or key in transitions:
            raise ModelError("duplicate or non-enabled transition row")
        transitions[key] = belief(row["successors"], states)
    if set(transitions) != required:
        raise ModelError("enabled transitions must be total and nonempty")
    reports = {}
    if type(m["reports"]) is not list:
        raise ModelError("report table must be a list")
    required_reports = {(y, a) for (s, a), ys in transitions.items() for y in ys}
    for entry in m["reports"]:
        row = fields(entry, {"state", "action", "observation"})
        key = (row["state"], row["action"])
        if key not in required_reports or key in reports or type(row["observation"]) is not str:
            raise ModelError("duplicate, unknown or malformed report")
        reports[key] = row["observation"]
    if set(reports) != required_reports:
        raise ModelError("missing post-state report")
    initial = belief(m["initial"], states)
    if type(m["targets"]) is not list:
        raise ModelError("target set must be listed by the model")
    target_rows = [belief(x, states) for x in m["targets"]]
    if len(target_rows) != len(set(target_rows)):
        raise ModelError("duplicate target belief")
    targets = frozenset(target_rows)
    rs = names(m["resolutions"])
    if type(m["valid_resolutions"]) is not dict or set(m["valid_resolutions"]) != set(states):
        raise ModelError("resolution checks must cover exactly the world carrier")
    valid = {s: names(m["valid_resolutions"][s]) for s in states}
    if any(not set(xs) <= set(rs) for xs in valid.values()):
        raise ModelError("undeclared resolution")
    if type(m["emissions"]) is not dict or not set(m["emissions"]) <= set(actions):
        raise ModelError("malformed emission map")
    for a, resolution in m["emissions"].items():
        if resolution not in rs:
            raise ModelError("unknown emitted resolution")
        for s in states:
            if a in enabled[s]:
                if resolution not in valid[s] or any((y,) not in targets for y in transitions[s, a]):
                    raise ModelError("unsafe emission or emission outside declared targets")
                if len(transitions[s, a]) != 1:
                    raise ModelError("emission must have a deterministic target")
    # Explore the relevant arena from input alone. Never read certificate keys.
    reachable, pending, raw_edges = {initial}, [initial], []
    for b in pending:
        if b in targets:
            continue
        for a in actions:
            if not all(a in enabled[s] for s in b):
                continue
            post = set(chain.from_iterable(transitions[s, a] for s in b))
            observations = {reports[y, a] for y in post}
            successors = tuple(sorted(tuple(sorted(y for y in post if reports[y, a] == o))
                                      for o in observations))
            raw_edges.append((b, a, successors))
            for y in successors:
                if y not in reachable:
                    reachable.add(y)
                    pending.append(y)
    if type(m["costs"]) is not list:
        raise ModelError("cost table must be a list")
    required_costs = {(b, a) for b, a, _ in raw_edges}
    costs = {}
    for entry in m["costs"]:
        row = fields(entry, {"belief", "action", "cost"})
        key = (belief(row["belief"], states), row["action"])
        if key not in required_costs or key in costs:
            raise ModelError("duplicate or unreachable cost row")
        costs[key] = rational(row["cost"], positive=True)
    if set(costs) != required_costs:
        raise ModelError("costs must cover every reachable enabled action")
    return Arena(digest(m), m["task_id"], assumptions,
                 json.dumps(m["authorization"], sort_keys=True, separators=(",", ":"), allow_nan=False),
                 states, initial, targets, tuple(sorted(reachable)),
                 tuple(sorted((b, a, costs[b, a], ys) for b, a, ys in raw_edges)),
                 tuple((b, tuple(r for r in rs if all(r in valid[s] for s in b)))
                       for b in sorted(reachable)))


def graph_model(graph, initial="s", targets=("t",), *, observations=None,
                emissions=None, valid_resolutions=None, task_id="finite-reachability",
                authorization=None):
    """Build one finite belief-model table from an explicit state graph."""
    if authorization is None:
        bound_authorization = {"effect": "None"}
    elif type(authorization) is not dict:
        raise ValueError("authorization binding must be an object")
    else:
        bound_authorization = json.loads(json.dumps(
            authorization, sort_keys=True, separators=(",", ":"), allow_nan=False))
    states = sorted(set(graph) | {y for moves in graph.values() for _, _, ys in moves for y in ys}
                    | set(targets))
    actions = sorted({a for moves in graph.values() for a, _, _ in moves})
    initial = tuple(sorted(initial if type(initial) is not str else [initial]))
    target_beliefs = {(t,) for t in targets}
    transitions = {(s, a): tuple(sorted(ys)) for s, moves in graph.items() for a, _, ys in moves}
    prices = {(s, a): str(c) for s, moves in graph.items() for a, c, _ in moves}
    enabled = {s: sorted(a for a, _, _ in graph.get(s, [])) for s in states}
    report_keys = {(y, a) for (_, a), ys in transitions.items() for y in ys}
    reports = {key: (observations or {}).get(key, key[0]) for key in report_keys}
    pending, known, costs = [initial], {initial}, []
    for b in pending:
        if b in target_beliefs:
            continue
        for a in actions:
            if not all(a in enabled[s] for s in b):
                continue
            ps = {Fraction(prices[s, a]) for s in b}
            if len(ps) != 1:
                raise ValueError("fixture needs an explicit belief-dependent cost")
            costs.append({"belief": list(b), "action": a, "cost": str(next(iter(ps)))})
            post = {y for s in b for y in transitions[s, a]}
            for o in sorted({reports[y, a] for y in post}):
                y = tuple(sorted(s for s in post if reports[s, a] == o))
                if y not in known:
                    known.add(y)
                    pending.append(y)
    resolutions = sorted(set((emissions or {}).values())
                         | {r for rows in (valid_resolutions or {}).values() for r in rows})
    return {"schema": "wdp-finite-belief-model-v1", "task_id": task_id,
            "assumptions": ["A1", "A2", "A4", "A5", "A6"],
            "authorization": bound_authorization, "states": states, "actions": actions,
            "enabled": enabled,
            "transitions": [{"state": s, "action": a, "successors": list(ys)}
                            for (s, a), ys in sorted(transitions.items())],
            "reports": [{"state": s, "action": a, "observation": o}
                        for (s, a), o in sorted(reports.items())],
            "initial": list(initial), "targets": [list(b) for b in sorted(target_beliefs)],
            "costs": sorted(costs, key=lambda row: (row["belief"], row["action"])),
            "resolutions": resolutions,
            "valid_resolutions": {s: sorted((valid_resolutions or {}).get(s, [])) for s in states},
            "emissions": emissions or {}}
