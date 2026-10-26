"""Target checker of record for MSS-042, row 42 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 42): check dual endpoints and progress of finite session
automata. Negative instance: two endpoints both waiting to receive are
rejected.

Input (closed): ``{"left": endpoint, "right": endpoint}`` where an endpoint
is ``{"start": state, "final": [state], "moves": [[state, "send" |
"receive", kind, state]]}``. A joint step fires when one endpoint sends a
kind and the other receives the same kind; both move.

Declared input class: finite deterministic endpoint automata (at most one
move per state, action and kind). The joint automaton is explored breadth
first from the pair of start states; every reachable joint state is decided.
Duality is decided as compatibility on the reachable joint states: whatever
one endpoint may send there, the other can receive.

Clauses, each recomputed from the joint automaton:

- C1 ``R042_BOTH_RECEIVE``: a reachable joint state where both endpoints
  wait only to receive (the level's negative);
- C2 ``R042_UNMATCHED_SEND``: a reachable joint state where one endpoint may
  send a kind the other cannot receive there;
- C3 ``R042_STUCK``: a reachable joint state with no joint step in which the
  endpoints are not both final;
- C4 ``R042_NO_END``: no joint state in which both endpoints are final is
  reachable.
"""

STAGE = 42
ROW_SHA256 = "sha256:9f48f96467f4eab25a941226f1406fd2a2743c3af0b82f900187dfbaf8fd7c38"
FIELDS = ("left", "right")
CLAUSES = (
    ("C1", "R042_BOTH_RECEIVE"),
    ("C2", "R042_UNMATCHED_SEND"),
    ("C3", "R042_STUCK"),
    ("C4", "R042_NO_END"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "left": {"final": ["s1"], "moves": [["s0", "receive", "int", "s1"]], "start": "s0"},
    "right": {"final": ["t1"], "moves": [["t0", "receive", "int", "t1"]], "start": "t0"},
}
OWN_NEGATIVE_CODE = "R042_BOTH_RECEIVE"
ACTIONS = ("receive", "send")


def _endpoint(value):
    _require(isinstance(value, dict) and set(value) == {"final", "moves", "start"}, "R_SCHEMA")
    start = _text(value["start"])
    final = {_text(s) for s in _seq(value["final"])}
    moves = {}
    for entry in _seq(value["moves"]):
        _seq(entry, 4)
        state, action, kind, nxt = _text(entry[0]), entry[1], _text(entry[2]), _text(entry[3])
        _require(action in ACTIONS and (state, action, kind) not in moves, "R_SCHEMA")
        moves[(state, action, kind)] = nxt
    return start, final, moves


def _offers(moves, state, action):
    return {kind: nxt for (s, a, kind), nxt in moves.items() if s == state and a == action}


def _decide(payload):
    left = _endpoint(payload["left"])
    right = _endpoint(payload["right"])
    start = (left[0], right[0])
    seen, queue, ended = {start}, [start], False
    while queue:
        p, q = queue.pop(0)
        p_send, p_recv = _offers(left[2], p, "send"), _offers(left[2], p, "receive")
        q_send, q_recv = _offers(right[2], q, "send"), _offers(right[2], q, "receive")
        waiting = p_recv and q_recv and not p_send and not q_send
        _require(not waiting, "R042_BOTH_RECEIVE")
        _require(set(p_send) <= set(q_recv) and set(q_send) <= set(p_recv), "R042_UNMATCHED_SEND")
        steps = [(p_send[k], q_recv[k]) for k in p_send if k in q_recv]
        steps += [(p_recv[k], q_send[k]) for k in q_send if k in p_recv]
        both_final = p in left[1] and q in right[1]
        ended = ended or both_final
        _require(steps or both_final, "R042_STUCK")
        for step in steps:
            if step not in seen:
                seen.add(step)
                queue.append(step)
    _require(ended, "R042_NO_END")
