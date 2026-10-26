"""Target checker of record for MSS-000, row 0 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 0): accept precisely the two bytes ``<>`` at this stage.
Negative instance: any interior glyph or nested packet is rejected.

Input (closed): ``{"packet": str}``, the stage-0 byte string.

Clauses, each decided on the recomputed bytes, never on a declared label:

- C1 ``R000_INTERIOR_GLYPH``: a frame ``<...>`` whose interior is a glyph;
- C2 ``R000_NESTED_PACKET``: a frame whose interior holds a bracket;
- C3 ``R000_NOT_A_FRAME``: bytes that are not a ``<...>`` frame at all.

Declared class: ASCII strings. The payload carries no list, so the receiving
side's ``lists_emptied`` probe equals the positive and is inapplicable.
"""

STAGE = 0
ROW_SHA256 = "sha256:faf300495fff35197561ac2fe03d01cb6ce1997f353b228f19e75e0e2306b2bc"
FIELDS = ("packet",)
CLAUSES = (
    ("C1", "R000_INTERIOR_GLYPH"),
    ("C2", "R000_NESTED_PACKET"),
    ("C3", "R000_NOT_A_FRAME"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"packet": "<a>"}
OWN_NEGATIVE_CODE = "R000_INTERIOR_GLYPH"


def _decide(payload):
    packet = payload["packet"]
    _require(isinstance(packet, str), "R_SCHEMA")
    if packet == "<>":
        return
    _require(len(packet) >= 2 and packet[0] == "<" and packet[-1] == ">", "R000_NOT_A_FRAME")
    interior = packet[1:-1]
    _require("<" not in interior and ">" not in interior, "R000_NESTED_PACKET")
    _refuse("R000_INTERIOR_GLYPH")
