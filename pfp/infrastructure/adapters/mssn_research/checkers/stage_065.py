"""Target checker of record for MSS-065, row 65 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 65): check commuting typed maps on a common finite carrier.
Negative instance: calling both theories equivalent without a map is
rejected.

Input (closed): ``{"source": system, "target": system, "map": [[s, t]] |
null, "back": [[t, s]] | null, "claim": "simulation" | "equivalence"}``. A
system is ``{"states": [state], "step": [[state, state]], "observe": [[state,
reading]]}``: finite states, a total deterministic step, and a total
observation. ``map`` is the producer's typed map f from source states to
target states; ``back`` is g the other way, required for an equivalence.

Declared input class: finite deterministic step systems with total
observations. Squares are checked on every state, never on an initial state
only; an equivalence needs both maps and both round trips the identity.

Clauses, decided in this order:

- C1 ``R065_NO_MAP``: no map is given (the level's negative);
- C2 ``R065_NOT_A_MAP``: the map (or the back map) is not a total function
  into the other system's states;
- C3 ``R065_STEP_SQUARE``: f(step_S(s)) != step_T(f(s)) for some s;
- C4 ``R065_OBSERVATION_SQUARE``: obs_T(f(s)) != obs_S(s) for some s;
- C5 ``R065_NOT_EQUIVALENT``: an equivalence is claimed but the back map is
  missing, fails its own squares, or a round trip is not the identity.
"""

STAGE = 65
ROW_SHA256 = "sha256:345906cb3ca750580e018517b1632d4b53ae04057cc26c495fd90b2ba1ce700e"
FIELDS = ("back", "claim", "map", "source", "target")
CLAUSES = (
    ("C1", "R065_NO_MAP"),
    ("C2", "R065_NOT_A_MAP"),
    ("C3", "R065_STEP_SQUARE"),
    ("C4", "R065_OBSERVATION_SQUARE"),
    ("C5", "R065_NOT_EQUIVALENT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "back": None,
    "claim": "equivalence",
    "map": None,
    "source": {
        "observe": [["0", "even"], ["1", "odd"], ["2", "even"], ["3", "odd"]],
        "states": ["0", "1", "2", "3"],
        "step": [["0", "1"], ["1", "2"], ["2", "3"], ["3", "0"]],
    },
    "target": {
        "observe": [["0", "even"], ["1", "odd"]],
        "states": ["0", "1"],
        "step": [["0", "1"], ["1", "0"]],
    },
}
OWN_NEGATIVE_CODE = "R065_NO_MAP"


def _table(value, keys):
    out = {}
    for item in _seq(value):
        _seq(item, 2)
        key = _text(item[0])
        _require(key in keys and key not in out, "R_SCHEMA")
        out[key] = _text(item[1])
    _require(set(out) == set(keys), "R_SCHEMA")
    return out


def _system(value):
    _require(isinstance(value, dict) and set(value) == {"observe", "states", "step"}, "R_SCHEMA")
    states = [_text(s) for s in _seq(value["states"])]
    _require(states and len(set(states)) == len(states), "R_SCHEMA")
    step = _table(value["step"], states)
    _require(all(t in states for t in step.values()), "R_SCHEMA")
    return states, step, _table(value["observe"], states)


def _map(value, keys, into):
    if value is None:
        return None
    out = {}
    for item in _seq(value):
        _require(isinstance(item, list) and len(item) == 2, "R065_NOT_A_MAP")
        _require(item[0] in keys and item[0] not in out and item[1] in into, "R065_NOT_A_MAP")
        out[item[0]] = item[1]
    _require(set(out) == set(keys), "R065_NOT_A_MAP")
    return out


def _decide(payload):
    source, target = _system(payload["source"]), _system(payload["target"])
    claim = payload["claim"]
    _require(claim in ("simulation", "equivalence"), "R_SCHEMA")
    _require(payload["map"] is not None, "R065_NO_MAP")
    f = _map(payload["map"], source[0], target[0])
    g = _map(payload["back"], target[0], source[0])
    for s in source[0]:
        _require(f[source[1][s]] == target[1][f[s]], "R065_STEP_SQUARE")
    for s in source[0]:
        _require(target[2][f[s]] == source[2][s], "R065_OBSERVATION_SQUARE")
    if claim == "equivalence":
        _require(g is not None, "R065_NOT_EQUIVALENT")
        _require(all(g[target[1][t]] == source[1][g[t]] for t in target[0]), "R065_NOT_EQUIVALENT")
        _require(all(source[2][g[t]] == target[2][t] for t in target[0]), "R065_NOT_EQUIVALENT")
        _require(all(g[f[s]] == s for s in source[0]), "R065_NOT_EQUIVALENT")
        _require(all(f[g[t]] == t for t in target[0]), "R065_NOT_EQUIVALENT")
