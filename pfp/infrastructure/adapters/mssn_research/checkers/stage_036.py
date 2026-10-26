"""Target checker of record for MSS-036, row 36 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 36): check positive evidence and exact normalized posterior.
Negative instance (paraphrased): conditioning on an event of zero total
probability weight is refused.

Input (closed): ``{"hypotheses": [name], "prior": [rational],
"observations": [[rational]], "posteriors": [[rational]]}``. Each
observation is the likelihood of one observed event under each hypothesis;
the observations are applied in order, and ``posteriors[i]`` is the declared
distribution after the first i + 1 of them.

Declared input class: finitely many hypotheses, exact rational weights,
sequential updating on declared likelihood columns. The evidence and each
posterior are recomputed; no declared number is read as the answer.

Clauses, each recomputed:

- C1 ``R036_PRIOR_NOT_NORMALISED``: the prior has a negative entry or does
  not sum to 1;
- C2 ``R036_LIKELIHOOD_RANGE``: a likelihood lies outside [0, 1];
- C3 ``R036_ZERO_EVIDENCE``: the evidence of an observation (the sum of
  current weight times likelihood) is zero (the level's negative);
- C4 ``R036_POSTERIOR_MISMATCH``: a declared posterior is not current weight
  times likelihood divided by the evidence.
"""

STAGE = 36
ROW_SHA256 = "sha256:e222e1096ddb8ae0084ce07a6862a7e64fef54b92887254f39f9f9a90951f8bf"
FIELDS = ("hypotheses", "observations", "posteriors", "prior")
CLAUSES = (
    ("C1", "R036_PRIOR_NOT_NORMALISED"),
    ("C2", "R036_LIKELIHOOD_RANGE"),
    ("C3", "R036_ZERO_EVIDENCE"),
    ("C4", "R036_POSTERIOR_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "hypotheses": ["h0", "h1"],
    "observations": [["0/1", "0/1"]],
    "posteriors": [["1/2", "1/2"]],
    "prior": ["1/2", "1/2"],
}
OWN_NEGATIVE_CODE = "R036_ZERO_EVIDENCE"


def _decide(payload):
    hypotheses = [_text(h) for h in _seq(payload["hypotheses"])]
    n = len(hypotheses)
    _require(n >= 1 and len(set(hypotheses)) == n, "R_SCHEMA")
    weights = _rats(payload["prior"], n)
    observations = [_rats(o, n) for o in _seq(payload["observations"])]
    posteriors = [_rats(p, n) for p in _seq(payload["posteriors"], len(observations))]
    _require(observations, "R_SCHEMA")
    _require(all(w >= 0 for w in weights) and sum(weights, Fraction(0)) == 1, "R036_PRIOR_NOT_NORMALISED")
    for likelihood in observations:
        _require(all(0 <= x <= 1 for x in likelihood), "R036_LIKELIHOOD_RANGE")
    for likelihood, declared in zip(observations, posteriors):
        evidence = sum((w * x for w, x in zip(weights, likelihood)), Fraction(0))
        _require(evidence != 0, "R036_ZERO_EVIDENCE")
        weights = [w * x / evidence for w, x in zip(weights, likelihood)]
        _require(declared == weights, "R036_POSTERIOR_MISMATCH")
