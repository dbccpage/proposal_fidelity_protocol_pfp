"""Target checker of record for MSS-012, row 12 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 12): recompute bounded transition with parent digest and typed
uncertainty. Negative instance: a model-written Pass without host proof is
rejected.

Input (closed): ``{"initial": state, "transitions": [[state, action, state]],
"events": [{"before", "action", "after", "parent", "query", "budget",
"value", "digest"}]}``. The transition table is deterministic.

The host replays the chain. Each event's transition is replayed from the
previous state; its ``parent`` must be the digest of the previous event (the
first event's parent is the digest of ``{"initial": state}``); its three-valued
``value`` is recomputed by the host as a bounded reachability verdict from
``after`` to ``query`` within ``budget`` steps: ``TRUE`` (reached), ``FALSE``
(the reachable set is exhausted without reaching it), or ``UNKNOWN`` (the
budget ran out first; never "true after the budget"). ``digest`` is the
SHA-256 of the canonical bytes (sorted keys, no whitespace, ASCII) of the
event without its digest.

Clauses:

- C1 ``R012_TRANSITION_NOT_REPLAYED``: the event does not continue from the
  previous state by a table transition;
- C2 ``R012_PARENT_MISMATCH``: the parent digest is not the previous event's;
- C3 ``R012_UNPROVEN_VALUE``: the declared value differs from the host's
  (the negative: a written TRUE where the host computes UNKNOWN);
- C4 ``R012_DIGEST_MISMATCH``: the event's digest does not recompute.
"""

import hashlib
import json

STAGE = 12
ROW_SHA256 = "sha256:3819784c68b909b7d9e78a0067c02c03a37b2ca0e44285bf2ef4651b87eb1392"
FIELDS = ("events", "initial", "transitions")
CLAUSES = (
    ("C1", "R012_TRANSITION_NOT_REPLAYED"),
    ("C2", "R012_PARENT_MISMATCH"),
    ("C3", "R012_UNPROVEN_VALUE"),
    ("C4", "R012_DIGEST_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
VALUES = ("FALSE", "TRUE", "UNKNOWN")
EVENT_FIELDS = ("action", "after", "before", "budget", "digest", "parent", "query", "value")


def digest(obj):
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(text.encode("ascii")).hexdigest()


def _body(event):
    return {key: event[key] for key in EVENT_FIELDS if key != "digest"}


def _bounded(table, start, target, budget):
    frontier, seen, depth = {start}, {start}, 0
    while True:
        if target in frontier:
            return "TRUE"
        following = {after for (before, _), after in table.items() if before in frontier} - seen
        if not following:
            return "FALSE"
        if depth == budget:
            return "UNKNOWN"
        seen |= following
        frontier, depth = following, depth + 1


def _own_negative():
    parent = digest({"initial": "s0"})
    event = {"action": "a", "after": "s1", "before": "s0", "budget": 0, "parent": parent, "query": "s2", "value": "TRUE"}
    event["digest"] = digest(event)
    return {"events": [event], "initial": "s0", "transitions": [["s0", "a", "s1"], ["s1", "a", "s2"]]}


OWN_NEGATIVE = _own_negative()
OWN_NEGATIVE_CODE = "R012_UNPROVEN_VALUE"


def _decide(payload):
    initial = _text(payload["initial"])
    table = {}
    for entry in _seq(payload["transitions"]):
        _seq(entry, 3)
        before, action, after = _text(entry[0]), _text(entry[1]), _text(entry[2])
        _require((before, action) not in table, "R_SCHEMA")
        table[(before, action)] = after
    events = _seq(payload["events"])
    _require(events, "R_SCHEMA")
    parent, current = digest({"initial": initial}), initial
    for event in events:
        _require(isinstance(event, dict) and set(event) == set(EVENT_FIELDS), "R_SCHEMA")
        for key in ("action", "after", "before", "digest", "parent", "query"):
            _text(event[key])
        budget = _nat(event["budget"])
        _require(event["value"] in VALUES, "R_SCHEMA")
        replayed = event["before"] == current and table.get((event["before"], event["action"])) == event["after"]
        _require(replayed, "R012_TRANSITION_NOT_REPLAYED")
        _require(event["parent"] == parent, "R012_PARENT_MISMATCH")
        _require(event["value"] == _bounded(table, event["after"], event["query"], budget), "R012_UNPROVEN_VALUE")
        own = digest(_body(event))
        _require(event["digest"] == own, "R012_DIGEST_MISMATCH")
        parent, current = own, event["after"]
