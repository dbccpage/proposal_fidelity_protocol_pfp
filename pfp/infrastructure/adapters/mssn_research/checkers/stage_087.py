"""Target checker of record for MSS-087, row 87 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 87): check challenger mutation changes expected verdict.
Negative instance: a negative fixture that still passes is flagged.

Input (closed): ``{"subject": [name] | [name, bound], "base": [nat],
"challenges": [{"mutant": [nat], "result": "PASS" | "FAIL"}]}``.

The audited subject is one of the checks pinned in this file, run here on
every fixture: ``nondecreasing``, ``distinct``, or ``bounded_sum`` with a
natural bound. A challenge is a mutant of the base fixture meant as a negative
fixture: the base must pass, the mutant must differ from it, and running the
subject on the mutant must change the verdict to FAIL. The challenger's
recorded result is compared with the recomputed one.

Declared input class: the three pinned subjects over lists of naturals. The
subject is never the producer's own code.

Clauses, decided in this order:

- C1 ``R087_BASE_REFUSED``: the subject refuses the base fixture, so no
  challenge can change its verdict;
- C2 ``R087_NOT_A_MUTATION``: a mutant equals the base;
- C3 ``R087_NEGATIVE_STILL_PASSES``: the subject still accepts a mutant (the
  level's negative, which is flagged);
- C4 ``R087_RESULT_MISMATCH``: a recorded result differs from the recomputed
  verdict.
"""

STAGE = 87
ROW_SHA256 = "sha256:d73bd7add88c5410df2d16a9669d74a41a3ac5bd6b17dcd49f0b6a0b8833f2c7"
FIELDS = ("base", "challenges", "subject")
CLAUSES = (
    ("C1", "R087_BASE_REFUSED"),
    ("C2", "R087_NOT_A_MUTATION"),
    ("C3", "R087_NEGATIVE_STILL_PASSES"),
    ("C4", "R087_RESULT_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "base": [1, 2, 3],
    "challenges": [{"mutant": [1, 2, 5], "result": "PASS"}],
    "subject": ["nondecreasing"],
}
OWN_NEGATIVE_CODE = "R087_NEGATIVE_STILL_PASSES"


def _subject(value):
    _seq(value)
    _require(len(value) in (1, 2), "R_SCHEMA")
    name = value[0]
    if name == "nondecreasing":
        _require(len(value) == 1, "R_SCHEMA")
        return lambda xs: all(a <= b for a, b in zip(xs, xs[1:]))
    if name == "distinct":
        _require(len(value) == 1, "R_SCHEMA")
        return lambda xs: len(set(xs)) == len(xs)
    _require(name == "bounded_sum" and len(value) == 2, "R_SCHEMA")
    bound = _nat(value[1])
    return lambda xs: sum(xs) <= bound


def _fixture(value):
    return [_nat(item) for item in _seq(value)]


def _decide(payload):
    subject = _subject(payload["subject"])
    base = _fixture(payload["base"])
    challenges = []
    for challenge in _seq(payload["challenges"]):
        _require(isinstance(challenge, dict) and set(challenge) == {"mutant", "result"}, "R_SCHEMA")
        _require(challenge["result"] in ("PASS", "FAIL"), "R_SCHEMA")
        challenges.append((_fixture(challenge["mutant"]), challenge["result"]))
    _require(challenges, "R_SCHEMA")
    _require(subject(base), "R087_BASE_REFUSED")
    for mutant, _ in challenges:
        _require(mutant != base, "R087_NOT_A_MUTATION")
    for mutant, _ in challenges:
        _require(not subject(mutant), "R087_NEGATIVE_STILL_PASSES")
    for mutant, result in challenges:
        _require(result == ("PASS" if subject(mutant) else "FAIL"), "R087_RESULT_MISMATCH")
