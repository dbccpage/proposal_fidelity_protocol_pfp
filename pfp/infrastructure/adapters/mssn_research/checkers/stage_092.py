"""Target checker of record for MSS-092, row 92 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 92): replay proof object in independent kernel. Negative
instance: a solver success flag with no proof is rejected.

Input (closed): ``{"claims": [{"cnf": [[literal]], "answer": "UNSAT" |
"SAT", "proof": [step] | null, "model": [literal] | null}]}``. A literal is a
variable name, or ``~`` and a variable name. A proof step is ``{"from": [i,
j], "pivot": v, "clause": [literal]}``: it resolves clause i with clause j on
variable v, where clauses are numbered from 0 through the CNF and then through
the steps already taken.

The kernel is this file: a resolution checker, independent of whatever solver
produced the claim. An UNSAT answer is accepted only with a proof object the
kernel replays step by step, recomputing every resolvent and ending in the
empty clause. A SAT answer is accepted only with a consistent model that
satisfies every clause. An answer with neither object is a bare success flag.

Declared input class: propositional CNF, resolution refutations and total or
partial models. No Lean term is rebuilt here, and no axiom report is read:
that is K11 of the reach checker, over the carrier's pinned report.

Clauses, decided in this order:

- C1 ``R092_FLAG_WITHOUT_PROOF``: an answer carries no proof object (UNSAT
  with no steps, SAT with no model) (the level's negative);
- C2 ``R092_BAD_STEP``: a step cites a clause not yet available, or a pivot
  that does not occur positively in one clause and negatively in the other;
- C3 ``R092_RESOLVENT_MISMATCH``: a step's clause is not the resolvent;
- C4 ``R092_NOT_REFUTATION``: the last clause derived is not empty;
- C5 ``R092_MODEL_FAILS``: a model assigns a variable both ways, or leaves a
  clause unsatisfied.
"""

STAGE = 92
ROW_SHA256 = "sha256:755d393947de2144415674e4e1c5e42c3ac211cbe2d386f39043083814b69e5b"
FIELDS = ("claims",)
CLAUSES = (
    ("C1", "R092_FLAG_WITHOUT_PROOF"),
    ("C2", "R092_BAD_STEP"),
    ("C3", "R092_RESOLVENT_MISMATCH"),
    ("C4", "R092_NOT_REFUTATION"),
    ("C5", "R092_MODEL_FAILS"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"claims": [{"answer": "UNSAT", "cnf": [["p"], ["~p"]], "model": None, "proof": None}]}
OWN_NEGATIVE_CODE = "R092_FLAG_WITHOUT_PROOF"
_LITERAL = re.compile(r"~?[a-z][a-z0-9_]*")


def _literal(value):
    _require(isinstance(value, str) and _LITERAL.fullmatch(value) is not None, "R_SCHEMA")
    return (value.lstrip("~"), not value.startswith("~"))


def _clause(value):
    return frozenset(_literal(item) for item in _seq(value))


def _claim(claim):
    _require(isinstance(claim, dict) and set(claim) == {"answer", "cnf", "model", "proof"}, "R_SCHEMA")
    _require(claim["answer"] in ("SAT", "UNSAT"), "R_SCHEMA")
    cnf = [_clause(c) for c in _seq(claim["cnf"])]
    _require(cnf, "R_SCHEMA")
    steps = None
    if claim["proof"] is not None:
        steps = []
        for step in _seq(claim["proof"]):
            _require(isinstance(step, dict) and set(step) == {"clause", "from", "pivot"}, "R_SCHEMA")
            origin = _seq(step["from"], 2)
            steps.append((_nat(origin[0]), _nat(origin[1]), _literal(step["pivot"]), _clause(step["clause"])))
    model = None if claim["model"] is None else [_literal(item) for item in _seq(claim["model"])]
    return claim["answer"], cnf, steps, model


def _decide(payload):
    claims = [_claim(c) for c in _seq(payload["claims"])]
    _require(claims, "R_SCHEMA")
    for answer, _, steps, model in claims:
        _require(steps if answer == "UNSAT" else model, "R092_FLAG_WITHOUT_PROOF")
    unsat = [(cnf, steps or []) for answer, cnf, steps, _ in claims if answer == "UNSAT"]
    derived = []
    for cnf, steps in unsat:
        available = list(cnf)
        resolvents = []
        good = True
        for i, j, pivot, _ in steps:
            if i >= len(available) or j >= len(available) or not pivot[1]:
                good = False
                break
            name = pivot[0]
            left, right = available[i], available[j]
            if (name, True) not in left or (name, False) not in right:
                good = False
                break
            resolvent = (left - {(name, True)}) | (right - {(name, False)})
            resolvents.append(resolvent)
            available.append(resolvent)
        _require(good, "R092_BAD_STEP")
        derived.append((steps, resolvents))
    for steps, resolvents in derived:
        for (_, _, _, claimed), resolvent in zip(steps, resolvents):
            _require(claimed == resolvent, "R092_RESOLVENT_MISMATCH")
    for steps, resolvents in derived:
        _require(resolvents and not resolvents[-1], "R092_NOT_REFUTATION")
    for answer, cnf, _, model in claims:
        if answer == "SAT":
            chosen = set(model or [])
            consistent = not any((name, not sign) in chosen for name, sign in chosen)
            _require(consistent and all(clause & chosen for clause in cnf), "R092_MODEL_FAILS")
