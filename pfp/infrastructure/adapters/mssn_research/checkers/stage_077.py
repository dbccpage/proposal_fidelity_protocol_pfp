"""Target checker of record for MSS-077, row 77 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 77): check serializable conflict graph and parent digest.
Negative instance: a conflicting uncommitted write is refused.

Input (closed): ``{"base": {key: value}, "schedule": [op], "receipts":
[{"txn": t, "parent_digest": d, "digest": d}]}``. An op is ``[t, "r", key]``,
``[t, "w", key, value]``, ``[t, "c"]`` (commit) or ``[t, "a"]`` (abort); no op
of a transaction follows its commit or abort.

The checker replays the schedule. It refuses any read or write of a key whose
last write belongs to another transaction that has neither committed nor
aborted. It builds the conflict graph over the committed transactions (an edge
Ti -> Tj when an op of Ti precedes a conflicting op of Tj on the same key, at
least one of them a write) and decides its acyclicity. The receipts must list
the committed transactions exactly once each, in an order that every conflict
edge respects (a serial order). Along that order it applies each
transaction's writes to the base state; a state's digest is the SHA-256 of its
canonical JSON (sorted keys, no whitespace, ASCII), and each receipt's parent
digest must be the digest of the state before it.

Declared input class: finite read/write/commit/abort schedules over string
keys and values; conflict serializability; strictness for writes.

Clauses, decided in this order:

- C1 ``R077_UNCOMMITTED_CONFLICT``: an op touches a key last written by
  another transaction that has not committed (the level's negative);
- C2 ``R077_CONFLICT_CYCLE``: the conflict graph has a cycle;
- C3 ``R077_ORDER``: the receipts are not the committed transactions, once
  each, in an order every conflict edge respects;
- C4 ``R077_PARENT_DIGEST``: a parent digest is not the digest of the state
  before its transaction;
- C5 ``R077_STATE_DIGEST``: a digest is not the digest of the state after its
  transaction.
"""

import hashlib
import json

STAGE = 77
ROW_SHA256 = "sha256:919c0c659fa905bdaddc5cc7a04927d360f81a96106218cb4aff14035e03ffb8"
FIELDS = ("base", "receipts", "schedule")
CLAUSES = (
    ("C1", "R077_UNCOMMITTED_CONFLICT"),
    ("C2", "R077_CONFLICT_CYCLE"),
    ("C3", "R077_ORDER"),
    ("C4", "R077_PARENT_DIGEST"),
    ("C5", "R077_STATE_DIGEST"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()


def state_digest(state):
    text = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(text.encode("ascii")).hexdigest()


OWN_NEGATIVE = {
    "base": {"y": "0"},
    "receipts": [
        {"digest": state_digest({"y": "1"}), "parent_digest": state_digest({"y": "0"}), "txn": "t1"},
        {"digest": state_digest({"y": "2"}), "parent_digest": state_digest({"y": "1"}), "txn": "t2"},
    ],
    "schedule": [["t1", "w", "y", "1"], ["t2", "w", "y", "2"], ["t1", "c"], ["t2", "c"]],
}
OWN_NEGATIVE_CODE = "R077_UNCOMMITTED_CONFLICT"


def _ops(schedule):
    ops = []
    ended = set()
    for op in _seq(schedule):
        _seq(op)
        _require(len(op) >= 2, "R_SCHEMA")
        txn, kind = _text(op[0]), op[1]
        _require(txn not in ended, "R_SCHEMA")
        if kind in ("c", "a"):
            _require(len(op) == 2, "R_SCHEMA")
            ended.add(txn)
            ops.append((txn, kind, None, None))
        elif kind == "r":
            _require(len(op) == 3, "R_SCHEMA")
            ops.append((txn, kind, _text(op[2]), None))
        else:
            _require(kind == "w" and len(op) == 4, "R_SCHEMA")
            ops.append((txn, kind, _text(op[2]), _text(op[3])))
    return ops


def _decide(payload):
    base = payload["base"]
    _require(isinstance(base, dict), "R_SCHEMA")
    for key, value in base.items():
        _text(key)
        _text(value)
    ops = _ops(payload["schedule"])
    receipts = []
    for receipt in _seq(payload["receipts"]):
        _require(isinstance(receipt, dict) and set(receipt) == {"digest", "parent_digest", "txn"}, "R_SCHEMA")
        receipts.append((_text(receipt["txn"]), _text(receipt["parent_digest"]), _text(receipt["digest"])))
    # C1: strictness for writes.
    open_writer = {}
    finished = set()
    for txn, kind, key, _ in ops:
        if kind in ("c", "a"):
            finished.add(txn)
            continue
        writer = open_writer.get(key)
        _require(writer is None or writer == txn or writer in finished, "R077_UNCOMMITTED_CONFLICT")
        if kind == "w":
            open_writer[key] = txn
    committed = [txn for txn, kind, _, _ in ops if kind == "c"]
    live = set(committed)
    # C2: the conflict graph over committed transactions.
    edges = set()
    for i, (ti, ki, key_i, _) in enumerate(ops):
        if ti not in live or ki not in ("r", "w"):
            continue
        for tj, kj, key_j, _ in ops[i + 1:]:
            if tj != ti and tj in live and kj in ("r", "w") and key_j == key_i and "w" in (ki, kj):
                edges.add((ti, tj))
    remaining = set(live)
    acyclic = True
    while remaining:
        sources = [t for t in remaining if not any(a in remaining and b == t for a, b in edges)]
        if not sources:
            acyclic = False
            break
        remaining -= set(sources)
    _require(acyclic, "R077_CONFLICT_CYCLE")
    # C3: the receipts are a serial order of the committed transactions.
    order = [txn for txn, _, _ in receipts]
    _require(sorted(order) == sorted(committed) and len(set(order)) == len(order), "R077_ORDER")
    position = {txn: index for index, txn in enumerate(order)}
    _require(all(position[a] < position[b] for a, b in edges), "R077_ORDER")
    # C4, C5: the digests along the serial order.
    writes = {txn: [] for txn in live}
    for txn, kind, key, value in ops:
        if kind == "w" and txn in live:
            writes[txn].append((key, value))
    state = dict(base)
    before, after = [], []
    for txn in order:
        before.append(state_digest(state))
        for key, value in writes[txn]:
            state[key] = value
        after.append(state_digest(state))
    for (_, parent, _), want in zip(receipts, before):
        _require(parent == want, "R077_PARENT_DIGEST")
    for (_, _, got), want in zip(receipts, after):
        _require(got == want, "R077_STATE_DIGEST")
