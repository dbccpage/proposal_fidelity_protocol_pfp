"""Target checker of record for MSS-045, row 45 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 45): recheck all steps against hashed axioms and inference
rules. Negative instance: a self-reported proof check is not host
certification.

Input (closed): ``{"axioms": [formula], "axiom_digest": "sha256:<hex>",
"proof": [[formula, justification]], "conclusion": formula}``. A formula is
an atom (a string) or ``["->", formula, formula]``. A justification is
``["axiom", k]`` (the k-th bound axiom) or ``["mp", i, j]`` (from line i, A,
and line j, A -> B, conclude B). ``axiom_digest`` binds the axiom list: the
SHA-256 of its canonical JSON (sorted keys, no whitespace, ASCII).

Declared input class: implicational propositional proofs with the axiom and
detachment rules only. The rule table is the checker's own; a producer
cannot extend it, and a producer's own report of having checked the proof is
not a rule.

Clauses, each recomputed:

- C1 ``R045_UNBOUND_AXIOMS``: the axiom list does not hash to the bound
  digest;
- C2 ``R045_UNKNOWN_RULE``: a line is justified by anything other than the
  two rules, such as a self-report (the level's negative);
- C3 ``R045_FORWARD_REFERENCE``: a detachment cites a line that is not
  strictly earlier;
- C4 ``R045_STEP_MISMATCH``: a line's formula is not what its justification
  yields;
- C5 ``R045_CONCLUSION_MISMATCH``: the declared conclusion is not the last
  line.
"""

import hashlib
import json

STAGE = 45
ROW_SHA256 = "sha256:15f0d8b7bd6530b04d0c2ef9a502aa7862c53b3373c901ad53828439e32a0c66"
FIELDS = ("axiom_digest", "axioms", "conclusion", "proof")
CLAUSES = (
    ("C1", "R045_UNBOUND_AXIOMS"),
    ("C2", "R045_UNKNOWN_RULE"),
    ("C3", "R045_FORWARD_REFERENCE"),
    ("C4", "R045_STEP_MISMATCH"),
    ("C5", "R045_CONCLUSION_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
_AXIOMS = ["P", ["->", "P", "Q"]]


def _digest(value):
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(text.encode("ascii")).hexdigest()


OWN_NEGATIVE = {
    "axiom_digest": _digest(_AXIOMS),
    "axioms": _AXIOMS,
    "conclusion": "Q",
    "proof": [["P", ["axiom", 0]], ["Q", ["self-reported"]]],
}
OWN_NEGATIVE_CODE = "R045_UNKNOWN_RULE"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


def _formula(value):
    if isinstance(value, str):
        return _text(value)
    node = _seq(value, 3)
    _require(node[0] == "->", "R_SCHEMA")
    return ("->", _formula(node[1]), _formula(node[2]))


def _decide(payload):
    axioms = [_formula(a) for a in _seq(payload["axioms"])]
    bound = payload["axiom_digest"]
    _require(isinstance(bound, str) and _DIGEST.fullmatch(bound) is not None, "R_SCHEMA")
    _require(_digest(payload["axioms"]) == bound, "R045_UNBOUND_AXIOMS")
    lines = []
    for entry in _seq(payload["proof"]):
        _seq(entry, 2)
        formula = _formula(entry[0])
        rule = _seq(entry[1])
        _require(rule and rule[0] in ("axiom", "mp"), "R045_UNKNOWN_RULE")
        if rule[0] == "axiom":
            _seq(rule, 2)
            k = _nat(rule[1])
            _require(k < len(axioms), "R_SCHEMA")
            _require(axioms[k] == formula, "R045_STEP_MISMATCH")
        else:
            _seq(rule, 3)
            i, j = _nat(rule[1]), _nat(rule[2])
            _require(i < len(lines) and j < len(lines), "R045_FORWARD_REFERENCE")
            _require(lines[j] == ("->", lines[i], formula), "R045_STEP_MISMATCH")
        lines.append(formula)
    _require(lines, "R_SCHEMA")
    _require(_formula(payload["conclusion"]) == lines[-1], "R045_CONCLUSION_MISMATCH")
