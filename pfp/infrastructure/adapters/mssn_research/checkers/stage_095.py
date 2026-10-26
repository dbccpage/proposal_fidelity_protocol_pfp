"""Target checker of record for MSS-095, row 95 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 95): check measured counters match run logs and environment.
Negative instance: a model estimated speedup is not a benchmark.

Input (closed): ``{"environment": {"implementation": tag, "counter": name},
"runs": [[procedure, input, count, log_digest]], "speedup": {"baseline": i,
"candidate": j, "ratio": r, "basis": "measured" | "estimated"}}``.

The procedures are pinned in this file and instrumented: ``insertion_sort``
and ``merge_sort`` over lists of naturals, each counting element comparisons
and logging the index pair of every comparison. The environment must name
this implementation (``IMPLEMENTATION``) and the counter ``comparisons``. The
checker reruns every procedure on its input, recounts, and recomputes the
SHA-256 of the canonical JSON of its comparison log. A speedup is the ratio of
the baseline run's count to the candidate run's count, both measured here on
the same input; a ratio stated on any other basis is refused.

Declared input class: the two pinned procedures on lists of at most 64
naturals. Wall-clock time is not measured: the counter is exact and the
environment is this file.

Clauses, decided in this order:

- C1 ``R095_ESTIMATED_SPEEDUP``: the speedup is not on the measured basis
  (the level's negative);
- C2 ``R095_ENVIRONMENT``: the environment is not this implementation and
  counter;
- C3 ``R095_COUNTER_MISMATCH``: a run's count is not the recounted one;
- C4 ``R095_LOG_MISMATCH``: a run's log digest is not the digest of its
  recomputed log;
- C5 ``R095_SPEEDUP_MISMATCH``: the two runs differ in input, or the ratio is
  not the ratio of their counts.
"""

import hashlib
import json

STAGE = 95
ROW_SHA256 = "sha256:0be42ee5ce471c2d46ce65ad2b4d019e55f1345cccae0cd6507a2653a3e0a1f7"
FIELDS = ("environment", "runs", "speedup")
CLAUSES = (
    ("C1", "R095_ESTIMATED_SPEEDUP"),
    ("C2", "R095_ENVIRONMENT"),
    ("C3", "R095_COUNTER_MISMATCH"),
    ("C4", "R095_LOG_MISMATCH"),
    ("C5", "R095_SPEEDUP_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
IMPLEMENTATION = "mss095-procedures-v1"


def insertion_sort(items):
    items, log = list(items), []
    for i in range(1, len(items)):
        j = i
        while j > 0:
            log.append([j - 1, j])
            if items[j - 1] <= items[j]:
                break
            items[j - 1], items[j] = items[j], items[j - 1]
            j -= 1
    return items, log


def merge_sort(items):
    log = []

    def sort(low, high, values):
        if high - low <= 1:
            return values[low:high]
        middle = (low + high) // 2
        left, right = sort(low, middle, values), sort(middle, high, values)
        out, i, j = [], 0, 0
        while i < len(left) and j < len(right):
            log.append([low + i, middle + j])
            if left[i] <= right[j]:
                out.append(left[i])
                i += 1
            else:
                out.append(right[j])
                j += 1
        return out + left[i:] + right[j:]

    return sort(0, len(items), list(items)), log


PROCEDURES = {"insertion_sort": insertion_sort, "merge_sort": merge_sort}


def log_digest(log):
    text = json.dumps(log, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(text.encode("ascii")).hexdigest()


def _measure(procedure, items):
    _, log = PROCEDURES[procedure](items)
    return len(log), log_digest(log)


_BASE = [5, 4, 3, 2, 1, 0]
OWN_NEGATIVE = {
    "environment": {"counter": "comparisons", "implementation": IMPLEMENTATION},
    "runs": [["insertion_sort", _BASE, len(insertion_sort(_BASE)[1]), log_digest(insertion_sort(_BASE)[1])],
             ["merge_sort", _BASE, len(merge_sort(_BASE)[1]), log_digest(merge_sort(_BASE)[1])]],
    "speedup": {"basis": "estimated", "baseline": 0, "candidate": 1, "ratio": "4/1"},
}
OWN_NEGATIVE_CODE = "R095_ESTIMATED_SPEEDUP"


def _decide(payload):
    environment = payload["environment"]
    _require(isinstance(environment, dict) and set(environment) == {"counter", "implementation"}, "R_SCHEMA")
    runs = []
    for run in _seq(payload["runs"]):
        _seq(run, 4)
        _require(run[0] in PROCEDURES, "R_SCHEMA")
        items = [_nat(v) for v in _seq(run[1])]
        _require(len(items) <= 64, "R_SCHEMA")
        runs.append((run[0], items, _nat(run[2]), _text(run[3])))
    speedup = payload["speedup"]
    _require(isinstance(speedup, dict) and set(speedup) == {"basis", "baseline", "candidate", "ratio"}, "R_SCHEMA")
    baseline, candidate = _nat(speedup["baseline"]), _nat(speedup["candidate"])
    _require(baseline < len(runs) and candidate < len(runs) and baseline != candidate, "R_SCHEMA")
    ratio = _rat(speedup["ratio"])
    _require(speedup["basis"] == "measured", "R095_ESTIMATED_SPEEDUP")
    _require(environment == {"counter": "comparisons", "implementation": IMPLEMENTATION}, "R095_ENVIRONMENT")
    measured = [_measure(procedure, items) for procedure, items, _, _ in runs]
    for (_, _, count, _), (want, _) in zip(runs, measured):
        _require(count == want, "R095_COUNTER_MISMATCH")
    for (_, _, _, digest), (_, want) in zip(runs, measured):
        _require(digest == want, "R095_LOG_MISMATCH")
    same_input = runs[baseline][1] == runs[candidate][1]
    counts = measured[baseline][0], measured[candidate][0]
    _require(same_input and counts[1] > 0 and ratio == Fraction(counts[0], max(counts[1], 1)), "R095_SPEEDUP_MISMATCH")
