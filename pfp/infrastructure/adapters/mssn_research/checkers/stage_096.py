"""Target checker of record for MSS-096, row 96 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 96): check immutable corpus and recompute interval from
counts. Negative instance: a point estimate with no trial count is rejected.

Input (closed): ``{"corpus": [[item, content]], "corpus_digest": d,
"trials": [[item, "success" | "failure"]], "estimate": {"successes": k,
"count": n | null, "point": p, "half_width": h, "alpha": a, "interval":
[lo, hi]}}``.

The corpus is immutable when it still hashes to its digest: the SHA-256 of
its canonical JSON. Every trial names a corpus item, at most once. The counts
are recounted from the trials, and the interval is recomputed from them by a
declared exact rule: the Chebyshev interval for a proportion,
[max(0, k/n - h), min(1, k/n + h)], valid at level 1 - a exactly when
1 / (4 n h^2) <= a. Every quantity is a rational, compared exactly.

Declared input class: one binomial proportion with a Chebyshev interval.
Wilson, Clopper-Pearson and normal intervals involve roots or quantiles and
are outside the class.

Clauses, decided in this order:

- C1 ``R096_POINT_ESTIMATE_WITHOUT_COUNT``: the estimate has no trial count,
  or a zero count (the level's negative);
- C2 ``R096_CORPUS_DIGEST``: the corpus does not hash to its digest;
- C3 ``R096_TRIAL_ITEM``: a trial names no corpus item, or an item twice;
- C4 ``R096_COUNT_MISMATCH``: k, n or the point estimate differ from the
  recount;
- C5 ``R096_INTERVAL``: the interval is not the Chebyshev interval, or its
  guarantee does not reach level 1 - a.
"""

import hashlib
import json

STAGE = 96
ROW_SHA256 = "sha256:5801e6b3e2c26841013024a85daa182dcd1e006f6aee4297fa3d278a492d4f45"
FIELDS = ("corpus", "corpus_digest", "estimate", "trials")
CLAUSES = (
    ("C1", "R096_POINT_ESTIMATE_WITHOUT_COUNT"),
    ("C2", "R096_CORPUS_DIGEST"),
    ("C3", "R096_TRIAL_ITEM"),
    ("C4", "R096_COUNT_MISMATCH"),
    ("C5", "R096_INTERVAL"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()


def corpus_digest(corpus):
    text = json.dumps(corpus, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(text.encode("ascii")).hexdigest()


_NEGATIVE_CORPUS = [["c1", "case 1"], ["c2", "case 2"]]
OWN_NEGATIVE = {
    "corpus": _NEGATIVE_CORPUS,
    "corpus_digest": corpus_digest(_NEGATIVE_CORPUS),
    "estimate": {"alpha": "1/20", "count": None, "half_width": "1/2", "interval": ["1/4", "1/1"],
                 "point": "3/4", "successes": 15},
    "trials": [["c1", "success"]],
}
OWN_NEGATIVE_CODE = "R096_POINT_ESTIMATE_WITHOUT_COUNT"


def _decide(payload):
    corpus = _seq(payload["corpus"])
    items = set()
    for entry in corpus:
        _seq(entry, 2)
        _require(_text(entry[0]) not in items, "R_SCHEMA")
        items.add(entry[0])
        _text(entry[1])
    digest = _text(payload["corpus_digest"])
    trials = []
    for trial in _seq(payload["trials"]):
        _seq(trial, 2)
        _require(trial[1] in ("success", "failure"), "R_SCHEMA")
        trials.append((_text(trial[0]), trial[1]))
    estimate = payload["estimate"]
    keys = {"alpha", "count", "half_width", "interval", "point", "successes"}
    _require(isinstance(estimate, dict) and set(estimate) == keys, "R_SCHEMA")
    successes = _nat(estimate["successes"])
    point = _rat(estimate["point"])
    half, alpha = _rat(estimate["half_width"]), _rat(estimate["alpha"])
    low, high = _rats(estimate["interval"], 2)
    _require(half > 0 and 0 < alpha < 1, "R_SCHEMA")
    count = estimate["count"]
    _require(count is not None and _nat(count) > 0, "R096_POINT_ESTIMATE_WITHOUT_COUNT")
    _require(digest == corpus_digest(corpus), "R096_CORPUS_DIGEST")
    named = [item for item, _ in trials]
    _require(set(named) <= items and len(set(named)) == len(named), "R096_TRIAL_ITEM")
    k = sum(1 for _, result in trials if result == "success")
    n = len(trials)
    _require(n > 0 and (successes, count, point) == (k, n, Fraction(k, max(n, 1))), "R096_COUNT_MISMATCH")
    want = (max(Fraction(0), point - half), min(Fraction(1), point + half))
    _require((low, high) == want and 1 <= alpha * 4 * n * half * half, "R096_INTERVAL")
