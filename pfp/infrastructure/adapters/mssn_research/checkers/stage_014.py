"""Target checker of record for MSS-014, row 14 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 14): enumerate finite domains and recompute mask from formula
tree. Negative instance: an unbounded quantifier with a finite step budget is
rejected.

Input (closed): ``{"formula": tree, "mask": [str], "budget": nat, "value":
"true" | "false"}``. A tree is a list:

- ``["forall" | "exists", variable, bound, body]``: the variable ranges over
  0 .. bound - 1; a bound of ``"nat"`` is unbounded;
- ``["eq" | "neq" | "lt", term, term]``: a term is a bound variable or a nat;
- ``["not", tree]``, ``["and" | "or", tree, tree]``.

The mask is the list of quantifier kinds in preorder, recomputed from the
tree. The step count is the number of atom evaluations under full
enumeration, recomputed; the value is recomputed by enumeration.

Clauses:

- C1 ``R014_UNBOUNDED``: a quantifier is unbounded (refused before any
  evaluation; a budget never turns it into a value);
- C2 ``R014_MASK_MISMATCH``: the declared mask is not the recomputed one;
- C3 ``R014_BUDGET_EXCEEDED``: full enumeration needs more steps than the
  budget (a typed budget stop, never a truth value);
- C4 ``R014_VALUE_MISMATCH``: the declared value is not the enumerated one.
"""

STAGE = 14
ROW_SHA256 = "sha256:50a29aa79a3e25896e8f98c5730b2b9c23ae534d1bc021c41be1dc5800a95607"
FIELDS = ("budget", "formula", "mask", "value")
CLAUSES = (
    ("C1", "R014_UNBOUNDED"),
    ("C2", "R014_MASK_MISMATCH"),
    ("C3", "R014_BUDGET_EXCEEDED"),
    ("C4", "R014_VALUE_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"budget": 10, "formula": ["forall", "x", "nat", ["eq", "x", "x"]], "mask": ["forall"], "value": "true"}
OWN_NEGATIVE_CODE = "R014_UNBOUNDED"
QUANTIFIERS = ("exists", "forall")
ATOMS = ("eq", "lt", "neq")
MAX_STEPS = 100000


def _scan(tree, bound, mask):
    """Check the tree's shape and scope; return its step count."""
    _require(isinstance(tree, list) and tree and isinstance(tree[0], str), "R_SCHEMA")
    head = tree[0]
    if head in QUANTIFIERS:
        _seq(tree, 4)
        variable, limit = _text(tree[1]), tree[2]
        _require(variable not in bound, "R_SCHEMA")
        _require(limit != "nat", "R014_UNBOUNDED")
        size = _nat(limit)
        mask.append(head)
        return size * _scan(tree[3], bound + (variable,), mask)
    if head in ATOMS:
        _seq(tree, 3)
        for term in tree[1:]:
            _require(isinstance(term, str) and term in bound or _nat(term) >= 0, "R_SCHEMA")
        return 1
    if head == "not":
        _seq(tree, 2)
        return _scan(tree[1], bound, mask)
    _require(head in ("and", "or"), "R_SCHEMA")
    _seq(tree, 3)
    return _scan(tree[1], bound, mask) + _scan(tree[2], bound, mask)


def _eval(tree, env):
    head = tree[0]
    if head in QUANTIFIERS:
        results = [_eval(tree[3], {**env, tree[1]: value}) for value in range(tree[2])]
        return all(results) if head == "forall" else any(results)
    if head in ATOMS:
        left, right = (env[t] if isinstance(t, str) else t for t in tree[1:])
        return {"eq": left == right, "lt": left < right, "neq": left != right}[head]
    if head == "not":
        return not _eval(tree[1], env)
    left, right = _eval(tree[1], env), _eval(tree[2], env)
    return (left and right) if head == "and" else (left or right)


def _decide(payload):
    mask = []
    steps = _scan(payload["formula"], (), mask)
    declared = _seq(payload["mask"])
    _require(declared == mask, "R014_MASK_MISMATCH")
    _require(steps <= MAX_STEPS, "R_SCHEMA")
    _require(steps <= _nat(payload["budget"]), "R014_BUDGET_EXCEEDED")
    _require(payload["value"] in ("false", "true"), "R_SCHEMA")
    value = "true" if _eval(payload["formula"], {}) else "false"
    _require(payload["value"] == value, "R014_VALUE_MISMATCH")
