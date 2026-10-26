# Restatement: `joint_payoffs`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two players each have a finite set of moves. A table gives the exact payoff
of each player for every joint move made of their own moves. A claim that a
joint move pays given amounts is evaluated on the table.

## Refused case

A claim at a joint move that uses a move the player does not have is
refused: an undefined joint move has no payoff, and cannot be counted as
anything.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| player, move, owns | supplied object-language datum | the players and their moves |
| val, pays, claims | supplied object-language datum | the exact payoffs and the claims |
| moves_given, pays_owned, claims_owned, table_complete, one_payoff, typed | derived definition | relational requirements over the claim |
| claims_match | derived definition | the value clause, decided over exact values |
| comparison of exact payoffs | metatheory apparatus | the harness's exact arithmetic, and its Lean twin |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. Whether a joint move is stable is not decided here.
