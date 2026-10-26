"""Target checker of record for MSS-026, row 26 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 26): check matching input colors and operadic unit and
associativity. Negative instance: substituting a binary output into a
mismatched color is rejected.

Input (closed): ``{"colours": [name], "bound": nat, "operations": [[name,
[colour], colour]], "units": [[colour, operation]], "substitutions": [[outer,
slot, inner, result]]}``. An operation has one or more input colours (its
slots, numbered from 0) and one output colour. A substitution row declares
outer composed with inner at the slot, the partial composition, as the named
result.

Declared input class: finite coloured operads truncated at a declared arity
bound, with no nullary operations. Every composite of arity at most the bound
must be in the table; the laws are decided on every instance inside the
truncation and on nothing beyond it.

Clauses, each recomputed from the table:

- C1 ``R026_KIND_MISMATCH``: a row substitutes an inner output into a slot of
  another colour (the level's negative), or names a result whose colours are
  not the composite's;
- C2 ``R026_TABLE_GAP``: a well-coloured substitution inside the truncation
  has no row;
- C3 ``R026_UNIT_LAW``: substituting an operation into a unit, or a unit into
  a slot, does not return the operation;
- C4 ``R026_BRACKETING``: sequential or parallel associativity fails on some
  composable triple inside the truncation.
"""

STAGE = 26
ROW_SHA256 = "sha256:315a03522d7fd23a4321d9dd8a1a0c700377b353dc7c27b92e83db2e41a052d5"
FIELDS = ("bound", "colours", "operations", "substitutions", "units")
CLAUSES = (
    ("C1", "R026_KIND_MISMATCH"),
    ("C2", "R026_TABLE_GAP"),
    ("C3", "R026_UNIT_LAW"),
    ("C4", "R026_BRACKETING"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "bound": 2,
    "colours": ["A", "B"],
    "operations": [["eA", ["A"], "A"], ["eB", ["B"], "B"], ["m", ["A", "A"], "A"], ["q", ["A", "A"], "B"]],
    "substitutions": [["m", 0, "q", "m"]],
    "units": [["A", "eA"], ["B", "eB"]],
}
OWN_NEGATIVE_CODE = "R026_KIND_MISMATCH"


def _decide(payload):
    colours = [_text(c) for c in _seq(payload["colours"])]
    _require(len(set(colours)) == len(colours), "R_SCHEMA")
    bound = _nat(payload["bound"])
    ops = {}
    for entry in _seq(payload["operations"]):
        _seq(entry, 3)
        name = _text(entry[0])
        inputs = tuple(_text(c) for c in _seq(entry[1]))
        output = _text(entry[2])
        _require(name not in ops and 1 <= len(inputs) <= bound, "R_SCHEMA")
        _require(set(inputs) <= set(colours) and output in colours, "R_SCHEMA")
        ops[name] = (inputs, output)
    units = {}
    for entry in _seq(payload["units"]):
        _seq(entry, 2)
        colour, name = _text(entry[0]), _text(entry[1])
        _require(colour in colours and colour not in units and ops.get(name) == ((colour,), colour), "R_SCHEMA")
        units[colour] = name
    _require(set(units) == set(colours), "R_SCHEMA")
    comp = {}
    for entry in _seq(payload["substitutions"]):
        _seq(entry, 4)
        outer, slot, inner, result = _text(entry[0]), _nat(entry[1]), _text(entry[2]), _text(entry[3])
        _require(outer in ops and inner in ops and result in ops, "R_SCHEMA")
        o_in, o_out = ops[outer]
        i_in, i_out = ops[inner]
        _require(slot < len(o_in) and (outer, slot, inner) not in comp, "R_SCHEMA")
        _require(o_in[slot] == i_out, "R026_KIND_MISMATCH")
        _require(ops[result] == (o_in[:slot] + i_in + o_in[slot + 1:], o_out), "R026_KIND_MISMATCH")
        comp[(outer, slot, inner)] = result
    for outer, (o_in, _) in ops.items():
        for slot, colour in enumerate(o_in):
            for inner, (i_in, i_out) in ops.items():
                if i_out == colour and len(o_in) + len(i_in) - 1 <= bound:
                    _require((outer, slot, inner) in comp, "R026_TABLE_GAP")
    for name, (inputs, output) in ops.items():
        _require(comp[(units[output], 0, name)] == name, "R026_UNIT_LAW")
        for slot, colour in enumerate(inputs):
            _require(comp[(name, slot, units[colour])] == name, "R026_UNIT_LAW")
    for (outer, i, inner), first in comp.items():
        arity = len(ops[inner][0])
        for k, colour in enumerate(ops[first][0]):
            for other, (x_in, x_out) in ops.items():
                if x_out != colour or (first, k, other) not in comp:
                    continue
                left = comp[(first, k, other)]
                if i <= k < i + arity:
                    right = comp[(outer, i, comp[(inner, k - i, other)])]
                elif k < i:
                    right = comp[(comp[(outer, k, other)], i + len(x_in) - 1, inner)]
                else:
                    right = comp[(comp[(outer, k - arity + 1, other)], i, inner)]
                _require(left == right, "R026_BRACKETING")
