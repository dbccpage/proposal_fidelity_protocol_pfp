"""Target checker of record for MSS-048, row 48 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 48): check declared basis and exact unit norm. Negative
instance: a nonunit vector cannot claim normalized state.

Input (closed): ``{"frame": [slot], "row": [pair]}``. ``frame`` is the
declared ordered basis, one distinct nonempty slot name per entry of ``row``.
Each entry of ``row`` is a pair ``[a, b]`` of canonical rationals standing for
a + b i. The payload claims that ``row`` is a unit row in ``frame``.

Declared input class: finite rows over Q(i) in a declared finite frame. The
size is the sesquilinear sum of mirror(v_k) * v_k = a_k^2 + b_k^2, computed
exactly; a bilinear sum of v_k^2 is not used (over Q(i) it is not positive:
(1, i) has bilinear square 0).

Clauses:

- C1 ``R048_FRAME``: the frame is empty, repeats a slot, or does not index
  the row one slot per entry;
- C2 ``R048_NOT_UNIT``: the recomputed size is not exactly 1 (the level's
  negative: w = (1, i) has size 2).
"""

STAGE = 48
ROW_SHA256 = "sha256:7b38beebd2f83a5894e26b8b0f5fa3704359ccd9f97d8a939c7e5d5938671a1d"
FIELDS = ("frame", "row")
CLAUSES = (
    ("C1", "R048_FRAME"),
    ("C2", "R048_NOT_UNIT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"frame": ["e0", "e1"], "row": [["1/1", "0/1"], ["0/1", "1/1"]]}
OWN_NEGATIVE_CODE = "R048_NOT_UNIT"


def _decide(payload):
    frame = [_text(slot) for slot in _seq(payload["frame"])]
    row = [tuple(_rats(entry, 2)) for entry in _seq(payload["row"])]
    _require(row, "R_SCHEMA")
    _require(frame and len(set(frame)) == len(frame) and len(frame) == len(row), "R048_FRAME")
    size = sum((a * a + b * b for a, b in row), Fraction(0))
    _require(size == 1, "R048_NOT_UNIT")
