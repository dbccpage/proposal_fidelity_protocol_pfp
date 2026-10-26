"""Target checker of record for MSS-040, row 40 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 40): check every unilateral deviation against declared
rational payoff. Negative instance: a profitable deviation refutes an
equilibrium claim.

Input (closed): ``{"players": [name], "moves": [[player, [move]]],
"payoffs": [[[move], [rational]]], "equilibria": [[move]]}``. The game is
written as at stage 39. Each ``equilibria`` row is a joint action claimed to
be stable: no player gains by changing only their own move.

Declared input class: finite normal-form games with exact rational payoffs
and pure-strategy claims. Mixed claims are not decided here.

Clauses, each recomputed from the table:

- C1 ``R040_TABLE_GAP``: some joint action has no payoff row, so not every
  deviation can be evaluated;
- C2 ``R040_PROFITABLE_DEVIATION``: for some claim, some player strictly gains
  by a unilateral change of move (the level's negative);
- C3 ``R040_UNDEFINED_PROFILE``: a claim or payoff row uses a move outside the
  player's declared moves.
"""

from itertools import product

STAGE = 40
ROW_SHA256 = "sha256:aff13a277e80b91c75bd78d0cf87a4415311f1698b15026a2d9f37ff49990e0b"
FIELDS = ("equilibria", "moves", "payoffs", "players")
CLAUSES = (
    ("C1", "R040_TABLE_GAP"),
    ("C2", "R040_PROFITABLE_DEVIATION"),
    ("C3", "R040_UNDEFINED_PROFILE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "equilibria": [["C", "C"]],
    "moves": [["P1", ["C", "D"]], ["P2", ["C", "D"]]],
    "payoffs": [
        [["C", "C"], ["3/1", "3/1"]], [["C", "D"], ["0/1", "5/1"]],
        [["D", "C"], ["5/1", "0/1"]], [["D", "D"], ["1/1", "1/1"]],
    ],
    "players": ["P1", "P2"],
}
OWN_NEGATIVE_CODE = "R040_PROFITABLE_DEVIATION"


def _profile(value, moves, players):
    profile = tuple(_text(m) for m in _seq(value, len(players)))
    _require(all(m in moves[p] for m, p in zip(profile, players)), "R040_UNDEFINED_PROFILE")
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
        _require(profile in table, "R040_TABLE_GAP")
    claims = [_profile(c, moves, players) for c in _seq(payload["equilibria"])]
    for claim in claims:
        for i, player in enumerate(players):
            for move in sorted(moves[player]):
                deviation = claim[:i] + (move,) + claim[i + 1:]
                _require(table[deviation][i] <= table[claim][i], "R040_PROFITABLE_DEVIATION")
