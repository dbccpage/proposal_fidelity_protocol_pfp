"""Target checker of record for MSS-033, row 33 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 33): check composition across scale steps and declared
approximation error. Negative instance: a scale jump without a loss bound is
rejected.

Input (closed): ``{"reading": [rational], "steps": [[[nat], rational]],
"jumps": [[from, to, [nat], rational | null]]}``. Scale 0 is the carrier of
``reading``. Step s maps scale s onto scale s + 1 (point i goes to block
``map[i]``; the blocks are 0..n-1, all used) and carries a declared error
bound. The reading at scale s + 1 is the block average of the reading at
scale s. The error of a map from scale i to scale j is the largest
|reading_i(x) - reading_j(map(x))|. A jump declares a map from scale i to a
later scale j and a bound.

Declared input class: finite chains of block maps on finite carriers, one
exact rational reading, block averaging as the coarse reading, and the
sup-norm error. Every quantity is an exact rational; no float is read.

Clauses, each recomputed:

- C1 ``R033_NOT_COMPOSITE``: a jump's map is not the composite of the steps
  between its scales;
- C2 ``R033_UNBOUNDED_JUMP``: a jump declares no bound (the level's
  negative);
- C3 ``R033_BOUND_TOO_SMALL``: a declared step or jump bound is below the
  recomputed error;
- C4 ``R033_BOUND_NOT_COMPOSED``: a jump's bound exceeds the sum of the bounds
  of the steps it composes, so it does not follow from them.
"""

STAGE = 33
ROW_SHA256 = "sha256:8f7850e69ccda5c3433803e4cd468881b18d5a8a19aa87c0f05df64a73af840d"
FIELDS = ("jumps", "reading", "steps")
CLAUSES = (
    ("C1", "R033_NOT_COMPOSITE"),
    ("C2", "R033_UNBOUNDED_JUMP"),
    ("C3", "R033_BOUND_TOO_SMALL"),
    ("C4", "R033_BOUND_NOT_COMPOSED"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "jumps": [[0, 2, [0, 0, 0, 0], None]],
    "reading": ["0/1", "1/1", "2/1", "3/1"],
    "steps": [[[0, 0, 1, 1], "1/2"], [[0, 0], "1/1"]],
}
OWN_NEGATIVE_CODE = "R033_UNBOUNDED_JUMP"


def _error(fine, coarse, mapping):
    return max(abs(value - coarse[mapping[i]]) for i, value in enumerate(fine))


def _decide(payload):
    readings = [_rats(payload["reading"])]
    _require(readings[0], "R_SCHEMA")
    maps, bounds = [], []
    for entry in _seq(payload["steps"]):
        _seq(entry, 2)
        mapping = [_nat(b) for b in _seq(entry[0], len(readings[-1]))]
        blocks = max(mapping) + 1
        _require(set(mapping) == set(range(blocks)), "R_SCHEMA")
        members = [[readings[-1][i] for i in range(len(mapping)) if mapping[i] == b] for b in range(blocks)]
        readings.append([sum(m, Fraction(0)) / len(m) for m in members])
        maps.append(mapping)
        bounds.append(_rat(entry[1]))
    jumps = []
    for entry in _seq(payload["jumps"]):
        _seq(entry, 4)
        start, end = _nat(entry[0]), _nat(entry[1])
        _require(start < end < len(readings), "R_SCHEMA")
        mapping = [_nat(b) for b in _seq(entry[2], len(readings[start]))]
        composite = list(range(len(readings[start])))
        for s in range(start, end):
            composite = [maps[s][b] for b in composite]
        _require(mapping == composite, "R033_NOT_COMPOSITE")
        jumps.append((start, end, mapping, entry[3]))
    for start, end, _, bound in jumps:
        _require(bound is not None, "R033_UNBOUNDED_JUMP")
    for s, bound in enumerate(bounds):
        _require(bound >= _error(readings[s], readings[s + 1], maps[s]), "R033_BOUND_TOO_SMALL")
    for start, end, mapping, bound in jumps:
        _require(_rat(bound) >= _error(readings[start], readings[end], mapping), "R033_BOUND_TOO_SMALL")
    for start, end, _, bound in jumps:
        _require(_rat(bound) <= sum(bounds[start:end], Fraction(0)), "R033_BOUND_NOT_COMPOSED")
