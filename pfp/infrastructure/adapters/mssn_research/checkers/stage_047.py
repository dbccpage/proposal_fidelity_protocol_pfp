"""Target checker of record for MSS-047, row 47 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 47): check addition, multiplication and conjugation of
rational pairs. Negative instance: a complex phase encoded as an untyped
decimal is rejected.

Input (closed): ``{"x": pair, "y": pair, "sum": pair, "product": pair,
"mirror_x": pair, "mirror_y": pair}``. A pair is ``[a, b]`` of canonical
rationals and stands for a + b i over Q(i). ``sum``, ``product``, ``mirror_x``
and ``mirror_y`` are the producer's claims; every one is recomputed here as
tuples of ``Fraction`` and none is trusted.

Declared input class: exact Gaussian rationals, one pair of operands per
payload. The field laws (associativity, distributivity, the conjugation laws)
are not re-proved per payload; they hold for the arithmetic implemented here.

Clauses, each recomputed from the operands:

- C1 ``R047_UNTYPED_DECIMAL``: a scalar written as a decimal or as a complex
  literal string (``"0.5"``, ``"0.5+0.333i"``, ``"1e-3"``) is refused before
  any arithmetic, never converted (the level's negative). A non-canonical
  rational such as ``"2/4"`` is refused ``R_NOT_EXACT``, not reduced;
- C2 ``R047_SUM``: the claimed sum differs from (a + c, b + d);
- C3 ``R047_PRODUCT``: the claimed product differs from (ac - bd, ad + bc);
- C4 ``R047_MIRROR``: a claimed conjugate differs from (a, -b).
"""

STAGE = 47
ROW_SHA256 = "sha256:63c7b3cd75070ccc69f2f3823683037551455bbb4b528eb77e2409f43f8408ef"
FIELDS = ("mirror_x", "mirror_y", "product", "sum", "x", "y")
CLAUSES = (
    ("C1", "R047_UNTYPED_DECIMAL"),
    ("C2", "R047_SUM"),
    ("C3", "R047_PRODUCT"),
    ("C4", "R047_MIRROR"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "mirror_x": ["1/2", "-1/3"],
    "mirror_y": ["-2/1", "-3/4"],
    "product": ["-5/4", "-7/24"],
    "sum": ["-3/2", "13/12"],
    "x": "0.5+0.333i",
    "y": ["-2/1", "3/4"],
}
OWN_NEGATIVE_CODE = "R047_UNTYPED_DECIMAL"
_LITERAL = re.compile(r"[-+0-9.eEij ]*[0-9][-+0-9.eEij ]*")


def _scalar(value):
    if isinstance(value, str) and _RATIONAL.fullmatch(value) is None:
        _require(not (_LITERAL.fullmatch(value) and any(ch in value for ch in ".eEij")), "R047_UNTYPED_DECIMAL")
    return _rat(value)


def _pair(value):
    if isinstance(value, str):
        _require(_LITERAL.fullmatch(value) is None, "R047_UNTYPED_DECIMAL")
        _refuse("R_SCHEMA")
    items = _seq(value, 2)
    return (_scalar(items[0]), _scalar(items[1]))


def _decide(payload):
    x, y = _pair(payload["x"]), _pair(payload["y"])
    claims = {name: _pair(payload[name]) for name in ("sum", "product", "mirror_x", "mirror_y")}
    (a, b), (c, d) = x, y
    _require(claims["sum"] == (a + c, b + d), "R047_SUM")
    _require(claims["product"] == (a * c - b * d, a * d + b * c), "R047_PRODUCT")
    _require(claims["mirror_x"] == (a, -b), "R047_MIRROR")
    _require(claims["mirror_y"] == (c, -d), "R047_MIRROR")
