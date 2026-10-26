# Restatement: `stable_profiles`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two players each have a finite set of moves, and a table gives each
player's exact payoff at every joint move. A joint move claimed stable must
survive every change of one player's move alone: that player is not paid
strictly more after the change.

## Refused case

A profitable change refutes a stability claim: at `(a, x)` in the table
`(a, x) 3, 3; (a, y) 0, 5; (b, x) 5, 0; (b, y) 1, 1`, the first player is paid
5 instead of 3 by moving `b` alone.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| player, move, owns, val, pays | supplied object-language datum | the players, their moves and the exact payoffs |
| stable | supplied object-language datum | the joint moves claimed stable |
| moves_given, pays_owned, stable_owned, table_complete, one_payoff, typed | derived definition | relational requirements over the claim |
| no_gain | derived definition | the value clause, decided over exact values |
| comparison of exact payoffs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Only joint moves of single moves are claimed; mixtures
of moves are not in the declared class. The payoff reading is the joint
payoffs level's own, imported and named as a source.
