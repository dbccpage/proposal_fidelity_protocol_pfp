"""Target checker of record for MSS-100, row 100 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 100): check all claimed scope has tests or explicitly typed
unresolved obligations. Negative instance: a release that declares final self
certification is refused.

Input (closed): ``{"claims": [id], "tests": [name], "evidence": [[claim,
test]], "open": [[claim, type, note]], "frontier": [claim],
"self_certification": "none" | "final", "authority_effect": text}``.

Every claim in scope must be covered: either some evidence row links it to a
declared test, or an open row types it as an unresolved obligation. The types
are closed: ``OPEN``, ``CONJECTURE``, ``BLOCKED`` and ``OUT_OF_SCOPE``. The
frontier is recomputed as the claims with no test, and the release's declared
frontier must equal it, so a release cannot declare itself complete while an
obligation is open. A release may not certify itself: it must say
``self_certification: none`` and carry ``authority_effect: None``.

Declared input class: finite release manifests. Whether a named test actually
tests its claim is not decided here; the manifest's links are checked for
resolution and coverage only.

Clauses, decided in this order:

- C1 ``R100_SELF_CERTIFICATION``: the release declares final self
  certification or any authority effect (the level's negative);
- C2 ``R100_UNCOVERED_CLAIM``: a claim has neither a test nor an open
  obligation;
- C3 ``R100_UNTYPED_OBLIGATION``: an open obligation's type is not one of the
  declared types;
- C4 ``R100_DANGLING_REFERENCE``: an evidence or open row names a claim not in
  scope or a test not declared;
- C5 ``R100_FRONTIER_MISMATCH``: the declared frontier is not the recomputed
  one.
"""

STAGE = 100
ROW_SHA256 = "sha256:daef995a27090e2d3a40ae1893e53569a4f286962021a4de869b4335dc95576d"
FIELDS = ("authority_effect", "claims", "evidence", "frontier", "open", "self_certification", "tests")
CLAUSES = (
    ("C1", "R100_SELF_CERTIFICATION"),
    ("C2", "R100_UNCOVERED_CLAIM"),
    ("C3", "R100_UNTYPED_OBLIGATION"),
    ("C4", "R100_DANGLING_REFERENCE"),
    ("C5", "R100_FRONTIER_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OBLIGATION_TYPES = ("BLOCKED", "CONJECTURE", "OPEN", "OUT_OF_SCOPE")
OWN_NEGATIVE = {
    "authority_effect": "None",
    "claims": ["c1", "c2"],
    "evidence": [["c1", "t_a"], ["c2", "t_b"]],
    "frontier": [],
    "open": [],
    "self_certification": "final",
    "tests": ["t_a", "t_b"],
}
OWN_NEGATIVE_CODE = "R100_SELF_CERTIFICATION"


def _names(value):
    out = [_text(item) for item in _seq(value)]
    _require(len(set(out)) == len(out), "R_SCHEMA")
    return out


def _decide(payload):
    claims = _names(payload["claims"])
    tests = set(_names(payload["tests"]))
    _require(claims, "R_SCHEMA")
    evidence = []
    for row in _seq(payload["evidence"]):
        _seq(row, 2)
        evidence.append((_text(row[0]), _text(row[1])))
    obligations = []
    for row in _seq(payload["open"]):
        _seq(row, 3)
        obligations.append((_text(row[0]), _text(row[1]), _text(row[2])))
    frontier = _names(payload["frontier"])
    _require(payload["self_certification"] in ("none", "final"), "R_SCHEMA")
    authority = _text(payload["authority_effect"])
    _require(payload["self_certification"] == "none" and authority == "None", "R100_SELF_CERTIFICATION")
    tested = {claim for claim, _ in evidence}
    held_open = {claim for claim, _, _ in obligations}
    _require(all(claim in tested or claim in held_open for claim in claims), "R100_UNCOVERED_CLAIM")
    _require(all(kind in OBLIGATION_TYPES for _, kind, _ in obligations), "R100_UNTYPED_OBLIGATION")
    scope = set(claims)
    _require(all(claim in scope and test in tests for claim, test in evidence), "R100_DANGLING_REFERENCE")
    _require(held_open <= scope, "R100_DANGLING_REFERENCE")
    recomputed = {claim for claim in claims if claim not in tested}
    _require(set(frontier) == recomputed, "R100_FRONTIER_MISMATCH")
