"""Target checker of record for MSS-075, row 75 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 75): check patched view equals recomputed view on fixture.
Negative instance: a nonempty deletion omitted from delta is rejected.

Input (closed): ``{"width": w, "base": [row], "new_base": [row], "delta":
{"inserted": [row], "deleted": [row]}, "view": {"column": i, "value": v},
"old_view": [row], "patched_view": [row]}``. A row is a list of w strings;
a table is a set of rows. The view selects the rows whose column i holds v.

The checker recomputes the view on the old table, the true difference between
the two tables, and the view on the new table. The patched view is compared
with the recomputed view, never with the producer's patch arithmetic.

Declared input class: one table of fixed width, set semantics, a selection
view on one column; no projection, joins or multiplicities.

Clauses, decided in this order:

- C1 ``R075_OLD_VIEW``: the old view is not the view of the old table;
- C2 ``R075_DELTA_NOT_APPLICABLE``: a deleted row is not in the old table, or
  an inserted row already is, or a row is both inserted and deleted;
- C3 ``R075_DELETION_OMITTED``: a row removed between the two tables is
  missing from the deletions (the level's negative);
- C4 ``R075_DELTA_MISMATCH``: the old table patched by the delta is not the
  new table (a spurious deletion, or an omitted or spurious insertion);
- C5 ``R075_STALE_VIEW``: the patched view is not the view recomputed on the
  new table.
"""

STAGE = 75
ROW_SHA256 = "sha256:9db8477da65ceff1d87f91dc2482e6d9527ac03c3bb9176d6aa07d4d2657381d"
FIELDS = ("base", "delta", "new_base", "old_view", "patched_view", "view", "width")
CLAUSES = (
    ("C1", "R075_OLD_VIEW"),
    ("C2", "R075_DELTA_NOT_APPLICABLE"),
    ("C3", "R075_DELETION_OMITTED"),
    ("C4", "R075_DELTA_MISMATCH"),
    ("C5", "R075_STALE_VIEW"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "base": [["a", "1"], ["b", "1"], ["c", "2"]],
    "delta": {"deleted": [], "inserted": [["d", "1"]]},
    "new_base": [["a", "1"], ["c", "2"], ["d", "1"]],
    "old_view": [["a", "1"], ["b", "1"]],
    "patched_view": [["a", "1"], ["b", "1"], ["d", "1"]],
    "view": {"column": 1, "value": "1"},
    "width": 2,
}
OWN_NEGATIVE_CODE = "R075_DELETION_OMITTED"


def _table(value, width):
    rows = []
    for row in _seq(value):
        _seq(row, width)
        rows.append(tuple(_text(cell) for cell in row))
    _require(len(set(rows)) == len(rows), "R_SCHEMA")
    return set(rows)


def _decide(payload):
    width = _nat(payload["width"])
    _require(width >= 1, "R_SCHEMA")
    base = _table(payload["base"], width)
    new = _table(payload["new_base"], width)
    delta = payload["delta"]
    _require(isinstance(delta, dict) and set(delta) == {"deleted", "inserted"}, "R_SCHEMA")
    inserted = _table(delta["inserted"], width)
    deleted = _table(delta["deleted"], width)
    view = payload["view"]
    _require(isinstance(view, dict) and set(view) == {"column", "value"}, "R_SCHEMA")
    column = _nat(view["column"])
    _require(column < width, "R_SCHEMA")
    value = _text(view["value"])
    old_view = _table(payload["old_view"], width)
    patched = _table(payload["patched_view"], width)

    def select(rows):
        return {row for row in rows if row[column] == value}

    _require(old_view == select(base), "R075_OLD_VIEW")
    _require(deleted <= base and not (inserted & base) and not (inserted & deleted), "R075_DELTA_NOT_APPLICABLE")
    _require(base - new <= deleted, "R075_DELETION_OMITTED")
    _require((base - deleted) | inserted == new, "R075_DELTA_MISMATCH")
    _require(patched == select(new), "R075_STALE_VIEW")
