"""Target checker of record for MSS-049, row 49 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 49): check two-component norm in declared field and basis.
Negative instance: an unnamed measurement basis is rejected.

Input (closed): ``{"carrier": tag, "frames": [[name, table]], "frame": name,
"coordinates": [pair, pair], "row": [pair, pair]}``. A pair ``[a, b]`` of
canonical rationals stands for a + b i. ``frames`` declares named 2 x 2
frame tables whose columns are the frame's slots written in the standard
frame. ``coordinates`` are taken in the named ``frame``; ``row`` is the
producer's claim of the same row in the standard frame.

Declared input class: two-slot rows; the carrier is ``"mirror_pairs"``
(Q(i)) or ``"rationals"`` (Q, every imaginary part zero). The frame name
decides the verdict: the same coordinates denote different rows in
different frames, so an unnamed frame is ambiguous.

Clauses, decided in this order:

- C1 ``R049_UNNAMED_FRAME``: ``frame`` is null, empty, or names no declared
  frame (the level's negative);
- C2 ``R049_CARRIER``: the carrier tag is unknown, or is ``"rationals"``
  while some entry has a nonzero imaginary part;
- C3 ``R049_FRAME_NOT_SIZE_KEEPING``: a declared frame table U has
  mirror(U)^T U != I, so its columns are not a unit frame;
- C4 ``R049_NOT_UNIT``: the coordinates do not have size exactly 1;
- C5 ``R049_ROW_MISMATCH``: the claimed standard row differs from U times
  the coordinates.
"""

STAGE = 49
ROW_SHA256 = "sha256:335da7ffdf91958db894e8a8dac971585472ed41f3fd08d80db206d372759141"
FIELDS = ("carrier", "coordinates", "frame", "frames", "row")
CLAUSES = (
    ("C1", "R049_UNNAMED_FRAME"),
    ("C2", "R049_CARRIER"),
    ("C3", "R049_FRAME_NOT_SIZE_KEEPING"),
    ("C4", "R049_NOT_UNIT"),
    ("C5", "R049_ROW_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
_I2 = [[["1/1", "0/1"], ["0/1", "0/1"]], [["0/1", "0/1"], ["1/1", "0/1"]]]
OWN_NEGATIVE = {
    "carrier": "mirror_pairs",
    "coordinates": [["3/5", "0/1"], ["0/1", "4/5"]],
    "frame": None,
    "frames": [
        ["b0", _I2],
        ["b1", [[["3/5", "0/1"], ["-4/5", "0/1"]], [["4/5", "0/1"], ["3/5", "0/1"]]]],
    ],
    "row": [["9/25", "-16/25"], ["12/25", "12/25"]],
}
OWN_NEGATIVE_CODE = "R049_UNNAMED_FRAME"
_CARRIERS = ("mirror_pairs", "rationals")


def _pair(value):
    return tuple(_rats(value, 2))


def _mul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def _add(x, y):
    return (x[0] + y[0], x[1] + y[1])


def _conj(x):
    return (x[0], -x[1])


def _table(value):
    return [[_pair(entry) for entry in _seq(row, 2)] for row in _seq(value, 2)]


def _decide(payload):
    frames = {}
    for item in _seq(payload["frames"]):
        _seq(item, 2)
        name = _text(item[0])
        _require(name not in frames, "R_SCHEMA")
        frames[name] = _table(item[1])
    coordinates = [_pair(entry) for entry in _seq(payload["coordinates"], 2)]
    row = [_pair(entry) for entry in _seq(payload["row"], 2)]
    name = payload["frame"]
    _require(name is not None and name != "" and name in frames, "R049_UNNAMED_FRAME")
    carrier = payload["carrier"]
    _require(carrier in _CARRIERS, "R049_CARRIER")
    if carrier == "rationals":
        entries = coordinates + row + [e for t in frames.values() for r in t for e in r]
        _require(all(entry[1] == 0 for entry in entries), "R049_CARRIER")
    zero, one = (Fraction(0), Fraction(0)), (Fraction(1), Fraction(0))
    for table in frames.values():
        for i in range(2):
            for j in range(2):
                total = zero
                for k in range(2):
                    total = _add(total, _mul(_conj(table[k][i]), table[k][j]))
                _require(total == (one if i == j else zero), "R049_FRAME_NOT_SIZE_KEEPING")
    size = sum((a * a + b * b for a, b in coordinates), Fraction(0))
    _require(size == 1, "R049_NOT_UNIT")
    table = frames[name]
    standard = [_add(_mul(table[i][0], coordinates[0]), _mul(table[i][1], coordinates[1])) for i in range(2)]
    _require(standard == row, "R049_ROW_MISMATCH")
