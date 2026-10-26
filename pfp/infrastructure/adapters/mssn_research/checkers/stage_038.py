"""Target checker of record for MSS-038, row 38 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 38): check both worlds reuse the same exogenous assignment.
Negative instance: a counterfactual changing the latent draw is rejected.

Input (closed): ``{"exogenous": [name], "equations": [[variable, [parent],
[bit]]], "observation": [[variable, bit]], "intervention": [variable, bit],
"query": variable, "twins": [[[bit], [bit]]], "answer": [bit]}``. The model
is written as at stage 37 (truth tables over parents; acyclic). Each twin
pairs the exogenous assignment of the factual world with the one used in the
counterfactual world. ``answer`` is the declared set of values the query
takes in the counterfactual world, over every twin.

Declared input class: Boolean structural models with at most 12 exogenous
bits. Abduction is exhaustive: the twins must cover exactly the exogenous
assignments consistent with the observation, and when more than one is
consistent the answer is a set, never a pick. The counterfactual is
evaluated from the factual assignment, with the intervened equation replaced
by its constant.

Clauses, each recomputed:

- C1 ``R038_REDRAWN_BACKGROUND``: a twin's counterfactual assignment is not its
  factual assignment (the level's negative);
- C2 ``R038_ABDUCTION_MISMATCH``: the twins' factual assignments are not
  exactly the assignments consistent with the observation;
- C3 ``R038_ANSWER_MISMATCH``: the declared answer set is not the recomputed
  set of counterfactual query values.
"""

from itertools import product

STAGE = 38
ROW_SHA256 = "sha256:2441efda5bd3d15167fb5fdf5dfc6aef80afb304241c6680f8f1ff6f55611e15"
FIELDS = ("answer", "equations", "exogenous", "intervention", "observation", "query", "twins")
CLAUSES = (
    ("C1", "R038_REDRAWN_BACKGROUND"),
    ("C2", "R038_ABDUCTION_MISMATCH"),
    ("C3", "R038_ANSWER_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "answer": [1],
    "equations": [["X", ["U"], [0, 1]], ["Y", ["X"], [0, 1]]],
    "exogenous": ["U"],
    "intervention": ["X", 1],
    "observation": [["X", 0]],
    "query": "Y",
    "twins": [[[0], [1]]],
}
OWN_NEGATIVE_CODE = "R038_REDRAWN_BACKGROUND"


def _bit(value):
    _require(_nat(value) <= 1, "R_SCHEMA")
    return value


def _decide(payload):
    exogenous = [_text(u) for u in _seq(payload["exogenous"])]
    _require(1 <= len(exogenous) <= 12 and len(set(exogenous)) == len(exogenous), "R_SCHEMA")
    equations = {}
    for entry in _seq(payload["equations"]):
        _seq(entry, 3)
        var = _text(entry[0])
        parents = [_text(p) for p in _seq(entry[1])]
        table = [_bit(b) for b in _seq(entry[2], 2 ** len(parents))]
        _require(var not in equations and var not in exogenous and len(set(parents)) == len(parents), "R_SCHEMA")
        equations[var] = (parents, table)
    order, placed = [], set(exogenous)
    for _ in range(len(equations)):
        ready = [v for v in equations if v not in placed and all(p in placed for p in equations[v][0])]
        for v in ready:
            order.append(v)
            placed.add(v)
    _require(len(order) == len(equations), "R_SCHEMA")
    observation = {}
    for row in _seq(payload["observation"]):
        _seq(row, 2)
        var = _text(row[0])
        _require(var in equations and var not in observation, "R_SCHEMA")
        observation[var] = _bit(row[1])
    intervention = _seq(payload["intervention"], 2)
    target, forced = _text(intervention[0]), _bit(intervention[1])
    query = _text(payload["query"])
    _require(target in equations and query in equations, "R_SCHEMA")

    def world(u, force):
        values = dict(zip(exogenous, u))
        for v in order:
            if v in force:
                values[v] = force[v]
                continue
            parents, table = equations[v]
            index = 0
            for p in parents:
                index = 2 * index + values[p]
            values[v] = table[index]
        return values

    factual = []
    for twin in _seq(payload["twins"]):
        _seq(twin, 2)
        u = tuple(_bit(b) for b in _seq(twin[0], len(exogenous)))
        u2 = tuple(_bit(b) for b in _seq(twin[1], len(exogenous)))
        _require(u == u2, "R038_REDRAWN_BACKGROUND")
        _require(u not in factual, "R_SCHEMA")
        factual.append(u)
    consistent = set()
    for u in product((0, 1), repeat=len(exogenous)):
        values = world(u, {})
        if all(values[v] == b for v, b in observation.items()):
            consistent.add(u)
    _require(set(factual) == consistent, "R038_ABDUCTION_MISMATCH")
    answer = [_bit(b) for b in _seq(payload["answer"])]
    _require(answer == sorted(set(answer)), "R_SCHEMA")
    recomputed = sorted({world(u, {target: forced})[query] for u in factual})
    _require(answer == recomputed, "R038_ANSWER_MISMATCH")
