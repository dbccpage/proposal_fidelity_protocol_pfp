"""Target checker of record for MSS-039, row 39 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 39): check strategy domains and evaluate payoffs on all joint
actions. Negative instance: an undefined action profile cannot count as
equilibrium.

Input (closed): ``{"players": [name], "moves": [[player, [move]]],
"payoffs": [[[move], [rational]]], "claims": [[[move], [rational]]]}``. A
payoff row gives a joint action (one move per player, in player order) and
the payoff of every player. A claim names a joint action and the payoffs the
producer says it yields.

Declared input class: finite normal-form games with exact rational payoffs.
The checker evaluates every claimed joint action on the table; it decides no
stability property (that is stage 40's obligation).

Clauses, each recomputed:

- C1 ``R039_UNDEFINED_MOVE``: a payoff row or a claim uses a move outside the
  player's declared moves (the level's negative);
- C2 ``R039_TABLE_GAP``: some joint action of the declared moves has no
  payoff row;
- C3 ``R039_PAYOFF_MISMATCH``: a claim's payoffs are not the table's.
"""

from itertools import product

STAGE = 39
ROW_SHA256 = "sha256:cd03a40a5177bf2604c3798d886b3cc5492fcb1d0161ed2e6695dca482053fb3"
FIELDS = ("claims", "moves", "payoffs", "players")
CLAUSES = (
    ("C1", "R039_UNDEFINED_MOVE"),
    ("C2", "R039_TABLE_GAP"),
    ("C3", "R039_PAYOFF_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "claims": [[["C", "x"], ["3/1", "3/1"]]],
    "moves": [["P1", ["A", "B"]], ["P2", ["x", "y"]]],
    "payoffs": [
        [["A", "x"], ["3/1", "3/1"]], [["A", "y"], ["0/1", "5/1"]],
        [["B", "x"], ["5/1", "0/1"]], [["B", "y"], ["1/1", "1/1"]],
    ],
    "players": ["P1", "P2"],
}
OWN_NEGATIVE_CODE = "R039_UNDEFINED_MOVE"


def _profile(value, moves, players):
    profile = tuple(_text(m) for m in _seq(value, len(players)))
    _require(all(m in moves[p] for m, p in zip(profile, players)), "R039_UNDEFINED_MOVE")
    return profile


def _decide(payload):
    players = [_text(p) for p in _seq(payload["players"])]
    _require(players and len(set(players)) == len(players), "R_SCHEMA")
    moves = {}
    for entry in _seq(payload["moves"]):
        _seq(entry, 2)
        player = _text(entry[0])
        options = [_text(m) for m in _seq(entry[1])]
        _require(player in players and player not in moves and options, "R_SCHEMA")
        _require(len(set(options)) == len(options), "R_SCHEMA")
        moves[player] = set(options)
    _require(set(moves) == set(players), "R_SCHEMA")
    table = {}
    for entry in _seq(payload["payoffs"]):
        _seq(entry, 2)
        profile = _profile(entry[0], moves, players)
        _require(profile not in table, "R_SCHEMA")
        table[profile] = _rats(entry[1], len(players))
    for profile in product(*(sorted(moves[p]) for p in players)):
        _require(profile in table, "R039_TABLE_GAP")
    for entry in _seq(payload["claims"]):
        _seq(entry, 2)
        profile = _profile(entry[0], moves, players)
        _require(_rats(entry[1], len(players)) == table[profile], "R039_PAYOFF_MISMATCH")
