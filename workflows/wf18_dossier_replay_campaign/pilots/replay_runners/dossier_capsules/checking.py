"""Exact finite witness checks for the dossier campaign; no stored-answer oracle."""
from __future__ import annotations

from fractions import Fraction as Q
from itertools import combinations, product
import re

from jsonschema import Draft202012Validator, validators
from jsonschema.exceptions import ValidationError

from omega_engine_pfp.domain.pilots.checker_registry import strict_json

StrictValidator = validators.extend(Draft202012Validator, type_checker=
    Draft202012Validator.TYPE_CHECKER.redefine("integer", lambda _, x: type(x) is int))
RATIONAL = {"type": "string", "pattern": r"^-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?$", "maxLength": 80}
INTEGER = {"type": "integer", "minimum": 0}


def array(items, length=None):
    value = {"type": "array", "items": items, "maxItems": 100}
    if length is not None:
        value.update(minItems=length, maxItems=length)
    return value


def record(**properties):
    return {"type": "object", "properties": properties, "required": list(properties),
            "additionalProperties": False}


def rational(value):
    if type(value) is not str or len(value) > 80 or not re.fullmatch(RATIONAL["pattern"], value):
        raise ValueError("EXACT_RATIONAL_REQUIRED")
    return Q(value)


def mv(a, x):
    if not a or any(len(row) != len(x) for row in a):
        raise ValueError("DIMENSION_MISMATCH")
    return [sum((Q(v) * Q(w) for v, w in zip(row, x)), Q(0)) for row in a]


def rank(a):
    a = [[Q(x) for x in row] for row in a]
    r = 0
    for j in range(len(a[0])):
        pivot = next((i for i in range(r, len(a)) if a[i][j]), None)
        if pivot is None:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        q = a[r][j]
        a[r] = [x / q for x in a[r]]
        for i in range(len(a)):
            if i != r:
                q = a[i][j]
                a[i] = [x - q * y for x, y in zip(a[i], a[r])]
        r += 1
    return r


def components(n, edges):
    groups = []
    remaining = set(range(n))
    while remaining:
        seen = {min(remaining)}
        while True:
            expanded = seen | {b for a, b in edges if a in seen} | {a for a, b in edges if b in seen}
            if expanded == seen:
                break
            seen = expanded
        groups.append(sorted(seen))
        remaining -= seen
    return sorted(groups)


def graph_facts(task):
    n, edges = task["n"], task["edges"]
    groups = components(n, edges)
    bridges = [i for i in range(len(edges)) if len(components(n, edges[:i] + edges[i+1:])) > len(groups)]
    edge_set = {tuple(sorted(e)) for e in edges}
    triangles = sum(all(tuple(sorted(e)) in edge_set for e in combinations(vs, 2))
                    for vs in combinations(range(n), 3))
    return dict(components=groups, bridges=bridges, cycle_rank=len(edges)-n+len(groups), triangles=triangles)


def answer_schema(task):
    kind = task["kind"]
    if kind == "linear":
        return record(solution=array(RATIONAL, len(task["b"])), target=RATIONAL)
    if kind == "graph":
        return record(components=array(array(INTEGER)), bridges=array(INTEGER), cycle_rank=INTEGER, triangles=INTEGER)
    if kind == "repair":
        return record(removed=array(INTEGER), cycle_rank=INTEGER)
    if kind == "lookup":
        return record(code={"enum": ["VALUE", "MAP_UNDEFINED", "MISSING_LENGTH"]},
                      value={"anyOf": [RATIONAL, {"type": "null"}]})
    if kind == "spin":
        return record(spins=array({"type": "integer", "enum": [0, 1]}, task["n"]),
                      residual=array({"type": "integer", "enum": [0, 1]}, len(task["edges"])),
                      weight=INTEGER)
    if kind == "lp":
        return record(potential=array(RATIONAL, len(task["matrix"][0])),
                      dual=array(RATIONAL, len(task["matrix"])), objective=RATIONAL)
    if kind == "scope":
        return record(ranks=array(INTEGER, 4), betti={"anyOf": [array(INTEGER, 5), {"type": "null"}]},
                      topology_status={"enum": ["MATCH", "DECLARED_TOPOLOGY_MISMATCH", "CHAIN_LAW_FAILURE"]},
                      cup_status={"enum": ["UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER"]})
    raise ValueError("UNKNOWN_TASK")


def check_answer(task, answer):
    StrictValidator(answer_schema(task)).validate(answer)
    kind = task["kind"]
    if kind == "linear":
        x = list(map(rational, answer["solution"]))
        return mv(task["matrix"], x) == list(map(Q, task["b"])) and rational(answer["target"]) == sum(Q(c)*v for c, v in zip(task["target"], x))
    if kind == "graph":
        canonical = dict(answer, components=sorted(sorted(g) for g in answer["components"]), bridges=sorted(answer["bridges"]))
        return canonical == graph_facts(task)
    if kind == "repair":
        removed = answer["removed"]
        if len(set(removed)) != len(removed) or any(i >= len(task["edges"]) for i in removed):
            return False
        remaining = [e for i, e in enumerate(task["edges"]) if i not in removed]
        original = components(task["n"], task["edges"])
        minimum = len(task["edges"]) - task["n"] + len(original)
        return (len(removed) == minimum and components(task["n"], remaining) == original
                and len(remaining) - task["n"] + len(original) == answer["cycle_rank"] == 0)
    if kind == "lookup":
        edge = next((e for e in task["edges"] if sorted(e[:2]) == sorted(task["query"])), None)
        code = "MAP_UNDEFINED" if edge is None else "MISSING_LENGTH" if edge[2] is None else "VALUE"
        return answer["code"] == code and (answer["value"] is None if code != "VALUE" else answer["value"] is not None and rational(answer["value"]) == Q(edge[2]))
    if kind == "spin":
        def residual(spins):
            return [c ^ spins[a] ^ spins[b] for (a, b), c in zip(task["edges"], task["target"])]
        r = residual(answer["spins"])
        minimum = min(sum(residual(s)) for s in product((0, 1), repeat=task["n"]))
        return answer["residual"] == r and answer["weight"] == sum(r) == minimum
    if kind == "lp":
        a, g, weights = task["matrix"], list(map(Q, task["flux"])), list(map(Q, task["weights"]))
        x, v = list(map(rational, answer["potential"])), list(map(rational, answer["dual"]))
        residual = [g_i - ax for g_i, ax in zip(g, mv(a, x))]
        primal = sum(w * abs(r) for w, r in zip(weights, residual))
        dual = sum(g_i * v_i for g_i, v_i in zip(g, v))
        return (all(z == 0 for z in mv(list(zip(*a)), v)) and all(abs(z) <= w for z, w in zip(v, weights))
                and primal == dual == rational(answer["objective"]))
    if kind == "scope":
        matrices = task["matrices"]
        ranks = list(map(rank, matrices))
        dims = [len(matrices[0][0])] + [len(a) for a in matrices]
        betti = [dims[i] - ([0] + ranks)[i] - (ranks + [0])[i] for i in range(5)]
        nilpotent = all(all(all(v == 0 for v in mv(b, col)) for col in zip(*a)) for a, b in zip(matrices, matrices[1:]))
        status = "CHAIN_LAW_FAILURE" if not nilpotent else "MATCH" if betti == task["declared_betti"] else "DECLARED_TOPOLOGY_MISMATCH"
        if not nilpotent:
            betti = None
        return answer == dict(ranks=ranks, betti=betti, topology_status=status, cup_status="UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER")
    raise ValueError("UNKNOWN_TASK")


def evaluate(task, raw, schema):
    try:
        payload = strict_json(raw)
        StrictValidator(schema).validate(payload)
        valid = check_answer(task, payload["answer"])
        return {"status": "HOST_ACCEPTED" if valid else "TYPED_REFUSAL", "code": "WITNESS_VALID" if valid else "WITNESS_INVALID"}
    except (ValueError, TypeError, KeyError, ZeroDivisionError) as exc:
        return {"status": "TYPED_REFUSAL", "code": type(exc).__name__}
    except ValidationError:
        return {"status": "TYPED_REFUSAL", "code": "SCHEMA_INVALID"}
