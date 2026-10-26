"""Target checker of record for MSS-032, row 32 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 32): check explicit scale map and record lost distinctions.
Negative instance: coarse map silently erasing a protected defect is
rejected.

Input (closed): ``{"fine": [name], "coarse": [name], "block_map": [[fine,
coarse]], "protected": [[fine, fine]], "ledger": [[fine, fine]],
"erasures": [[fine, fine]]}``. Pairs are unordered and written in the order
of ``fine``. The ledger records every distinction the block map loses; an
erasure record is the explicit permission to lose a protected distinction.

Declared input class: distinctions are pairs of points of a finite fine
carrier. A defect carried by a class (a cycle value or a torsion order) is
not decided here.

Clauses, each recomputed from the block map, never read from a declared flag:

- C1 ``R032_NOT_A_MAP``: the block map is not a total function from the fine
  carrier onto the coarse carrier;
- C2 ``R032_LEDGER_INCOMPLETE``: a merged pair is not in the ledger;
- C3 ``R032_LEDGER_PADDED``: a ledger pair or erasure record is not a merged
  pair;
- C4 ``R032_SILENT_PROTECTED_MERGE``: a protected pair is merged without an
  erasure record (the level's negative).
"""

STAGE = 32
ROW_SHA256 = "sha256:bf94cffc4989ab0a1af25798ca83f451bd15cfa3504c2ae39535c373bd2b2d4f"
FIELDS = ("block_map", "coarse", "erasures", "fine", "ledger", "protected")
CLAUSES = (
    ("C1", "R032_NOT_A_MAP"),
    ("C2", "R032_LEDGER_INCOMPLETE"),
    ("C3", "R032_LEDGER_PADDED"),
    ("C4", "R032_SILENT_PROTECTED_MERGE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ("block_map",)
OWN_NEGATIVE = {
    "block_map": [["0", "a"], ["1", "a"], ["2", "b"]],
    "coarse": ["a", "b"],
    "erasures": [],
    "fine": ["0", "1", "2"],
    "ledger": [],
    "protected": [["0", "1"]],
}
OWN_NEGATIVE_CODE = "R032_SILENT_PROTECTED_MERGE"


def _pairs(rows, rank):
    out = []
    for row in _seq(rows):
        _seq(row, 2)
        x, y = _text(row[0]), _text(row[1])
        _require(x in rank and y in rank and rank[x] < rank[y] and (x, y) not in out, "R_SCHEMA")
        out.append((x, y))
    return set(out)


def _decide(payload):
    fine = [_text(x) for x in _seq(payload["fine"])]
    coarse = [_text(x) for x in _seq(payload["coarse"])]
    _require(len(set(fine)) == len(fine) and len(set(coarse)) == len(coarse), "R_SCHEMA")
    rank = {x: i for i, x in enumerate(fine)}
    block = {}
    for row in _seq(payload["block_map"]):
        _seq(row, 2)
        x, b = _text(row[0]), _text(row[1])
        _require(x in rank and x not in block and b in coarse, "R032_NOT_A_MAP")
        block[x] = b
    _require(set(block) == set(fine) and set(block.values()) == set(coarse), "R032_NOT_A_MAP")
    protected = _pairs(payload["protected"], rank)
    ledger = _pairs(payload["ledger"], rank)
    erasures = _pairs(payload["erasures"], rank)
    merged = {(x, y) for x in fine for y in fine if rank[x] < rank[y] and block[x] == block[y]}
    for pair in protected & merged:
        _require(pair in erasures, "R032_SILENT_PROTECTED_MERGE")
    _require(merged <= ledger, "R032_LEDGER_INCOMPLETE")
    _require(ledger <= merged and erasures <= merged, "R032_LEDGER_PADDED")
