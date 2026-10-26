"""Test-only draft checker in the receiving side's module form, for the arc
challenge in the harness's draft input schema.  Never registered, never a
checker of record: it exists to prove that the harness's completed records
pass the receiving side's checks up to the checker-of-record cap.

AuthorityEffect: None
"""
import re

STAGE = 2
ROW_SHA256 = "sha256:be4535c6f0efcbb83557a22549d06c7860f0aba47643902d710dd1fe13c3aa6d"
CODES = ("R_EMPTY_INPUT", "R_VERDICT_FIELD", "R_SCHEMA", "R002D_ABSENT", "R002D_SOURCE", "R002D_TARGET",
         "R002D_COLLAPSED")
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"protected": [[0, 2]], "relations": [["arc", [0, 1]], ["arc", [1, 3]]], "sorts": [["node", 3]],
                "symbols": [{"name": "arc", "sorts": ["node", "node"]}], "values": []}
OWN_NEGATIVE_CODE = "R002D_ABSENT"
VERDICT = re.compile(r"^(is_.*|has_.*|verified|passes|passed|valid|ok|verdict|outcome|grade|status)$", re.I)


def _keys(v):
    if isinstance(v, dict):
        return list(v) + [k for x in v.values() for k in _keys(x)]
    if isinstance(v, list):
        return [k for x in v for k in _keys(x)]
    return []


def _leaves(v):
    if isinstance(v, dict):
        return [x for y in v.values() for x in _leaves(y)]
    if isinstance(v, list):
        return [x for y in v for x in _leaves(y)]
    return [v]


def check(payload):
    if not isinstance(payload, dict) or not any(x not in (None, "") for x in _leaves(payload)):
        return ("REFUSED", "R_EMPTY_INPUT")
    data = [x for x in _leaves(payload) if x is not None]
    if any(VERDICT.match(k) for k in _keys(payload)) or all(isinstance(x, bool) for x in data):
        return ("REFUSED", "R_VERDICT_FIELD")
    if set(payload) != {"protected", "relations", "sorts", "symbols", "values"}:
        return ("REFUSED", "R_SCHEMA")
    if not payload["sorts"]:
        return ("REFUSED", "R_EMPTY_INPUT")
    nodes, off = set(), 0
    for name, count in payload["sorts"]:
        if name == "node":
            nodes = set(range(off, off + count))
        off += count
    for _, args in payload["relations"]:
        if len(args) != 2 or args[0] >= off or args[1] >= off:
            return ("REFUSED", "R002D_ABSENT")
        if args[0] not in nodes:
            return ("REFUSED", "R002D_SOURCE")
        if args[1] not in nodes:
            return ("REFUSED", "R002D_TARGET")

    def profile(d):
        out = {("node",)} if d in nodes else set()
        for name, args in payload["relations"]:
            if d in args:
                out.add((name, tuple(None if a == d else a for a in args)))
        return out

    for p, q in payload["protected"]:
        if profile(p) == profile(q):
            return ("REFUSED", "R002D_COLLAPSED")
    return ("PASS", None)
