"""Target checker of record for MSS-060, row 60 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 60): check commuting generators and unique declared syndrome
behaviour. Negative instance: anticommuting check generators are rejected.

Input (closed): ``{"sites": n, "checks": [[x, z]], "errors": [[x, z]],
"readings": [bits]}``. A word (x | z) over n two-bit sites is two strings of
``0``/``1`` of length n. Two words commute when the exchange count
x . z' + z . x' is even. ``readings[e]`` is the producer's reading of error e:
one bit per check, the parity of the exchange count of e with that check.

Declared input class: words over GF(2)^(2n), n >= 1; finitely many checks and
declared errors. Words of the wrong length are refused before any comparison
(never truncated).

Clauses, decided in this order:

- C1 ``R060_LENGTH``: a word does not have length n in both halves;
- C2 ``R060_ANTICOMMUTING``: two checks have an odd exchange count (the
  level's negative);
- C3 ``R060_NOT_DISTINCT``: the recomputed readings of the declared errors are
  not all nonzero and pairwise distinct;
- C4 ``R060_READING``: a claimed reading differs from the recomputed one.
"""

STAGE = 60
ROW_SHA256 = "sha256:63fd1d60fd44ab660739d592ff1681c858fa66c5a1904244a08a5985e492948e"
FIELDS = ("checks", "errors", "readings", "sites")
CLAUSES = (
    ("C1", "R060_LENGTH"),
    ("C2", "R060_ANTICOMMUTING"),
    ("C3", "R060_NOT_DISTINCT"),
    ("C4", "R060_READING"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "checks": [["100", "000"], ["000", "100"]],
    "errors": [["010", "000"]],
    "readings": ["00"],
    "sites": 3,
}
OWN_NEGATIVE_CODE = "R060_ANTICOMMUTING"
_BITS = re.compile(r"[01]*")


def _word(value):
    _seq(value, 2)
    for half in value:
        _require(isinstance(half, str) and _BITS.fullmatch(half) is not None, "R_SCHEMA")
    return value[0], value[1]


def _exchange(u, v):
    return sum(int(a) * int(b) for a, b in zip(u[0], v[1])) + sum(int(a) * int(b) for a, b in zip(u[1], v[0]))


def _decide(payload):
    n = _nat(payload["sites"])
    _require(n >= 1, "R_SCHEMA")
    checks = [_word(w) for w in _seq(payload["checks"])]
    errors = [_word(w) for w in _seq(payload["errors"])]
    readings = [r for r in _seq(payload["readings"])]
    _require(checks and errors, "R_SCHEMA")
    _require(all(isinstance(r, str) and _BITS.fullmatch(r) is not None for r in readings), "R_SCHEMA")
    _require(all(len(x) == n and len(z) == n for x, z in checks + errors), "R060_LENGTH")
    for i, u in enumerate(checks):
        for v in checks[i + 1:]:
            _require(_exchange(u, v) % 2 == 0, "R060_ANTICOMMUTING")
    recomputed = ["".join(str(_exchange(e, c) % 2) for c in checks) for e in errors]
    zero = "0" * len(checks)
    _require(zero not in recomputed and len(set(recomputed)) == len(recomputed), "R060_NOT_DISTINCT")
    _require(readings == recomputed, "R060_READING")
