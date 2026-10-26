"""Target checker of record for MSS-066, row 66 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 66): check exact signed totals and residual support. Negative
instance: a claimed zero with unpaired signed terms is rejected.

Input (closed): ``{"terms": [rational], "pairs": [[i, j]], "rest": [i],
"total": T}``. The producer's cancellation certificate splits the index set of
``terms`` into exact-opposite pairs and a rest; the rest must be single
signed. Its nonzero entries are the residual support, and T must be the
exact total. A zero total alone is never a certificate.

Declared input class: finite lists of exact signed rationals. As an
independent second decision the checker also applies the counting criterion
(a certificate with a single-signed rest exists exactly when one sign
dominates the other at every magnitude); a verified certificate that the
criterion contradicts is refused as a schema fault of the checker's input,
which cannot happen for a correct certificate.

Clauses, decided in this order:

- C1 ``R066_NOT_A_PARTITION``: the pairs and the rest do not use every index
  exactly once;
- C2 ``R066_NOT_OPPOSITE``: a pair's two terms do not sum to exactly 0, or
  are zero;
- C3 ``R066_UNPAIRED_REST``: the rest holds both a positive and a negative
  term (the level's negative: 2, -1, -1 with total 0 and no pairs);
- C4 ``R066_TOTAL``: the claimed total differs from the exact sum.
"""

STAGE = 66
ROW_SHA256 = "sha256:750f6456620a8d16bdb54b2c364aaf3b17a41d0621a72f3ddf6b7837fe576b9b"
FIELDS = ("pairs", "rest", "terms", "total")
CLAUSES = (
    ("C1", "R066_NOT_A_PARTITION"),
    ("C2", "R066_NOT_OPPOSITE"),
    ("C3", "R066_UNPAIRED_REST"),
    ("C4", "R066_TOTAL"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"pairs": [], "rest": [0, 1, 2], "terms": ["2/1", "-1/1", "-1/1"], "total": "0/1"}
OWN_NEGATIVE_CODE = "R066_UNPAIRED_REST"


def _dominated(terms):
    """The counting criterion: one sign dominates at every magnitude."""
    magnitudes = {abs(t) for t in terms if t != 0}
    plus = {m: sum(1 for t in terms if t == m) for m in magnitudes}
    minus = {m: sum(1 for t in terms if t == -m) for m in magnitudes}
    return all(plus[m] >= minus[m] for m in magnitudes) or all(minus[m] >= plus[m] for m in magnitudes)


def _decide(payload):
    terms = _rats(payload["terms"])
    _require(terms, "R_SCHEMA")
    pairs = []
    for item in _seq(payload["pairs"]):
        _seq(item, 2)
        pairs.append((_nat(item[0]), _nat(item[1])))
    rest = [_nat(i) for i in _seq(payload["rest"])]
    total = _rat(payload["total"])
    used = [i for pair in pairs for i in pair] + rest
    _require(sorted(used) == list(range(len(terms))), "R066_NOT_A_PARTITION")
    _require(all(terms[i] + terms[j] == 0 and terms[i] != 0 for i, j in pairs), "R066_NOT_OPPOSITE")
    signs = {1 if terms[i] > 0 else -1 for i in rest if terms[i] != 0}
    _require(len(signs) <= 1, "R066_UNPAIRED_REST")
    _require(_dominated(terms), "R_SCHEMA")
    _require(total == sum(terms, Fraction(0)), "R066_TOTAL")
