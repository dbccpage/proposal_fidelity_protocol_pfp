"""Target checker of record for MSS-089, row 89 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 89): check algebraic sum or justified dependence of error
bounds. Negative instance: two correlated errors assumed independent are
rejected.

Input (closed): ``{"weights": [p], "sources": [[id, [e]]], "composed": [e],
"rule": "sum" | "independent" | "dependent", "bound": B}``. The outcomes are
finitely many, with rational probabilities ``weights``; source i has error
e_i(w) at outcome w. The composed error is the pointwise sum.

The three composition rules and what the checker decides for each:

- ``sum``: the algebraic (worst-case) sum. B must be at least the sum over
  sources of max |e_i|, which bounds |sum e_i(w)| at every outcome.
- ``independent``: a variance bound by root-sum-square. The sources must be
  pairwise independent under the weights, decided exactly from the joint
  distribution of their values, and B^2 must be at least the sum of Var(e_i).
- ``dependent``: justified dependence. B^2 must be at least Var(sum e_i),
  computed exactly with every covariance.

Declared input class: finite outcome spaces with rational weights; bounds on
the worst case (``sum``) or on the standard deviation of the composed error
(the other two), compared through squares so no root is taken.

Clauses, decided in this order:

- C1 ``R089_ASSUMED_INDEPENDENT``: the rule is ``independent`` and two
  sources are not independent (the level's negative);
- C2 ``R089_SUM_BOUND``: the rule is ``sum`` and B is below the algebraic
  sum of worst-case errors;
- C3 ``R089_VARIANCE_BOUND``: B^2 is below the variance the rule requires;
- C4 ``R089_COMPOSED_MISMATCH``: the claimed composed errors are not the
  pointwise sums.
"""

STAGE = 89
ROW_SHA256 = "sha256:9fcfdd1b96d6ce9e907f0b5e802a4b4dba5ce3cd7b60d316b88e54a948118f3a"
FIELDS = ("bound", "composed", "rule", "sources", "weights")
CLAUSES = (
    ("C1", "R089_ASSUMED_INDEPENDENT"),
    ("C2", "R089_SUM_BOUND"),
    ("C3", "R089_VARIANCE_BOUND"),
    ("C4", "R089_COMPOSED_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "bound": "3/2",
    "composed": ["2/1", "2/1", "-2/1", "-2/1"],
    "rule": "independent",
    "sources": [["e1", ["1/1", "1/1", "-1/1", "-1/1"]], ["e2", ["1/1", "1/1", "-1/1", "-1/1"]]],
    "weights": ["1/4", "1/4", "1/4", "1/4"],
}
OWN_NEGATIVE_CODE = "R089_ASSUMED_INDEPENDENT"


def _mean(values, weights):
    return sum((v * w for v, w in zip(values, weights)), Fraction(0))


def _variance(values, weights):
    mean = _mean(values, weights)
    return _mean([(v - mean) ** 2 for v in values], weights)


def _independent(xs, ys, weights):
    def law(values):
        out = {}
        for v, w in zip(values, weights):
            out[v] = out.get(v, Fraction(0)) + w
        return out

    joint = law(list(zip(xs, ys)))
    px, py = law(xs), law(ys)
    return all(joint.get((a, b), Fraction(0)) == px[a] * py[b] for a in px for b in py)


def _decide(payload):
    weights = _rats(payload["weights"])
    _require(weights and all(w > 0 for w in weights) and sum(weights) == 1, "R_SCHEMA")
    sources = []
    for source in _seq(payload["sources"]):
        _seq(source, 2)
        _text(source[0])
        sources.append(_rats(source[1], len(weights)))
    _require(sources, "R_SCHEMA")
    composed = _rats(payload["composed"], len(weights))
    rule = payload["rule"]
    _require(rule in ("sum", "independent", "dependent"), "R_SCHEMA")
    bound = _rat(payload["bound"])
    _require(bound >= 0, "R_SCHEMA")
    total = [sum(values, Fraction(0)) for values in zip(*sources)]
    if rule == "independent":
        for i, xs in enumerate(sources):
            for ys in sources[i + 1:]:
                _require(_independent(xs, ys, weights), "R089_ASSUMED_INDEPENDENT")
    if rule == "sum":
        _require(bound >= sum((max(abs(v) for v in values) for values in sources), Fraction(0)), "R089_SUM_BOUND")
    if rule == "independent":
        _require(bound * bound >= sum((_variance(values, weights) for values in sources), Fraction(0)),
                 "R089_VARIANCE_BOUND")
    if rule == "dependent":
        _require(bound * bound >= _variance(total, weights), "R089_VARIANCE_BOUND")
    _require(composed == total, "R089_COMPOSED_MISMATCH")
