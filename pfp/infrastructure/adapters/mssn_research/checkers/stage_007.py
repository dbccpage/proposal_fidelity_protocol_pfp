"""Target checker of record for MSS-007, row 7 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 7): check orbit closure, minimal period and cyclic
representative. Negative instance: ``00`` cannot be a primitive period-two
orbit.

Input (closed): ``{"alphabet": [one-character str], "transitions":
[[a, b]], "length": nat, "orbits": [{"members": [word], "period": nat,
"representative": word}]}``. ``transitions`` is the explicit table of allowed
consecutive symbols (a shift of finite type of memory one; a block shift is
recoded with blocks as symbols). A word of the declared length is a periodic
point when every cyclic consecutive pair, including the wrap-around, is
allowed.

Clauses, recomputed by enumerating every word of the declared length:

- C1 ``R007_NOT_ALLOWED``: a listed word uses a forbidden transition;
- C2 ``R007_ORBIT_NOT_CLOSED``: an orbit's members are not exactly the
  rotations of its representative;
- C3 ``R007_PERIOD_MISMATCH``: the declared period is not the recomputed
  minimal period. A word is primitive exactly when its minimal period equals
  the length, so "``00`` as a primitive period-two orbit" declares period 2
  where the minimal period is 1;
- C4 ``R007_NONCANONICAL_REP``: the representative is not the least rotation;
- C5 ``R007_MISSING_ORBIT``: some allowed periodic word lies in no listed orbit.
"""

from itertools import product

STAGE = 7
ROW_SHA256 = "sha256:37ab079458518cac96e73a7667ffd6a7b44c1f68bbb45eef49082704f7a88b6b"
FIELDS = ("alphabet", "length", "orbits", "transitions")
CLAUSES = (
    ("C1", "R007_NOT_ALLOWED"),
    ("C2", "R007_ORBIT_NOT_CLOSED"),
    ("C3", "R007_PERIOD_MISMATCH"),
    ("C4", "R007_NONCANONICAL_REP"),
    ("C5", "R007_MISSING_ORBIT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "alphabet": ["0", "1"],
    "length": 2,
    "orbits": [
        {"members": ["00"], "period": 2, "representative": "00"},
        {"members": ["01", "10"], "period": 2, "representative": "01"},
        {"members": ["11"], "period": 1, "representative": "11"},
    ],
    "transitions": [["0", "0"], ["0", "1"], ["1", "0"], ["1", "1"]],
}
OWN_NEGATIVE_CODE = "R007_PERIOD_MISMATCH"
MAX_LENGTH = 12


def _decide(payload):
    alphabet = [_text(symbol) for symbol in _seq(payload["alphabet"])]
    _require(all(len(s) == 1 for s in alphabet) and len(set(alphabet)) == len(alphabet), "R_SCHEMA")
    allowed = set()
    for pair in _seq(payload["transitions"]):
        _seq(pair, 2)
        _require(pair[0] in alphabet and pair[1] in alphabet, "R_SCHEMA")
        allowed.add((pair[0], pair[1]))
    n = _nat(payload["length"])
    _require(1 <= n <= MAX_LENGTH, "R_SCHEMA")

    def word(value):
        _require(isinstance(value, str) and len(value) == n and set(value) <= set(alphabet), "R_SCHEMA")
        return value

    def periodic(w):
        return all((w[i], w[(i + 1) % n]) in allowed for i in range(n))

    def rotations(w):
        return {w[i:] + w[:i] for i in range(n)}

    def minimal_period(w):
        return min(p for p in range(1, n + 1) if n % p == 0 and w[p:] + w[:p] == w)

    covered = set()
    for record in _seq(payload["orbits"]):
        _require(isinstance(record, dict) and set(record) == {"members", "period", "representative"}, "R_SCHEMA")
        representative = word(record["representative"])
        members = [word(m) for m in _seq(record["members"])]
        _require(periodic(representative) and all(periodic(m) for m in members), "R007_NOT_ALLOWED")
        _require(len(set(members)) == len(members) and set(members) == rotations(representative), "R007_ORBIT_NOT_CLOSED")
        _require(_nat(record["period"]) == minimal_period(representative), "R007_PERIOD_MISMATCH")
        _require(representative == min(rotations(representative)), "R007_NONCANONICAL_REP")
        _require(not (set(members) & covered), "R_SCHEMA")
        covered |= set(members)
    every = {"".join(letters) for letters in product(alphabet, repeat=n)}
    _require(covered == {w for w in every if periodic(w)}, "R007_MISSING_ORBIT")
