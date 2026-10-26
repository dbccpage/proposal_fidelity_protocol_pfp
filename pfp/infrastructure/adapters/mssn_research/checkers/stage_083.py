"""Target checker of record for MSS-083, row 83 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 83): check every derived value points to immutable inputs.
Negative instance: a missing source breaks provenance.

Input (closed): ``{"sources": [[id, value, digest]], "derived": [[id, op,
[[input, pinned_digest]], value, digest]]}``. Values are canonical rationals;
op is ``sum`` or ``product``. A record's digest is the SHA-256 of the
canonical JSON of ``{"id", "value"}``.

Each derived value names its inputs by id *and* by the digest the input had
when it was used, so an input is immutable exactly when its current record
still hashes to that pin. An input must be a source or a derived value listed
earlier. The checker recomputes every value from its inputs, every record
digest from its content, and compares every pin.

Declared input class: finite lineage graphs over exact rational values with
the two declared operations; lineage by listed order (no cycles can be
expressed).

Clauses, decided in this order:

- C1 ``R083_MISSING_SOURCE``: an input names no source and no earlier derived
  value (the level's negative);
- C2 ``R083_VALUE``: a derived value is not its operation applied to its
  inputs;
- C3 ``R083_RECORD_DIGEST``: a record's digest does not hash its content;
- C4 ``R083_INPUT_CHANGED``: an input's pinned digest is not the input's
  digest (the input was mutated after use).
"""

import hashlib
import json

STAGE = 83
ROW_SHA256 = "sha256:cec44692edd0aca47d0369a778343b0f63ce7daabb344cce35894c0245fabefa"
FIELDS = ("derived", "sources")
CLAUSES = (
    ("C1", "R083_MISSING_SOURCE"),
    ("C2", "R083_VALUE"),
    ("C3", "R083_RECORD_DIGEST"),
    ("C4", "R083_INPUT_CHANGED"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()


def record_digest(name, value):
    text = json.dumps({"id": name, "value": value}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(text.encode("ascii")).hexdigest()


OWN_NEGATIVE = {
    "derived": [["v1", "sum", [["s1", record_digest("s1", "3/1")], ["s3", record_digest("s3", "4/1")]], "7/1",
                 record_digest("v1", "7/1")]],
    "sources": [["s1", "3/1", record_digest("s1", "3/1")]],
}
OWN_NEGATIVE_CODE = "R083_MISSING_SOURCE"


def _decide(payload):
    sources = []
    for source in _seq(payload["sources"]):
        _seq(source, 3)
        sources.append((_text(source[0]), source[1], _text(source[2])))
        _rat(source[1])
    derived = []
    for item in _seq(payload["derived"]):
        _seq(item, 5)
        _require(item[1] in ("sum", "product"), "R_SCHEMA")
        inputs = []
        for pair in _seq(item[2]):
            _seq(pair, 2)
            inputs.append((_text(pair[0]), _text(pair[1])))
        _require(inputs, "R_SCHEMA")
        _rat(item[3])
        derived.append((_text(item[0]), item[1], inputs, item[3], _text(item[4])))
    names = [s[0] for s in sources] + [d[0] for d in derived]
    _require(derived and len(set(names)) == len(names), "R_SCHEMA")
    known = {name for name, _, _ in sources}
    for name, _, inputs, _, _ in derived:
        _require(all(source in known for source, _ in inputs), "R083_MISSING_SOURCE")
        known.add(name)
    records = {name: (value, digest) for name, value, digest in sources}
    records.update({name: (value, digest) for name, _, _, value, digest in derived})
    for name, op, inputs, value, _ in derived:
        operands = [_rat(records[source][0]) for source, _ in inputs]
        result = Fraction(0) if op == "sum" else Fraction(1)
        for operand in operands:
            result = result + operand if op == "sum" else result * operand
        _require(_rat(value) == result, "R083_VALUE")
    for name, (value, digest) in records.items():
        _require(digest == record_digest(name, value), "R083_RECORD_DIGEST")
    for _, _, inputs, _, _ in derived:
        for source, pinned in inputs:
            _require(pinned == records[source][1], "R083_INPUT_CHANGED")
