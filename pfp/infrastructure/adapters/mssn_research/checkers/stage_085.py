"""Target checker of record for MSS-085, row 85 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 85): check delegated scope is a subset of principal scope.
Negative instance: an agent expands its own authorization is refused.

Input (closed): ``{"principal": id, "principal_scope": [permission],
"handoffs": [[from, to, [permission]]], "tasks": [[agent, permission]]}``.

Handoffs are applied in listed order. The principal holds its declared scope;
an agent holds exactly the permissions of the last handoff it received. A
handoff may only be made by a holder, and only with a subset of what the
delegator holds at that moment, so a handoff an agent makes to itself can
narrow its scope but never widen it. Every routed task must fall inside its
agent's final scope.

Declared input class: finite permission sets, exact names (no hierarchy or
implication between permissions), handoffs in one declared order.

Clauses, decided in this order:

- C1 ``R085_AUTHORITY_EXPANSION``: a handoff carries a permission its
  delegator does not hold (the level's negative, when the delegator hands
  itself more);
- C2 ``R085_UNROOTED_DELEGATOR``: a handoff is made by an agent that holds
  nothing (neither the principal nor an earlier recipient);
- C3 ``R085_TASK_OUTSIDE_SCOPE``: a routed task's permission is not in its
  agent's final scope.
"""

STAGE = 85
ROW_SHA256 = "sha256:b2d852808763892a7383b2e8bf9035cbfcad9ef4ed175086158969408174998b"
FIELDS = ("handoffs", "principal", "principal_scope", "tasks")
CLAUSES = (
    ("C1", "R085_AUTHORITY_EXPANSION"),
    ("C2", "R085_UNROOTED_DELEGATOR"),
    ("C3", "R085_TASK_OUTSIDE_SCOPE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "handoffs": [["lead", "a1", ["read"]], ["a1", "a1", ["deploy", "read"]]],
    "principal": "lead",
    "principal_scope": ["deploy", "read", "write"],
    "tasks": [["a1", "deploy"]],
}
OWN_NEGATIVE_CODE = "R085_AUTHORITY_EXPANSION"


def _perms(value):
    out = [_text(item) for item in _seq(value)]
    _require(len(set(out)) == len(out), "R_SCHEMA")
    return set(out)


def _decide(payload):
    principal = _text(payload["principal"])
    handoffs = []
    for handoff in _seq(payload["handoffs"]):
        _seq(handoff, 3)
        handoffs.append((_text(handoff[0]), _text(handoff[1]), _perms(handoff[2])))
    tasks = []
    for task in _seq(payload["tasks"]):
        _seq(task, 2)
        tasks.append((_text(task[0]), _text(task[1])))
    _require(tasks, "R_SCHEMA")

    def replay():
        held = {principal: _perms(payload["principal_scope"])}
        steps = []
        for source, target, granted in handoffs:
            steps.append((source in held, granted <= held.get(source, set())))
            if target != principal:
                held[target] = set(granted)
        return held, steps

    held, steps = replay()
    for rooted, subset in steps:
        _require(subset or not rooted, "R085_AUTHORITY_EXPANSION")
    for rooted, _ in steps:
        _require(rooted, "R085_UNROOTED_DELEGATOR")
    for agent, permission in tasks:
        _require(permission in held.get(agent, set()), "R085_TASK_OUTSIDE_SCOPE")
