"""Target checker of record for MSS-086, row 86 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 86): check event parents are acyclic and evidence links
resolve. Negative instance: a circular dependency without base witness is
rejected.

Input (closed): ``{"events": [[id, agent, [parent], [evidence]]],
"witnesses": [[id, content, digest]]}``. Events may be listed in any order;
the dependency graph is given by the parent lists alone. A witness's digest is
the SHA-256 of its content's UTF-8 bytes.

The checker decides acyclicity of the parent graph by repeatedly removing
events with no remaining parent, requires every root event (one with no
parent) to carry at least one evidence link (its base witness), and resolves
every evidence link to a witness whose digest recomputes.

Declared input class: finite traces of any number of agents; evidence as
content-addressed text witnesses.

Clauses, decided in this order:

- C1 ``R086_UNKNOWN_PARENT``: a parent is not an event of the trace;
- C2 ``R086_CIRCULAR``: the parent graph has a cycle (the level's negative);
- C3 ``R086_UNGROUNDED_ROOT``: a root event carries no evidence link;
- C4 ``R086_UNRESOLVED_EVIDENCE``: an evidence link names no witness;
- C5 ``R086_WITNESS_DIGEST``: a witness's digest does not hash its content.
"""

import hashlib

STAGE = 86
ROW_SHA256 = "sha256:df781350f93c259e0eeddd7b95ec571e62d8fcb276a22faa5f33d08211ceb529"
FIELDS = ("events", "witnesses")
CLAUSES = (
    ("C1", "R086_UNKNOWN_PARENT"),
    ("C2", "R086_CIRCULAR"),
    ("C3", "R086_UNGROUNDED_ROOT"),
    ("C4", "R086_UNRESOLVED_EVIDENCE"),
    ("C5", "R086_WITNESS_DIGEST"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "events": [["e1", "planner", ["e2"], []], ["e2", "coder", ["e1"], []]],
    "witnesses": [],
}
OWN_NEGATIVE_CODE = "R086_CIRCULAR"


def content_digest(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _names(value):
    out = [_text(item) for item in _seq(value)]
    _require(len(set(out)) == len(out), "R_SCHEMA")
    return out


def _decide(payload):
    events = {}
    for event in _seq(payload["events"]):
        _seq(event, 4)
        name = _text(event[0])
        _text(event[1])
        _require(name not in events, "R_SCHEMA")
        events[name] = (_names(event[2]), _names(event[3]))
    witnesses = {}
    for witness in _seq(payload["witnesses"]):
        _seq(witness, 3)
        _require(_text(witness[0]) not in witnesses, "R_SCHEMA")
        witnesses[witness[0]] = (_text(witness[1]), _text(witness[2]))
    _require(events, "R_SCHEMA")
    for parents, _ in events.values():
        _require(all(parent in events for parent in parents), "R086_UNKNOWN_PARENT")
    remaining = set(events)
    acyclic = True
    while remaining:
        free = [name for name in remaining if not any(p in remaining for p in events[name][0])]
        if not free:
            acyclic = False
            break
        remaining -= set(free)
    _require(acyclic, "R086_CIRCULAR")
    for parents, evidence in events.values():
        _require(parents or evidence, "R086_UNGROUNDED_ROOT")
    for _, evidence in events.values():
        _require(all(link in witnesses for link in evidence), "R086_UNRESOLVED_EVIDENCE")
    for content, digest in witnesses.values():
        _require(digest == content_digest(content), "R086_WITNESS_DIGEST")
