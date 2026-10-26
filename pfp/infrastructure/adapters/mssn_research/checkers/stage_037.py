"""Target checker of record for MSS-037, row 37 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 37): check graph acyclicity and replace structural assignment
for intervention. Negative instance: an observational correlation is not
labeled a causal effect.

Input (closed): ``{"exogenous": [name], "equations": [[variable, [parent],
[bit]]], "report": [treatment, outcome, rational | null, rational]}``. Each
exogenous variable is a uniform independent bit. An equation gives a
variable's value as a truth table over its parents (assignments in binary
order, the first parent most significant). ``report`` declares, for a
treatment and an outcome, the observed difference P(Y=1 | X=1) - P(Y=1 |
X=0) (null when a conditioning event is empty) and the forced difference
P(Y=1 | do X=1) - P(Y=1 | do X=0).

Declared input class: Boolean structural models with at most 12 uniform
exogenous bits; probabilities are exact counts over every exogenous
assignment; binary treatment and outcome; risk differences only. Forcing
replaces the treatment's equation by a constant and re-evaluates.

Clauses, each recomputed:

- C1 ``R037_CYCLIC``: the parent graph of the equations has a cycle;
- C2 ``R037_OBSERVATION_MISMATCH``: the declared observed difference is not
  the recomputed one;
- C3 ``R037_OBSERVATION_AS_FORCED``: the declared forced difference repeats
  the observed difference while the recomputed forced difference differs
  from it (the level's negative: a correlation labelled a causal effect);
- C4 ``R037_FORCED_MISMATCH``: the declared forced difference is otherwise
  not the recomputed one.
"""

from itertools import product

STAGE = 37
ROW_SHA256 = "sha256:db70887e89843981b8d219856ff1d90f96c67767a31300311c1359046b10cb24"
FIELDS = ("equations", "exogenous", "report")
CLAUSES = (
    ("C1", "R037_CYCLIC"),
    ("C2", "R037_OBSERVATION_MISMATCH"),
    ("C3", "R037_OBSERVATION_AS_FORCED"),
    ("C4", "R037_FORCED_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "equations": [["Z", ["U"], [0, 1]], ["X", ["Z"], [0, 1]], ["Y", ["Z"], [0, 1]]],
    "exogenous": ["U"],
    "report": ["X", "Y", "1/1", "1/1"],
}
OWN_NEGATIVE_CODE = "R037_OBSERVATION_AS_FORCED"


def _decide(payload):
    exogenous = [_text(u) for u in _seq(payload["exogenous"])]
    _require(1 <= len(exogenous) <= 12 and len(set(exogenous)) == len(exogenous), "R_SCHEMA")
    equations = {}
    for entry in _seq(payload["equations"]):
        _seq(entry, 3)
        var = _text(entry[0])
        parents = [_text(p) for p in _seq(entry[1])]
        table = [_nat(b) for b in _seq(entry[2], 2 ** len(parents))]
        _require(var not in equations and var not in exogenous and all(b <= 1 for b in table), "R_SCHEMA")
        _require(len(set(parents)) == len(parents), "R_SCHEMA")
        equations[var] = (parents, table)
    for parents, _ in equations.values():
        _require(all(p in equations or p in exogenous for p in parents), "R_SCHEMA")
    order, placed = [], set(exogenous)
    for _ in range(len(equations)):
        ready = [v for v in equations if v not in placed and all(p in placed for p in equations[v][0])]
        for v in ready:
            order.append(v)
            placed.add(v)
    _require(len(order) == len(equations), "R037_CYCLIC")
    report = _seq(payload["report"], 4)
    x, y = _text(report[0]), _text(report[1])
    _require(x in equations and y in equations and x != y, "R_SCHEMA")

    def world(u, forced):
        values = dict(zip(exogenous, u))
        for v in order:
            if v in forced:
                values[v] = forced[v]
                continue
            parents, table = equations[v]
            index = 0
            for p in parents:
                index = 2 * index + values[p]
            values[v] = table[index]
        return values

    worlds = [world(u, {}) for u in product((0, 1), repeat=len(exogenous))]
    rates = []
    for value in (1, 0):
        chosen = [w for w in worlds if w[x] == value]
        rates.append(None if not chosen else Fraction(sum(w[y] for w in chosen), len(chosen)))
    observed = None if None in rates else rates[0] - rates[1]
    declared = None if report[2] is None else _rat(report[2])
    _require(declared == observed, "R037_OBSERVATION_MISMATCH")
    forced_rates = []
    for value in (1, 0):
        runs = [world(u, {x: value}) for u in product((0, 1), repeat=len(exogenous))]
        forced_rates.append(Fraction(sum(w[y] for w in runs), len(runs)))
    forced = forced_rates[0] - forced_rates[1]
    claim = _rat(report[3])
    _require(not (claim == observed and forced != observed), "R037_OBSERVATION_AS_FORCED")
    _require(claim == forced, "R037_FORCED_MISMATCH")
