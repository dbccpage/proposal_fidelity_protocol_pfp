"""Target checker of record for MSS-099, row 99 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 99): replay seed and shrink without changing failure
predicate. Negative instance: a reported failure without replay seed is
quarantined.

Input (closed): ``{"generator": {"max_len": L, "max_value": V}, "seed":
s | null, "property": [name, k], "failing_input": [nat], "shrink_trace":
[[nat]]}``.

The generator is pinned in this file: a 32-bit linear congruential sequence
x' = (1664525 x + 1013904223) mod 2^32 started at the seed; the first draw
mod (L + 1) is the length, and each following draw mod (V + 1) is an element.
The properties are pinned too: ``sum_below`` k (the sum is less than k) and
``no_value`` k (k does not occur). One shrink step removes one element or
lowers one element by one. The checker replays the seed, re-evaluates the
property at every step, and requires the last list of the trace to be a local
minimum: no single shrink step from it still fails.

Declared input class: the pinned generator with L <= 32 and V <= 1000; the
two pinned properties; greedy shrinking by the two declared steps.

Clauses, decided in this order:

- C1 ``R099_NO_REPLAY_SEED``: the failure carries no seed (the level's
  negative: it is quarantined, not accepted);
- C2 ``R099_REPLAY_MISMATCH``: replaying the seed does not generate the
  reported failing input;
- C3 ``R099_NOT_A_FAILURE``: the property holds on the reported input;
- C4 ``R099_SHRINK_STEP``: a trace entry is not one shrink step from its
  predecessor, or the property holds on it (the failure predicate changed);
- C5 ``R099_NOT_SHRUNK``: some single shrink step from the last entry still
  fails.
"""

STAGE = 99
ROW_SHA256 = "sha256:bbd8ca4444942fa098cfc80308b16964d9621b166a43fca6b7fb45d3ebdc1346"
FIELDS = ("failing_input", "generator", "property", "seed", "shrink_trace")
CLAUSES = (
    ("C1", "R099_NO_REPLAY_SEED"),
    ("C2", "R099_REPLAY_MISMATCH"),
    ("C3", "R099_NOT_A_FAILURE"),
    ("C4", "R099_SHRINK_STEP"),
    ("C5", "R099_NOT_SHRUNK"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()


def generate(seed, max_len, max_value):
    state = seed % 2 ** 32

    def draw():
        nonlocal state
        state = (1664525 * state + 1013904223) % 2 ** 32
        return state

    length = draw() % (max_len + 1)
    return [draw() % (max_value + 1) for _ in range(length)]


def fails(prop, values):
    name, k = prop
    return sum(values) >= k if name == "sum_below" else k in values


def shrinks(values):
    out = [values[:i] + values[i + 1:] for i in range(len(values))]
    out += [values[:i] + [values[i] - 1] + values[i + 1:] for i in range(len(values)) if values[i] > 0]
    return out


OWN_NEGATIVE = {
    "failing_input": [9, 8, 7],
    "generator": {"max_len": 6, "max_value": 9},
    "property": ["sum_below", 20],
    "seed": None,
    "shrink_trace": [[9, 8, 3]],
}
OWN_NEGATIVE_CODE = "R099_NO_REPLAY_SEED"


def _list(value):
    return [_nat(v) for v in _seq(value)]


def _decide(payload):
    generator = payload["generator"]
    _require(isinstance(generator, dict) and set(generator) == {"max_len", "max_value"}, "R_SCHEMA")
    max_len, max_value = _nat(generator["max_len"]), _nat(generator["max_value"])
    _require(max_len <= 32 and max_value <= 1000, "R_SCHEMA")
    prop = _seq(payload["property"], 2)
    _require(prop[0] in ("sum_below", "no_value"), "R_SCHEMA")
    prop = (prop[0], _nat(prop[1]))
    failing = _list(payload["failing_input"])
    trace = [_list(entry) for entry in _seq(payload["shrink_trace"])]
    seed = payload["seed"]
    _require(seed is not None, "R099_NO_REPLAY_SEED")
    _require(generate(_nat(seed), max_len, max_value) == failing, "R099_REPLAY_MISMATCH")
    _require(fails(prop, failing), "R099_NOT_A_FAILURE")
    previous = failing
    for entry in trace:
        _require(entry in shrinks(previous) and fails(prop, entry), "R099_SHRINK_STEP")
        previous = entry
    _require(not any(fails(prop, smaller) for smaller in shrinks(previous)), "R099_NOT_SHRUNK")
