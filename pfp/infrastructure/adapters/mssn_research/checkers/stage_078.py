"""Target checker of record for MSS-078, row 78 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 78): check parent references and causal monotonicity.
Negative instance: an event referencing a future parent is rejected.

Input (closed): ``{"events": [[id, node, clock, [parent]]]}``, in log order
(the order the log appended them). Clocks are natural numbers.

Every parent must be an event of the log that was appended before the event
naming it; a clock must be strictly greater than each parent's clock; and at
each node the clocks strictly increase in log order.

Declared input class: one merged append-only log of finitely many events
with scalar clocks; no vector clocks and no clock recomputation beyond the
two monotonicity laws.

Clauses, decided in this order (each over the whole log):

- C1 ``R078_MISSING_PARENT``: a parent is not an event of the log;
- C2 ``R078_FUTURE_PARENT``: a parent is the event itself or was appended
  after it (the level's negative);
- C3 ``R078_CLOCK_NOT_MONOTONE``: an event's clock does not exceed a
  parent's clock;
- C4 ``R078_NODE_ORDER``: two events at one node do not have increasing
  clocks in log order.
"""

STAGE = 78
ROW_SHA256 = "sha256:862794dfdf2bf02beb548325a4bf006776bc8e3a377ea27dd7a15de9695fdcdf"
FIELDS = ("events",)
CLAUSES = (
    ("C1", "R078_MISSING_PARENT"),
    ("C2", "R078_FUTURE_PARENT"),
    ("C3", "R078_CLOCK_NOT_MONOTONE"),
    ("C4", "R078_NODE_ORDER"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"events": [["e1", "n1", 1, ["e2"]], ["e2", "n2", 2, []]]}
OWN_NEGATIVE_CODE = "R078_FUTURE_PARENT"


def _decide(payload):
    events = []
    for event in _seq(payload["events"]):
        _seq(event, 4)
        events.append((_text(event[0]), _text(event[1]), _nat(event[2]), [_text(p) for p in _seq(event[3])]))
    _require(events, "R_SCHEMA")
    index = {}
    for position, (name, _, _, parents) in enumerate(events):
        _require(name not in index and len(set(parents)) == len(parents), "R_SCHEMA")
        index[name] = position
    for _, _, _, parents in events:
        _require(all(parent in index for parent in parents), "R078_MISSING_PARENT")
    for position, (_, _, _, parents) in enumerate(events):
        _require(all(index[parent] < position for parent in parents), "R078_FUTURE_PARENT")
    for _, _, clock, parents in events:
        _require(all(events[index[parent]][2] < clock for parent in parents), "R078_CLOCK_NOT_MONOTONE")
    last = {}
    for _, node, clock, _ in events:
        _require(node not in last or last[node] < clock, "R078_NODE_ORDER")
        last[node] = clock
