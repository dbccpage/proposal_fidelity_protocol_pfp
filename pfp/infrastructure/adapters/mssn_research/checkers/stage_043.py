"""Target checker of record for MSS-043, row 43 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 43): check scope and effect inclusion at each execution edge.
Negative instance: an effect outside granted capability is refused.

Input (closed): ``{"operations": [[operation, [effect]]], "scopes": [[scope,
parent | null, [effect]]], "edges": [[edge, scope, [operation]]]}``. Each
operation has a declared effect row. Scopes form a tree (one root, whose
parent is null); each grants a set of effects. An execution edge runs in its
innermost scope and performs a list of operations; its effects are computed
as the union of their effect rows, never declared.

Declared input class: finite scope trees and finite execution edges; effects
are atomic names; a scope's grant is checked against its parent's (grants
may only narrow going inward).

Clauses, each recomputed:

- C1 ``R043_OUTSIDE_GRANT``: an edge's computed effects are not all granted by
  its innermost scope (the level's negative);
- C2 ``R043_GRANT_ESCALATION``: a nested scope grants an effect its parent
  does not;
- C3 ``R043_UNKNOWN_OPERATION``: an edge performs an operation with no
  declared effect row, so its effects cannot be computed.
"""

STAGE = 43
ROW_SHA256 = "sha256:e2ef5290f08323f430e84b7b93dcf19f72b6e4f53658fa8c92fb4a1b8293e950"
FIELDS = ("edges", "operations", "scopes")
CLAUSES = (
    ("C1", "R043_OUTSIDE_GRANT"),
    ("C2", "R043_GRANT_ESCALATION"),
    ("C3", "R043_UNKNOWN_OPERATION"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "edges": [["e1", "S1", ["load"]], ["e2", "S1", ["store"]]],
    "operations": [["load", ["read"]], ["store", ["write"]]],
    "scopes": [["S1", None, ["read"]]],
}
OWN_NEGATIVE_CODE = "R043_OUTSIDE_GRANT"


def _names(value):
    out = [_text(x) for x in _seq(value)]
    _require(len(set(out)) == len(out), "R_SCHEMA")
    return set(out)


def _decide(payload):
    rows = {}
    for entry in _seq(payload["operations"]):
        _seq(entry, 2)
        name = _text(entry[0])
        _require(name not in rows, "R_SCHEMA")
        rows[name] = _names(entry[1])
    scopes = {}
    for entry in _seq(payload["scopes"]):
        _seq(entry, 3)
        name = _text(entry[0])
        parent = None if entry[1] is None else _text(entry[1])
        _require(name not in scopes, "R_SCHEMA")
        scopes[name] = (parent, _names(entry[2]))
    roots = [s for s, (parent, _) in scopes.items() if parent is None]
    _require(len(roots) == 1, "R_SCHEMA")
    for name, (parent, _) in scopes.items():
        seen, current = {name}, parent
        while current is not None:
            _require(current in scopes and current not in seen, "R_SCHEMA")
            seen.add(current)
            current = scopes[current][0]
    for name, (parent, grant) in scopes.items():
        if parent is not None:
            _require(grant <= scopes[parent][1], "R043_GRANT_ESCALATION")
    edges = []
    for entry in _seq(payload["edges"]):
        _seq(entry, 3)
        name, scope = _text(entry[0]), _text(entry[1])
        _require(scope in scopes and name not in [e for e, _, _ in edges], "R_SCHEMA")
        ops = [_text(o) for o in _seq(entry[2])]
        edges.append((name, scope, ops))
    for _, _, ops in edges:
        _require(all(op in rows for op in ops), "R043_UNKNOWN_OPERATION")
    for _, scope, ops in edges:
        effects = set().union(*(rows[op] for op in ops)) if ops else set()
        _require(effects <= scopes[scope][1], "R043_OUTSIDE_GRANT")
