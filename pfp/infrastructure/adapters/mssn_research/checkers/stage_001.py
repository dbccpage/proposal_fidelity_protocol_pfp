"""Target checker of record for MSS-001, row 1 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 1): reparse the source ``<>`` and preserve it under the first
lift. Negative instance: a lift omitting the source is rejected.

Input (closed): ``{"source": str, "lift": str}``. ``lift`` is a wire string
``op<`` item... ``>``, each item ``<`` binary digits ``>``; the first item is
the opcode and the rest are operands.

Clauses, decided by reparsing ``lift``:

- C1 ``R001_SOURCE_OMITTED``: no operand is the source ``<>``;
- C2 ``R001_SOURCE_DISPLACED``: the source is present but is not the first
  operand exactly once, so the down map (first operand) does not return it;
- C3 ``R001_GENERATORS``: the operands after the source are not exactly the
  two generators ``<0>``, ``<1>`` in that order;
- C4 ``R001_UNPARSED_LIFT``: ``lift`` is not in the wire grammar;
- C5 ``R001_SOURCE_NOT_PRIMITIVE``: the declared source is not ``<>``.

The down map is ``d(lift) = first operand``; ``d(u(<>)) = <>`` is checked on the
reparsed operands, never read from a field. No list in the payload, so the
``lists_emptied`` probe is inapplicable.
"""

STAGE = 1
ROW_SHA256 = "sha256:e711c29b276d5fc4ca031acdd7dd8d6bfbf379d22177adbfbf2d10c078b3ab98"
FIELDS = ("lift", "source")
CLAUSES = (
    ("C1", "R001_SOURCE_OMITTED"),
    ("C2", "R001_SOURCE_DISPLACED"),
    ("C3", "R001_GENERATORS"),
    ("C4", "R001_UNPARSED_LIFT"),
    ("C5", "R001_SOURCE_NOT_PRIMITIVE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"lift": "op<<0><0><1>>", "source": "<>"}
OWN_NEGATIVE_CODE = "R001_SOURCE_OMITTED"

_LIFT = re.compile(r"op<((?:<[01]*>)+)>")
_ITEM = re.compile(r"<([01]*)>")


def _decide(payload):
    source, lift = payload["source"], payload["lift"]
    _require(isinstance(source, str) and isinstance(lift, str), "R_SCHEMA")
    _require(source == "<>", "R001_SOURCE_NOT_PRIMITIVE")
    match = _LIFT.fullmatch(lift)
    _require(match is not None, "R001_UNPARSED_LIFT")
    items = ["<" + body + ">" for body in _ITEM.findall(match.group(1))]
    opcode, operands = items[0], items[1:]
    _require(opcode != "<>", "R001_UNPARSED_LIFT")
    _require(source in operands, "R001_SOURCE_OMITTED")
    _require(operands[0] == source and operands.count(source) == 1, "R001_SOURCE_DISPLACED")
    _require(operands[1:] == ["<0>", "<1>"], "R001_GENERATORS")
